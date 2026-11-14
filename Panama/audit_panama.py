"""
Panama — Canalul care știe prea multe (CanalQA Contamination Audit)
Identifies English and Spanish-translated benchmark QA leaks in the fine-tuning corpus,
recalculates honest accuracy, writes report.json, and opens audit_seal.json.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

STOPWORDS = {
    "the", "of", "is", "as", "what", "which", "value", "recorded", "according",
    "to", "canal", "registry", "state", "tell", "me", "a", "an", "in", "for",
    "and", "year",
}


def norm_tokens(text: str) -> list[str]:
    s = unicodedata.normalize("NFKD", text.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", s)


def main() -> None:
    downloads = Path("/working_dir/c_0e3ceed3e71af2d7/downloads")
    audit_path = downloads / "panama_canalqa_audit.json"
    seal_path = downloads / "panama_audit_seal.json"
    if not audit_path.exists():
        audit_path = Path("canalqa_audit.json")
        seal_path = Path("audit_seal.json")

    data = json.loads(audit_path.read_text(encoding="utf-8"))
    preds = {p["id"]: p for p in data["model_predictions"]}
    gloss = {" ".join(norm_tokens(k)): " ".join(norm_tokens(v)) for k, v in data["glossary_es_en"].items()}

    corpus_sets: list[tuple[str, str, set[str]]] = []
    for doc in data["corpus"]:
        toks = norm_tokens(doc["text"])
        if doc["lang"] == "es":
            toks = [gloss.get(t, t) for t in toks]
        corpus_sets.append((doc["doc_id"], doc["lang"], set(toks)))

    excluded_ids: list[str] = []
    for item in data["benchmark"]:
        q_toks = [t for t in norm_tokens(item["question"]) if t not in STOPWORDS]
        g_toks = norm_tokens(item["gold"])
        best_sc = 0.0
        for _, _, tset in corpus_sets:
            q_hit = sum(1 for t in q_toks if t in tset) / max(1, len(q_toks))
            g_hit = sum(1 for t in g_toks if t in tset) / max(1, len(g_toks))
            sc = 0.6 * q_hit + 0.4 * g_hit
            if q_hit == 1.0 and g_hit > 0.0 and sc > best_sc:
                best_sc = sc
        if best_sc >= 0.73:
            excluded_ids.append(item["id"])

    remaining = [p for bid, p in preds.items() if bid not in set(excluded_ids)]
    honest_acc = sum(1 for p in remaining if p["correct"]) / len(remaining)

    report = {
        "excluded_ids": sorted(excluded_ids),
        "honest_accuracy": round(honest_acc, 4),
    }
    out_report = Path(__file__).resolve().with_name("report.json")
    out_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    sys.path.insert(0, str(downloads))
    try:
        import open_seal as os_mod
    except ImportError:
        import panama_open_seal as os_mod

    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    payload = os_mod.unseal(seal, excluded_ids)
    print(f"Excluded: {len(excluded_ids)}/80 | Honest accuracy: {honest_acc:.4f} ({sum(1 for p in remaining if p['correct'])}/{len(remaining)})")
    print("Seal payload:", payload)


if __name__ == "__main__":
    main()