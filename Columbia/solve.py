"""Recover the Bogotá Sound Check flag, offline, using the saved source corpus.

Run: python3 Columbia/solve.py
Only Python's standard library is required. See explanation.md for provenance.
"""
import csv
import gzip
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source_data/reviews_Musical_Instruments_5.json.gz"
SOURCE_URL = "https://snap.stanford.edu/data/amazon/productGraph/categoryFiles/reviews_Musical_Instruments_5.json.gz"
BENIGN = str.maketrans({"’": "'", "–": "-"})
REPAIR = str.maketrans({"а": "a", "с": "c", "е": "e", "о": "o", "\u200b": ""})


def lookup_key(summary, text):
    # Repair visually hidden text changes only to find the original review.
    return tuple(re.sub(r"[^a-z0-9]", "", s.translate(REPAIR).lower())
                 for s in (summary, text))


def canonical(s):
    # These punctuation variants also occur in trusted, unaltered records.
    return s.translate(BENIGN)


def main():
    data = json.loads((HERE / "reviews.json").read_text())
    with gzip.open(SOURCE, "rt", encoding="utf-8") as f:
        originals = [json.loads(line) for line in f]
    by_key = defaultdict(list)
    for original in originals:
        by_key[lookup_key(original["summary"], original["reviewText"])].append(original)

    def find_original(review):
        matches = by_key[lookup_key(review["summary"], review["review_text"])]
        if not matches:
            raise RuntimeError("No original found for " + review["summary"])
        exact = [m for m in matches
                 if canonical(review["summary"].translate(REPAIR)) == canonical(m["summary"])
                 and canonical(review["review_text"].translate(REPAIR)) == canonical(m["reviewText"])]
        if exact:
            matches = exact
        signatures = {(canonical(m["summary"]), canonical(m["reviewText"]), int(m["overall"]))
                      for m in matches}
        if len(signatures) != 1:
            raise RuntimeError("Ambiguous original for " + review["summary"])
        return matches[0]

    # Establish that the external source reproduces ALL supplied trusted records.
    for review in data["trusted_reference"]:
        original = find_original(review)
        assert canonical(review["summary"]) == canonical(original["summary"])
        assert canonical(review["review_text"]) == canonical(original["reviewText"])
        assert review["rating"] == int(original["overall"])

    trusted_chars = {ch for r in data["trusted_reference"]
                     for field in ("summary", "review_text") for ch in r[field]}
    altered = []
    for review in data["samples"]:
        original = find_original(review)
        changed_text = any(canonical(review[a]) != canonical(original[b])
                           for a, b in (("summary", "summary"), ("review_text", "reviewText")))
        changed_rating = review["rating"] != int(original["overall"])
        if changed_text or changed_rating:
            unusual = sorted(set(review["summary"] + review["review_text"]) - trusted_chars)
            altered.append({
                "sample_index": review["sample_index"],
                "change": "text and rating" if changed_text and changed_rating else "text" if changed_text else "rating",
                "supplied_rating": review["rating"], "original_rating": int(original["overall"]),
                "summary": review["summary"],
                "unusual_characters": "; ".join(f"U+{ord(c):04X} {unicodedata.name(c)}" for c in unusual),
                "source_asin": original["asin"], "source_reviewer_id": original["reviewerID"],
            })
    altered.sort(key=lambda r: r["sample_index"])
    indices = [r["sample_index"] for r in altered]
    index_text = ",".join(map(str, indices))
    mask = hashlib.sha256(index_text.encode("utf-8")).digest()
    hits = []
    for section in ("trusted_reference", "samples"):
        for position, review in enumerate(data[section]):
            tag = bytes.fromhex(review["archive_tag"])
            assert len(tag) == len(mask) == 32
            message = bytes(a ^ b for a, b in zip(tag, mask)).rstrip(b"\x00")
            if re.fullmatch(rb"SIGMOID_[A-Z_]+", message):
                hits.append({"section": section, "position_zero_based": position,
                             "archive_tag": review["archive_tag"], "flag": message.decode("ascii")})
    assert len(hits) == 1, f"Expected one flag, found {len(hits)}"
    report = {
        "source_url": SOURCE_URL,
        "source_gzip_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "input_sha256": hashlib.sha256((HERE / "reviews.json").read_bytes()).hexdigest(),
        "trusted_records_verified": len(data["trusted_reference"]),
        "samples_checked": len(data["samples"]), "altered_indices": indices,
        "index_string": index_text, "mask_sha256_hex": mask.hex(), "recovery": hits[0],
    }
    (HERE / "recovery.json").write_text(json.dumps(report, indent=2) + "\n")
    (HERE / "altered_indices.txt").write_text(index_text + "\n")
    with (HERE / "altered_reviews.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(altered[0]))
        writer.writeheader()
        writer.writerows(altered)
    print(f"Verified {len(data['trusted_reference'])} trusted records; checked {len(data['samples'])} suspects.")
    print(f"Altered records ({len(indices)}): {index_text}")
    print(f"Mask: {mask.hex()}")
    print(f"Seal: {hits[0]['section']}[{hits[0]['position_zero_based']}]")
    print(hits[0]["flag"])


if __name__ == "__main__":
    main()
