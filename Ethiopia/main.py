import csv
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.ndimage import uniform_filter1d
from scipy.signal import spectrogram


WEIGHTS = np.array([.22, .19, .13, .08, .06, .09, .10, .13])


def features(rate, audio):
    x = audio.astype(np.float32)
    if x.ndim == 1:
        x = x[:, None]
    x -= x.mean(axis=0)
    x /= max(float(np.abs(x).max()), 1e-12)
    hop = max(1, round(rate * 0.10))
    size = min(len(x), max(hop, round(rate * 0.19)))
    freq, times, power = spectrogram(x.T, rate, window="hann", nperseg=size,
                                     noverlap=size - min(size, hop))
    power = power.mean(axis=0)
    power = np.maximum(power, 1e-16)
    log_power = 10 * np.log10(power)
    bins = np.searchsorted(freq, np.geomspace(25, rate / 2, 34))
    bins = np.unique(np.r_[0, bins, len(freq)])
    bands = np.array([10 * np.log10(power[a:b].mean(axis=0))
                      for a, b in zip(bins[:-1], bins[1:])]).T
    bins = np.unique(np.r_[0, np.searchsorted(freq, np.geomspace(95, rate / 2, 9)), len(freq)])
    intervals = [(a, b) for a, b in zip(bins[:-1], bins[1:]) if b - a > 2]
    flat = np.array([log_power[a:b].mean(axis=0) - 10 * np.log10(power[a:b].mean(axis=0))
                     for a, b in intervals]).T
    floor = np.array([np.quantile(log_power[a:b], 0.25, axis=0) for a, b in intervals]).T
    relative = bands - 10 * np.log10(power.sum(axis=0))[:, None]
    variation = uniform_filter1d(np.abs(np.diff(relative, axis=0, prepend=relative[:1])),
                                 size=5, axis=0)
    slope = np.diff(relative, axis=1)
    tuning = np.zeros((len(times), 4))
    pitch_bins = np.flatnonzero((freq[1:-1] >= 140) & (freq[1:-1] <= 1700)) + 1
    if pitch_bins.size:
        idx = pitch_bins[np.argmax(power[pitch_bins], axis=0)]
        frames = np.arange(len(times))
        left, middle, right = (log_power[idx + offset, frames] for offset in (-1, 0, 1))
        offset = .5 * (left - right) / np.minimum(left + right - 2 * middle, -1e-6)
        peak = (idx + np.clip(offset, -.6, .6)) * freq[1]
        phase = 24 * np.pi * np.log2(peak / 440)
        tuning = np.column_stack((np.cos(phase), np.sin(phase), np.cos(2 * phase), np.sin(2 * phase)))
    return times, (bands, relative, flat, variation, slope, tuning, floor)


def standardize(features, floor):
    median = np.median(features, axis=0)
    scale = np.maximum(1.4826 * np.median(np.abs(features - median), axis=0), floor)
    x = np.clip((features - median) / scale, -10, 10)
    return x - x.mean(axis=0)


def whiten(x):
    cov = x.T @ x / len(x)
    eigenvalues, basis = np.linalg.eigh(0.65 * cov + 0.35 * np.diag(cov.diagonal()) +
                                        0.05 * np.eye(x.shape[1]))
    return (x @ basis) / np.sqrt(eigenvalues)


def scan(groups, times, duration):
    n = len(times)
    step = times[1] - times[0]
    shoulders = max(2, round(1.0 / step))
    indices = np.arange(n + 1)
    left = np.maximum(0, indices - shoulders)
    right = np.minimum(n, indices + shoulders)
    centered = np.column_stack(groups)
    prefix = np.vstack((np.zeros(centered.shape[1]), np.cumsum(centered, axis=0)))
    cuts = (prefix[right] - prefix[indices]) / np.maximum(1, right - indices)[:, None]
    cuts -= (prefix[indices] - prefix[left]) / np.maximum(1, indices - left)[:, None]
    cuts[np.minimum(indices, n - indices) < shoulders // 2] = 0
    offsets = np.r_[0, np.cumsum([group.shape[1] for group in groups])]
    strengths = np.maximum(1e-9, np.median(np.abs(cuts), axis=0).mean())
    scores = []
    for span in range(max(2, round(0.75 / step)), min(n - 2, round(min(26, .48 * duration) / step)) + 1):
        sums = prefix[span:] - prefix[:-span]
        contrast = np.add.reduceat(sums * sums, offsets[:-1], axis=1) * (n / (span * (n - span)))
        uphill = np.einsum("ij,ij->i", sums, cuts[:-span])
        downhill = -np.einsum("ij,ij->i", sums, cuts[span:])
        alignment = np.minimum(uphill, downhill) / (np.linalg.norm(sums, axis=1) + 1e-9)
        seam = np.tanh(np.maximum(0, alignment) / (3 * strengths))
        scores.append((span, contrast, seam))
    scales = np.maximum(1e-9, np.max([c.max(axis=0) for _, c, _ in scores], axis=0))
    averages = np.mean([c.mean(axis=0) for _, c, _ in scores], axis=0)
    concentration = np.clip(np.log(scales / np.maximum(averages, 1e-9)), 0.5, 3)
    explained = scales / np.maximum(1e-9, np.add.reduceat((centered ** 2).sum(axis=0), offsets[:-1]))
    group_weights = WEIGHTS * concentration * (.03 + explained) ** 1.6
    group_weights /= group_weights.sum()
    best = (-1, 0, 0)
    for span, contrast, seam in scores:
        contrast = (contrast / scales) @ group_weights
        score = contrast * (1 + .18 * seam)
        i = int(score.argmax())
        if score[i] > best[0]:
            best = score[i], i, i + span
    _, start, end = best
    return (0. if start == 0 else times[start] - step / 2,
            duration if end == n else times[end - 1] + step / 2)


def detect(rate, audio):
    duration = len(audio) / rate
    if duration < 1.5:
        return 0., duration
    times, (bands, relative, flat, variation, slope, tuning, floor) = features(rate, audio)
    raw = standardize(bands, 2.)
    groups = (raw, whiten(raw), whiten(standardize(relative, 2.)),
              whiten(standardize(flat, 1.)), whiten(standardize(variation, .75)),
              whiten(standardize(slope, 1.)), whiten(standardize(tuning, .2)),
              whiten(standardize(floor, 1.5)))
    return scan(groups, times, duration)


if __name__ == "__main__":
    rate, audio = wavfile.read(Path(sys.argv[1]).name)
    start, end = detect(rate, audio)
    with open("detection.csv", "w", newline="") as file:
        csv.writer(file).writerows([("start_s", "end_s"), (f"{start:.3f}", f"{end:.3f}")])
