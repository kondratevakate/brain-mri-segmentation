import ants
import os
import glob
import shutil
from pathlib import Path
import sys

# Add project root to PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent.parent))

def find_matching_file(base_path, patterns):
    """
    Find file by given patterns in directory and its subdirectories
    
    Args:
        base_path: base directory for search
        patterns: list of patterns to search for files
        
    Returns:
        Path: path to found file
    """
    # First search in root directory
    for pattern in patterns:
        for file in base_path.glob(pattern):
            return file
            
    # Then in mri subdirectory
    mri_dir = base_path / 'mri'
    if mri_dir.exists():
        for pattern in patterns:
            for file in mri_dir.glob(pattern):
                return file
                
    # Finally recursive search
    for pattern in patterns:
        for path in base_path.rglob(pattern):
            return path
            
    raise FileNotFoundError(f"Could not find file matching patterns {patterns} in {base_path}")

def register_to_template(template_path, moving_image_path, aseg_path, output_dir):
    """
    Registers aseg file to template using nearest neighbor interpolation
    
    Args:
        template_path: path to template image (from first session)
        moving_image_path: path to moving image
        aseg_path: path to aseg file
        output_dir: directory to save results
    """
    print("\nRegistration paths:")
    print(f"Template path: {template_path}")
    print(f"Moving image path: {moving_image_path}")
    print(f"Aseg path: {aseg_path}")
    print(f"Output directory: {output_dir}")
    
    # Load images
    template = ants.image_read(str(template_path))
    moving_image = ants.image_read(str(moving_image_path))
    aseg = ants.image_read(str(aseg_path))
    
    # Register
    transform = ants.registration(
        fixed=template,
        moving=moving_image,
        type_of_transform='Rigid'
    )
    
    # Apply transformation to aseg with nearest neighbor interpolation
    registered_aseg = ants.apply_transforms(
        fixed=template,
        moving=aseg,
        transformlist=transform['fwdtransforms'],
        interpolator='genericLabel'
    )
    
    # Save results
    output_path = output_dir / 'aparc.DKTatlas+aseg.registered.mgz'
    ants.image_write(registered_aseg, str(output_path))
    print(f"Saved registered file to: {output_path}")
    
    return output_path

def copy_template_session(session_dir, output_dir):
    """
    Copy template session files without changes
    
    Args:
        session_dir: path to template session directory
        output_dir: path to output directory
    """
    session_name = Path(session_dir).name
    print(f"Copying template session {session_name}...")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find and copy aseg file
    aseg_path = find_matching_file(session_dir, ['*aparc.DKTatlas+aseg.mgz', '*aparcDKT+aseg.mgz', '*aseg.mgz'])
    output_path = output_dir / 'aparc.DKTatlas+aseg.registered.mgz'
    shutil.copy2(aseg_path, output_path)
    print(f"Saved template file to: {output_path}")

def process_session(session_dir, template_path, output_base_dir, aseg_path):
    """
    Process a single session
    
    Args:
        session_dir: path to session directory
        template_path: path to template image (from first session)
        output_base_dir: base directory for outputs
        aseg_path: path to aseg file
    """
    # Get session name from aseg filename (format: sub-01_ses-siteATV)
    session_name = aseg_path.stem.split('_aparcDKT+aseg')[0]
    print(f"\nProcessing session: {session_name}")
    print(f"Template path: {template_path}")
    print(f"Aseg path: {aseg_path}")
    
    # Create output directory
    output_dir = output_base_dir / session_name
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    try:
        # Find orig file for current session using session name in pattern
        session_pattern = f"*{session_name}*orig.mgz"
        moving_image_path = find_matching_file(session_dir, [session_pattern, f"*{session_name}*T1w.mgz", f"*{session_name}*T1.mgz"])
        if not moving_image_path:
            raise FileNotFoundError(f"Could not find orig file for session {session_name}")
        
        # Verify that moving image and aseg belong to the same session
        moving_session = moving_image_path.stem.split('_aparcDKT+aseg')[0]
        aseg_session = aseg_path.stem.split('_aparcDKT+aseg')[0]
        
        print("\nSession verification:")
        print(f"Moving image session: {moving_session}")
        print(f"Aseg session: {aseg_session}")
        print(f"Expected session: {session_name}")
        
        if moving_session != session_name or aseg_session != session_name:
            raise ValueError(f"Session mismatch! Moving image belongs to {moving_session}, Aseg belongs to {aseg_session}, expected {session_name}")
            
        print(f"Moving image path: {moving_image_path}")
        
        registered_path = register_to_template(
            template_path,  # Use orig file from template session
            moving_image_path,  # Use orig file from current session
            aseg_path,
            output_dir
        )
        print(f"Successfully registered {session_name} to template")
        print(f"Registered file saved to: {registered_path}")
    except Exception as e:
        print(f"Error processing {session_name}: {str(e)}")

def main():
    """
    Script entry point
    """
    from src.config.paths_second_dataset import PROCESSED_FILES_DIR, REGISTERED_FILES_DIR
    input_dir = PROCESSED_FILES_DIR
    output_base_dir = REGISTERED_FILES_DIR
    
    # Create output directory
    output_base_dir.mkdir(parents=True, exist_ok=True)
    print(f"Base output directory: {output_base_dir}")
    
    # Get list of all aseg files
    aseg_files = sorted(glob.glob(str(input_dir / '*aparcDKT+aseg.mgz')))
    if not aseg_files:
        print(f"No aseg files found in directory {input_dir}")
        return
    
    print(f"\nFound {len(aseg_files)} aseg files")
    
    # Group files by sessions
    sessions = {}
    for aseg_file in aseg_files:
        aseg_path = Path(aseg_file)
        session_name = aseg_path.stem.split('_aparcDKT+aseg')[0]
        if session_name not in sessions:
            sessions[session_name] = (aseg_path.parent, aseg_path)
            print(f"Found session: {session_name}")
    
    if not sessions:
        print("No valid sessions found")
        return
    
    print(f"\nFound {len(sessions)} unique sessions")
    
    # Use first session as template
    template_session = list(sessions.keys())[0]
    template_dir, template_aseg = sessions[template_session]
    
    # Find orig file for template
    try:
        template_path = find_matching_file(template_dir, ['*orig.mgz', '*T1w.mgz', '*T1.mgz'])
        print(f"\nUsing {template_session} as template")
        print(f"Template orig file: {template_path}")
        print(f"Template aseg file: {template_aseg}")
    except FileNotFoundError:
        print(f"Error: Could not find orig file for template session {template_session}")
        return
    
    # Create output directory for template
    template_output_dir = output_base_dir / template_session
    template_output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Template output directory: {template_output_dir}")
    
    # Copy template session without changes
    copy_template_session(template_dir, template_output_dir)
    
    # Process all other sessions
    for session_name, (session_dir, aseg_path) in sessions.items():
        if session_name == template_session:
            continue
            
        process_session(session_dir, template_path, output_base_dir, aseg_path)
            
    print("\nRegistration to template completed successfully")

if __name__ == "__main__":
    main() 