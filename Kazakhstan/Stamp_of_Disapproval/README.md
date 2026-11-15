# Kazakhstan: Stamp of Disapproval

**Status: unresolved. No verified flag or passing competition submission.**

The detector outputs do not produce five stable, readable letters. Separate letter fits and a shared-layout fit disagree across models. Their automatically generated letter sequences are hypotheses, not flags.

## Materials

- [Original pixel detector: boxes](pixel-output/boxes.csv), [detections](pixel-output/detections.json), [album overlays](pixel-output/album-overlays.png).
- [Refined detector: boxes](synthetic-output/boxes.csv), [detections](synthetic-output/detections.json), [album overlays](synthetic-output/album-overlays.png).
- Each output directory contains 130 saved heatmaps and 130 annotated page images.
- [Pixel detector development validation](pixel-validation.json), [synthetic training record](synthetic-training.json), [earlier observed experiments](observed-experiments.json).
- [Independent album-template fits](joint-letter-analysis.json), [shared-layout analysis](shared-geometry/results.json).
- Saved model weights: pixel-detector.pt and pixel-synthetic-detector.pt.
- [Input manifest](manifest.json) records the source IDs, sizes and SHA-256 hashes of all 192 inputs.
- [Execution environment](environment.txt) records the original remote pixel run.

The original and refined outputs each contain exactly 26 pages in each of five albums. Bounding boxes use the supplied album,page,x,y,w,h convention on 1600 by 1200 images.

## Method in four lines

1. Detect the three stamp areas on each page and extract color and local noise measurements.
2. Train segmentation models using the 30 supplied exhibit images and masks, then apply the detector to each page.
3. Refine the pixel model using synthetic copy and erasure operations plus mostly normal crops from the unlabelled albums.
4. Overlay page detections and test all alphabet candidates, including one shared layout across the albums.

No hints, catalogue images, pristine stamp copies, or manually labelled album regions were used. The unlabelled album crops are not guaranteed pristine; their rare true alterations can contaminate the synthetic adaptation's negative examples.

## What the results establish

The original pixel model was selected after 700 steps on a six-exhibit development split. Its selected checkpoint's predicted center was inside the mask for 4 of 6 held-out exhibits. Mean average precision was 0.5721. The final detector was retrained on all 30 exhibits using the selected length.

This small selected development split does not establish album accuracy. The synthetic refinement starts from that fully fitted model, so its training loss is not independent validation. Neural localization scores are uncalibrated and must not be read as probabilities of a correct page detection.

The letter analysis uses all 26 alphabet candidates, without a dictionary or a hard-coded word. Template fitting constrains positions geometrically and can force plausible shapes out of noisy detections. The shared-layout diagrams show those adjusted positions separately from raw maxima. A fitted shape does not verify the flag.

## Earlier experiments

- Extra Trees on 126 local color, gradient, noise and recompression features: 15/30 center hits in the recorded cyclic five-fold exhibit test.
- A feature-map spatial network: 5/6 center hits on its selected small development split.
- Resizing, JPEG-phase and noise augmentation: no readable album letters.
- Unmodified pretrained TruFor: 5/30 exhibit center hits.
- A supervised adapter over frozen TruFor decoder features: 7/30 exhibit center hits.
- Dense within-image copy matching, learned spatial priors, density maps and independent glyph fits also failed to establish a flag.

These experiments and their limitations are recorded in observed-experiments.json. No competition pass is inferred from a successful workflow run.

## Reproduce the saved pixel runs

Use Python 3.11. Install the CPU build of PyTorch and the remaining requirements:

```sh
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python download.py
python pixel_model.py
python pixel_detect.py
python synthetic_train.py
python synthetic_detect.py
python joint_letter_analysis.py
python global_letters.py
python validate_materials.py
```

download.py retries transient failures, avoids a shared cookie file, and verifies each input against the manifest. The saved environment.txt gives the original remote run's package versions. Exact floating-point outputs can differ across environments.

The GitHub Actions workflows preserve model weights, validation, heatmaps, boxes, annotated images and overlays. Their successful completion establishes execution and structural checks, not hidden-label detection accuracy.

## Additional forensic model

The TruFor experiments use the official [TruFor repository](https://github.com/grip-unina/TruFor) at commit ae54475df6f41a491d7615100feb19263dec13f7 and its official pretrained weights. The downloaded archive's MD5 is 7bee48f3476c75616c3c5721ab256ff8. The upstream license applies. Clone the upstream code into trufor/ and place its weights in trufor-weights/ to run those optional experiments. The pixel runs do not require TruFor.

## Source

[Challenge data](https://drive.google.com/drive/folders/1VKPTZUZf9sUxQrBkpr4kuDpcAXRfKZoC)
