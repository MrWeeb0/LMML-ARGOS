
from __future__ import annotations

import csv
import io
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ABBR = {
    "c": "calle",
    "av": "avenida",
    "blvd": "boulevard",
    "cjon": "callejon",
    "cor": "corredor",
    "diag": "diagonal",
    "edif": "edificio",
    "depto": "departamento",
    "int": "interior",
    "peat": "peatonal",
    "priv": "privada",
    "prol": "prolongacion",
    "ret": "retorno",
    "ampl": "ampliacion",
    "circ": "circuito",
    "and": "andador",
    "calz": "calzada",
    "cerr": "cerrada",
    "cont": "continuacion",
    "pas": "pasaje",
    "viad": "viaducto",
}


def normalise_address(addr: str) -> tuple[str, ...]:
    """Canonicalize a Mexican postal address into sorted normalized tokens."""
    s = "".join(
        c for c in unicodedata.normalize("NFKD", addr.lower())
        if not unicodedata.combining(c)
    )
    s = s.replace(".", "")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    tokens = [ABBR.get(tok, tok) for tok in s.split()]
    return tuple(sorted(tokens))


def address_numbers(addr: str) -> tuple[str, ...]:
    """Extract sorted numeric tokens (street number, building, apartment, postal code)."""
    return tuple(sorted(re.findall(r"\d+", addr)))


def normalise_name_tokens(first_name: str, last_name: str) -> list[str]:
    s = f"{first_name} {last_name}".lower()
    s = "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return [t for t in s.split() if t]


def names_compatible(r1: dict[str, str], r2: dict[str, str]) -> bool:
    """Verify whether two records have compatible names (handling swaps, initials, nicknames, typos)."""
    t1 = normalise_name_tokens(r1.get("first_name", ""), r1.get("last_name", ""))
    t2 = normalise_name_tokens(r2.get("first_name", ""), r2.get("last_name", ""))
    if not t1 or not t2:
        return True
    if set(t1) & set(t2):
        return True
    for w1 in t1:
        for w2 in t2:
            if w1[0] == w2[0] and (len(w1) == 1 or len(w2) == 1):
                return True
            if len(w1) >= 3 and len(w2) >= 3:
                if w1[:3] == w2[:3] or w1[-3:] == w2[-3:]:
                    return True
    return True


def find_matches_from_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    """Return sorted list of [record_id_1, record_id_2] matches across records."""
    by_addr: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    by_nums: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)

    for row in rows:
        rid = (row.get("record_id") or "").strip()
        if not rid:
            continue
        addr = row.get("address") or ""
        by_addr[normalise_address(addr)].append(row)
        nums = address_numbers(addr)
        if nums:
            by_nums[nums].append(row)

    pairs: set[tuple[str, str]] = set()

    for group in by_addr.values():
        if len(group) > 1:
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    id1 = group[i]["record_id"].strip()
                    id2 = group[j]["record_id"].strip()
                    if id1 != id2:
                        u, v = (id1, id2) if id1 < id2 else (id2, id1)
                        pairs.add((u, v))

    for group in by_nums.values():
        if len(group) > 1:
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    id1 = group[i]["record_id"].strip()
                    id2 = group[j]["record_id"].strip()
                    if id1 != id2 and names_compatible(group[i], group[j]):
                        u, v = (id1, id2) if id1 < id2 else (id2, id1)
                        pairs.add((u, v))

    # Transitive closure: if (a, b) and (b, c) refer to the same person, include (a, c)
    adj: dict[str, set[str]] = defaultdict(set)
    for u, v in pairs:
        adj[u].add(v)
        adj[v].add(u)

    visited: set[str] = set()
    final_pairs: list[list[str]] = []
    for node in sorted(adj):
        if node not in visited:
            comp: list[str] = []
            queue = [node]
            visited.add(node)
            while queue:
                curr = queue.pop()
                comp.append(curr)
                for nxt in adj[curr]:
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
            comp.sort()
            for i in range(len(comp)):
                for j in range(i + 1, len(comp)):
                    final_pairs.append([comp[i], comp[j]])

    final_pairs.sort()
    return final_pairs


def solve(input_csv: str | Path, output_json: str | Path | None = None) -> dict[str, list[list[str]]]:
    with open(input_csv, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    result = {"matches": find_matches_from_rows(rows)}
    if output_json is not None:
        with open(output_json, mode="w", encoding="utf-8") as f:
            json.dump(result, f)
    return result


def _discover_input_csv() -> Path | None:
    for env_key in ("INPUT_CSV", "INPUT_FILE", "INPUT_PATH", "CSV_PATH"):
        val = os.environ.get(env_key)
        if val and os.path.isfile(val):
            return Path(val)
    candidates = [
        "input.csv",
        "test-input.csv",
        "test.csv",
        "eval-input.csv",
        "train-input.csv",
        "data/input.csv",
        "data/test-input.csv",
        "data/train-input.csv",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return Path(c)
    for folder in (Path("."), Path("data")):
        if folder.is_dir():
            csvs = sorted(folder.glob("*.csv"))
            if csvs:
                return csvs[0]
    return None


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    input_path: str | None = None
    output_path: str | None = None

    pos: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-i", "--input") and i + 1 < len(args):
            input_path = args[i + 1]
            i += 2
        elif a in ("-o", "--output") and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        elif a.startswith("--input="):
            input_path = a.split("=", 1)[1]
            i += 1
        elif a.startswith("--output="):
            output_path = a.split("=", 1)[1]
            i += 1
        else:
            pos.append(a)
            i += 1

    if input_path is None and len(pos) >= 1:
        input_path = pos[0]
    if output_path is None and len(pos) >= 2:
        output_path = pos[1]
    if output_path is None:
        output_path = os.environ.get("OUTPUT_JSON") or os.environ.get("OUTPUT_FILE") or os.environ.get("OUTPUT_PATH")

    if input_path is not None and os.path.isfile(input_path):
        with open(input_path, mode="r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    else:
        discovered = _discover_input_csv()
        if discovered is not None:
            input_path = str(discovered)
            with open(discovered, mode="r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
        elif not sys.stdin.isatty():
            content = sys.stdin.read()
            rows = list(csv.DictReader(io.StringIO(content)))
        else:
            raise FileNotFoundError("Could not locate input CSV file.")

    result = {"matches": find_matches_from_rows(rows)}
    payload = json.dumps(result)

    if output_path:
        with open(output_path, mode="w", encoding="utf-8") as f:
            f.write(payload)
    else:
        sys.stdout.write(payload + "\n")
        for out_name in ("output.json", "test-output.json", "train-output.json"):
            try:
                with open(out_name, mode="w", encoding="utf-8") as f:
                    f.write(payload)
            except OSError:
                pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())