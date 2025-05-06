# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy",
#   "pandas",
#   "scipy",
# ]
# ///

"""
Script to process braidz files and interpolate stimulus headings.

This script processes braidz files to extract stimulus data and interpolates
heading values based on a lookup table. The results are saved to a new CSV file.
"""

import argparse
import glob
import io
import os
import urllib.parse
import urllib.request
import zipfile
from io import StringIO

import numpy as np
import pandas as pd
from scipy import interpolate

# Hard-coded screen2heading mapping from heading_results.csv
SCREEN2HEADING_DATA = """
screen,heading
0,2.3513283485530456
80,1.2179812647799937
160,0.5031545295746856
240,-0.3078141744904855
320,-0.8746949393526915
400,-1.5019022477483523
480,-2.185375561680841
560,-3.0123437340031307
640,2.3513283485530456
"""


def open_filename_or_url(filename_or_url):
    """
    Open a file from a local path or URL.

    Args:
        filename_or_url (str): Path to local file or URL

    Returns:
        File object with seek capability
    """
    parsed = urllib.parse.urlparse(filename_or_url)
    is_windows_drive = len(parsed.scheme) == 1
    if is_windows_drive or parsed.scheme == "":
        # No scheme, so this is a filename
        fileobj_with_seek = open(filename_or_url, mode="rb")
    else:
        # Is URL
        req = urllib.request.Request(
            filename_or_url, headers={"User-Agent": "Python Script"}
        )
        fileobj = urllib.request.urlopen(req)
        fileobj_with_seek = io.BytesIO(fileobj.read())
    return fileobj_with_seek


def initialize_csv_writer(filename):
    """
    Initialize a CSV file with appropriate headers.

    Args:
        filename (str): Path to the output CSV file

    Returns:
        str: Path to the initialized file
    """
    with open(filename, "w") as f:
        f.write("obj_id,frame,stim_heading\n")
    return filename


def write_to_csv(filename, obj_id, frame, stim_heading):
    """
    Append a row to the CSV file.

    Args:
        filename (str): Path to the CSV file
        obj_id (int): Object ID
        frame (int): Frame number
        stim_heading (float): Interpolated stimulus heading
    """
    with open(filename, "a") as f:
        f.write(f"{obj_id},{frame},{stim_heading}\n")


def create_interpolation_function(screen2heading_path=None):
    """
    Create an interpolation function based on screen-to-heading mapping.

    Args:
        screen2heading_path (str, optional): Path to the CSV file containing screen-to-heading mapping.
            If None, uses the hard-coded SCREEN2HEADING_DATA.

    Returns:
        function: A function that takes a screen value and returns the interpolated heading
    """
    if screen2heading_path is None:
        # Use hard-coded data
        screen2heading = pd.read_csv(StringIO(SCREEN2HEADING_DATA))
    else:
        # Read from file
        screen2heading = pd.read_csv(screen2heading_path)

    # Organize original data
    screen_values = np.array(screen2heading["screen"])
    heading_values = np.array(screen2heading["heading"])

    # Convert heading angles to Cartesian coordinates
    x = np.cos(heading_values)
    y = np.sin(heading_values)

    # Create interpolation functions for x and y components
    f_x = interpolate.interp1d(
        screen_values, x, kind="linear", fill_value="extrapolate"
    )
    f_y = interpolate.interp1d(
        screen_values, y, kind="linear", fill_value="extrapolate"
    )

    def get_heading(screen_value):
        """
        Get the interpolated heading for a given screen value.

        Args:
            screen_value (float): The screen value to interpolate

        Returns:
            float: The interpolated heading in radians
        """
        interp_x = f_x(screen_value)
        interp_y = f_y(screen_value)
        return np.arctan2(interp_y, interp_x)

    return get_heading


def process_braidz_file(braidz_path, output_path, get_heading_func):
    """
    Process a braidz file and generate a CSV with interpolated headings.

    Args:
        braidz_path (str): Path to the braidz file
        output_path (str): Directory where the output CSV will be saved
        get_heading_func (function): Function to calculate heading from screen value

    Returns:
        bool: True if successful, False otherwise
    """
    # Read stim data from braidz
    try:
        fileobj = open_filename_or_url(braidz_path)
        with zipfile.ZipFile(file=fileobj, mode="r") as z:
            # Check if 'stim.csv' exists in the archive
            if "stim.csv" in z.namelist():
                stim = pd.read_csv(z.open("stim.csv"))
            elif "opto.csv" in z.namelist():
                stim = pd.read_csv(z.open("opto.csv"))
            else:
                print(f"No stim or opto data found in {braidz_path}")
                return False
    except Exception as e:
        print(f"Error reading {braidz_path}: {e}")
        return False

    # Extract filename without extension for the output file
    file_basename = os.path.basename(braidz_path).split(".")[0] + ".csv"
    output_file = os.path.join(output_path, file_basename)

    # Initialize CSV file
    csv_file = initialize_csv_writer(output_file)

    # Interpolate and write to CSV
    for idx, row in stim.iterrows():
        obj_id = row["obj_id"]
        frame = row["frame"]
        if "stim_position_screen" not in row:
            # If stim_position_screen is not present, use heading directly
            stim_heading = row["heading"]
        else:
            # Use stim_position_screen for heading interpolation
            stim_heading = row["stim_position_screen"]

        # Interpolate heading
        stim_heading = get_heading_func(stim_heading)

        write_to_csv(csv_file, obj_id, frame, stim_heading)

    print(f"Interpolated {braidz_path} to {output_file}")
    return True


def main():
    """Main function to parse arguments and process files."""
    parser = argparse.ArgumentParser(
        description="Process braidz files to interpolate stimulus headings."
    )
    parser.add_argument(
        "braidz_path",
        help="Path to the braidz file or directory containing braidz files",
    )
    parser.add_argument(
        "output_path", help="Directory where output CSV files will be saved"
    )
    parser.add_argument(
        "--screen2heading_path",
        help="Path to the CSV file containing screen-to-heading mapping (optional, uses built-in data if not provided)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process all braidz files in subdirectories recursively",
    )

    args = parser.parse_args()

    # Check if output directory exists, create if it doesn't
    if not os.path.exists(args.output_path):
        os.makedirs(args.output_path)
        print(f"Created output directory: {args.output_path}")

    # Create interpolation function
    get_heading_func = create_interpolation_function(args.screen2heading_path)

    # Determine if braidz_path is a file or directory
    if os.path.isfile(args.braidz_path) and args.braidz_path.endswith(".braidz"):
        # Process a single braidz file
        process_braidz_file(args.braidz_path, args.output_path, get_heading_func)
    elif os.path.isdir(args.braidz_path):
        # Process all braidz files in the directory
        pattern = os.path.join(
            args.braidz_path, "**" if args.recursive else "", "*.braidz"
        )
        braidz_files = glob.glob(pattern, recursive=args.recursive)

        if not braidz_files:
            print(f"No braidz files found in {args.braidz_path}")
            return

        for braidz_file in braidz_files:
            process_braidz_file(braidz_file, args.output_path, get_heading_func)
    else:
        print(f"Error: {args.braidz_path} is not a valid braidz file or directory")
        return

    print("Processing complete!")


if __name__ == "__main__":
    main()


## USAGE EXAMPLE ##
# Using built-in heading data
# python braidz_processor.py path/to/file.braidz path/to/output

# Using custom heading data (optional)
# python braidz_processor.py path/to/file.braidz path/to/output --screen2heading_path custom_heading.csv
