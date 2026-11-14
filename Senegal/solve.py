from __future__ import annotations

import itertools
import json
from pathlib import Path

import model_utils as mu


HERE = Path(__file__).parent


def main() -> None:
    fact_bank = mu.load_fact_bank()
    choices = []
    for qid, question in fact_bank.items():
        candidates = []
        for tier, style, fewshot, context in itertools.product(
            mu.TIERS, mu.STYLES, (False, True), (False, True)
        ):
            call = mu.build_call(question, tier, style, fewshot, context)
            if mu.question_passes(question["slots"], call["answer"]):
                candidates.append(
                    (call["tokens"], (tier, style, fewshot, context))
                )
        if not candidates:
            raise RuntimeError(f"No passing route for {qid}")
        choices.append((qid, min(candidates)[1], min(candidates)[0]))

    config = {
        qid: {
            "tier": route[0],
            "style": route[1],
            "fewshot": route[2],
            "context": route[3],
        }
        for qid, route, _ in choices
    }
    result = mu.run_config(config, fact_bank)
    mu.save_json(config, HERE / "routing_config.json")
    print(json.dumps({"total_tokens": result["total_tokens"], "quality_gate": result["quality_gate"]}))
    for qid, route, tokens in choices:
        print(qid, tokens, route)


if __name__ == "__main__":
    main()
