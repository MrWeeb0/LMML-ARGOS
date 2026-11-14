"""Recover the injected pointillist letters from the Paris listings."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


REFERENCE_URL = (
    "https://data.insideairbnb.com/france/ile-de-france/paris/"
    "2026-09-16/data/listings.csv.gz"
)
FEATURES = ["longitude", "latitude", "price", "availability_365"]
READING = "NEURON"
ANGLES = [330, 320, 270, 90, 0, 30]
FLIP_VERTICAL = [False, False, False, True, False, False]
COLORS = ["#166baf", "#00968b", "#759b22", "#d29216", "#c95052", "#8757b2"]


def source_matches(data: pd.DataFrame, reference_path: Path) -> np.ndarray:
    """Return rows present in the public source, excluding replaced IDs."""
    keys = [column for column in data.columns if column != "listing_id"]
    source_names = [
        "neighbourhood_cleansed" if column == "neighbourhood" else column
        for column in keys
    ]
    reference = pd.read_csv(reference_path, usecols=source_names, low_memory=False)
    reference = reference.rename(columns={"neighbourhood_cleansed": "neighbourhood"})
    reference["price"] = pd.to_numeric(
        reference["price"].str.replace("$", "", regex=False).str.replace(",", "", regex=False),
        errors="coerce",
    )
    reference["host_is_superhost"] = reference["host_is_superhost"].map({"t": True, "f": False})
    for column in ["latitude", "longitude"]:
        reference[column] = reference[column].round(5)
    for column in ["price", "review_scores_rating", "reviews_per_month"]:
        reference[column] = reference[column].round(2)
    lookup = reference[keys].drop_duplicates()
    joined = (
        data.reset_index(names="row_index")
        .merge(lookup, on=keys, how="left", indicator=True, validate="many_to_one")
        .sort_values("row_index")
    )
    return joined["_merge"].eq("both").to_numpy()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("France/paris_listings.csv"))
    parser.add_argument("--reference", type=Path, default=Path("France/insideairbnb.csv.gz"))
    parser.add_argument("--output", type=Path, default=Path("France"))
    parser.add_argument("--download-reference", action="store_true")
    args = parser.parse_args()
    if not args.reference.exists():
        if not args.download_reference:
            parser.error("reference file missing; pass --download-reference")
        args.reference.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(REFERENCE_URL, args.reference)

    data = pd.read_csv(args.input)
    matched = source_matches(data, args.reference)
    candidate_indices = np.flatnonzero(~matched)
    candidates = data.iloc[candidate_indices]
    scaled = StandardScaler().fit_transform(candidates[FEATURES])
    raw_labels = HDBSCAN(
        min_cluster_size=40, min_samples=6, cluster_selection_method="eom"
    ).fit_predict(scaled)
    groups = sorted(
        set(raw_labels) - {-1},
        key=lambda label: candidates.loc[raw_labels == label, "price"].mean(),
    )
    if len(groups) != len(READING):
        raise RuntimeError(f"expected six clusters, found {len(groups)}")

    labels = data[["listing_id", *FEATURES]].copy()
    labels.insert(0, "row_index", np.arange(len(data)))
    labels["source_match"] = matched
    labels["cluster"] = -1
    labels["letter"] = ""
    projections = []
    summary = []
    for order, (raw_label, letter) in enumerate(zip(groups, READING), start=1):
        selected = raw_labels == raw_label
        indices = candidate_indices[selected]
        rows = data.iloc[indices]
        points = PCA(n_components=2, whiten=True).fit_transform(
            StandardScaler().fit_transform(rows[FEATURES])
        )
        theta = np.deg2rad(ANGLES[order - 1])
        displayed = points @ np.array(
            [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]
        ).T
        if FLIP_VERTICAL[order - 1]:
            displayed[:, 1] *= -1
        labels.loc[indices, ["cluster", "letter"]] = [order, letter]
        projections.append((points, displayed, indices))
        summary.append({
            "cluster": order,
            "letter": letter,
            "count": len(indices),
            "mean_price": float(rows["price"].mean()),
            "mean_availability_365": float(rows["availability_365"].mean()),
        })

    args.output.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 6, figsize=(17, 4.3), layout="constrained")
    for i, (ax, (_, displayed, _), record) in enumerate(zip(axes, projections, summary)):
        ax.scatter(displayed[:, 0], displayed[:, 1], s=10, color=COLORS[i], alpha=.85, linewidths=0)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"{i + 1} · {record['letter']}\n{record['count']} points", pad=15)
    fig.suptitle("Point par point — letters ordered by increasing mean price", fontsize=17)
    fig.savefig(args.output / "pointillist_clusters.png", dpi=180, facecolor="white")
    plt.close(fig)
    labels.to_csv(args.output / "labels.csv", index=False)
    result = {
        "flag": f"SIGMOID_{READING}",
        "reference_url": REFERENCE_URL,
        "rows": len(data),
        "exact_source_matches": int(matched.sum()),
        "artwork_rows": int(labels["cluster"].gt(0).sum()),
        "clusters": summary,
    }
    (args.output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
