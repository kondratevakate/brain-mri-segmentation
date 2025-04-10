"""
Configuration file for directory paths
"""

from pathlib import Path

# Base directories
BASE_DIR = Path('/mnt/mydisk')

# Registration paths
PROCESSED_FILES_DIR = BASE_DIR / 'simon_data'
REGISTERED_FILES_DIR = BASE_DIR / 'simon_registered_mni_nn'
ATLAS_DIR = BASE_DIR / 'atlas/mni_icbm152_nlin_asym_09c/mni_icbm152_t1_tal_nlin_asym_09c.nii'
# ATLAS_DIR = '/mnt/mydisk/simon_data/ses-001/orig.mgz'



# File names
FREESURFER_FILES = {
    "ORIG": "orig.mgz",
    "APARC": "aparc.DKTatlas+aseg.mgz",
    "APARC_REGISTERED": "aparc.DKTatlas+aseg.mgz"
}

# Output files
OUTPUT_FILES = {
    "VOLUME_ANALYSIS": "volume_analysis_results.csv",
    "VOLUME_CHANGES": "volume_changes.png"
}

# FreeSurfer specific paths
FREESURFER_APARC_FILE = "aparc.DKTatlas+aseg.mgz"

