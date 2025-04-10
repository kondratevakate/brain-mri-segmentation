import os
import numpy as np
import pandas as pd
from nibabel import load
import matplotlib.pyplot as plt
from scipy import stats
import sys
sys.path.append('/mnt/mydisk/brain_mri_segmentation')
from brain_mri_segmentation.src.config.paths import (
    FREESURFER_DIR,
    FREESURFER_APARC_FILE,
    RESULTS_DIR,
    VOLUME_ANALYSIS_CSV,
    VOLUME_CHANGES_PLOT
)

def load_freesurfer_stats(file_path):
    """Load FreeSurfer stats file and return as dictionary."""
    stats_dict = {}
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split(',')
                stats_dict[key] = float(value)
    return stats_dict

def calculate_r2s(volumes, time_points):
    """Calculate R2s (rate of change) for each volume."""
    r2s = {}
    for region, values in volumes.items():
        if len(values) >= 2:
            # Check if time points are unique
            if len(set(time_points)) > 1:
                # Calculate R2s using linear regression
                slope, _, r_value, p_value, _ = stats.linregress(time_points, values)
                r2s[region] = {
                    'slope': slope,
                    'r_squared': r_value**2,
                    'p_value': p_value
                }
            else:
                print(f"Warning: Cannot calculate R2s for {region} - all time points are identical")
                # If all time points are identical, there is no linear relationship
                # R² = 0 because there is no variance explained by the model
                r2s[region] = {
                    'slope': 0,
                    'r_squared': 0.0,  # No variance explained by the model
                    'p_value': 1.0     # Cannot reject null hypothesis
                }
    return r2s

def main():
    # Create results directory if it doesn't exist
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Initialize data structures
    volumes = {}
    time_points = []
    subjects = []
    
    # Find all aparc.DKTatlas+aseg.mgz files
    dkt_files = []
    for root, dirs, files in os.walk(FREESURFER_DIR):
        for file in files:
            if file == FREESURFER_APARC_FILE:
                dkt_files.append(os.path.join(root, file))
    
    # Process each file
    for dkt_file in dkt_files:
        # Extract subject and session information
        path_parts = dkt_file.split('/')
        session = path_parts[-3]  # session is third from end
        subject = path_parts[-4]  # subject is fourth from end
        
        # Load the image
        img = load(dkt_file)
        data = img.get_fdata()
        
        # Calculate volumes for each label
        unique_labels = np.unique(data)
        for label in unique_labels:
            if label != 0:  # Skip background
                volume = np.sum(data == label) * img.header.get_zooms()[0] * img.header.get_zooms()[1] * img.header.get_zooms()[2]
                region_name = f"region_{int(label)}"
                if region_name not in volumes:
                    volumes[region_name] = []
                volumes[region_name].append(volume)
        
        # Add time point and subject
        try:
            time_point = float(session.split('-')[1])  # Assuming session format is ses-XXX
            time_points.append(time_point)
            subjects.append(subject)
            print(f"Processing {subject} at time point {time_point}")
        except (IndexError, ValueError) as e:
            print(f"Warning: Could not parse time point from session {session} for subject {subject}")
            continue
    
    # Print time points information
    print("\nTime points summary:")
    print(f"Number of time points: {len(time_points)}")
    print(f"Unique time points: {sorted(set(time_points))}")
    print(f"Time points per subject: {len(set(subjects))}")
    
    # Calculate R2s
    r2s = calculate_r2s(volumes, time_points)
    
    # Create DataFrame for results
    results_df = pd.DataFrame({
        'subject': subjects,
        'time_point': time_points,
        **{region: values for region, values in volumes.items()}
    })
    
    # Save results
    results_df.to_csv(os.path.join(RESULTS_DIR, VOLUME_ANALYSIS_CSV), index=False)
    
    # Create summary plot
    plt.figure(figsize=(12, 6))
    for region in volumes.keys():
        plt.plot(time_points, volumes[region], label=region)
    plt.xlabel('Time Point')
    plt.ylabel('Volume (mm³)')
    plt.title('Volume Changes Over Time')
    plt.legend()
    plt.savefig(os.path.join(RESULTS_DIR, VOLUME_CHANGES_PLOT))
    plt.close()
    
    # Print R2s results
    print("\nR2s Results:")
    for region, stats in r2s.items():
        print(f"\n{region}:")
        print(f"Slope: {stats['slope']:.2f}")
        print(f"R-squared: {stats['r_squared']:.2f}")
        print(f"P-value: {stats['p_value']:.4f}")

if __name__ == "__main__":
    main() 