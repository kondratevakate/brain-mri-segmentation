"""
Configuration file for second dataset
"""

from pathlib import Path

# Base directories
ATLAS_DIR = Path('/mnt/d/YandexDisk/kondratevakate/01_insidekatesbrain/brain-mri-segmentation/src/preprocessing/utils/mni_icbm152_t1_tal_nlin_asym_09c.nii')
BASE_DIR = ATLAS_DIR.parent

# Registration paths
PROCESSED_FILES_DIR = Path('/mnt/d/data/fastserfer_second_dataset')  # Путь к директории с вашими данными
REGISTERED_FILES_DIR = Path('/mnt/d/data/registration/second_dataset')  # Путь для сохранения результатов

# File names
FREESURFER_FILES = {
    "ORIG": "orig.mgz",
    "APARC": "aparc.DKTatlas+aseg.mgz",
    "APARC_REGISTERED": "aparc.DKTatlas+aseg.mgz"
}

# FreeSurfer specific paths
FREESURFER_APARC_FILE = "aparc.DKTatlas+aseg.mgz"

# Jupyter notebook paths
JUPYTER_DATA_DIR = Path(r"D:\data\registration\second_dataset")  # Путь для Jupyter ноутбука 