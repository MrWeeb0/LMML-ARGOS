# Laos: Bad BOMB

Unsupervised anomaly detection for close-up shell images.

## Submission and result

Submit [test-output.txt](test-output.txt), containing 28 relative image paths, one per line.

The competition feedback supplied by the user reports **Passed: 20/28 matches, 71.43% accuracy, 200 points**, for the submission displayed at **14/11/2026 22:43:49**. The pass threshold is 70%.

[evaluation.json](evaluation.json) records the feedback and its source. The hidden evaluator was not rerun during publication. The feedback does not include a file hash, so the recovered revision-2 output is preserved unchanged rather than claiming a verified byte-for-byte association with the evaluated upload. The flag was not supplied.

## Algorithm in four lines

1. Segment each shell, rotate its principal axis upright, crop and resize to 64 by 256 pixels, then normalize brightness.
2. Learn normal surface color with position-wise medians and median absolute deviations, and rank coherent local color defects.
3. Add frozen ImageNet ResNet-18 features scored by regularized Mahalanobis distance, plus silhouette anomalies measured through PCA reconstruction errors.
4. Retain the strongest 26 color candidates and select two new candidates with the smallest neural-rank times shape-rank product, producing exactly 28 paths.

Main methods: foreground segmentation, geometric alignment, chromaticity normalization, robust statistics, ResNet feature extraction, Mahalanobis distance, PCA, and rank fusion. No supplied defect labels are used.

## Files

| File | Purpose |
| --- | --- |
| main.py | Align images, fit or load the color atlas, rank images, and validate the saved selection. |
| model.npz | Saved median and MAD color atlas. |
| resnet_audit.py | Build aligned views, extract frozen ResNet features, and rank patch anomalies. |
| shape_audit.py | Rank silhouette anomalies using a 12-component PCA model. |
| refine.py | Combine the three rankings and regenerate the revised 28-image selection. |
| revision2/rankings.csv | Complete saved color, neural, and silhouette rank table. |
| test-output.txt | Recovered revision-2 submission. |
| baseline-output.txt | Earlier color-only selection, reported at 19/28. |
| manifest.json | Source image IDs, filenames, sizes, and SHA-256 hashes. |
| download.py | Download and hash-check the images in the manifest. |
| scores.csv | Baseline color scores and alignment geometry. |
| review.py, review.jpg | Generate and preserve a visual review of the selected images. |
| revision.json, summary.json, provenance.json | Historical generation records from the prepared revision. |
| evaluation.json | Later passing result reported by the user. |
| train-output.txt | Original format example, not training labels. |

Historical metadata retains the pre-evaluation unknown result. Use evaluation.json for the later user-reported feedback.

## Check the recovered submission

Use Python 3.11:

```sh
python -m pip install -r requirements.txt
python main.py --check
```

This verifies selection structure and rank agreement without downloading images. The published workflow runs the same check.

## Regenerate from the source images

Run from this directory:

```sh
python -m pip install -r requirements-refine.txt
python download.py
python main.py
python resnet_audit.py
python shape_audit.py
python refine.py --refresh
python main.py --check
python review.py
```

The saved rank table supports selection checks without ResNet weights or feature caches. Full regeneration downloads the official ResNet-18 checkpoint.

The task description lists 1,125 images. The prepared collection contains 1,225 unique names from 1,241 entries, after 16 byte-identical duplicate-name pairs were collapsed. The original manifest and saved model are preserved.

## Sources

- [Challenge data](https://drive.google.com/drive/folders/1NY2_0QtTSZC7k439HWP8SUMOrEeFEUow)
- [Prepared revision](https://github.com/MrWeeb0/LMML-ARGOS/commit/80f576ef631b906971cd9037b72aac910a2a5e80)
