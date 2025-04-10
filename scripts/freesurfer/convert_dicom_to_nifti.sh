#!/bin/bash

# Set FreeSurfer environment
export FREESURFER_HOME=/usr/local/freesurfer/8.0.0
source $FREESURFER_HOME/SetUpFreeSurfer.sh

# Base directories
BASE_DIR="/mnt/mydisk/images/images/"
ORIG_DIR="$BASE_DIR/"

echo "Starting conversion from $ORIG_DIR"

# Check if ORIG_DIR exists
if [ ! -d "$ORIG_DIR" ]; then
    echo "Error: Directory $ORIG_DIR does not exist"
    exit 1
fi

# Process each year directory
for year_dir in "$ORIG_DIR"/*; do
    if [ -d "$year_dir" ]; then
        year=$(basename "$year_dir")
        echo "Processing year: $year"
        echo "Year directory: $year_dir"
        
        # Create nifti directory for this year
        nifti_year_dir="$BASE_DIR/$year/nifti/"
        echo "Creating nifti directory: $nifti_year_dir"
        mkdir -p "$nifti_year_dir"
        
        # Process each session directory
        for session_dir in "$year_dir"/orig/*; do
            if [ -d "$session_dir" ]; then
                session=$(basename "$session_dir")
                echo "Processing session: $session"
                echo "Session directory: $session_dir"
                
                # Find DICOM files in the session directory
                dicom_file=$(find "$session_dir" -type f -name "*.dcm" | head -n 1)
                
                # If no .dcm files found, try to find any file
                if [ -z "$dicom_file" ]; then
                    dicom_file=$(find "$session_dir" -type f | head -n 1)
                fi
                
                if [ -z "$dicom_file" ]; then
                    echo "Warning: No files found in $session_dir, skipping"
                    continue
                fi
                
                # Convert DICOM to NIFTI
                output_file="$nifti_year_dir/${session}.nii.gz"
                echo "Converting to: $output_file"
                
                # Use the directory of DICOM files or a specific file
                mri_convert "$dicom_file" "$output_file"
                
                # Check if conversion was successful
                if [ $? -eq 0 ]; then
                    echo "Successfully converted $session to NIFTI format"
                else
                    echo "Error: Failed to convert $session to NIFTI format"
                fi
            fi
        done
    fi
done

echo "Conversion process completed"