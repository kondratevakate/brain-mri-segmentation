import os
import logging
import shutil
import numpy as np
import nibabel as nib
from pathlib import Path
import ants
import sys
import glob
# Add project root to PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.labels import LABELS, PROCESS_LABELS
from src.config.paths import (
    ATLAS_DIR,
    PROCESSED_FILES_DIR,
    REGISTERED_FILES_DIR,
    FREESURFER_FILES
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_label(aseg_path, label):
    """
    Extract single label from aseg file and create binary mask
    """
    # Load aseg file
    aseg_img = nib.load(aseg_path)
    aseg_data = aseg_img.get_fdata()
    
    # Create binary mask for label
    mask = (aseg_data == label).astype(np.float32)
    
    # Create new NIfTI file
    mask_img = nib.Nifti1Image(mask, aseg_img.affine, aseg_img.header)
    return mask_img

def compute_session_transform(atlas_path, aseg_path, first_label, output_dir):
    """
    Compute transformation matrix for the session using first label
    """
    # Extract first label
    mask_img = extract_label(aseg_path, first_label)
    mask_path = output_dir / f"{first_label}_mask.nii.gz"
    nib.save(mask_img, mask_path)
    
    # Load images
    atlas = ants.image_read(str(atlas_path))
    mask = ants.image_read(str(mask_path))
    
    # Compute transform
    transform = ants.registration(
        fixed=atlas,
        moving=mask,
        type_of_transform='Rigid'
    )
    
    # Save transform matrix
    transform_path = output_dir / "atlas_transform.mat"
    shutil.copy(transform['fwdtransforms'][0], transform_path)
    
    return transform_path

def register_label(atlas_path, aseg_path, label, transform_path, output_dir):
    """
    Register single label using precomputed transform
    """
    # Extract label
    mask_img = extract_label(aseg_path, label)
    mask_path = output_dir / f"{label}_mask.nii.gz"
    nib.save(mask_img, mask_path)
    
    # Load images
    atlas = ants.image_read(str(atlas_path))
    mask = ants.image_read(str(mask_path))
    
    # Apply transform
    registered_mask = ants.apply_transforms(
        fixed=atlas,
        moving=mask,
        transformlist=[str(transform_path)],
        interpolator='nearestNeighbor'
    )
    
    # Round values to 0 and 1
    registered_data = registered_mask.numpy()
    registered_data = np.round(registered_data)
    registered_data = np.clip(registered_data, 0, 1)
    
    # Save result
    registered_mask = ants.from_numpy(registered_data, 
                                     origin=registered_mask.origin,
                                     spacing=registered_mask.spacing,
                                     direction=registered_mask.direction)
    output_path = output_dir / f"{label}.mgz"
    ants.image_write(registered_mask, str(output_path))
    
    return output_path

def process_session(atlas_path, aseg_path, labels, output_dir):
    """
    Process all labels for a single session
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    transform_path = output_dir / "atlas_transform.mat"
    
    # Compute transform if not exists
    if not transform_path.exists():
        logger.info("Computing session transform")
        first_label = LABELS[labels[0]]
        transform_path = compute_session_transform(atlas_path, aseg_path, first_label, output_dir)
    
    # Process all labels
    results = {}
    for label_name in labels:
        label_value = LABELS[label_name]
        try:
            logger.info(f"Processing label {label_name} ({label_value})")
            result_path = register_label(atlas_path, aseg_path, label_value, transform_path, output_dir)
            results[label_name] = result_path
            logger.info(f"Label {label_name} processed successfully")
        except Exception as e:
            logger.error(f"Error processing label {label_name}: {str(e)}")
            continue
    
    return results

def main():
    # Paths
    atlas_path = ATLAS_DIR
    output_base_dir = REGISTERED_FILES_DIR 
    
    # Get all sessions
    sessions = sorted(glob.glob(str(Path(PROCESSED_FILES_DIR) / 'ses-*/')))
    
    if not sessions:
        raise ValueError(f"No session found in {PROCESSED_FILES_DIR}")
    
    for session in sessions:
        session_name = Path(session).name
        logger.info(f"Processing session {session_name}")
        
        # Create output directory for session
        session_output_dir = output_base_dir / session_name
        session_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Path to aseg file for current session
        aseg_path = Path(session) / FREESURFER_FILES['APARC']
        
        try:
            results = process_session(atlas_path, aseg_path, PROCESS_LABELS, session_output_dir)
            logger.info(f"Registration of labels for {session_name} completed")
            logger.info(f"Results saved in {session_output_dir}")
        except Exception as e:
            logger.error(f"Error processing session {session_name}: {str(e)}")
            continue
    
    logger.info("Processing all sessions completed")

if __name__ == "__main__":
    main() 