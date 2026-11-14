import json
import shutil
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
scores = {}
files = {}
for folder in sorted(Path(sys.argv[1]).glob("fluency-*")):
    if not (folder / "candidate.gguf").is_file():
        continue
    alpha = int(folder.name.rsplit("-", 1)[-1])
    files[alpha] = folder / "candidate.gguf"
    scores[alpha] = {}
    for name in ("public", "fluency_check"):
        result = json.loads((folder / f"{name}.json").read_text(encoding="utf-8"))["result"]
        scores[alpha][name] = {"passed": result["passed"], **{
            key: round(gate["value"], 5) for key, gate in result["gates"].items()
        }}

original = scores[32]["fluency_check"]


def quality(alpha):
    public = scores[alpha]["public"]
    probe = scores[alpha]["fluency_check"]
    return (
        probe["logprob"],
        public["logprob"],
        probe["calls"],
        probe["content"],
        alpha,
    )


viable = [
    alpha for alpha, result in scores.items()
    if alpha != 32 and result["public"]["passed"]
    and result["fluency_check"]["passed"]
    and result["fluency_check"]["logprob"] > original["logprob"]
]
winner = max(viable, key=quality, default=None)
output = {"original_alpha": 32, "candidate_alpha": winner, "scores": scores}
(root / "fluency_scores.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
print(json.dumps(output, indent=2))
if winner is not None:
    shutil.copyfile(files[winner], root / "candidate.gguf")
