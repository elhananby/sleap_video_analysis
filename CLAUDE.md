# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands
- Environment setup: `conda env create -f env.yml`
- Install deps: `pip install -e .`
- Run notebook: `jupyter notebook video_analysis.ipynb` or `jupyter notebook braidz_analysis.ipynb`
- Extract stimulus data: `python extract_stimulus_heading_for_camera.py <braidz_path> <output_path>`

## Code Style Guidelines
- Python version: >=3.10 (>=3.11 for scripts)
- Imports: Standard library first, then third-party (numpy, pandas, scipy)
- Docstrings: Google-style with Args/Returns sections
- Error handling: Use try/except for file operations with descriptive messages
- Naming: snake_case for functions/variables, PascalCase for classes
- Function organization: Single responsibility, descriptive names
- Comments: Add for complex algorithms and non-obvious functionality
- Data handling: Handle NaN values explicitly; use vectorized operations

## Data Processing Pattern
- Use pandas DataFrames for tabular data
- Use numpy arrays for numerical calculations
- Use proper circular statistics for angular data
- Prefer functional transformations over in-place modifications