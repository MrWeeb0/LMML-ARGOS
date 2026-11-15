"""Full Fourier Transform (FFT + STFT Spectrogram) analysis for nigeria_challenge.wav."""

import wave
import numpy as np
import matplotlib.pyplot as plt


def load_wav_mono(path: str) -> tuple[int, np.ndarray]:
    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        n_frames = w.getnframes()
        n_channels = w.getnchannels()
        sampwidth = w.getsampwidth()
        raw = w.readframes(n_frames)

    if sampwidth == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    elif sampwidth == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128.0) * 256.0
    elif sampwidth == 4:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float64)
    else:
        raise ValueError(f"Unsupported sample width: {sampwidth}")

    if n_channels > 1:
        data = data.reshape(-1, n_channels).mean(axis=1)

    # Normalize to [-1, 1]
    max_abs = np.max(np.abs(data))
    if max_abs > 0:
        data = data / max_abs
    return sr, data


def compute_fft(data: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray]:
    # Apply Hann window to reduce spectral leakage
    window = np.hanning(len(data))
    spectrum = np.abs(np.fft.rfft(data * window))
    freqs = np.fft.rfftfreq(len(data), d=1.0 / sr)
    return freqs, spectrum


def compute_stft(
    data: np.ndarray,
    sr: int,
    win_size: int = 1024,
    hop_size: int = 256,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    window = np.hanning(win_size)
    n_frames = 1 + (len(data) - win_size) // hop_size
    frames = np.lib.stride_tricks.sliding_window_view(data, win_size)[::hop_size][:n_frames]
    stft_matrix = np.fft.rfft(frames * window, axis=1)
    mag_db = 20.0 * np.log10(np.abs(stft_matrix).T + 1e-10)
    freqs = np.fft.rfftfreq(win_size, d=1.0 / sr)
    times = (np.arange(n_frames) * hop_size) / sr
    return times, freqs, mag_db


def main(wav_path: str = "nigeria_challenge.wav") -> None:
    sr, data = load_wav_mono(wav_path)
    duration = len(data) / sr
    print(f"Loaded {wav_path}: sample_rate={sr} Hz, samples={len(data)}, duration={duration:.3f} s")

    # 1. Global FFT
    freqs, spectrum = compute_fft(data, sr)
    top_idx = np.argsort(spectrum)[-10:][::-1]
    print("\nTop 10 dominant frequencies (Hz):")
    for idx in top_idx:
        print(f"  {freqs[idx]:8.2f} Hz  | magnitude = {spectrum[idx]:.2f}")

    # 2. Short-Time Fourier Transform (STFT)
    times, stft_freqs, mag_db = compute_stft(data, sr, win_size=1024, hop_size=256)

    # 3. Plot FFT + Full Spectrogram + Zoomed Band (2500-4500 Hz)
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), constrained_layout=True)

    # Panel 1: Global FFT
    axes[0].plot(freqs, spectrum, linewidth=0.8, color="#1f77b4")
    axes[0].set_title("Global FFT Magnitude Spectrum")
    axes[0].set_xlabel("Frequency (Hz)")
    axes[0].set_ylabel("Magnitude")
    axes[0].set_xlim(0, sr / 2)
    axes[0].grid(alpha=0.3)

    # Panel 2: Full STFT Spectrogram
    im1 = axes[1].pcolormesh(times, stft_freqs, mag_db, shading="auto", cmap="inferno")
    axes[1].set_title("STFT Spectrogram (Full Band)")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Frequency (Hz)")
    fig.colorbar(im1, ax=axes[1], label="dB")

    # Panel 3: Zoomed Spectrogram around the dominant 2500-4500 Hz band
    band_mask = (stft_freqs >= 2500) & (stft_freqs <= 4500)
    im2 = axes[2].pcolormesh(
        times, stft_freqs[band_mask], mag_db[band_mask], shading="auto", cmap="inferno"
    )
    axes[2].set_title("STFT Spectrogram (Zoomed: 2500 - 4500 Hz)")
    axes[2].set_xlabel("Time (s)")
    axes[2].set_ylabel("Frequency (Hz)")
    fig.colorbar(im2, ax=axes[2], label="dB")

    out_png = "nigeria_fft_spectrogram.png"
    plt.savefig(out_png, dpi=150)
    print(f"\nSaved plot to {out_png}")


if __name__ == "__main__":
    main("downloads/nigeria_challenge.wav")