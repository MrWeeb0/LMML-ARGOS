from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from challenge_model import (
    IMAGE_FORMAT,
    IMAGE_MODE,
    MAX_OUTPUT_BYTES,
    MAX_PIXEL_DELTA,
    MIN_TARGET_CONFIDENCE,
    TARGET_CLASS_ID,
    load_model,
    normalize_batch,
    pil_to_tensor,
    predict_tensor,
    tensor_to_rgb_image,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Targeted L-inf (delta <= 1/255) adversarial attack for Ciclopaseo Mirage."
    )
    parser.add_argument("--input", type=Path, default=Path("test-input.png"))
    parser.add_argument("--output", type=Path, default=Path("test-output.png"))
    parser.add_argument(
        "--model", type=Path, default=Path("classifier/mobilenet_v3_large-5c1a4163.pth")
    )
    return parser.parse_args()


def quantize_with_budget(
    adv_tensor: torch.Tensor,
    orig_pixels: np.ndarray,
    budget: int,
) -> Image.Image:
    candidate = np.array(tensor_to_rgb_image(adv_tensor), dtype=np.int16)
    low = np.clip(orig_pixels - budget, 0, 255)
    high = np.clip(orig_pixels + budget, 0, 255)
    bounded = np.clip(candidate, low, high).astype(np.uint8)
    return Image.fromarray(bounded, mode=IMAGE_MODE)


def main() -> None:
    start_time = time.monotonic()
    args = parse_args()
    torch.set_num_threads(2)
    torch.manual_seed(42)

    model = load_model(args.model, device="cpu")
    for param in model.parameters():
        param.requires_grad_(False)

    with Image.open(args.input) as img:
        source_image = img.convert(IMAGE_MODE) if img.mode != IMAGE_MODE else img.copy()

    orig_pixels = np.array(source_image, dtype=np.int16)
    x0 = pil_to_tensor(source_image, device="cpu")

    eps = MAX_PIXEL_DELTA / 255.0
    low_t = torch.from_numpy(
        np.clip(orig_pixels - MAX_PIXEL_DELTA, 0, 255).astype(np.float32) / 255.0
    ).permute(2, 0, 1).unsqueeze(0)
    high_t = torch.from_numpy(
        np.clip(orig_pixels + MAX_PIXEL_DELTA, 0, 255).astype(np.float32) / 255.0
    ).permute(2, 0, 1).unsqueeze(0)

    delta = torch.zeros_like(x0, requires_grad=True)
    optimizer = torch.optim.Adam([delta], lr=0.4 / 255.0)
    target = torch.tensor([TARGET_CLASS_ID], dtype=torch.long)

    best_image: Image.Image | None = None
    best_target_conf = -1.0

    max_steps = 100
    time_budget_s = 45.0

    for step in range(1, max_steps + 1):
        optimizer.zero_grad(set_to_none=True)
        adv = torch.clamp(x0 + delta, min=low_t, max=high_t)
        logits = model(normalize_batch(adv))
        loss = F.cross_entropy(logits, target)
        loss.backward()
        optimizer.step()

        with torch.no_grad():
            delta.clamp_(-eps, eps)
            delta.copy_(torch.clamp(x0 + delta, min=low_t, max=high_t) - x0)
            cont_prob = logits.softmax(dim=1)[0, TARGET_CLASS_ID].item()

        if step % 5 == 0 or cont_prob >= 0.992 or step == max_steps:
            q_img = quantize_with_budget(x0 + delta, orig_pixels, MAX_PIXEL_DELTA)
            q_pred = predict_tensor(model, pil_to_tensor(q_img, device="cpu"))
            if q_pred.target_confidence > best_target_conf:
                best_target_conf = q_pred.target_confidence
                best_image = q_img

            if (
                q_pred.class_id == TARGET_CLASS_ID
                and q_pred.target_confidence >= max(MIN_TARGET_CONFIDENCE + 0.005, 0.995)
            ):
                break

        if time.monotonic() - start_time > time_budget_s:
            break

    if best_image is None:
        best_image = quantize_with_budget(x0 + delta, orig_pixels, MAX_PIXEL_DELTA)

    best_image.save(args.output, format=IMAGE_FORMAT, optimize=True)
    if args.output.stat().st_size > MAX_OUTPUT_BYTES:
        best_image.save(args.output, format=IMAGE_FORMAT, compress_level=9)

    with Image.open(args.output) as saved:
        saved_pixels = np.array(saved, dtype=np.int16)
        max_delta = int(np.abs(saved_pixels - orig_pixels).max())
        final_pred = predict_tensor(model, pil_to_tensor(saved, device="cpu"))

    print(
        f"Saved {args.output} | class={final_pred.class_id} ({final_pred.class_name}) "
        f"| target_conf={final_pred.target_confidence:.6f} | max_delta={max_delta} "
        f"| bytes={args.output.stat().st_size} | elapsed={time.monotonic() - start_time:.2f}s"
    )


if __name__ == "__main__":
    main()