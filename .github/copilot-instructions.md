# Brain MRI Segmentation - AI Coding Agent Instructions

## Project Overview
A neuroimaging research pipeline comparing three brain MRI segmentation methods (FreeSurfer, SynthSeg) across two datasets (SIMON and SRPBS/Traveling Subjects). The project is **data-heavy** and **computationally intensive**, with distinct pipeline phases and dataset-specific configurations.

## Architecture & Data Flow

### Core Components
1. **Configuration Layer** (`src/config/`): Dataset-specific path configurations
   - Multiple path files for different datasets: `paths_simon.py`, `paths_srpbs.py`, `paths_simon_fasts.py`, etc.
   - Use appropriate config import based on dataset being processed
   - Paths include atlas references (MNI ICBM152 atlas) and directory structures

2. **Preprocessing Layer** (`src/preprocessing/`):
   - **Image Registration**: Uses ANTs library (`ants.registration()` with Rigid transforms)
   - `register_to_atlas.py`: Registers segmentation (aseg) to standard atlas space
   - `register_to_first_ses.py`: Registers multi-session data to first session
   - `register_to_template.py`: Template registration workflow
   - Critical pattern: Use `multiLabel` interpolator for segmentation data (preserves label integrity)

3. **Segmentation Analysis** (`src/segmentation/synthseg/`):
   - `calculate_volumes_r2s.py`: Computes volume trajectories and R² values for temporal analysis
   - `calculate_session_metrics.py`: Computes reproducibility metrics including:
     - **Dice Coefficient**: Volume overlap between segmentations
     - **Surface Distance**: Hausdorff distances between masks
     - **Surface Dice**: Overlap at specified tolerance (e.g., 5mm boundary tolerance)
   - Pairwise comparisons across sessions using `itertools.combinations()`

4. **Visualization Layer** (`src/visualizations/`):
   - Uses seaborn/matplotlib with paper-style formatting
   - Hemisphere-specific plots: filters data for 'L' (left) and 'R' (right) structures
   - Standard figure size: (16, 8), DPI: 70

### Data Processing Patterns
- **Session-based organization**: Data is multi-session; always check for ses-* subdirectories
- **Subject-session naming**: Files reference `${subject}_${session}` pairs
- **Neuroimaging file formats**: `.mgz` (FreeSurfer), `.nii/.nii.gz` (NIfTI standard)
- **Label preservation**: Use `ndimage.binary_erosion()` for surface extraction; maintain label indices in transformations

## Critical Developer Workflows

### Setting Up Environment
```bash
# From config/paths.sh pattern
export FREESURFER_HOME=/usr/local/freesurfer
source $FREESURFER_HOME/SetUpFreeSurfer.sh
export SUBJECTS_DIR=/path/to/freesurfer/outputs
# Thread limitations for stability
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=1
export OMP_NUM_THREADS=1
export FS_OPENMP_THREADS=1
```

### Processing Pipeline
1. **DICOM to NIfTI conversion**: `scripts/freesurfer/convert_dicom_to_nifti.sh`
2. **FreeSurfer reconstruction**: `scripts/freesurfer/run_recon_all_simon.sh` (subject-session iteration pattern)
3. **Registration pipeline**: Uses ANTs for image alignment (rigid → atlas/template space)
4. **Metrics computation**: Batch processing with progress tracking (`tqdm`)
5. **Visualization**: Hemisphere-separated boxplots comparing methods

### Key Commands (Inferred from Scripts)
- `recon-all -i <T1w.nii.gz> -subjid <subject> -sd $SUBJECTS_DIR`: FreeSurfer recon pipeline
- ANTs registration: `.registration(fixed=atlas, moving=image, type_of_transform='Rigid')`
- Data I/O: `ants.image_read()` / `ants.image_write()`, `nibabel.load()`, `pandas.read_csv()`

## Project-Specific Conventions

### Configuration Import Pattern
```python
# Always append project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))
# Or: sys.path.append('/mnt/brain_mri_segmentation')

# Import dataset-specific config
from src.config.paths_simon import (
    BASE_DIR, PROCESSED_FILES_DIR, REGISTERED_FILES_DIR, ATLAS_DIR
)
```

### Naming & Directory Traversal
- Iterate subjects/sessions with glob patterns: `glob.glob(f"{base}/**/ses-*/", recursive=True)`
- Expect file naming: `sub-{id}_ses-{num}_T1w.nii.gz`
- Aparc files (parcellations): `aparc.DKTatlas+aseg.mgz`

### Numpy/Scipy Scientific Computation
- Metrics use `scipy.stats.linregress()` for temporal trends (R² values)
- Distance computation: vectorized `.dot()` operations for speed
- Binary operations: `mask_gt & mask_pred` for intersection (Dice coefficient numerator)

### Data Output
- Results stored as CSV: contains volume measurements, metrics across subjects/regions
- Plots saved with consistent styling: seaborn paper context, 70 DPI for web

## Integration Points & External Dependencies

### Core Libraries
- **ANTs**: C++ registration engine accessed via Python wrapper; expects ANTs to be system-installed
- **FreeSurfer**: Command-line tool; requires `$FREESURFER_HOME` environment setup
- **NiBabel**: NIfTI/MGZ I/O; handle `.mgz` (FreeSurfer native) and `.nii.gz` (standard neuroimaging)
- **SciPy/scikit-image**: Scientific computing for metrics and image processing

### Data Assumptions
- All neuroimaging files are 3D volumetric data (or 4D with time dimension)
- Images should be in consistent anatomical space before metrics computation
- CSV outputs follow brain atlas conventions (FreeSurfer Desikan-Killiany atlas with L/R hemisphere labels)

## Common Pitfalls & Solutions

1. **Path management**: Always use `Path` from `pathlib`; hardcoded mount paths (`/mnt/mydisk`) must be replaced for portability
2. **Interpolation in registration**: Use `interpolator='multiLabel'` for segmentation masks, NOT linear (prevents label bleeding)
3. **Thread safety**: FreeSurfer/ITK require single-thread execution (`*_THREADS=1`) to avoid corruption
4. **Missing sessions**: Validate `glob` results before processing; some subjects may lack all sessions
5. **Coordinate systems**: Atlas registration requires fixed/moving image order consistency across functions

