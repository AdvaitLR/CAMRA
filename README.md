# CAMRA

Code and results for **CAMRA: Cross-Architecture Multimodal Reinforcement Learning with Federated Adaptation for IoT Malware Detection and Classification**.

CAMRA fuses three behavioural data streams of IoT malware executions (network traffic **PCAP**, system-resource logs **SAR**, and system calls **STRACE**) through cross-modal attention, across four CPU architectures (ARM, MIPS, MIPSEL, x86). A reinforcement-learning controller adapts the per-class loss weights during training, and a federated stage adapts the centrally trained model to architecture-specific clients.

## Repository structure

```
CAMRA/
├── notebooks/
│   ├── 01_dataset_creation.ipynb   # raw parquet files -> hash-aligned, curated dataset (+ Fig. 2 raw counts)
│   ├── 02_camra_pipeline.ipynb     # pre-processing, training, ablations, holdouts, statistics
│   └── 03_figures.ipynb            # regenerates every figure from results/base
├── results/                        # outputs of the final runs reported in the paper
│   ├── base/                       # base configuration (no holdout)
│   ├── exArch-ARM/  exArch-MIPS/  exArch-MIPSEL/  exArch-x86/          # architecture holdouts
│   ├── exFam-DarkNexus/                                                # family holdout
│   └── exArch-<arch>_exFam-DarkNexus/                                  # combined holdouts (x4)
│       ├── reports/     # multiseed_results.json, paired_statistics*.json, computational_complexity*.json, umap_cluster_scores.json
│       ├── artifacts/   # predictions, curves, training histories, RL controller logs, UMAP projections
│       └── manifests/   # split_manifest*.csv, preprocessing_manifest*.json
├── scripts/prepare_release.py      # (maintainers) produces notebooks/02 from the Kaggle notebook
├── requirements.txt
├── CITATION.cff
└── LICENSE
```

## Dataset

The **CIC-YNU-IoT-MAL-26** dataset is not redistributed here. Download it from the Canadian Institute for Cybersecurity and cite:

> S. Dadkhah et al., "CIC-YNU-IoTMal: A comprehensive multilayer dataset for static and dynamic analysis of IoT malware behavior," *Information Systems*, vol. 140, p. 102722, 2026.

The **split manifests** (`results/<run>/manifests/split_manifest*.csv`) list the file hash, architecture, malware family, and split (train / val_select / val_reward / test) of every one of the 17,023 aligned executions, so the exact splits used in the paper can be rebuilt from the dataset. The **preprocessing manifests** list the 151 selected features (38 PCAP, 38 SAR, 75 STRACE), the label mapping, and the class weights.

## Environment

The experiments were run on Kaggle notebooks (2 × NVIDIA T4 GPU, 4-core Intel Xeon CPU).

```bash
pip install -r requirements.txt
```

## Reproducing the results

### 1. Build the aligned dataset — `01_dataset_creation.ipynb`

Set `DATA_ROOT` (folder with one sub-folder per architecture, each containing `PCAP.parquet`, `SAR.parquet`, `STRACE.parquet`) and `OUT_DIR` in the configuration cell, then run all cells. The notebook drops `Unknown` labels and constant features, computes per-hash statistics for each file, joins the three streams on the file hash, merges families with fewer than five executions into `Other`, and saves `aligned_dataset.parquet`. STEP 4 counts the raw rows per architecture, modality, and label used for Fig. 2.

### 2. Run the pipeline — `02_camra_pipeline.ipynb`

Point `ALIGNED_DATASET_PATH` to the folder containing `aligned_dataset.parquet` and `OUT_DIR` to an output folder (the notebook ships with the Kaggle paths used for the paper). With the default settings, one run trains every configuration over the ten seeds `[42, 16, 29, 34, 56, 67, 71, 86, 99, 46]`:

- CAMRA (centralized DRL) and the federated model,
- Fixed Weighting and Focal Loss, the single-modality and pairwise models, and the RF / XGBoost / MLP / 1D-CNN baselines,
- the test-time modality holdout and, for holdout runs, the evaluation on the held-out rows,
- paired statistics (bootstrap CIs, Wilcoxon tests, Holm correction), complexity, and communication cost.

One base run takes about 5 hours on the hardware above.

**Holdout configurations.** Set the following in the configuration cell and rerun:

| Configuration | `EXCLUDE_ARCH` | `EXCLUDE_MALWARE_FAMILY` |
|---|---|---|
| Base | `None` | `None` |
| Architecture holdout | `"ARM"`, `"MIPS"`, `"MIPSEL"`, or `"x86"` | `None` |
| Family holdout | `None` | `"DarkNexus"` |
| Combined holdout | `"ARM"`, `"MIPS"`, `"MIPSEL"`, or `"x86"` | `"DarkNexus"` |

Excluded rows are removed from training and validation and added to the test set. Output files are tagged with the configuration (e.g. `multiseed_results.json` inside the run's output folder, `plot_data_exArch-ARM.json`).

**Focal Loss + Prior control.** The control reported for the base configuration is run from the "Optional: Focal Loss + Prior control" cell by setting `RUN_FOCAL_PRIOR_CONTROL = True` and pointing `PREV_DATA` at a completed base run (base configuration only); its results are in `results/base/reports/focal_prior_control.json`.

### 3. Regenerate the figures — `03_figures.ipynb`

Runs entirely from `results/` (no training, no dataset needed) and writes every figure of the paper to `figures/`.

## Results in this repository

`results/` contains the outputs of the ten final runs reported in the paper (the base configuration and nine holdouts). Per-seed values of every configuration are in `reports/multiseed_results.json` under `raw_per_seed`, and the paired comparisons in `reports/paired_statistics*.json`. Headline results in the base configuration (mean ± population standard deviation over ten seeds):

| Model | Macro-F1 | Accuracy |
|---|---|---|
| CAMRA (centralized DRL) | 0.752 ± 0.012 | 0.984 |
| Federated model | 0.741 ± 0.008 | 0.986 |
| Fixed Weighting | 0.751 ± 0.017 | 0.988 |
| Focal Loss + Prior (control) | 0.757 ± 0.011 | 0.984 |

**Metric note.** Macro-F1 (the primary metric) averages per-class F1 over classes with at least five test samples; in the base configuration this excludes only `Other`, which has one test sample. The all-class Macro-F1 is reported alongside it in every results file (`macro_f1_all`).

## Citation

If you use this code, please cite the paper (see `CITATION.cff`) and the CIC-YNU-IoT-MAL-26 dataset.

## License

Released under the MIT License (see `LICENSE`). The dataset is subject to its own terms from the Canadian Institute for Cybersecurity.
