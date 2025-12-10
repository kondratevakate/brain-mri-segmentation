import os
import numpy as np
import pandas as pd
from nibabel import load
from scipy import stats
import sys
from itertools import combinations
import surface_distance as surfdist
from tqdm import tqdm
import argparse
from pathlib import Path
from src.config.paths_srpbs import FREESURFER_APARC_FILE

FREESURFER_DIR = os.environ.get("FREESURFER_DIR", "/mnt/freesurfer_data/fs_longitudinal")
RESULTS_DIR = os.environ.get("RESULTS_DIR", "./data")
RESULTS_PATH = Path(RESULTS_DIR) / "session_metrics.csv"
VOLUME_ANALYSIS_CSV = "session_metrics.csv"
VOLUME_CHANGES_PLOT = "volume_changes.png"



def is_long_path(path: str) -> bool:
    # parent of mri/ is the session/subject folder, e.g. ses-001.long.base...
    parts = Path(path).parts
    if len(parts) < 3:
        return False
    run_dir = parts[-3]
    return ".long." in run_dir

import re

def parse_subject_session(run_dir: str):
    # run_dir examples:
    #  - sub-01_ses-siteATV.long.sub01_base_all_sites
    #  - ses-017.long.simonBase_all_2025
    if run_dir.startswith("sub-"):
        subject = run_dir.split("_")[0]           # sub-01
        session = run_dir
    elif run_dir.startswith("ses-"):
        subject = "simon"                        # group all SIMON sessions under one subject
        session = run_dir
    else:
        subject = run_dir.split(".long.")[0]
        session = run_dir
    return subject, session


def compute_surface_distances(mask_gt, mask_pred, spacing):
    """Compute surface distances between two masks."""
    from scipy import ndimage
    
    # Get surface points using faster operations
    surface_gt = ndimage.binary_erosion(mask_gt) != mask_gt
    surface_pred = ndimage.binary_erosion(mask_pred) != mask_pred
    
    # Get coordinates of surface points
    gt_points = np.array(np.where(surface_gt)).T
    pred_points = np.array(np.where(surface_pred)).T
    
    if len(gt_points) == 0 or len(pred_points) == 0:
        return None
    
    # Scale points by spacing
    gt_points = gt_points * np.array(spacing)
    pred_points = pred_points * np.array(spacing)
    
    # Compute distances using vectorized operations
    gt_points_expanded = gt_points[:, np.newaxis, :]
    pred_points_expanded = pred_points[np.newaxis, :, :]
    
    distances_matrix = np.sqrt(np.sum((gt_points_expanded - pred_points_expanded)**2, axis=2))
    
    distances_gt_to_pred = np.min(distances_matrix, axis=1)
    distances_pred_to_gt = np.min(distances_matrix, axis=0)
    
    return {
        "distances_gt_to_pred": distances_gt_to_pred,
        "distances_pred_to_gt": distances_pred_to_gt,
        "surfel_areas_gt": np.ones(len(distances_gt_to_pred)),
        "surfel_areas_pred": np.ones(len(distances_pred_to_gt))
    }

def compute_surface_dice(surface_distances, tolerance_mm):
    """Compute surface DICE coefficient at specified tolerance."""
    if surface_distances is None:
        return 0.0
        
    distances_gt_to_pred = surface_distances["distances_gt_to_pred"]
    distances_pred_to_gt = surface_distances["distances_pred_to_gt"]
    surfel_areas_gt = surface_distances["surfel_areas_gt"]
    surfel_areas_pred = surface_distances["surfel_areas_pred"]
    
    overlap_gt = np.sum(surfel_areas_gt[distances_gt_to_pred <= tolerance_mm])
    overlap_pred = np.sum(surfel_areas_pred[distances_pred_to_gt <= tolerance_mm])
    
    surface_dice = (overlap_gt + overlap_pred) / (np.sum(surfel_areas_gt) + np.sum(surfel_areas_pred))
    return surface_dice

def compute_dice_coefficient(mask_gt, mask_pred):
    """Compute Dice coefficient between two masks."""
    volume_sum = mask_gt.sum() + mask_pred.sum()
    if volume_sum == 0:
        return np.nan
    volume_intersect = (mask_gt & mask_pred).sum()
    return 2 * volume_intersect / volume_sum

def process_session_pair(sessions_data, ses1, ses2):
    """Process a single pair of sessions."""
    results = []
    
    # Load images
    img1 = load(sessions_data[ses1])
    img2 = load(sessions_data[ses2])
    
    data1 = img1.get_fdata()
    data2 = img2.get_fdata()
    spacing = img1.header.get_zooms()
    
    # Get unique labels
    unique_labels = np.unique(np.concatenate([data1, data2]))
    unique_labels = unique_labels[unique_labels != 0]  # Remove background
    
    # Calculate metrics for each label
    for label in unique_labels:
        mask1 = data1 == label
        mask2 = data2 == label
        
        # Calculate volume differences
        vol1 = np.sum(mask1) * np.prod(spacing)
        vol2 = np.sum(mask2) * np.prod(spacing)
        vol_diff = vol2 - vol1
        
        # Calculate Dice coefficient
        dice = compute_dice_coefficient(mask1, mask2)
        
        # Calculate surface distances and surface Dice using surface-distance package
        surface_distances = surfdist.compute_surface_distances(mask1, mask2, spacing_mm=spacing)
        surface_dice = surfdist.compute_surface_dice_at_tolerance(surface_distances, tolerance_mm=1.0)
        
        # Calculate HD95
        hd95 = surfdist.compute_robust_hausdorff(surface_distances, percent=95)
        
        # Store results
        results.append({
            'session1': ses1,
            'session2': ses2,
            'label': int(label),
            'volume1': vol1,
            'volume2': vol2,
            'volume_diff': vol_diff,
            'dice': dice,
            'surface_dice': surface_dice,
            'hd95': hd95
        })
    
    return results

def process_subject(subject, sessions, writer, chunk_size=5):
    """Process a single subject, flushing results in chunks."""
    session_list = sorted(sessions.keys())
    session_pairs = list(combinations(session_list, 2))
    print(f"Processing {subject}: {len(session_list)} sessions, {len(session_pairs)} pairs")

    buffer = []
    for idx, (ses1, ses2) in enumerate(session_pairs, 1):
        session_results = process_session_pair(sessions, ses1, ses2)
        for result in session_results:
            result['subject'] = subject
        buffer.extend(session_results)

        if len(buffer) >= chunk_size:
            writer(buffer)
            print(f"  {subject}: wrote {len(buffer)} rows at pair {idx}/{len(session_pairs)}")
            buffer.clear()

    if buffer:
        writer(buffer)
        print(f"  {subject}: wrote final {len(buffer)} rows")

def calculate_session_metrics():
    parser = argparse.ArgumentParser()
    parser.add_argument("--long-only", action="store_true",
                        help="process only sessions whose directory name contains '.long.'")
    parser.add_argument("--subjects", nargs="+", help="filter to specific subjects")
    parser.add_argument("--out", help="output CSV path (default: RESULTS_DIR/session_metrics.csv)")
    parser.add_argument("--chunk-size", type=int, default=5,
                        help="write out every N rows to make progress visible")
    args = parser.parse_args()

    results_path = Path(args.out) if args.out else Path(RESULTS_PATH)

    print("Starting session metrics calculation...")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    print("Searching for FreeSurfer files...")
    dkt_files = []
    for root, dirs, files in os.walk(FREESURFER_DIR):
        for file in files:
            if file == FREESURFER_APARC_FILE:
                full = os.path.join(root, file)
                if args.long_only and not is_long_path(full):
                    continue
                dkt_files.append(full)

    subject_files = {}
    for dkt_file in dkt_files:
        run_dir = Path(dkt_file).parent.parent.name
        subject, session = parse_subject_session(run_dir)
        if args.subjects and subject not in args.subjects:
            continue
        subject_files.setdefault(subject, {})[session] = dkt_file

    print(f"Found {len(dkt_files)} files" + (" (long-only)" if args.long_only else ""))
    print(f"Found {len(subject_files)} subjects")

    
    # Process subjects sequentially
    print("Processing subjects...")
    header_written = results_path.exists()

    def writer(rows):
        nonlocal header_written
        if not rows:
            return
        df = pd.DataFrame(rows)
        df.to_csv(results_path, mode="a", header=not header_written, index=False)
        header_written = True

    for subject, sessions in tqdm(subject_files.items(), desc="Processing subjects"):
        if not sessions:
            continue
        process_subject(subject, sessions, writer, chunk_size=args.chunk_size)
    
    if not results_path.exists():
        print("No results written.")
        return
    print(f"\nResults saved to {results_path}")

if __name__ == "__main__":
    calculate_session_metrics() 
