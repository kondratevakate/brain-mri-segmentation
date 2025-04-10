import os
import numpy as np
import pandas as pd
from nibabel import load
from scipy import stats
import sys
from itertools import combinations
import surface_distance as surfdist
from tqdm import tqdm
sys.path.append('/mnt/mydisk/brain_mri_segmentation')
from brain_mri_segmentation.src.config.paths import (
    FREESURFER_DIR,
    FREESURFER_APARC_FILE,
    RESULTS_DIR,
    VOLUME_ANALYSIS_CSV,
    VOLUME_CHANGES_PLOT
)

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

def process_subject(subject, sessions):
    """Process a single subject."""
    results = []
    session_list = sorted(sessions.keys())
    
    # Process each pair of sessions
    for ses1, ses2 in combinations(session_list, 2):
        session_results = process_session_pair(sessions, ses1, ses2)
        for result in session_results:
            result['subject'] = subject
        results.extend(session_results)
    
    return results

def calculate_session_metrics():
    print("Starting session metrics calculation...")
    
    # Create results directory if it doesn't exist
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Find all aparc.DKTatlas+aseg.mgz files
    print("Searching for FreeSurfer files...")
    dkt_files = []
    for root, dirs, files in os.walk(FREESURFER_DIR):
        for file in files:
            if file == FREESURFER_APARC_FILE:
                dkt_files.append(os.path.join(root, file))
    
    print(f"Found {len(dkt_files)} files")
    
    # Group files by subject
    print("Grouping files by subject...")
    subject_files = {}
    for dkt_file in dkt_files:
        path_parts = dkt_file.split('/')
        subject = path_parts[-4]
        session = path_parts[-3]
        
        if subject not in subject_files:
            subject_files[subject] = {}
        subject_files[subject][session] = dkt_file
    
    print(f"Found {len(subject_files)} subjects")
    
    # Process subjects sequentially
    print("Processing subjects...")
    all_results = []
    for subject, sessions in tqdm(subject_files.items(), desc="Processing subjects"):
        results = process_subject(subject, sessions)
        all_results.extend(results)
    
    # Create DataFrame and save results
    print("Saving results...")
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(os.path.join(RESULTS_DIR, 'session_metrics.csv'), index=False)
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("\nVolume Differences:")
    print(results_df.groupby('label')['volume_diff'].describe())
    
    print("\nDice Coefficients:")
    print(results_df.groupby('label')['dice'].describe())
    
    print("\nSurface Dice Coefficients:")
    print(results_df.groupby('label')['surface_dice'].describe())
    
    print("\nHD95 (mm):")
    print(results_df.groupby('label')['hd95'].describe())
    
    print(f"\nResults saved to {os.path.join(RESULTS_DIR, 'session_metrics.csv')}")

if __name__ == "__main__":
    calculate_session_metrics() 