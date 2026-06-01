# Handoff: finish the FreeSurfer 7.4 longitudinal template (Exp 2)

This is a self-contained recipe to **resume the longitudinal run on another
machine** and to **extract the conclusion once it finishes**. The runnable script
is public: `pipeline/run_fs_longitudinal.sh` in
[your-brain-mri-visualization](https://github.com/kondratevakate/your-brain-mri-visualization).

## Why this experiment exists (so it isn't lost)

The MIDL paper *showed* longitudinal FreeSurfer 8 in one figure but **did not
quantify** how much the unbiased-template `-long` pipeline reduces within-subject
variance, and explicitly listed in Limitations: *"we did not evaluate FastSurfer
in longitudinal mode (`--long`)"* and (commented out) *"we treat all sessions
independently and not use `--long`."* The paper's only longitudinal reproducibility
number is **ICC(SIMON) = 0.14 (poor)** on cross-sectional processing.

**This run fills that gap:** measure, on the n=1 three-scanner data, how much the
`-long` pipeline lowers the method floor vs independent cross-sectional processing.
Predicted (design logic, not yet measured): `-long` lowers the processing floor
(~1.4%) but NOT the cross-scanner spread (~17%) — confirming the scanner effect is
real. Risk: cross-vendor (5 mm / 1 mm / 0.5 mm) base template may be degenerate or
a timepoint may fail surface recon — that failure is itself a finding.

## State at thread close (2026-06-01)

| Stage | State |
|---|---|
| 2018 cross-sectional | ✅ DONE (`fs_long/2018/scripts/recon-all.done`) |
| 2022 cross-sectional (5 mm) | ~90% (Sphere rh) — slow on the thick slice, as predicted |
| 2024 cross-sectional (0.5 mm) | ⛔ not started |
| `-base` template (`kate_base`) | ⛔ not started (barrier: needs ≥2 cross-sectional) |
| `-long` ×N | ⛔ not started |

Outputs live under `…/01_my_brain_years/reprocessed_2026/fs_long/`
(2018 ≈ 264 MB, 2022 ≈ 166 MB so far).

## Run on the second laptop (container)

**Critical — avoid the two-writer race.** `fs_long/` syncs via YandexDisk. Do NOT
run two machines writing the same synced `fs_long/` at once → corrupted recon-all.
Pick ONE:
- **(A) Move the run:** stop the first laptop's container, then run on laptop B
  against the synced folder (idempotent — skips 2018, resumes the rest, parallel).
- **(B) Isolate output (recommended if sync is flaky):** on laptop B point `DATA`
  at a folder whose `reprocessed_2026/fs_long` is **local, not synced**; copy the
  finished `summary` back at the end. Inputs (`images/`) can stay read-only synced.

```bash
# laptop B, one-time
docker pull freesurfer/freesurfer:7.4.1
git clone https://github.com/kondratevakate/your-brain-mri-visualization
cd your-brain-mri-visualization

# point at the data root (folder containing images/ and reprocessed_2026/)
export DATA="/path/to/01_my_brain_years"
export FS_LICENSE_FILE="/path/to/license.txt"
export FS_PARALLEL=3        # run 3 subjects at once (recon-all is ~single-threaded;
export FS_THREADS=2         #   data-parallel beats -threads on one subject)

bash pipeline/run_fs_longitudinal.sh
```

The script is **idempotent**: it skips any timepoint with a `recon-all.done`
marker, runs cross-sectional in parallel (`FS_PARALLEL`), builds the `kate_base`
barrier, then runs the `-long` passes in parallel. A partial timepoint (no `.done`)
is restarted from scratch — so 2022 will restart unless its `.done` exists when B
starts.

## Extract the conclusion once it finishes

After `-long` completes you have, per timepoint, two segmentations:
- cross-sectional: `fs_long/<tp>/stats/aseg.stats`
- longitudinal:    `fs_long/<tp>.long.kate_base/stats/aseg.stats`

The headline number is **within-subject variance, cross-sectional vs longitudinal**:

```python
# per structure: CV across the 3 timepoints, computed both ways
import re, statistics as st
def vols(p):
    o={}
    for L in open(p):
        if L.startswith('#') or not L.strip(): continue
        c=L.split()
        if len(c)>=5: o[c[4]]=float(c[3])/1000   # Volume_mm3 -> mL
    return o
tps=['2018','2022','2024']
xs=[vols(f'fs_long/{t}/stats/aseg.stats') for t in tps]                 # cross-sectional
lo=[vols(f'fs_long/{t}.long.kate_base/stats/aseg.stats') for t in tps]  # longitudinal
for k in ['Left-Hippocampus','Right-Amygdala','Left-Pallidum']:
    cv_x=st.pstdev([d[k] for d in xs])/st.mean([d[k] for d in xs])*100
    cv_l=st.pstdev([d[k] for d in lo])/st.mean([d[k] for d in lo])*100
    print(f'{k}: cross-sectional CV {cv_x:.1f}%  ->  longitudinal CV {cv_l:.1f}%')
```

**The conclusion to record (in `docs/RESULTS_n1_pilot.md` as Table 10):**
- If longitudinal CV < cross-sectional CV → `-long` reduces the *method* floor
  (expected). Report the magnitude — this is the number the paper never gave.
- Compare the reduction against the cross-scanner spread (~17%): if the spread
  survives, the scanner effect is confirmed real and not fixable by `-long`.
- Note any timepoint that failed surface recon (esp. 2022 5 mm) — a partial base
  template is itself a finding about cross-vendor longitudinal processing.

## Where this is tracked
- Plan / checklist: `docs/NEXT_STEPS.md` (Exp 2).
- Framework + paper-gap: `docs/FUTURE_WORK.md`.
- Results tables: `docs/RESULTS_n1_pilot.md` (add Table 10 when done).
- Script: viz repo `pipeline/run_fs_longitudinal.sh` (parallel, idempotent).
