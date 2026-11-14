#!/usr/bin/env python3
"""Script complet pentru Google Colab — Task CHINA (Scrijelit în oase, întipărit în inimă).

Poți lipi acest cod direct într-o celulă Google Colab (Runtime -> Change runtime type -> T4 GPU)
sau îl poți rula din terminal cu `python3 solve_china_colab.py`.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import cv2
import numpy as np
import pandas as pd


def prepare_yolo_dataset(data_dir: Path, work_dir: Path) -> tuple[Path, dict[str, int]]:
    crates = pd.read_csv(data_dir / "crates.csv")
    target_glyphs = list(crates["glyph_id"])
    glyph_to_cls = {g: i for i, g in enumerate(target_glyphs)}

    labels = pd.read_csv(data_dir / "train_labels.csv")
    img_dir = data_dir / "train" / "images"

    all_imgs = sorted(labels["image"].unique())
    rng = np.random.default_rng(42)
    perm = rng.permutation(len(all_imgs))
    val_count = max(1, int(0.1 * len(all_imgs)))
    val_set = set(all_imgs[i] for i in perm[:val_count])

    for split in ("train", "val"):
        (work_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (work_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    grouped = labels.groupby("image")
    for img_name in all_imgs:
        src = img_dir / img_name
        if not src.exists():
            continue
        split = "val" if img_name in val_set else "train"
        dst_img = work_dir / "images" / split / img_name
        if not dst_img.exists():
            shutil.copy2(src, dst_img)

        img = cv2.imread(str(src), cv2.IMREAD_GRAYSCALE)
        h_img, w_img = img.shape[:2]

        yolo_lines = []
        if img_name in grouped.groups:
            sub = grouped.get_group(img_name)
            for r in sub.itertuples():
                if r.glyph_id not in glyph_to_cls:
                    continue
                cls_id = glyph_to_cls[r.glyph_id]
                xc = (r.x + r.w / 2.0) / w_img
                yc = (r.y + r.h / 2.0) / h_img
                wn = r.w / w_img
                hn = r.h / h_img
                yolo_lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {wn:.6f} {hn:.6f}")

        lbl_path = work_dir / "labels" / split / f"{Path(img_name).stem}.txt"
        lbl_path.write_text("\n".join(yolo_lines), encoding="utf-8")

    yaml_path = work_dir / "data.yaml"
    names_block = "\n".join(f"  {i}: {g}" for i, g in enumerate(target_glyphs))
    yaml_path.write_text(
        f"path: {work_dir.resolve()}\n"
        f"train: images/train\n"
        f"val: images/val\n"
        f"names:\n{names_block}\n",
        encoding="utf-8",
    )
    return yaml_path, glyph_to_cls


def decode_flag(counts_df: pd.DataFrame) -> None:
    """Încearcă decodarea cuvântului de 8 litere din cele 5 seturi per ladă (cod binar 5 biți)."""
    print("\n=== MATRICEA DE NUMĂRĂTORI ===")
    piv = counts_df.pivot(index="crate", columns="set", values="count")
    print(piv)

    vals = counts_df["count"].values
    low_med = np.percentile(vals, 25)
    high_med = np.percentile(vals, 75)
    thresh = (low_med + high_med) / 2.0

    for msb_first in (True, False):
        word = []
        for crate in sorted(piv.index):
            row = [int(piv.loc[crate, c] >= thresh) for c in sorted(piv.columns)]
            bits = row if msb_first else list(reversed(row))
            val = sum(b << (4 - i) for i, b in enumerate(bits))
            if 1 <= val <= 26:
                word.append(chr(ord("A") + val - 1))
            elif 0 <= val <= 25:
                word.append(chr(ord("A") + val))
            else:
                word.append("?")
        order_str = "MSB->LSB" if msb_first else "LSB->MSB"
        print(f"Decodare ({order_str}, prag={thresh:.1f}): SIGMOID_{''.join(word)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("/content/drive/MyDrive/task_china"))
    ap.add_argument("--work", type=Path, default=Path("/content/yolo_china"))
    ap.add_argument("--out", type=Path, default=Path("counts.csv"))
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--conf", type=float, default=0.35)
    # parse_known_args() ignoră argumentele interne ale kernel-ului Jupyter/Colab (-f ...)
    args, _ = ap.parse_known_args()

    from ultralytics import YOLO

    yaml_path, glyph_to_cls = prepare_yolo_dataset(args.data, args.work)
    model = YOLO("yolov8s.pt")
    model.train(
        data=str(yaml_path),
        epochs=args.epochs,
        imgsz=640,
        batch=16,
        patience=8,
        project=str(args.work / "runs"),
        name="oracle_glyphs",
    )

    crates = pd.read_csv(args.data / "crates.csv")
    rows = []
    for crate, glyph_id in zip(crates["crate"], crates["glyph_id"]):
        target_cls = glyph_to_cls[glyph_id]
        for set_dir in sorted((args.data / "crates" / crate).iterdir()):
            if not set_dir.is_dir():
                continue
            imgs = sorted(str(p) for p in set_dir.glob("*.jpg"))
            results = model.predict(imgs, conf=args.conf, iou=0.45, imgsz=640, verbose=False)
            total_count = 0
            for res in results:
                if res.boxes is not None and len(res.boxes) > 0:
                    cls_ids = res.boxes.cls.cpu().numpy().astype(int)
                    total_count += int(np.sum(cls_ids == target_cls))
            rows.append([crate, set_dir.name, glyph_id, total_count])

    out_df = pd.DataFrame(rows, columns=["crate", "set", "glyph_id", "count"])
    out_df.to_csv(args.out, index=False)
    print("Salvat:", args.out)
    decode_flag(out_df)


if __name__ == "__main__":
    main()