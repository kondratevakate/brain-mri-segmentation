# Kate n=1 reprocessing — SynthSeg volumetry (MIDL 2026 hook)

### Table 1 — cross-vendor longitudinal (T1, SynthSeg)

| Region | 2018 (3T GE) | 2022 (1.5T Siemens) | 2024 (1.5T Philips) | Max Δ % |
|---|---|---|---|---|
| L Hippocampus | 3.85 | 3.79 | 3.59 | 7.3 |
| R Hippocampus | 3.77 | 3.58 | 3.26 | 15.7 |
| L Amygdala | 1.71 | 1.72 | 1.61 | 6.5 |
| R Amygdala | 1.85 | 1.57 | 1.45 | 28.2 |
| L Thalamus | 6.72 | 6.67 | 7.12 | 6.8 |
| R Thalamus | 6.86 | 6.78 | 7.08 | 4.5 |
| L Caudate | 3.88 | 3.37 | 4.37 | 29.7 |
| R Caudate | 3.85 | 3.69 | 4.10 | 11.1 |
| L Putamen | 5.28 | 4.52 | 5.34 | 18.2 |
| R Putamen | 5.39 | 4.58 | 5.16 | 17.7 |
| L Pallidum | 1.44 | 0.99 | 1.27 | 45.3 |
| R Pallidum | 1.64 | 1.29 | 1.43 | 27.8 |

### Table 2 — within-session multi-contrast (2024 Philips, SynthSeg)

| Region | T1 3DI (0.5mm) | T1 FFE ax | T1 FFE sag | T2 FLAIR | T2 TSE ax | T2 TSE cor | Max Δ % |
|---|---|---|---|---|---|---|---|
| L Hippocampus | 3.59 | 3.71 | 3.87 | 3.51 | 3.56 | 3.68 | 10.4 |
| R Hippocampus | 3.26 | 3.46 | 3.73 | 3.45 | 3.53 | 3.39 | 14.4 |
| L Amygdala | 1.61 | 1.54 | 1.62 | 1.55 | 1.62 | 1.78 | 15.5 |
| R Amygdala | 1.45 | 1.62 | 1.68 | 1.94 | 1.57 | 1.74 | 33.9 |
| L Thalamus | 7.12 | 6.60 | 7.46 | 6.87 | 6.77 | 7.13 | 13.0 |
| R Thalamus | 7.08 | 6.72 | 7.16 | 7.18 | 6.95 | 6.88 | 6.9 |
| L Caudate | 4.37 | 3.49 | 3.70 | 3.76 | 3.51 | 3.42 | 27.8 |
| R Caudate | 4.10 | 3.81 | 3.66 | 4.23 | 3.84 | 3.67 | 15.4 |
| L Putamen | 5.34 | 5.19 | 4.92 | 5.35 | 5.35 | 5.30 | 8.7 |
| R Putamen | 5.16 | 5.07 | 4.67 | 5.35 | 5.03 | 5.16 | 14.6 |
| L Pallidum | 1.27 | 1.16 | 1.12 | 1.27 | 1.29 | 1.36 | 22.2 |
| R Pallidum | 1.43 | 1.42 | 1.33 | 1.56 | 1.47 | 1.59 | 19.3 |

### SynthSeg QC scores (native, 0–1; flag < 0.65)

- **2018_ge_fspgr**: min=0.73 — ok
- **2022_sie_t1se**: min=0.72 — ok
- **2024_phi_3di**: min=0.60 — FLAG general grey matter=0.60
- **2024_phi_flair**: min=0.72 — ok
- **2024_phi_t1ffe_ax**: min=0.72 — ok
- **2024_phi_t1ffe_sag**: min=0.72 — ok
- **2024_phi_t2tse_ax**: min=0.73 — ok
- **2024_phi_t2tse_cor**: min=0.71 — ok

### Table 3 — cross-pipeline (SynthSeg vs FastSurfer seg_only, mL, vox_size 1mm)

**2018 GE (3T, 1mm)**

| Region | SynthSeg | FastSurfer | diff % |
|---|---|---|---|
| L Hippocampus | 3.85 | 3.91 | +1.6 |
| R Hippocampus | 3.77 | 3.95 | +4.7 |
| L Amygdala | 1.71 | 1.47 | -14.3 |
| R Amygdala | 1.85 | 1.58 | -14.9 |
| L Thalamus | 6.72 | 6.78 | +1.0 |
| R Thalamus | 6.86 | 6.32 | -7.8 |
| L Caudate | 3.88 | 3.42 | -11.9 |
| R Caudate | 3.85 | 3.45 | -10.6 |
| L Putamen | 5.28 | 4.90 | -7.3 |
| R Putamen | 5.39 | 4.89 | -9.3 |
| L Pallidum | 1.44 | 1.74 | +20.4 |
| R Pallidum | 1.64 | 1.69 | +2.8 |

**2024 Philips (1.5T, 0.5mm, 3D-IR) — FastSurfer FAILED (do not use numbers)**

FastSurfer self-flagged the run: `run_prediction.py:713 WARNING: Total segmentation
volume is too small. Segmentation may be corrupted.` BrainSeg = 167 mL (normal ~1200 mL);
subcortical labels collapsed to ~0 (thalamus 0.01 mL, caudate/pallidum 0.00 mL).

Cause: the 2024 scan is 3D inversion-recovery (IR) contrast; FastSurfer's VINN network is
trained on T1-MPRAGE-like contrast and has no contrast-agnostic mode, so this scan is
out-of-distribution and the segmentation collapsed. SynthSeg (contrast-agnostic by design)
segmented the same scan successfully (see Table 1).

=> This is itself a reproducibility finding (pipeline x contrast interaction), NOT a valid
   volume comparison. The raw garbage numbers are intentionally omitted.


### Table 4 — FastSurfer FULL recon QC, 2018 GE only (the one valid surface scan)

Real topological QC (unavailable from SynthSeg/seg_only). 2022 (5mm) and 2024 (3D-IR) excluded.

| Metric | Value | Note |
|---|---|---|
| Surface holes (defects pre-fix) | lh 25 / rh 20 / **total 45** | clean for 3T 1mm (brake threshold ~hundreds) |
| Final surface Euler | 2 (0 holes) both hemispheres | topology fixed successfully |
| Mean cortical thickness | lh 2.504 / rh 2.518 mm | normal adult ~2.5 mm |
| BrainSegVol | 1087.2 mL | — |
| eTIV | 1379.9 mL | matches SynthSeg ICV 1350 mL (independent cross-check) |
| recon-surf runtime | 2.54 h CPU | — |

### Table 5 — Reuter symmetry test: method-variance FLOOR vs cross-scanner (2018, SynthSeg)

Same 2018 scan, +/-3deg trilinear pair (both interpolated). Within-pair spread = method floor.

| Region | FLOOR % | cross-scanner % | ratio |
|---|---|---|---|
| L Hippocampus | 2.4 | 7.3 | 3.1x |
| R Hippocampus | 0.9 | 15.7 | 18.2x |
| L Amygdala | 2.6 | 6.5 | 2.5x |
| R Amygdala | 0.2 | 28.2 | 130.5x |
| L Thalamus | 1.2 | 6.8 | 5.8x |
| R Thalamus | 1.3 | 4.5 | 3.4x |
| L Caudate | 0.9 | 29.7 | 33.1x |
| R Caudate | 1.9 | 11.1 | 5.9x |
| L Putamen | 1.5 | 18.2 | 11.8x |
| R Putamen | 0.4 | 17.7 | 45.2x |
| L Pallidum | 1.6 | 45.3 | 27.7x |
| R Pallidum | 2.2 | 27.8 | 12.7x |

Median floor 1.4% vs median cross-scanner 16.7% => cross-scanner variability is 12x the method floor (scanner effect is real, not processing noise).


### Table 6 — Decomposition of rotation floor: physics vs model instability

Same 2018 scan, +3° rotation. Floor = 1.4% consists of:

| Component | Value | What it is |
|---|---|---|
| Interpolation only (physics) | **0.05%** | rotate the label map, no model re-run |
| Model instability | **1.36%** | what the network adds on top |
| **Total floor** | **1.37%** | 97% is model, 3% is physics |

A perfectly equivariant model would give 0.05%. SynthSeg is not equivariant.

### Table 7 — 9-angle TTA sweep (SynthSeg, -12° to +12° in 3° steps)

| Region | CV % | TTA mean (mL) | max excursion at ±12° |
|---|---|---|---|
| L Hippocampus | 0.72 | 3.789 | 1.36% |
| R Hippocampus | 1.27 | 3.757 | 2.34% |
| L Amygdala | 1.81 | 1.662 | 5.49% |
| R Amygdala | 1.83 | 1.839 | 4.80% |
| L Thalamus | 1.21 | 6.751 | 1.98% |
| R Thalamus | 1.29 | 6.821 | 2.52% |
| L Caudate | 0.69 | 3.854 | 2.02% |
| R Caudate | 0.88 | 3.863 | 1.45% |
| L Putamen | 0.71 | 5.317 | 0.21% |
| R Putamen | 0.28 | 5.384 | 0.24% |
| L Pallidum | 1.36 | 1.469 | 3.19% |
| R Pallidum | 1.38 | 1.650 | 2.43% |

Median CV = **1.24%** (9-angle TTA). Amygdala most sensitive (5.5% at ±12°).
Orientation response is ASYMMETRIC for most structures — TTA reduces bias, not just variance.
TTA-corrected volumes = "TTA mean (mL)" column above.

### Key numbers for presentation

| Metric | Value |
|---|---|
| Physics interpolation floor | 0.05% |
| Model instability (SynthSeg, ±3°) | 1.36% |
| TTA floor (9 angles) | 1.24% CV |
| Cross-scanner median spread | 16.7% |
| Cross-scanner max (pallidum) | 45.3% |
| Scanner / method floor ratio | **12x** |
| Clinical detection target | ~2%/year |
| SynthSeg vs FastSurfer (amygdala) | −14% systematic offset |
| FastSurfer surface holes (2018) | 45 (clean) |
| Cortical thickness (2018) | lh 2.50 / rh 2.52 mm |

### Table 8 — Rotation floor: SynthSeg vs FastSurfer (same ±3° pair, 2018)

| Region | SynthSeg floor % | FastSurfer floor % |
|---|---|---|
| L Hippocampus | 2.37 | 0.58 |
| R Hippocampus | 0.87 | 2.01 |
| L Amygdala | 2.57 | 2.40 |
| R Amygdala | 0.22 | 2.14 |
| L Thalamus | 1.17 | 0.89 |
| R Thalamus | 1.31 | 1.25 |
| L Caudate | 0.90 | 2.03 |
| R Caudate | 1.87 | 1.62 |
| L Putamen | 1.54 | 1.69 |
| R Putamen | 0.39 | 1.34 |
| L Pallidum | 1.64 | 1.11 |
| R Pallidum | 2.18 | 0.70 |

Median: SynthSeg **1.43%** vs FastSurfer **1.48%** — essentially tied.
Both DL segmenters have the same ~1.5% rotation floor → orientation instability
is a general property of non-equivariant CNNs, not architecture-specific.
Combined with cross-method r=-0.068 (uncorrelated errors): same floor magnitude,
different failure locations.

### Table 9 — Atlas-based reference (FreeSurfer 7.4) vs DL, 2018 GE (mL)

Exp 3 (Reuter): FS7.4 is atlas-based (GCA, Talairach) — the established reference.
SynthSeg(=FS8) and FastSurfer are DL. FS7.4 is a reference by convention, not
ground truth; n=1, one scan. 2022/2024 pending (longitudinal recon still running).

| Region | FS7.4 atlas | SynthSeg | FastSurfer | SS vs atlas | FS vs atlas |
|---|---|---|---|---|---|
| L Hippocampus | 3.85 | 3.85 | 3.91 | −0.0% | +1.6% |
| R Hippocampus | 3.74 | 3.77 | 3.95 | +0.8% | +5.5% |
| L Amygdala | 1.56 | 1.71 | 1.47 | +10.0% | −5.7% |
| R Amygdala | 1.70 | 1.85 | 1.58 | +9.0% | −7.2% |
| L Thalamus | 6.28 | 6.72 | 6.78 | +7.1% | +8.1% |
| R Thalamus | 5.68 | 6.86 | 6.32 | +20.7% | +11.3% |
| L Caudate | 3.28 | 3.88 | 3.42 | +18.3% | +4.3% |
| R Caudate | 3.40 | 3.85 | 3.45 | +13.3% | +1.3% |
| L Putamen | 4.71 | 5.28 | 4.90 | +12.1% | +4.0% |
| R Putamen | 4.69 | 5.39 | 4.89 | +14.8% | +4.1% |
| L Pallidum | 1.52 | 1.44 | 1.74 | −5.1% | +14.3% |
| R Pallidum | 1.66 | 1.64 | 1.69 | −0.7% | +2.1% |

Median |Δ| from atlas: **SynthSeg 9.5%, FastSurfer 4.9%** — FastSurfer is closer
to the atlas reference. SynthSeg systematically over-estimates subcortical volumes
(thalamus/caudate/putamen). Confirms FS8/SynthSeg is not a neutral reference.
