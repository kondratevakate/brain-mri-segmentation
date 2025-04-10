#!/bin/bash
# Load configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "/mnt/mydisk/brain_mri_segmentation/config/paths.sh"

# Set FreeSurfer environment variables
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=1
export OMP_NUM_THREADS=1
export FS_OPENMP_THREADS=1
export SUBJECTS_DIR="$FREESURFER_DIR"

# Function to get current memory usage
get_memory_usage() {
    free -h | grep Mem | awk '{print $3}'
}

# Function to get current CPU usage
get_cpu_usage() {
    top -bn1 | grep "Cpu(s)" | awk '{print $2}'
}

# Function to log resource usage
log_resources() {
    local subject=$1
    local session=$2
    local start_time=$3
    local end_time=$4
    local memory_usage=$5
    local cpu_usage=$6
    
    # Calculate duration
    duration=$((end_time - start_time))
    hours=$((duration / 3600))
    minutes=$(( (duration % 3600) / 60 ))
    seconds=$((duration % 60))
    
    # Create log entry
    log_entry="$(date '+%Y-%m-%d %H:%M:%S') | Subject: $subject | Session: $session | Duration: ${hours}h ${minutes}m ${seconds}s | Memory: $memory_usage | CPU: ${cpu_usage}%"
    
    # Log to file
    echo "$log_entry" >> "$FREESURFER_LOG_DIR/freesurfer_processing.log"
    echo "$log_entry"
}

# Function to process a single subject
process_subject() {
    local subject=$1
    local subject_dir="$SRPBS_DIR/$subject"
    
    echo "Processing subject: $subject"
    
    # Loop through all session directories except ATT
    for session_dir in "$subject_dir"/ses-*; do
        if [ -d "$session_dir" ]; then
            session_name=$(basename "$session_dir")
            
            # Skip ATT sessions
            if [[ "$session_name" == ses-siteATT* ]]; then
                echo "Skipping ATT session: $session_name"
                continue
            fi
            
            echo "Processing session: $session_name"
            
            # Look for T1w image in anat directory
            t1_file=$(find "$session_dir" -name "*T1w.nii.gz" | head -n 1)
            
            if [ -n "$t1_file" ]; then
                echo "T1 file: $t1_file"
                
                # Create subject name for FreeSurfer (subject_session)
                fs_subject_name="${subject}_${session_name}"
                
                # Record start time and resources
                start_time=$(date +%s)
                start_memory=$(get_memory_usage)
                start_cpu=$(get_cpu_usage)
                
                # Run recon-all
                recon-all -all -s "$fs_subject_name" -i "$t1_file" -threads 1
                
                # Record end time and resources
                end_time=$(date +%s)
                end_memory=$(get_memory_usage)
                end_cpu=$(get_cpu_usage)
                
                # Log resource usage
                log_resources "$subject" "$session_name" "$start_time" "$end_time" "$end_memory" "$end_cpu"
            else
                echo "No T1w image found for session: $session_name"
            fi
        fi
    done
}

# Main processing loop
for subject_dir in "$SRPBS_DIR"/sub-*; do
    if [ -d "$subject_dir" ]; then
        subject=$(basename "$subject_dir")
        process_subject "$subject"
    fi
done

ps aux | grep run_freesurfer_srpbs.sh 