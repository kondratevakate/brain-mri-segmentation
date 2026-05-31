# Datasets for structural MRI test-retest segmentation benchmarking

Curated for this project: **comparing reproducibility of FreeSurfer / SynthSeg / Brainchop** across repeated scans of the same subjects. Organised by how directly each dataset fits the benchmark.

Currently in use: **SIMON** (`data/SIMON_pheno.csv`) and **SRPBS** (`data/srpbs_*`).

---

## Tier 1 — Already in use

| Dataset | N subj | Scans/subj | Field | Access | Notes |
|---|---|---|---|---|---|
| [**SIMON**](http://fcon_1000.projects.nitrc.org/indi/retro/SIMON.html) | 1 | 73 | varies, multi-site | Open S3 / [CONP BIDS](https://github.com/conpdatasets/SIMON-dataset) | Single volunteer × 73 sessions × multiple scanners; gold standard for single-subject reliability |
| [**SRPBS Traveling Subject MRI**](https://bicr-resource.atr.jp/srpbsts/) | 9 | 143 sessions total (~12–16/subj) | GE/Siemens/Philips 3T | ATR application | 9 subjects × 12 sites × 143 sessions; best Asian multi-vendor traveling-subjects resource |

---

## Tier 2 — Drop-in additions (open, BIDS, T1 structural)

These can be added to the benchmark with minimal preprocessing work.

| Year | Dataset | N subj | Scans/subj | Interval | Field | Access |
|---|---|---|---|---|---|---|
| 2022 | [**MR-ART**](https://openneuro.org/datasets/ds004173) | 148 | 3 (still / low-motion / high-motion) | within session | 3T | OpenNeuro ds004173 |
| 2022 | [**MICA-MICs**](https://openneuro.org/datasets/ds003634) | 50 | 2 T1 + qT1 per subject | within session | 3T | OpenNeuro ds003634 |
| 2017 | [**MSC (Midnight Scan Club)**](https://openfmri.org/dataset/ds000224/) | 10 | 4 T1 + T2 | within ~6 weeks | 3T Siemens | OpenfMRI ds000224 |
| 2015 | [**MPI 7T test-retest**](http://openscience.cbs.mpg.de/7t_trt/) | 22 | 2 sessions, multi T1 | days apart | 7T | Open |
| 2014 | [**Maclaren test-retest**](https://openfmri.org/dataset/ds000239/) | 3 | **20 each** | 31 days | 3T GE | OpenfMRI ds000239 — flagship reliability dataset |
| 2013 | [**HCP-YA Test-Retest**](https://www.humanconnectome.org/) | 45 | 2 full sessions (T1+T2) | 1–11 months | 3T Siemens | HCP application |

**Recommended next addition: MR-ART** — 148 subjects, 3 controlled motion levels, BIDS. Directly tests segmenter robustness to motion without changing scanner or subject.

---

## Tier 3 — Multi-site / multi-vendor (traveling-subjects style)

Key for testing whether segmentors are robust to scanner differences — the main confound in clinical use.

| Year | Dataset | N subj | Sites/scanners | Field | Access |
|---|---|---|---|---|---|
| 2025 | [**ON-Harmony**](https://openneuro.org/datasets/ds004712) | 20 | 6 scanners × 3 vendors (GE/Siemens/Philips) | 3T | OpenNeuro — open, BIDS |
| 2021 | [**FTHP (Frequently Traveling Human Phantom)**](https://www.nitrc.org/projects/fthp) | — | multi-site | varies | NITRC |
| 2019 | [**SRPBS Traveling** (already in use)](https://bicr-resource.atr.jp/srpbsts/) | 9 | 12 sites Japan | mixed | ATR application |
| 2018 | Hawco 2018 | 4 | 5 scanners, 3 years | varies | No public link |
| — | [**CC-359 (Calgary-Campinas)**](https://sites.google.com/view/calgary-campinas-dataset/) | 359 | 3 vendors × 1.5T+3T | 1.5T/3T | Open — not retest but multi-vendor |
| — | [**CoRR**](http://fcon_1000.projects.nitrc.org/indi/CoRR/html/) | 1629 across 32 sites | 32 sites | varies | Open INDI — meta-aggregator |

---

## Tier 4 — Dense single-subject (longitudinal reliability)

Useful for studying within-subject variance over time (atrophy, measurement drift).

| Year | Dataset | Subject | # T1 scans | Span | Access |
|---|---|---|---|---|---|
| 2017 | [**Day2day**](https://bmcneurosci.biomedcentral.com/articles/10.1186/s12868-017-0383-y) | 8 (6F/2M, 24–32 yr) | 11–50 | 6 months | Email authors |
| 2015 | [**MyConnectome**](http://myconnectome.org/wp/) | M, 45 yr | 104 | 1.5 yr | Open |
| 2015 | [**Kirby Weekly**](http://www.nitrc.org/projects/kirbyweekly) | M, 40 yr | **158** | 3.5 yr | Open NITRC |
| 2015 | [**CCBD (Hangzhou Normal)**](https://doi.org/10.6084/m9.figshare.2007483) | 30 | 10 | 1 month | Open figshare |
| 2017 | [**MASSIVE**](http://www.massive-data.org/) | F, 25 yr | 18 | varies | Open |
| 2025+ | [**Taylor Hanayik**](https://github.com/hanayik/Taylor-Hanayik-Brain-Scans) | M, 24+ yr | ≥1/month ongoing | years | Open GitHub |

---

## Tier 5 — Ultra-high-field (7T) and ex-vivo references

For ceiling analysis: what is the maximum achievable segmentation detail?

| Dataset | N | Resolution | Field | Access |
|---|---|---|---|---|
| [**AHEAD (Amsterdam)**](https://uvaauas.figshare.com/articles/dataset/_/10007840) | 105 (18–80 yr) | 0.7 mm iso T1 + qMRI; v2: 0.5 mm subcortex | 7T | Open figshare |
| [**HCP 7T Test-Retest**](https://www.humanconnectome.org/) | 33 | submm T1+T2 | 7T | HCP application |
| [**MPI 7T test-retest**](http://openscience.cbs.mpg.de/7t_trt/) | 22 | T1 submm | 7T | Open |
| [**Edlow 100-micron ex-vivo**](https://www.nature.com/articles/s41597-019-0254-8) | 1 cadaver (F, 58 yr) | **100 µm isotropic** | 7T, 100h scan | Open — ground truth ceiling |

---

## Tier 6 — Low-field / portable (clinical translation)

Tests whether segmentors can run at all in resource-limited or bedside settings.

| Year | Dataset | N | Setup | Access |
|---|---|---|---|---|
| 2025 | [**ULF morphometry test-retest**](https://direct.mit.edu/imag/article/doi/10.1162/IMAG.a.930/) | — | 64mT Hyperfine ↔ 3T same-day, healthy adults | Raw images public |
| 2023 | [**M4Raw (0.3T k-space)**](https://zenodo.org/records/7523691) | 183 healthy (18–32 yr) | 0.3T multi-channel, T1/T2/FLAIR; **not defaced** | Zenodo open |
| 2024 | [**LISA (neonatal ULF)**](https://www.medrxiv.org/content/10.1101/2025.07.01.25330469.full.pdf) | neonates, multi-site | 64mT SWOOP, Africa+Pakistan | Release pipeline |
| 2024 | [**Nigerian Clinical-MRI**](https://www.nature.com/articles/s41597-025-04743-0) | 88 (HC+dementia+PD) | 1.5T/3T clinical quality Africa | Open Sci Data 2025 |

---

## Tier 7 — Longitudinal clinical cohorts (disease + aging)

For testing segmentor performance across pathology and atrophy trajectories.

### Alzheimer's / MCI

| Dataset | N | T1 schedule | Access |
|---|---|---|---|
| [**MIRIAD**](https://www.ucl.ac.uk/drc/research/methods/minimal-interval-resonance-imaging-alzheimers-disease-miriad) | 69 (46 AD + 23 ctrl) | Up to 9 scans over 2 yr | Open (registration) |
| [**ADNI 1/GO/2/3/4**](https://adni.loni.usc.edu/) | 2400+ | 6–12 mo intervals, up to 10+ scans | Application |
| [**OASIS-3**](https://www.oasis-brains.org/) | 1098 | ~2000 sessions | Application |
| [**OASIS-Longitudinal**](https://www.oasis-brains.org/) | 150 | ≥2 (183–1707 d) | Open |

### Multiple sclerosis (lesion + atrophy)

| Dataset | N | T1 schedule | Access |
|---|---|---|---|
| [**MSSEG-2**](https://portal.fli-iam.irisa.fr/msseg-2/) | 100 | 2 timepoints ~1 yr | Open (challenge) |
| [**ISBI 2015 MS Lesion**](https://smart-stats-tools.org/lesion-challenge) | 9 | 4–6 timepoints | Open |

### Tumor / post-op (TCIA)

| Dataset | N | T1 timepoints | Access |
|---|---|---|---|
| [**LUMIERE**](https://www.cancerimagingarchive.net/collection/lumiere/) | 91 GBM | Pre-op + ~4 follow-ups | Open TCIA |
| [**Burdenko-GBM-Progression**](https://www.cancerimagingarchive.net/collection/burdenko-gbm-progression/) | 180 | Multi-timepoint | TCIA |
| [**UPENN-GBM**](https://www.cancerimagingarchive.net/collection/upenn-gbm/) | 630 | Pre + post-op | TCIA |

### Aging / lifespan

| Dataset | N | T1 schedule | Access |
|---|---|---|---|
| [**Lothian Birth Cohort 1936**](https://www.ed.ac.uk/lothian-birth-cohorts) | ~1000 | T1 at ages 73, 76, 79, 82, 86, 88 (6 waves) | Application |
| [**UK Biobank Imaging**](https://www.ukbiobank.ac.uk/) | 100k target | Baseline + repeat (~10k done) | Application |
| [**CCNP (Chinese Color Nest)**](https://www.nature.com/articles/s41597-023-02377-8) | 1520 target | 3 waves, 6–90 yr | National Science Data Bank |

---

## Asian cohorts (complement to SRPBS already in use)

| Dataset | N | Country | T1 design | Access |
|---|---|---|---|---|
| [**KBASE**](https://dss.niagads.org/cohorts/korean-brain-aging-study-for-the-early-diagnosis-and-prediction-of-ad-kbase/) | ~500 | 🇰🇷 Korea | CN/MCI/AD longitudinal | NIAGADS |
| [**J-ADNI**](https://humandbs.dbcls.jp/en/hum0043-v1) | 537 | 🇯🇵 Japan | ADNI protocol longitudinal | NBDC |
| [**CHIMGEN**](https://www.nature.com/articles/s41380-019-0627-6) | 7000+ | 🇨🇳 China | Cross-sectional, 33 sites | Consortium |
| [**SLIM**](http://fcon_1000.projects.nitrc.org/indi/retro/southwestuni_qiu_index.html) | ~600 | 🇨🇳 China | 3 longitudinal waves | INDI open |
| [**IBID**](https://pmc.ncbi.nlm.nih.gov/articles/PMC8114860/) | 300 | 🇮🇷 Iran | 20–70 yr balanced | NBML application |

---

## Raw k-space (for reconstruction / degradation experiments)

These provide **raw k-space**, not just reconstructed NIfTI — required for the
information-loss / k-space degradation framework (see `docs/FUTURE_WORK.md`):
degrade k-space → reconstruct with method X → segment → measure recovery.
All three are *structural* (anatomical T1/T2/FLAIR) k-space, not fMRI BOLD.

| Year | Dataset | N subj | Field | Contrast | Access | Notes |
|---|---|---|---|---|---|---|
| 2017 | [**Calgary-Campinas k-space**](https://www.ccdataset.com/download) | 526 | 1.5T+3T | structural | Open (custom) | Raw k-space HDF5 + paired NIfTI; 3 vendors; not defaced; 90 GB |
| 2023 | [**M4Raw**](https://zenodo.org/records/7523691) | 183 | 0.3T | T1/T2/FLAIR | Open CC-BY-4.0 | Multi-channel k-space; explicitly NOT defaced; partial head coverage; doi:10.1038/s41597-023-02181-4 |
| 2019 | [**fastMRI Brain**](https://fastmri.med.nyu.edu/) | 6970 | 1.5T+3T | structural | Application (DUA) | Raw k-space HDF5; deidentified, not defaced; DUA from NYU; doi:10.1148/ryai.2020190007 |

**Privacy note:** none of these are defaced, and raw k-space reconstructs the full
head — facial-reconstruction / re-identification risk applies. Deface after
reconstruction before any sharing.

**Recommended for the k-space experiment: Calgary-Campinas** — has *paired
NIfTI + raw k-space* from 3 vendors, so reconstruction-ensemble and cross-vendor
degradation can both be tested against a known reference.

---

## Priority for next benchmarking steps

Based on the current project scope (FreeSurfer vs SynthSeg vs Brainchop reproducibility):

| Priority | Dataset | Reason |
|---|---|---|
| **High** | MR-ART | Tests motion robustness — directly relevant to clinical translation |
| **High** | ON-Harmony | Multi-vendor structural: does ICC differ by vendor × segmentor? |
| **High** | Maclaren (3 × 20 scans) | Gold-standard reliability; small enough to process quickly |
| **Medium** | HCP Test-Retest (45 subj) | Large N, 2 full protocols; ABCD standard comparison |
| **Medium** | MIRIAD | AD atrophy: does segmentor ICC hold under pathology? |
| **Low** | AHEAD 7T | Ceiling analysis: what can the best scanner resolve? |
| **Low** | ULF morphometry | Floor analysis: can segmentors work at 64mT? |

---

## How to add a new dataset

1. Download / apply for access (see links above)
2. Convert to BIDS T1 NIfTI: `mri_convert <input> <output>.nii.gz`
3. Add entry to `data/` and update `data/` CSV inventory
4. Run segmentation pipeline: `scripts/run_all_segmentors.sh <subject_dir>`
5. Update reproducibility analysis: `scripts/evaluation/compute_icc.py`
