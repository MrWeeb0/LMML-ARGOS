# The Azmari's Borrowed Melody

This Ethiopia CTF solution finds the start and end of a replaced phrase in a WAV recording. Submit [`main.py`](main.py) to the competition checker.

## Run locally

Download `train-input.wav` and `train-output.csv` from the [training folder](https://drive.google.com/drive/folders/1AH_ZNPVpkA5hDu9uvMm32Gyu__iYg9w7?usp=sharing). Place them in the same directory as `main.py`.

```sh
python -m pip install numpy scipy
python main.py train-input.wav
```

Pass the WAV filename from the working directory. The program writes a single `detection.csv` with times in seconds. A run on the training file produces:

```csv
start_s,end_s
14.945,20.945
```

## How the detector works

The script measures frequency balance, background noise, and tuning in short audio frames. It scores intervals by how much their measurements differ from the rest of the recording. It gives extra weight to two boundaries where the audio shifts in opposite directions. Running sums let the script test many start times and durations without recomputing the features.

## Local verification

| Training boundary | Expected | Detected | Absolute error |
| --- | ---: | ---: | ---: |
| Start | 14.960 s | 14.945 s | 0.015 s |
| End | 20.965 s | 20.945 s | 0.020 s |

The revised detector passed 193 of 216 synthetic edits made from the training recording. Mild treble changes were the main failure case. The competition flag requires both boundaries to fall within 1.5 seconds on each of the three hidden recordings.

[Technical documentation](https://docs.google.com/document/d/1p_6r8P2pofKUiE7aQ2c0r3k4UfAOaqQ3z-Hi-jSnCmE)
