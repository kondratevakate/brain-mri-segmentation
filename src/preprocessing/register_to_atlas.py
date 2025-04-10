import ants
import os
import glob
from pathlib import Path
import sys

# Добавляем путь к корню проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.paths import (
    BASE_DIR,
    PROCESSED_FILES_DIR,
    REGISTERED_FILES_DIR,
    ATLAS_DIR,
    FREESURFER_FILES
)

def register_to_atlas(atlas_path, moving_image_path, aseg_path, output_dir):
    """
    Registers aseg file to atlas using nearest neighbor interpolation

    https://nist.mni.mcgill.ca/icbm-152-nonlinear-atlases-2009/
    mni_icbm152_t1_tal_nlin_asym_09c.nii

    Args:
        atlas_path: path to atlas image
        moving_image_path: path to moving image
        aseg_path: path to aseg file
        output_dir: directory to save results
        
    Returns:
        Path to registered aseg file
    """
    # Load images
    atlas = ants.image_read(str(atlas_path))
    moving_image = ants.image_read(str(moving_image_path))
    aseg = ants.image_read(str(aseg_path))
    
    # Register
    transform = ants.registration(
        fixed=atlas,
        moving=moving_image,
        type_of_transform='Rigid'
    )
    
    # Apply transformation to aseg with nearest neighbor interpolation
    registered_aseg = ants.apply_transforms(
        fixed=atlas,
        moving=aseg,
        transformlist=transform['fwdtransforms'],
        interpolator='multiLabel'
    )
    
    # Save results
    output_path = output_dir / FREESURFER_FILES['APARC_REGISTERED']
    ants.image_write(registered_aseg, str(output_path))
    
    return output_path

def process_all_sessions(atlas_path, input_dir, output_dir):
    """
    Process all sessions in input directory
    
    Args:
        atlas_path: path to atlas image
        input_dir: directory with sessions
        output_dir: directory to save results
    """
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get list of all sessions
    sessions = sorted(glob.glob(str(Path(input_dir) / 'ses-*/')))
    
    if not sessions:
        raise ValueError(f"No sessions found in directory {input_dir}")
    
    # Process each session
    for session in sessions:
        session_name = Path(session).name
        print(f"Processing {session_name}...")
        
        # Create session output directory
        session_output_dir = output_dir / session_name 
        session_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Paths for current session
        orig_path = Path(session) / FREESURFER_FILES['ORIG']
        aseg_path = Path(session) / FREESURFER_FILES['APARC']
        
        # Register to atlas
        try:
            registered_path = register_to_atlas(
                atlas_path,
                orig_path,
                aseg_path,
                session_output_dir
            )
            print(f"Successfully registered {session_name} to atlas")
        except Exception as e:
            print(f"Error processing {session_name}: {str(e)}")
            continue

def main():
    """
    Script entry point
    """
    # Paths
    atlas_path = ATLAS_DIR
    input_dir = PROCESSED_FILES_DIR
    output_dir = REGISTERED_FILES_DIR
    
    try:
        process_all_sessions(atlas_path, input_dir, output_dir)
        print("Registration to atlas completed successfully")
    except Exception as e:
        print(f"Error during registration: {str(e)}")
        raise

if __name__ == "__main__":
    main() 