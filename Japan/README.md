# Japan: City of Subtitles

Status: camera attribution completed; hidden word and flag unresolved. This is an investigation checkpoint, not a passing flag submission.

## Reproduce the attribution

Download the [original dataset](https://drive.google.com/drive/folders/1dKvKxO5BTcpjR9QSumq5pAfeRYXYYS92). Keep its credited/ and anonymous/ folders under Japan/dataset/.

From the repository root:

```sh
python -m pip install -r Japan/requirements.txt
python Japan/prepare.py
python Japan/attribute.py
```

An alternative dataset directory is accepted by prepare.py as its first argument. Intermediate arrays require approximately 2.3 GB of disk space. Pairwise matrix products benefit from a BLAS implementation. No GPU, trained model or API key is needed.

prepare.py produces metadata.npz, spectrum.npy, vectors.npy and kernel.npy. attribute.py produces attribution.csv with all 145 classifications and scores, plus toorisugari.csv with the selected 45 photos. Only source code and the target list are committed.

The committed scripts package the computations used in the local investigation. The original computation ran successfully. This packaged version has not received a fresh end-to-end run because the execution environment disconnected.

## Method

Each camera leaves a weak fixed spatial pattern in its photographs. The subtitle treatment adds stronger grain, image edges, JPEG block structure and captions. Comparing unprocessed images mainly measures those distractions.

prepare.py loads JPEG luminance, subtracts a Gaussian blur, and crops a symmetric central region. Local residual variance reduces the contribution of textured regions. Brightness weights reduce dark and saturated regions. Row, column and eight-pixel phase means suppress shared processing artifacts.

A pooled Fourier power estimate weights the remaining frequencies. Each residual is normalized, and pairwise correlations are calculated for the original orientation, a 180-degree rotation and two reflections.

A 180-degree change of sensor orientation is the critical attribution issue. The visible scene stays upright while the weak sensor pattern changes orientation. Averaging frames before aligning their sensor patterns weakens the template.

attribute.py estimates credited-frame orientations separately for each handle. It takes the leading eigenvector of the difference between direct and rotated correlation matrices. The sign selects the orientation, anchored to the first credited frame.

A camera score averages correlations against its aligned reference frames. Three refinement rounds add confident anonymous frames with limited weights. A query never contributes its own diagonal correlation to its score.

Validation holds out a complete credited week at a time. Anonymous images participate without their labels. Seven parameter variants are compared, so the resulting score is development validation, not an untouched test result.

The strongest local development result classified 108 of 108 credited photographs correctly across the held-out weeks. The final unconstrained anonymous counts were 44 Toorisugari, 21 Shuuden and 20 for each remaining handle.

The anonymous set strongly supports nine Toorisugari and four photos for each other handle in every week. This balance is an inference, not a rule stated in the challenge. A maximum-score assignment under that balance resolves two weak week-10 choices. In particular, w10_012.jpg is assigned to Toorisugari. The committed target list contains 45 photos.

## Target photos

| Week | Counters |
| --- | --- |
| 8 | 002, 004, 006, 010, 011, 013, 017, 019, 023 |
| 9 | 001, 004, 008, 011, 013, 014, 015, 021, 022 |
| 10 | 010, 011, 012, 018, 019, 020, 022, 027, 028 |
| 11 | 003, 011, 012, 014, 016, 025, 027, 028, 029 |
| 12 | 001, 002, 005, 008, 010, 020, 025, 027, 029 |

The orientation column in toorisugari.csv uses 0 for the posted residual and 1 for its 180-degree rotation. This convention is relative to the first credited Toorisugari frame, not a physical phone direction.

## Hidden-word investigation

No candidate word has been verified. The following attempts did not produce a readable message:

- Sensor-aligned averages, medians and estimates weighted by intensity.
- Per-week residual differences, local covariance, local energy and Fourier maps.
- Colour channels, low-frequency image averages and camera-subtracted residuals.
- Additional coherent components within the Toorisugari group.
- Filename-selection grids and orientation-bit encodings.
- Caption contact sheets and visible scene comparisons.
- JPEG headers, comments, appended data and decoded-pixel low bits.
- Exact JPEG Huffman decoding, followed by luminance/chroma coefficient sign and parity streams, MCU and raster order, frequency order, several coefficient filters, and byte alignments. All 45 selected files were scanned. No SIGMOID prefix was found.

These are negative experimental results, not proofs ruling out every encoding. Camera attribution alone does not satisfy the challenge. A valid submission still needs the hidden word and an explanation showing how it was recovered.

## Independent cross-check

After reconstructing the target list, public competitor work was inspected. The [Nasalciuc investigation](https://github.com/Nasalciuc/LMML-hacktone-2026/tree/main/30%20Japan/01%20City%20of%20Subtitles) lists the same 45 files. A [second investigation](https://github.com/dbossu186-arch/sigmoid-lmml-2026/blob/main/Japan/v2/NOTES.md) also reports the 180-degree trap and nine target photos per week. Both inspected write-ups leave the flag unresolved. Their agreement supports attribution but does not verify the secret.
