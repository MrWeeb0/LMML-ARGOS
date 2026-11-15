# Ngiyakuzwa? — isiZulu voice note recorded in a stadium

**Flag: `SIGMOID_ULWAZI`**

A 10 min 30 s voice note (16 kHz, mono) contains short isiZulu phrases read under heavy stadium noise.
The word spoken right after *ikhodi* ("the code") is the key. It is *ulwazi* ("knowledge, information").

| | |
|---|---|
| Input | `voice_note.wav` (an MP3 copy of it was used for this run) |
| Noise | two steady vuvuzela tones (harmonic combs on f0 ≈ 217.9 Hz and ≈ 233.1 Hz), crowd noise, horn bursts |
| Speech | continuous isiZulu prose, cut into ~100 phrases of about 2.4 s, one every ~5.5 s |
| Where the key is | *ikhodi* at ≈ 438.7 s, next word at ≈ 439.8–440.6 s |

## Approach

1. **Look at the signal** (`src/00_analyze_spectrum.py`).
   The long-term spectrum has strong stationary lines on two harmonic series.
   Those are the vuvuzelas. They sit around 30–40 dB above the speech.
   ![raw spectrogram](figures/spectrogram_raw_0-30s.png)
2. **Notch the vuvuzelas** (`src/01_notch_filter.py`).
   Per STFT frame (4096 samples, 512 hop) the script finds the actual peak near each expected harmonic,
   because the tones drift, and clamps ±2 bins around it to the local noise floor (median over ±12 bins).
   The RMS drops from 0.2319 to 0.0452. A fixed-frequency least-squares harmonic fit was tried first and left visible line residue.
   ![notched spectrogram](figures/spectrogram_notched_0-30s.png)
3. **Transcribe with a model that knows isiZulu** (`src/02_transcribe.py`).
   Whisper has no isiZulu: large-v3 with Shona/Swahili as stand-in language looped on garbage.
   A phone recogniser (Allosaurus, `zul` inventory) returned only a sparse, unreliable phone stream.
   Meta's **Omnilingual ASR** (CTC, 1600 languages, ONNX int8 build shipped with sherpa-onnx) reads the notched audio as real isiZulu.
   Both the 300M and 1B models were run over the whole file in 20 s windows (hop 10 s).
   Full text: `results/transcript_omnilingual_1B.txt`, `results/transcript_omnilingual_300M.txt`.
4. **Keyword search on posteriors instead of text** (`src/03_ctc_posteriors.py`, `src/04_keyword_spot.py`).
   The greedy transcript never prints "ikhodi" because the model drops quiet words and the text contains near-misses such as *ikhophi* ("copy").
   So the frame-level CTC posteriors are saved, and for every sliding window (0.6–1.3 s) the CTC log-likelihood of the target
   string is compared with the log-likelihood of the window's best path (LLR, 0 = as likely as the best transcription).
5. **Read the next word** (`src/05_show_posteriors.py`) from the posteriors at the best hit.

## Evidence

Keyword search for `ikhodi` (300M model, notched audio), best window per location, `results/keyword_spot_300M.txt`:

| rank | time | LLR vs. best path |
|---|---|---|
| 1 | **438.72 s** | **−2.45** |
| 2 | 113.12 s | −4.74 |
| 3 | 176.32 s | −6.86 |
| 4 | 12.56 s | −7.25 |

Hit 2 (113 s) and the near-misses at 12.7 s and 350–360 s decode as *ikopi / ikhophi* ("copy") in the 1B transcript, so they are ordinary words.
At 438.7 s the model reads *i · k · h · u · t(0.69)/d(0.25) · i*, and the keyword score is the best in the file.
Posteriors right after it (`results/posteriors_438-441s_300M.txt`, `figures/posteriors_438-441s.png`):

```
439.78  <space>:0.91
439.90  u:0.89
440.04  n:0.61  l:0.31
440.08  w:0.66
440.18  a:0.95
440.34  z:0.92
440.46  o:0.63  i:0.19
```

That spells *u-l(n)-w-a-z-o/i*. *Ulwazi* is the isiZulu word that fits; the model's greedy text for this window was *ulwazo* (300M) and *unywazi* (1B, first pass).
The last vowel is the weakest part of the evidence (o 0.63 vs. i 0.19), so the standard spelling was used.

## Reproduce

```bash
pip install -r requirements.txt

# models (int8 ONNX, from the k2-fsa/sherpa-onnx "asr-models" release)
#   sherpa-onnx-omnilingual-asr-1600-languages-300M-ctc-int8-2025-11-12.tar.bz2   (~290 MB)
#   sherpa-onnx-omnilingual-asr-1600-languages-1B-ctc-int8-2025-11-12.tar.bz2     (~790 MB)
# unpack into ./models/

python src/00_analyze_spectrum.py lines voice_note.wav
python src/01_notch_filter.py voice_note.wav notched.wav
python src/02_transcribe.py notched.wav 1B transcript_1B.json
python src/03_ctc_posteriors.py 300M notched.wav posteriors_300M.npy
python src/04_keyword_spot.py posteriors_300M.npy ikhodi,khodi,ikhoti
python src/05_show_posteriors.py posteriors_300M.npy 438.2 441.0 figures/posteriors_438-441s.png
```

Runtime on 2 CPU cores: notch filter about 30 s, 300M posterior extraction about 2.5 min, 1B transcription about 12 min, keyword search a few seconds per target string.

## Layout

```
src/        00 analysis · 01 notch filter · 02 transcribe · 03 posteriors · 04 keyword spotting · 05 evidence plot
results/    transcripts (300M, 1B), keyword-spotting output, posteriors around the hit
figures/    spectrograms before/after notching, posterior heat-map at 438–441 s
```

## Limitations

* The run used an 80 kbps MP3 copy of the recording, not the original WAV. MP3 coding can bury very faint speech under loud tones, so a run on the WAV should do at least as well.
* Posteriors were extracted for the 300M model only. The 1B model was used for full-file text transcription, and its posterior extraction was stopped before finishing.
* Whisper and Allosaurus were tried and abandoned (see Approach, step 3). They are not part of the pipeline.
* The audio is not included in this repository.
