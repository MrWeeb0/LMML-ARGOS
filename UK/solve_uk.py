"""
Call My BLEUff (UK) — Detecting BLEU-gaming bluffers and identifying the honest panellist.

Three bluffing mechanisms identified in panel.csv:
1. Repetition / Length-Padding: repeating clauses or 4-grams within a card to inflate
   corpus brevity penalty and n-gram matches (caught via 4-gram repetition excess).
2. Word Salad / N-gram Stitching: stitching local n-grams with broken syntax/grammar
   that still score well on BLEU (caught via top-tail unseen trigram rate vs references).
3. Selective Attribute Omission: writing short, safe, high-precision phrases on several
   cards while dropping venue name, cuisine, price, or rating (caught via bottom-tail
   contextual semantic consensus recall).
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
for candidate in [HERE, Path("/working_dir/c_0e3ceed3e71af2d7/downloads")]:
    if (candidate / "uk_bleu.py").exists() or (candidate / "bleu.py").exists():
        sys.path.insert(0, str(candidate))
        break

try:
    from bleu import corpus_bleu, tokenize
except ImportError:
    from uk_bleu import corpus_bleu, tokenize

SEMANTIC_MAP = {
    "kids": "FAM", "children": "FAM", "child": "FAM", "family": "FAM", "families": "FAM",
    "british": "english", "sushi": "japanese",
    "inexpensive": "CHEAP", "cheap": "CHEAP", "budget": "CHEAP", "20": "CHEAP",
    "moderate": "MOD", "moderately": "MOD", "medium": "MOD", "mid": "MOD", "25": "MOD",
    "expensive": "EXP", "costly": "EXP", "pricey": "EXP", "30": "EXP",
    "poor": "LOW", "poorly": "LOW", "1": "LOW", "one": "LOW",
    "average": "AVG", "decent": "AVG", "3": "AVG", "three": "AVG",
    "excellent": "HIGH", "great": "HIGH", "5": "HIGH", "five": "HIGH", "top": "HIGH",
    "river": "riverside", "riverfront": "riverside",
    "centre": "center", "café": "cafe",
}

STOPWORDS = {
    "the", "a", "an", "is", "are", "in", "on", "at", "of", "and", "with", "to", "for",
    "it", "its", "that", "which", "has", "have", "by", "as", "be", "this", "from", "or",
    "but", "not", "there", "very", "also", "you", "can", "they", "their", "was", "were",
    "will", "out", "near", "located", "area", "called", "named", "price", "range",
    "customer", "rating", "ratings", "stars", "star", "food", "serves", "serving",
    "offers", "offering", "friendly", "oriented", "restaurant", "pub", "coffee",
    "shop", "venue", "place", "establishment", "eatery", "beside", "besides",
    "next", "close", "around",
}


def norm_sem(text: str) -> set[str]:
    t = text.lower()
    t = re.sub(r"\blow[\s-]+pric\w*|\blow[\s-]+cost\w*", " cheap ", t)
    t = re.sub(r"\bhigh[\s-]+pric\w*|\bhigher[\s-]+pric\w*", " expensive ", t)
    t = re.sub(r"\blow[\s-]+rat\w*", " 1 ", t)
    t = re.sub(r"\bhigh[\s-]+rat\w*", " 5 ", t)
    out: set[str] = set()
    for w in tokenize(t):
        if w.isalnum():
            if w == "low":
                out.add("LOW")
            elif w == "high":
                out.add("HIGH")
            else:
                out.add(SEMANTIC_MAP.get(w, w))
    return out


def decode(seats: list[int]) -> str:
    word = ""
    for i in range(0, len(seats), 3):
        d1, d2, d3 = (s - 1 for s in seats[i : i + 3])
        word += chr(ord("A") + 9 * d1 + 3 * d2 + d3)
    return word


def main() -> None:
    data_dir = Path("/working_dir/c_0e3ceed3e71af2d7/downloads")
    refs_path = data_dir / "uk_references.csv"
    panel_path = data_dir / "uk_panel.csv"
    if not refs_path.exists():
        refs_path = HERE / "dataset" / "references.csv"
        panel_path = HERE / "dataset" / "panel.csv"

    refs = pd.read_csv(refs_path)
    panel = pd.read_csv(panel_path)
    ref_map = refs.groupby(["round", "card"]).reference.apply(list).to_dict()

    c3: Counter = Counter()
    for r in refs.reference:
        toks = ["<s>", "<s>"] + tokenize(r) + ["</s>"]
        c3.update(zip(toks, toks[1:], toks[2:]))

    rows = []
    for (rnd, seat), deck in panel.groupby(["round", "seat"]):
        bleu_res = corpus_bleu(list(deck.text), [ref_map[(rnd, c)] for c in deck.card])
        covs, u3s, rep4_sum = [], [], 0
        for text, card in zip(deck.text, deck.card):
            ot_raw = tokenize(text)
            ot = norm_sem(text)
            rts = [norm_sem(r) for r in ref_map[(rnd, card)]]
            df_tok: Counter = Counter()
            for s in rts:
                df_tok.update(s)
            cons = {w for w, cnt in df_tok.items() if cnt >= 3 and w not in STOPWORDS}
            covs.append(len(ot & cons) / max(1, len(cons)))

            pt = ["<s>", "<s>"] + ot_raw + ["</s>"]
            u3s.append(
                sum(1 for tg in zip(pt, pt[1:], pt[2:]) if c3[tg] == 0) / max(1, len(pt) - 2)
            )
            fgs = list(zip(ot_raw, ot_raw[1:], ot_raw[2:], ot_raw[3:]))
            rep4_sum += len(fgs) - len(set(fgs))

        bot8_cov = float(np.mean(sorted(covs)[:8]))
        top8_u3 = float(np.mean(sorted(u3s, reverse=True)[:8]))
        honesty_score = bot8_cov - 0.35 * top8_u3 - 0.05 * max(0, rep4_sum - 2)

        rows.append(
            {
                "round": rnd,
                "seat": seat,
                "bleu": bleu_res["bleu"],
                "bot8_cov": bot8_cov,
                "top8_u3": top8_u3,
                "rep4_sum": rep4_sum,
                "honesty_score": honesty_score,
            }
        )

    df = pd.DataFrame(rows)
    winners = df.loc[df.groupby("round").honesty_score.idxmax()].sort_values("round")
    bleu_winners = df.loc[df.groupby("round").bleu.idxmax()].sort_values("round")

    print("BLEU word   : SIGMOID_" + decode(list(bleu_winners.seat)))
    print("Honest word : SIGMOID_" + decode(list(winners.seat)))
    print("Honest seats:", list(winners.seat))

    fig, axes = plt.subplots(2, 1, figsize=(12, 6.8), sharex=True)
    colors = {1: "#1f77b4", 2: "#ff7f0e", 3: "#2ca02c"}
    for seat, grp in df.groupby("seat"):
        axes[0].scatter(grp["round"], grp["bleu"], label=f"Seat {seat}", color=colors[seat], s=42, alpha=0.85)
        axes[1].scatter(grp["round"], grp["honesty_score"], label=f"Seat {seat}", color=colors[seat], s=42, alpha=0.85)

    axes[0].set_ylabel("House BLEU-4")
    axes[0].set_title("House BLEU-4 (Rewarding Bluffers) vs. Honesty Quality Score (Catching Bluffers)")
    axes[0].legend(frameon=False, ncol=3)
    axes[1].set_ylabel("Honesty Quality Score")
    axes[1].set_xlabel("Round (1–24)")
    axes[1].set_xticks(range(1, 25))
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="x", linestyle=":", alpha=0.4)

    out_png = HERE / "honesty_separation.png"
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    print(f"Saved figure: {out_png}")


if __name__ == "__main__":
    main()