# Future Work: Measuring the Information Loss Boundary in Brain MRI Segmentation

## Motivation

The reproducibility experiments in this paper (cross-scanner variability, n=1
pilot) reveal a gap: we can measure *that* segmentation results differ across
conditions, but we cannot yet measure *why* or *how much input degradation is
recoverable*. The following experimental design addresses this directly.

## Core idea

Current segmentation pipelines give a single point-estimate per scan. We
propose treating segmentation as a **signal recovery problem**: how much can we
degrade the input image and still recover a reference-level estimate?

The key insight from our pilot data: even the same scan produces different
volumes depending on head orientation (~1.2–1.8% CV across ±12° rotations).
This is not physics — it is model instability. The physically-grounded
interpolation floor is **0.05%**. Any gap above 0.05% is recoverable in
principle by a better method.

---

## Proposed experiment design

### Step 1 — Establish a pseudo-reference via TTA

Take one high-quality T1 (≥1 mm isotropic, clean SNR). Generate N augmented
copies (rotations, small intensity perturbations) and segment each with
FastSurfer or SynthSeg. Average the resulting label maps (or volumes).

This TTA-consensus estimate is the **pseudo-reference R**. It is not ground
truth (no in-vivo gold standard exists for subcortical volumes), but it is the
best single-method estimate obtainable, with reduced model instability:

```
R = mean(segment(augment_k(I)))  for k = 1..N
```

**Pilot data (this paper, n=1, SynthSeg, N=9, rotations ±12°):**
- Median CV across angles: **1.24%** (max: amygdala 1.83%)
- Amygdala excursion at ±12°: up to **5.5%** from 0°
- Importantly: most structures are **asymmetric** — TTA reduces bias, not just
  variance. The improvement from TTA is approximately 1.37% → 1.24%, modest,
  because the dominant effect is systematic orientation bias, not random noise.

### Step 2 — Controlled degradation

Apply a controlled degradation operator D_θ to the reference image I:
```
I_θ = D_θ(I)
```
Degradation types to sweep, in order of clinical relevance:

| Operator | Parameter θ | Clinical analogue |
|---|---|---|
| Rotation | 0–45° | head repositioning between sessions |
| Gaussian noise | σ = 0.01–0.5 (normalised) | low-SNR scanner / thin slice |
| Bias field | polynomial order 1–5 | B1 inhomogeneity (1.5T, surface coils) |
| Resolution downsampling | 1 → 2 → 3 → 5 mm | thick-slice clinical protocol |
| Contrast shift | ±20–60% intensity scale | different T1 sequence (FSPGR vs MPRAGE vs SE) |
| k-space subsampling | acceleration ×2–×8 | compressed sensing / accelerated acquisition |

### Step 3 — Recovery with method X, then TTA

For each degradation level θ, apply recovery method X, then compute TTA
consensus:
```
R_θ,X = mean(segment(augment_k(X(I_θ))))  for k = 1..N
```

**Method X candidates (in order of complexity):**
1. No recovery (identity) — baseline degradation curve
2. Simple preprocessing: N4 bias correction, denoising (ANTs, FSL), super-resolution
3. Existing pipeline components: SynthSR (super-resolution to 1mm), FreeSurfer's
   internal normalisation, SynthSeg's contrast-agnostic resampling
4. Generative harmonisation: flow-matching-based synthesis (e.g., MAISI-v2 style
   rectified flow, AAAI 2026); translate degraded scan to reference-contrast domain

### Step 4 — Measure the information loss boundary

For each structure s, degradation type D, and recovery method X, compute:
```
Δ(θ, X, s) = |R(s) - R_θ,X(s)| / R(s)  [%]
```

**Information is preserved** when `Δ(θ, X, s) < ε_interp = 0.05%`
(the physically-grounded interpolation floor measured in this paper).

**Information is partially recoverable** when `ε_interp ≤ Δ < ε_TTA = 0.5%`
(the TTA-reduced model floor).

**Information is lost** when `Δ > ε_TTA` and no method X achieves recovery
below this threshold.

The **information loss boundary** for structure s under degradation D is:
```
θ*(s, D, X) = min θ such that Δ(θ, X, s) > ε_TTA
```

This gives a concrete, quantitative limit: "hippocampal volumes are recoverable
from noise up to σ=0.3 with SynthSR, but not beyond."

---

## Biological validation (proxy signal)

For datasets with repeated single-subject measurements over time (e.g., the
SIMON dataset used in this paper, or IXI/ABIDE test-retest cohorts), a correctly
functioning segmentation pipeline should recover a monotone biological trend:

- Hippocampal volume decreases ~0.5%/year in healthy adults, ~2–4%/year in MCI
- Lateral ventricle volume increases with age

**Proposed test:** given a longitudinal single-subject series processed with
TTA-consensus, does the estimated trajectory:
(a) lie within the expected biological envelope for age/sex?
(b) show less variance across sessions than the single-pass estimate?

This is a *consistency* test, not accuracy vs ground truth. It provides a
second, independent validation that the pipeline is tracking biology rather than
scanner noise.

**Key threshold:** if within-subject session-to-session variance (TTA-corrected)
exceeds the expected annual biological change rate, the pipeline cannot detect
real longitudinal effects in a single subject — it is blind to the signal it was
designed to detect.

From our pilot: SynthSeg cross-sectional session variance ~17% (cross-scanner);
expected annual atrophy signal ~0.5%. The longitudinal pipeline is essential to
bridge this gap.

---

## Why current approaches do not fully solve this

**Longitudinal pipelines** (Reuter et al. 2012) reduce within-scanner
cross-sectional variance from ~2–3% to ~0.4–0.8% by joint estimation across
timepoints. They do not address cross-scanner variance or model instability.

**TTA with rotations** (our pilot, this paper): reduces variance from 1.4% to
~1.2% (median). Improvement modest — because dominant effect is orientation bias
(asymmetric model response), not symmetric random noise. TTA cannot correct
systematic bias.

**Equivariant architectures** (SE(3)-equivariant networks, e.g., using e3nn)
would reduce the rotation component to the physics floor (~0.05%) by
construction. Not yet practical for whole-brain segmentation at clinical scale
(memory/compute cost ~10× standard CNN).

**Generative harmonisation** (flow-matching models, e.g., MAISI-v2 AAAI 2026)
is theoretically promising for cross-scanner recovery but has not been validated
for subcortical volumetry accuracy — only for perceptual image quality. This
is an open research gap.

---

## Practical significance

The numbers from this paper's pilot define concrete, clinically meaningful
thresholds:

| Signal | Value | Method floor (this paper) |
|---|---|---|
| Annual hippocampal atrophy (healthy) | ~0.5%/year | SynthSeg cross-sectional: ~1.4% |
| Annual hippocampal atrophy (MCI) | ~2–4%/year | TTA-corrected: ~1.2% |
| Cross-scanner variability (this paper) | ~17% median, 45% max | — |
| Physics interpolation floor | 0.05% | — |

Single-subject longitudinal tracking with cross-sectional DL segmentation is
statistically underpowered for detecting healthy ageing. The proposed framework
gives a principled way to identify which degradations, recovery methods, and
anatomical structures cross the threshold from "recoverable" to "information
lost."

---

## Related work to position against

- Rotation/augmentation robustness of DL segmenters: Billot et al. 2023 (SynthSeg)
- Longitudinal pipeline for within-subject variance reduction: Reuter et al. 2012
- Test-time augmentation for medical image segmentation: general TTA literature
- Equivariant networks for 3D medical imaging: e3nn-based approaches
- Generative harmonisation: MAISI-v2 (Zhao et al. AAAI 2026), FlowLet (Jan 2026)
- FOMO25 challenge findings: foundation model generalisation under domain shift
- Clinical-ComBat for harmonisation: requires N>20 subjects per site — not
  applicable to single-subject design

---

---

## Multi-method TTA: independent errors but incompatible biases

**Pilot finding (n=1, SynthSeg vs FastSurfer, +3° rotation, 2018 scan):**

The rotation responses of SynthSeg and FastSurfer are nearly **uncorrelated**
(r = −0.068 across 12 subcortical structures). For 4 of 12 structures the two
methods move in *opposite* directions under the same rotation.

However, the methods have **large systematic offsets in absolute volumes**
(e.g. amygdala: SynthSeg 1.71 mL vs FastSurfer 1.47 mL, −14%; pallidum: +20%).
These are not noise — they reflect different operational definitions of structure
boundaries across training atlases. Statistical independence of TTA errors and
systematic inter-method bias are orthogonal properties:

- Independent errors allow variance reduction *within a method* via TTA.
- Systematic bias means naively averaging absolute volumes across methods yields
  a third quantity that does not correspond to either method's definition, and is
  no closer to ground truth (which does not exist in-vivo without histology).

**What can be meaningfully combined:**

- **Relative changes (Δ%)** rather than absolute volumes. If method M consistently
  underestimates structure S by a fixed factor, that factor cancels in longitudinal
  Δ: a true 2%/year atrophy appears as 2%/year in both SynthSeg and FastSurfer.
  For the information-loss experiment, Δ(θ, X, s) should be computed within one
  method, not across methods.

- **Consistency of direction** as a binary signal: do both methods agree that the
  volume increased / decreased / stayed stable? Agreement despite different absolute
  values is meaningful evidence that the change is real and method-independent.

- **Error correlation structure** as a diagnostic: the near-zero cross-method
  correlation (r ≈ 0) is itself a finding — the two methods fail differently,
  meaning their errors are not driven by the same image features. This motivates
  measuring the full pairwise correlation matrix across all available methods to
  identify whether there is a common latent failure mode (orientation bias shared
  by all CNNs) versus method-specific failure modes.

**Proposed extension:** sweep the full 9-angle TTA for FastSurfer, compute
pairwise Δ% correlations across methods (not absolute volumes), and characterise
the shared vs method-specific components of model instability.

---

## Which segmenter is best for which anatomy?

A systematic question this paper does not answer: across available tools, which
achieves the most reproducible estimates for cortical, subcortical, and
white-matter tract measurements?

### Segmenters to compare

**Subcortical** (hippocampus, amygdala, thalamus, basal ganglia):

| Tool | Approach | Status in this study |
|---|---|---|
| SynthSeg (FreeSurfer 8) | DL, contrast/resolution-agnostic | ✅ all 3 scanners |
| FastSurfer VINN | DL, multi-view CNN | ✅ 2018 (2024 failed: IR contrast) |
| FreeSurfer 7.4 | Atlas-based (GCA), talairach-registered | ⏳ running (2018) |
| FIRST (FSL) | Shape + appearance model, subcortical-specific | ❌ not yet run |
| BrainChop | Browser-based DL, multiple model options | ❌ not yet run |

**Cortical** (thickness, parcellation, volume per lobe):

| Tool | Approach | Status |
|---|---|---|
| FreeSurfer 7.4 recon-all | Surface-based, Desikan-Killiany / Destrieux | ⏳ running |
| FastSurfer surface module | Surface-based, faster than FS | ✅ 2018 (full recon done) |
| CAT12 (SPM-based) | Voxel-based morphometry + surface | ❌ not yet run |
| SynthSeg --parc | Cortical parcellation, contrast-agnostic | ❌ not yet run |

**White matter tracts:**

| Tool | Approach | Status |
|---|---|---|
| TractSeg (Wasserthal 2018) | DL bundle segmentation from FOD | ❌ requires ≥30-dir DWI |
| TRACULA (FreeSurfer) | Probabilistic tractography, atlas priors | ❌ requires ≥30-dir DWI |
| AFQ / pyAFQ | Classical streamline-based bundle extraction | ❌ requires ≥30-dir DWI |

**Note on this dataset:** the 2024 session has DWI (701_dw_ssh.nii.gz, b=800,
N=2 directions, 5.5 mm slices). This is a clinical screening acquisition —
insufficient for tractography (minimum ~6 directions required; research-grade
needs ≥30). Any tract comparison would require a dedicated DWI acquisition.

### What is actually unknown

Published comparisons (e.g. Tustison et al., Wachinger et al.) typically evaluate
on T1-MPRAGE at 1 mm isotropic. Cross-scanner reproducibility specifically for
each anatomy type, comparable to our n=1 pilot, has not been reported for the
full method matrix above. The following remain open questions:

1. **Subcortical reproducibility per method** across 1.5T / 3T / different vendors:
   does atlas-based (FS7.4) outperform DL (FastSurfer, SynthSeg) when the input
   diverges from training distribution?

2. **Cortical thickness reproducibility at 5 mm slice thickness** (2022 Siemens):
   all surface-based methods require near-isotropic input; at 5 mm, only
   SynthSeg `--parc` is expected to attempt cortical parcellation. What does
   the information-loss curve look like for cortical vs subcortical?

3. **Optimal ensemble composition:** given pairwise error correlations, what
   is the minimum set of methods that achieves a stable pseudo-reference?
   Pilot data suggests SynthSeg + FastSurfer is already near-orthogonal (r ≈ 0);
   adding an atlas-based method (FS7.4) with a different failure mode
   (orientation-invariant but morphology-dependent) would further diversify.

---

---

## Beyond volume scalars: probabilistic aggregation and shape models

### What already exists — do not reinvent

**SynthSeg soft volumes (Billot et al. 2023, PMC10154424):**
The SynthSeg paper itself states: *"hippocampal volumes are computed by summing
the corresponding soft predictions, thus accounting for segmentation uncertainties
and, to a certain extent, for partial voluming."* The `--post` flag outputs
per-voxel probability maps (~0.9 GB/scan, 26 classes, confirmed in FreeSurfer 8).
This is **not a novelty claim** — it is the intended use. What is missing is TTA
on top of these soft maps, and their application to the reproducibility question.

**Trautmann et al. 2025 (arXiv:2503.10527):**
"How Should We Evaluate Uncertainty in Accelerated MRI Reconstruction?"
University of Sussex. Directly relevant: they apply reconstruction ensembles
(5–10 members) to accelerated k-space, then run SynthSeg on each reconstruction
to measure downstream segmentation variance. Key finding: *high SSIM/PSNR does
not imply stable segmentation volumes* — substantial biases were found for
specific structures even in high-quality reconstructions. Uncertainty metrics:
Jacobian determinant variance, volume variation, Hausdorff distance.
**This is our Experiment B done for reconstruction uncertainty; our contribution
would be extending it to the information-loss boundary framework and including
TTA at the segmentation level.**

**Mesh2SSM++ (Iyer, Karanam, Elhabian, arXiv:2502.07145, Feb 2025):**
Probabilistic framework for unsupervised statistical shape models from surface
meshes. Learns correspondences without pre-existing shape model; quantifies
aleatoric uncertainty (inherent data variability). Validated across diverse
anatomies. **This is the ready-made tool for the probabilistic mesh step** —
apply to hippocampus/amygdala meshes from TTA segmentations to get a shape
distribution rather than a volume scalar.

**SPHARM-OT (Oguz et al., SPIE Medical Imaging 2023):**
Spherical harmonic surface modeling with optimal transport for amygdala shape
analysis in Alzheimer's disease. Extends classical SPHARM-PDM with better
spherical parametrization. Representative of the SSM literature for the
structures we measure.

**Review: Valiuddin et al. 2024 (arXiv:2411.16370, updated 2026):**
Comprehensive review of Bayesian uncertainty quantification in deep probabilistic
image segmentation. Four task categories: Observer Variability, Active Learning,
Model Introspection, Model Generalization. Framework for positioning our work
relative to the UQ literature.

### What is still missing (our contribution)

None of the above combines:
1. **K-space degradation** as controlled input perturbation
2. **Reconstruction ensemble** (multiple recon methods of same k-space)
3. **Segmentation TTA** (multiple orientations per reconstruction)
4. **Probability map averaging** (soft aggregation, not argmax)
5. **Shape model fitting** (Mesh2SSM++ / SPHARM) to the resulting mesh ensemble
6. **Information-loss boundary** as the unified metric

The closest work (Trautmann 2025) does steps 2+3 but uses hard segmentation and
focuses on image quality metrics, not the information-loss boundary. The proposed
framework integrates all six steps into a single reproducibility evaluation
pipeline.

---

## Probabilistic aggregation: volume → probability map → mesh

Averaging volume scalars (mL) discards spatial information. Two estimates can
agree on total hippocampal volume while disagreeing on where exactly the boundary
runs — a distinction critical for shape-based biomarkers (e.g. CA1 atrophy in
early Alzheimer's). Two richer aggregation levels are possible.

### Level 1: averaging posterior probability maps

Before hard segmentation (argmax), each method produces per-voxel probabilities:
P(voxel x ∈ region r) ∈ [0, 1]. SynthSeg exposes these via `--post` (confirmed
available in FreeSurfer 8; ~0.9 GB per scan for 26 classes at 1 mm³).

Averaging probability maps across TTA reconstructions yields a **consensus
probability map** — the proper Bayesian combination when models are treated as
equally-weighted committee members:

```python
P_consensus(x, r) = mean_k( P_k(x, r) )   # across k TTA variants
```

From this single object everything else is derived without additional information
loss:

| Derived quantity | Formula | Advantage over scalar |
|---|---|---|
| Expected volume | Σ_x P_consensus(x,r) × vox_vol | Threshold-free, lower variance |
| Hard segmentation | argmax_r P_consensus(x,r) | More stable boundaries |
| Boundary mesh | isosurface at P=0.5 | Spatially coherent |
| Uncertainty map | H(P) = −P log P − (1−P)log(1−P) per voxel | Shows WHERE boundary is uncertain |
| Volume distribution | vary threshold 0.3–0.7, measure volume | Sensitivity analysis |

The uncertainty map is particularly valuable: it directly shows which parts of
a structure's boundary are stable across reconstructions (interior voxels,
P ≈ 1.0) versus uncertain (boundary voxels, P ≈ 0.5). This spatial uncertainty
profile is a richer QC signal than a single CV% per structure.

**Feasibility now:** run `mri_synthseg --post` on the 9-angle TTA sweep for
2018. Average the 9 probability maps → consensus map → compare expected volumes
to argmax volumes → quantify threshold sensitivity. Storage: ~8 GB for 9 scans,
manageable.

**Inter-method combination caveat:** probability maps from SynthSeg and
FastSurfer CANNOT be directly averaged — they operate in different atlas spaces
with different boundary definitions (same bias problem as volumes, now per-voxel).
Within-method averaging across reconstructions/TTA: valid. Cross-method: invalid
at the probability level, same as at the volume level.

### Level 2: mesh averaging (cortical surfaces)

For **cortical surfaces**, FreeSurfer and FastSurfer produce meshes in
correspondence via spherical registration to `fsaverage`. Vertex positions can
be directly averaged across TTA runs:

```
vertex_mean(v) = mean_k( vertex_k(v) )        # same topological address
vertex_std(v)  = std_k( vertex_k(v) )          # per-vertex uncertainty
```

This gives a **3D uncertainty field on the cortical surface** — in which gyri
and sulci is the boundary most variable? — rather than a per-lobe CV%.

For **subcortical structures**, meshes generated from different label maps are
NOT automatically in correspondence (marching cubes gives arbitrary vertex
ordering). Correspondence requires:
- Registration to a shape template (FSL FIRST, SPHARM-PDM, ShapeWorks)
- Or: work at the probability map level and derive meshes from the consensus map
  (preferred — avoids the correspondence problem entirely)

### Summary: aggregation hierarchy

```
Probability map  ←  most information, basis for everything
      ↓
   Mesh          ←  spatial, needs correspondence for averaging
      ↓
   Volume        ←  scalar, what we have now; useful but lossy
```

The k-space reconstruction ensemble (Experiment A above) should be evaluated
at the probability map level where possible, with volumes and meshes derived
from the consensus map rather than averaged independently.

---

## K-space as the starting point: solving the inter-method bias problem

The multi-method TTA section above identifies a fundamental obstacle: averaging
segmentation volumes across methods is invalid because systematic inter-method
biases (e.g. amygdala SynthSeg −14% vs FastSurfer) reflect different boundary
definitions, not measurement noise. Starting from k-space resolves this by
changing what is varied.

### Core insight

Different **reconstructions of the same k-space** physically represent the same
proton distribution. They differ in how acquisition noise, undersampling
artefacts, and regularisation are handled — not in where anatomical boundaries
are defined. Segmentations of different reconstructions of the same k-space CAN
be averaged: the bias problem is absent by construction.

```
                      ┌─ recon_1 (IFFT)           ─┐
                      ├─ recon_2 (CS, λ=0.01)      ─┤
raw k-space ─────────►├─ recon_3 (CS, λ=0.1)       ─┼──► segment each ──► average ──► R_kspace
                      ├─ recon_4 (DL, e.g. E2E-Var) ─┤
                      └─ recon_5 (zero-fill)         ─┘
```

This pseudo-reference R_kspace is strictly more principled than TTA over
image-space rotations: it averages over reconstruction uncertainty rather than
orientation sensitivity, and all inputs represent the same physical measurement.

### Experiment A: k-space reconstruction ensemble as pseudo-reference

For each available T1 scan, simulate k-space from the NIfTI image (3D FFT),
reconstruct with N methods, segment each with single-method TTA, average volumes.

Reconstruction variants to include:
- Standard IFFT (baseline)
- Compressed sensing with varying regularisation (λ sweep)
- Partial Fourier (6/8, 7/8 sampling) + zero-filling
- Partial Fourier + homodyne / POCS reconstruction
- Deep learning reconstruction (E2E-VarNet, MoDL) if pre-trained weights available

The spread of segmentation volumes across reconstruction methods isolates
**reconstruction uncertainty** — a third variance component not captured by
either the image-space rotation floor or the inter-method comparison.

### Experiment B: k-space degradation + recovery + TTA

K-space degradation has direct physical meaning, unlike image-space rotation:

| K-space operator | Physical analogue | Clinical meaning |
|---|---|---|
| Undersampling (R=2×, 4×, 8×) | Parallel imaging acceleration | Can we halve scan time? |
| K-space noise (σ sweep) | Reduced averages / lower field | Thin slice at 1.5T vs 3T |
| Outer k-space truncation | Lower matrix size / resolution | 2mm vs 1mm acquisition |
| Central k-space dropout | Motion artefact simulation | Patient movement |
| Phase-encode undersampling | Standard GRAPPA trajectory | Common clinical protocol |

For each degradation level θ, apply recovery method X, then TTA-segment:

```
k_deg(θ) = degrade(k_full, θ)
R_θ,X    = mean_k( segment( TTA( recon_X(k_deg(θ)) ) ) )
Δ(θ,X,s) = |R_kspace(s) - R_θ,X(s)| / R_kspace(s)
```

This gives information-loss curves with **direct protocol-design interpretation**:
"hippocampal volume is recoverable from R=4× acceleration to within ε%."

### Why this is stronger than image-space rotation

| Property | Image-space rotation | K-space degradation |
|---|---|---|
| Physical meaning | Arbitrary transform, no scanner analogue | Direct scanner parameter |
| Applicable to averaging | No (rotation changes orientation → bias) | Yes (same physics, no boundary bias) |
| Clinical translation | None direct | Acquisition protocol design |
| Separates reconstruction vs segmentation noise | No | Yes |

### Practical caveat: simulation vs real k-space

This experiment can be run **retrospectively** (simulate k-space from NIfTI via
3D FFT) or **prospectively** (acquire raw k-space from scanner).

Retrospective simulation (available now):
- Simulate k-space from existing NIfTIs via `numpy.fft.fftn`
- Apply degradation and reconstruct
- Limitation: missing real coil noise correlations, B0 inhomogeneity, and
  k-space trajectory effects (EPI, spiral). Results are valid for information
  content, not for absolute SNR calibration.

Prospective acquisition (higher validity, future work):
- Request TWIX export (Siemens), PAR/REC raw (Philips), or ScanArchive (GE)
- Reconstruction toolkits: BART, MRZero, SigPy, PyNUFFT
- Enables real noise characterisation and cross-vendor k-space comparison

For this paper's dataset: retrospective simulation is immediately possible from
existing NIfTIs. Real k-space was not exported at acquisition time.

### Relation to reconstruction uncertainty literature

This framework connects to the fastMRI challenge (Knoll et al., 2020) evaluation
paradigm but extends it: instead of measuring image quality (SSIM, PSNR) as the
reconstruction target, we use **segmentation consistency** as the downstream
metric. This is clinically more relevant — the purpose of MRI reconstruction is
not to produce a nice-looking image but to support a reliable measurement.

---

---

## UV-anchored Gaussians for brain anatomy: borrowing from multi-view head avatars

Two recent papers solve the mesh-correspondence problem in a way directly
transferable to the brain anatomy case.

**HeadsUp** (Ntavelis et al., Apple, arXiv:2605.04035, 2026):
UV-parameterized 3D Gaussians anchored to a neutral head template mesh.
Gaussian count is decoupled from input view count. An encoder-decoder compresses
N multi-view images into a compact latent → decodes into Gaussians at fixed UV
positions on the template.

**MATCH** (Prinzler et al., arXiv:2603.15811, March 2026, code released):
Feed-forward transformer (0.5 s/frame) predicts Gaussian splat textures in the
fixed UV layout of a template mesh. Key mechanism: *registration-guided attention*
— each UV-map token attends exclusively to image tokens depicting its
corresponding mesh region.

### What transfers to brain MRI (and what does not)

**Transferable:**

| Concept | From | Brain MRI adaptation |
|---|---|---|
| UV-anchored Gaussians on template | HeadsUp | Replace head template with FIRST/FreeSurfer atlas per structure (hippocampus, amygdala, thalamus) |
| Automatic correspondence via UV | HeadsUp | UV(u,v) always addresses the same anatomical location — no SPHARM-PDM required |
| Σ_⊥ as boundary uncertainty | Both | Gaussian covariance perpendicular to surface normal = uncertainty in boundary location at that point |
| Registration-guided attention | MATCH | Each anatomical UV-token attends to MRI voxels from its spatial region — natural for multi-contrast fusion (T1, T2, FLAIR) |
| Encoder: N inputs → latent → Gaussians | HeadsUp | Encode N TTA reconstructions → consensus Gaussian parameters |

**Not transferable:**
- Rendering / splatting pipeline (not needed: we do not synthesise MRI images)
- View synthesis (no concept of "novel view" for volumetric MRI)
- Head-specific geometric prior (replaced by anatomical atlas)

### Why UV anchoring solves the correspondence problem

The obstacle for mesh averaging (Section above) was that marching-cubes meshes
from different segmentations have no consistent vertex ordering. UV anchoring
resolves this without complex spherical harmonics:

```
atlas mesh (e.g. FIRST hippocampus template)
       ↓
UV parametrisation: each surface point → (u, v) coordinate
       ↓
Gaussian_i at UV(u_i, v_i): position μ_i, covariance Σ_i, opacity α_i
```

Across N TTA reconstructions, each producing a segmentation mesh registered
to the same atlas:
- **μ_UV** = mean boundary position at anatomical location (u,v)
- **Σ_UV** = covariance of boundary positions = 3D uncertainty ellipsoid
- **Σ_UV⊥** (component perpendicular to surface normal) = boundary uncertainty
- **Σ_UV∥** (tangential components) = shape uncertainty

This gives a **spatially-resolved uncertainty map on the anatomy surface**:
"the boundary of CA1 hippocampus is uncertain by ±0.3 mm; the boundary of
subiculum is uncertain by ±1.1 mm" — clinically more informative than a
single CV% per whole structure.

### Full pipeline integrating all components

```
k-space
  → N reconstructions (varied method/regularisation)
  → SynthSeg --post per reconstruction → P_n(x ∈ r)
  → average probability maps → P_consensus(x ∈ r)
  → isosurface P=0.5 → consensus mesh
  → register to FIRST atlas → UV coordinates
  → fit UV-anchored Gaussians
  → Σ_UV⊥ = boundary uncertainty map
  → compare to clean-acquisition reference → information-loss surface
```

The information-loss boundary (Section 1) is now defined not as a scalar Δ%
but as a **surface field**: at which anatomical locations does degradation
cause boundary uncertainty to exceed the physics floor (0.05 mm equivalent)?

### Open question: registration-guided attention for multi-contrast

MATCH's attention mechanism (UV-token ↔ image-region) is directly applicable
to multi-contrast MRI: instead of N camera views, use T1 / T2 / FLAIR / DWI
as input channels. Each anatomical UV point attends to the voxels from its
spatial neighbourhood across all contrasts. This is architecturally cleaner
than concatenating contrasts as input channels and could be used to train a
contrast-aware probabilistic atlas.

Whether this architecture can be fine-tuned from the face/head domain to brain
anatomy (domain adaptation from RGB multi-view to MRI multi-contrast) is an
open question. The geometric framework (UV template + Gaussian covariance)
transfers regardless of the input modality.

---

*Pilot data collected on n=1 (self), 3 scanners (GE 3T 2018, Siemens 1.5T 2022,
Philips 1.5T 2024), SynthSeg robust, FreeSurfer 8.0.0. Scripts in `reprocess_2026/`.*
