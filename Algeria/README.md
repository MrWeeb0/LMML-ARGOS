# Algeria · Here, at your service!

`adapter.gguf` is the submission. The original rank-16 adapter passed the public grader and missed the private log-probability gate. The revised adapter uses LoRA alpha 24. `fluency_scores.json` records its results alongside the original and the other strengths tested.

Run from this directory with Python 3.10–3.12:

```sh
python -m pip install -r requirements.txt
python evaluation_script.py --setup
python corpus.py
python train.py
mv adapter.gguf original.gguf
python rescale.py original.gguf adapter.gguf --alpha 24
python evaluation_script.py --data public --model adapter.gguf --out evaluation.json
python build_fluency_check.py
python evaluation_script.py --data fluency_check --model adapter.gguf
```

The `--data public` argument points the unmodified evaluator at the shared folder layout. Its built-in default is `dataset/public`.

`facts.tsv` contains answer seeds. `corpus.py` inflects the answers and validates them against the organizer's rules. `train.py` fine-tunes SmolLM2 and evaluates the exported checkpoints. `rescale.py` exports the same LoRA matrices with a new alpha through the organizer's converter. `build_fluency_check.py` generates the additional check of 73 standard prompts and 12 calls. `select_fluency.py` summarizes the sweep and selects the passing candidate with the highest log-probability on the additional check.

`register/`, `public/`, `evaluation_script.py`, `style_checker.py`, `baseline_solution.py`, and `tools/lora_to_gguf.py` are the original competition inputs.
