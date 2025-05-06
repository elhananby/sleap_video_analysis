#!/bin/bash
#SBATCH --job-name=sleap_convert            # Job name
#SBATCH --mail-type=END,FAIL                           # Mail events (NONE, BEGIN, END, FAIL, ALL)
#SBATCH --mail-user=elhanan.buchsbaum@mpinb.mpg.de     # Where to send mail (adjust as needed)
#SBATCH --partition=CPU                                # Partition
#SBATCH --time=12:00:00                                # Time limit hrs:min:sec
#SBATCH --mem=4G                                # Memory per task
#SBATCH --array=0-35%36                        # Array job with 36 tasks (one per directory)
#SBATCH --ntasks=1                            # Number of tasks per array job
#SBATCH --cpus-per-task=4                   # CPU cores per task
#SBATCH --output=logs/sleap_convert_%A_%a.out  # Standard output log
#SBATCH --error=logs/sleap_convert_%A_%a.err   # Standard error log

# Create logs directory if it doesn't exist
mkdir -p logs

# Source directory
SOURCE_DIR="/gpfs/soma_fs/home/buchsbaum/sleap_projects/highspeed/predictions"

# Destination directory
DEST_DIR="/gpfs/soma_fs/home/buchsbaum/src/sleap_video_analysis/data"

# Get all directories in the source
readarray -t directories < <(find "${SOURCE_DIR}" -maxdepth 1 -mindepth 1 -type d | sort)
dir_count=${#directories[@]}

# Check if directory count matches array size
if [ $dir_count -ne 36 ]; then
  echo "Warning: Found $dir_count directories, but SLURM array is set to 0-35 (36 tasks)"
  echo "You may need to adjust the --array parameter in the job script"
fi

# Get the directory for this task
dir_index=${SLURM_ARRAY_TASK_ID}
if [ $dir_index -ge $dir_count ]; then
  echo "Error: Task ID $dir_index is out of range (0-$((dir_count-1)))"
  exit 1
fi

current_dir=${directories[$dir_index]}
dir_name=$(basename "$current_dir")

echo "Processing directory: $current_dir (Task ID: ${SLURM_ARRAY_TASK_ID})"

# Create output directory if it doesn't exist
output_dir="${DEST_DIR}/${dir_name}"
mkdir -p "$output_dir"

# Process all .slp files in the directory
for file in "${current_dir}"/*.slp; do
  # Skip if no files found
  [ -e "$file" ] || continue
  
  # Generate output filename (replace .slp with .csv)
  filename=$(basename "$file")
  output_file="${output_dir}/${filename%.slp}.csv"
  
  echo "Converting $file to $output_file"
  
  # Run the conversion command
  mamba run -n sleap sleap-convert "$file" --format analysis.csv --output "$output_file"
done

echo "Task ${SLURM_ARRAY_TASK_ID} (Directory: ${dir_name}) completed"