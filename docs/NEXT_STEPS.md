# Next steps — reproducibility follow-up (post-acceptance, for talk + future work)

Paper accepted (MIDL 2026). These items respond to review feedback and prepare a
planned follow-up study. Processing scripts live in `reprocess_2026/`; outputs +
the detailed protocol are in the data folder (not in git — derived volumes).

## Terminology / correctness fixes to carry into the talk / any revision
- [ ] FastSurfer has **no `recon-all`** — entry is `run_fastsurfer.sh` -> `recon-surf.sh`.
- [ ] FastSurferVINN = **CNN with internal re-scaling** (voxel-size-independent NN),
      NOT a vision transformer. Cite Henschel et al. 2022,
      doi:10.1016/j.neuroimage.2022.118933.
- [ ] FreeSurfer 8 is **not a neutral reference** (its segmentation IS SynthSeg).
      Use atlas-based **FreeSurfer 7.4** as the reference.
- [ ] State the **FreeSurfer version** wherever "recon-all" appears.
- [ ] Longitudinal pipeline citation: Reuter et al. 2012,
      doi:10.1016/j.neuroimage.2012.02.084.
- [ ] Re-verify every reference (placeholder/author-stub citations were flagged).

## Experiments
- [x] **Exp 1 — Symmetry / method-variance floor** (pilot, SynthSeg, 2018).
      +/-3 deg trilinear pair (both interpolated). Result: median method floor
      **1.4%** vs median cross-scanner spread **16.7%** (~12x; up to 130x for
      R amygdala). => scanner effect is real, not processing noise. Addresses the
      "cross-sectional overestimates variance" critique. (Table 5 in summary.)
- [ ] **Exp 1b** — push the same pair through FreeSurfer 7.4 + FastSurfer
      **longitudinal** pipelines for each method's floor; sweep rotation 1/3/5 deg.
- [~] **Exp 2 — FreeSurfer 7.4 within-subject longitudinal template** (RUNNING).
      `recon-all -all` x3 sessions -> `-base` -> `-long`. Compare cross-sectional
      vs longitudinal variance (the key point: longitudinal shrinks within-subject
      variance). Risk: 2022 (5mm) / 2024 (3D-IR) may fail surface recon — failure
      is itself a finding. Script: `run_fs_longitudinal.sh`.
- [ ] **Exp 3 — FS7.4 atlas vs DL reference table.** Once Exp 2a lands, tabulate
      FS7.4 aseg vs SynthSeg(=FS8) vs FastSurfer for 2018. No extra compute.
- [ ] **Exp 4 — FastSurfer longitudinal** (second machine). 2024 IR will fail VINN.

## SIMON longitudinal design notes
- [ ] Separate variance sources: acquisition (hardware/software/calibration/motion)
      vs biology (incl. hydration) vs processing. Exp 1 isolates processing.
- [ ] Slope estimation with dedicated longitudinal processing; note both anatomy
      AND scanners change over years.
- [ ] Where same-hardware isn't possible: scan multiple participants on old+new
      scanner to estimate the scanner effect; include **site as a factor** in the
      statistical model (standard multi-centre approach).
- [ ] Always interpolate BOTH images in any symmetric / test-retest construction.

## Logistics
- [ ] Decide hardware split: machine A = Exp 2; machine B = Exp 4 + Exp 1b.
