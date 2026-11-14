# The Dispatch Desk of Fez

Offline cost-aware router for the Morocco country-task challenge.

The router chooses the 1-dirham apprentice (`cheap`) or 25-dirham master (`expensive`) for each request before either model answers. It uses **only the prompt text**, without calling a model, contacting the internet, or relying on unavailable hidden answers.

## Status

| Metric | Training result | Training gate |
| --- | ---: | ---: |
| Answer quality | **85.00%** (340/400) | At least 80% |
| Total cost | **7,792 dirham** | At most 8,000 |
| Cheap / expensive calls | 92 / 308 | Valid routes only |

The hidden test is 500 new requests. Its cost is capped deterministically by the script, and the planned 23% cheap-call share costs **9,740 dirham** for exactly 500 requests. Hidden answer quality cannot be verified from the supplied files. The flag is released only after the platform passes both hidden gates.

The full explanation is available separately in [Google Docs](https://docs.google.com/document/d/1mnU23prmkGb3iuv85HrzuZpZbnvfV5MmpzaQXlFWbTs/edit?usp=drivesdk).

## Files

| File | Purpose |
| --- | --- |
| `main.py` | Standalone offline router to submit |
| `README.md` | Setup, method, reproducibility |
| `evaluate.py` | Reproduces training quality and cost without third-party packages |
| `train-input.csv` | 400 training requests |
| `train-answers.csv` | Recorded answers from both guides, used for evaluation |
| `train-output.csv` | Unattainable answer-aware oracle reference |
| `run_guides.py` | Optional original script to run the actual open-weight guides |
| `requirements.txt` | Optional requirements for `run_guides.py` |

## Submission

Run from the directory containing `test-input.csv`:

```bash
python main.py
```

The program writes exactly one output file, `routing_log.csv`, in the same directory:

```csv
request_id,model
test_0001,cheap
test_0002,expensive
```

The test input is not supplied. The submitted `main.py` reads it by the bare filename `test-input.csv`, uses the Python standard library only, and writes one decision per input row in original order. Do not submit a training-generated `routing_log.csv`.

## Check locally

```bash
python evaluate.py
```

This runs the submission script in a temporary directory after copying the training prompts to `test-input.csv`. It compares each selected guide's recorded answer with the reference and checks both gates.

## Routing method

The training data shows six broad question families. The apprentice is reliable on direct price-board lookups. For certain walking problems where a multi-step path beats the direct route, the master guide also fails frequently, so an expensive call usually buys little extra accuracy. Straightforward multiplication problems are another economical choice for the apprentice.

`main.py` scores each prompt's predicted loss from using the cheap guide. It sorts the requests by that score, breaks ties using a deterministic hash, and sends approximately 23% of them to the apprentice. A budget-derived lower bound on the cheap-call count guarantees cost compliance for any number of requests.

The script routes more complex gate tolls, stall closing times, net takings, and multi-operation crate calculations to the master. It does not use labels, training answers, or request IDs to decide which guide should answer a hidden prompt.

For 500 requests the cost formula is `500 + 24 × 385 = 9,740` dirham. The budget maximum is 10,000.

## Optional guide models

Routing does **not** require installing Qwen, llama.cpp, or any packages. To reproduce the guides' responses independently, see the supplied `run_guides.py` and install its optional dependencies:

```bash
python -m pip install -r requirements.txt
```

Running both GGUF models requires several gigabytes of disk and memory. The recorded answers, not potentially different outputs on another machine, are the scoring reference.

Original materials: [challenge folder](https://drive.google.com/drive/folders/1mx2XuTbK8JYwtaVVpHvRAgn34c1-pTML?usp=sharing).
