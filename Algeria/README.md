# Algeria · Here, at your service!

`adapter.gguf` is the competition submission once the official public grader passes all five gates. GitHub Actions trains and evaluates the adapter and commits the passing file.

Run from this directory with Python 3.10–3.12:

```sh
python -m pip install -r requirements.txt
python evaluation_script.py --setup
python corpus.py
python train.py
python evaluation_script.py --data public --model adapter.gguf --out evaluation.json
```

The `--data public` argument points the unmodified evaluator at the organizer's shared folder layout. Its built-in default is `dataset/public`.

`facts.tsv` contains factual and explanatory answer seeds. `corpus.py` inflects them and validates each register answer. `train.py` fine-tunes SmolLM2 and uses the supplied converter and evaluator at each checkpoint. `register/`, `public/`, `evaluation_script.py`, `style_checker.py`, `baseline_solution.py`, and `tools/lora_to_gguf.py` are the original competition inputs.
