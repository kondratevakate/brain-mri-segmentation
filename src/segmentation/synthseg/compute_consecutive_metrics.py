#!/usr/bin/env python3
"""
Compute consecutive-session metrics (volume diff, Dice, surface Dice, HD95) for FreeSurfer/SynthSeg outputs.
Only adjacent sessions are compared (ses-001 vs ses-002, ses-002 vs ses-003, ...).

Expected file layout:
  <FREESURFER_DIR>/<subject>/<session>/mri/aparc.DKTatlas+aseg.mgz
or flat FastSurfer names like *_aparcDKT+aseg.mgz

Columns in the output CSV:
subject,session1,session2,label,label_name,structure,region_category,volume1,volume2,volume_diff,dice,surface_dice,hd95
"""

import argparse
import os
import re
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd
import surface_distance as surfdist
from nibabel import load

from src.config.regions import CORTICAL_AND_SUBCORTICAL


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freesurfer-dir", default=os.environ.get("FREESURFER_DIR", ""),
                        help="root directory with session subfolders")
    parser.add_argument("--out", required=True, help="output CSV path")
    parser.add_argument("--subjects", nargs="+", help="optional subject filter")
    parser.add_argument("--max-depth", type=int, default=None,
                        help="limit directory walk depth relative to freesurfer dir")
    parser.add_argument("--aparc-names", nargs="+",
                        default=["aparc.DKTatlas+aseg.mgz", "aparcDKT+aseg.mgz"],
                        help="filenames to treat as segmentation")
    parser.add_argument("--labels", nargs="+", type=int,
                        default=CORTICAL_AND_SUBCORTICAL,
                        help="label IDs to compute")
    parser.add_argument("--lut", help="optional CSV with columns label,label_name,structure,region_category")
    return parser.parse_args()


def load_lut(path: str):
    if not path:
        return {}
    df = pd.read_csv(path)
    lut = {}
    for _, row in df.iterrows():
        lut[int(row["label"])] = {
            "label_name": row.get("label_name"),
            "structure": row.get("structure"),
            "region_category": row.get("region_category"),
        }
    return lut


def find_segmentations(root: str, aparc_names, max_depth=None, subject_filter=None):
    root = Path(root)
    base_depth = len(root.parts)
    found = []
    for dirpath, dirs, files in os.walk(root):
        if max_depth is not None:
            depth = len(Path(dirpath).parts) - base_depth
            if depth >= max_depth:
                dirs[:] = []
        for f in files:
            if f in aparc_names or f.endswith("_aparcDKT+aseg.mgz"):
                full = Path(dirpath) / f
                # try to derive subject/session from path or flat name
                run_dir = full.parent.parent.name   # e.g., ses-001 or sub-01_ses-siteATV
                parent_dir = full.parent.parent.parent.name if len(full.parts) >= 4 else ""
                session = run_dir
                if run_dir.startswith("ses-"):
                    # SIMON long layout under root
                    subject = "long.simonBase_all_2025"
                elif run_dir.startswith("sub-"):
                    subject = run_dir.split("_ses-")[0]
                else:
                    subject = parent_dir
                # flat FastSurfer: sub-01_ses-XXX_aparcDKT+aseg.mgz
                m = re.match(r"(sub-[^_]+)_(ses-[^_]+)_aparcDKT\+aseg\.mgz", full.name)
                if m:
                    subject, session = m.group(1), m.group(2)
                if subject_filter and subject not in subject_filter:
                    continue
                found.append((subject, session, full))
    return found


def session_sort_key(session: str):
    """Robust sort key: parse ses-XXX numbers; otherwise fall back to string form."""
    s = str(session)
    m = re.search(r"ses-([0-9]+)", s)
    if m:
        try:
            return (0, int(m.group(1)))
        except ValueError:
            return (1, s)
    return (1, s)


def compute_metrics(path1: Path, path2: Path, labels):
    img1, img2 = load(path1), load(path2)
    d1, d2 = img1.get_fdata(), img2.get_fdata()
    if d1.shape != d2.shape:
        return None  # skip mismatched shapes
    spacing = img1.header.get_zooms()
    rows = []
    for lbl in labels:
        m1 = d1 == lbl
        m2 = d2 == lbl
        vol1 = np.sum(m1) * np.prod(spacing)
        vol2 = np.sum(m2) * np.prod(spacing)
        sd = surfdist.compute_surface_distances(m1, m2, spacing_mm=spacing)
        rows.append({
            "label": int(lbl),
            "volume1": vol1,
            "volume2": vol2,
            "volume_diff": vol2 - vol1,
            "dice": (2 * (m1 & m2).sum() / (m1.sum() + m2.sum())) if (m1.sum() + m2.sum()) else np.nan,
            "surface_dice": surfdist.compute_surface_dice_at_tolerance(sd, tolerance_mm=1.0),
            "hd95": surfdist.compute_robust_hausdorff(sd, percent=95),
        })
    return rows


def main():
    args = parse_args()
    if not args.freesurfer_dir:
        raise SystemExit("Specify --freesurfer-dir or set FREESURFER_DIR")
    lut = load_lut(args.lut)

    segs = find_segmentations(args.freesurfer_dir, args.aparc_names, args.max_depth, args.subjects)
    if not segs:
        raise SystemExit("No segmentation files found")
    by_subj = {}
    for subj, sess, path in segs:
        by_subj.setdefault(subj, {})[sess] = path

    rows = []
    for subj, sessions in by_subj.items():
        ses_sorted = sorted(sessions.keys(), key=session_sort_key)
        for s1, s2 in pairwise(ses_sorted):
            res = compute_metrics(sessions[s1], sessions[s2], args.labels)
            if res is None:
                print(f"Skipping {s1} vs {s2} (shape mismatch)")
                continue
            for r in res:
                r.update({"subject": subj, "session1": s1, "session2": s2})
                meta = lut.get(r["label"], {})
                r["label_name"] = meta.get("label_name")
                r["structure"] = meta.get("structure")
                r["region_category"] = meta.get("region_category")
                rows.append(r)
        print(f"{subj}: {len(ses_sorted)} sessions -> {max(len(ses_sorted)-1,0)} consecutive pairs")

    if not rows:
        raise SystemExit("No rows computed")
    df = pd.DataFrame(rows, columns=[
        "subject","session1","session2","label","label_name","structure","region_category",
        "volume1","volume2","volume_diff","dice","surface_dice","hd95"
    ])
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows -> {out_path}")


if __name__ == "__main__":
    main()
