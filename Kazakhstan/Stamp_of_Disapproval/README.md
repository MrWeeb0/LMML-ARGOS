# Kazakhstan: Stamp of Disapproval

Status: investigation in progress. No verified flag has been recovered. This checkpoint preserves detector code after a local runtime interruption.

The source manifest contains 130 album pages, 30 exhibit images with 30 masks, and the two supplied text files. Every downloaded input was SHA-256 checked. Detection uses the supplied exhibit labels and within-image forensic features. No hints, catalogue images, pristine stamp copies, or manually labelled album regions are used.

## Reproduce

Use Python 3.11:

```sh
python -m pip install -r requirements.txt
python download.py
python train_experiment.py
python detect.py
python augment_exhibits.py
python context_model.py
python context_detect.py --aug
python pixel_model.py
```

The feature extractor computes local color, gradient, noise, median-residual and recompression measurements. An Extra Trees classifier and spatial segmentation networks learn from the labelled exhibits. Album detections are combined into five overlays. Current overlays do not establish a readable flag.

The direct pixel model uses original colors and three local residual families. Its validation and final training are separate. The held-out exhibit images never appear in its training partition. The final model is retrained on all 30 exhibits after selecting the training length.

## Recorded experiments

- The first feature model located 15 of 30 exhibit regions in five image-held-out folds. Its cyclic split was also an unusually strict test of edit-family transfer.
- A spatial model located 5 of 6 held-out exhibit regions at the selected checkpoint. This small development split is not an album accuracy estimate.
- Resizing and recompression augmentation did not produce readable album letters.
- The unmodified pretrained TruFor model located 5 of 30 exhibit regions. A supervised linear adapter over its internal features reached 7 of 30. These experiments did not solve the task.
- Copy matching, learned spatial priors, density aggregation, and alphabet-template fitting are exploratory. Their outputs are not verified flags.

The local experiment records will be added alongside the supporting outputs. A task pass must not be inferred from successful code execution or exhibit validation.

## External forensic model

The TruFor experiments use the official [TruFor repository](https://github.com/grip-unina/TruFor) at commit ae54475df6f41a491d7615100feb19263dec13f7 and the official pretrained weights. The downloaded weight archive MD5 is 7bee48f3476c75616c3c5721ab256ff8. Its upstream license applies. The final detector does not require TruFor unless its experiment is explicitly run.

## Source

[Challenge data](https://drive.google.com/drive/folders/1VKPTZUZf9sUxQrBkpr4kuDpcAXRfKZoC)
