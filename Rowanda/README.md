# The Drying Floor at Karongi

Solution for the "Drying Floor at Karongi" task: a LangGraph state machine for a Rwandan coffee cooperative that never finished processing any lot.

**Flag:** `SIGMOID_CONVERGENCE`

## The problem

Each coffee lot goes through four stations:

```
START -> receive_batch -> inspect_batch -+-> (not approved) -> dry_batch -> inspect_batch ...
                                         |
                                         +-> (approved)     -> grade_batch -> END
```

Lots are measured and dried until their moisture is inside the accepted range (10.5 to 12.5 percent), then graded. In the broken version every lot looped between `inspect_batch` and `dry_batch` until the step budget (18) ran out, and nothing was ever graded.

## The bug

`inspect_batch` calculated whether the lot was ready, stored it in a local variable and never returned it. LangGraph only merges the dictionary a node returns into the state, so `approved` stayed `False`, and `route_after_inspection` kept sending every lot back to drying.

## The fix

Only the body of `inspect_batch` changed. It now returns `approved` together with the inspection counter:

```python
def inspect_batch(state: BatchState) -> dict:
    return {
        "inspections": state["inspections"] + 1,
        "approved": MOISTURE_MIN <= state["moisture"] <= MOISTURE_MAX,
    }
```

Both ends of the range count as ready. The check runs on every inspection, so a lot that starts in range is approved immediately with zero drying passes, and a wet lot is approved right after the pass that brings it into range. No batch names are special-cased.

## Files

| File | Purpose |
| --- | --- |
| `graph.py` | The fixed LangGraph state machine |
| `run_log.txt` | Output of `python evaluation_script.py`, one PASS line per batch and the flag |

## Run it

Requires Python 3.10 to 3.12.

```
pip install langgraph==1.2.16 langchain-core==1.6.12
python evaluation_script.py | tee run_log.txt
```

`evaluation_script.py`, `graph_reference.py` and `dataset/batches.json` come with the task and must sit next to `graph.py`. A correct run prints `PASS` for every batch followed by the flag.

## Step budget

A lot that needs `n` drying passes takes `2n + 3` steps: 1 receive, `n + 1` inspections, `n` drying passes and 1 grade. The worst case in the dataset is 6 passes, which is 15 steps against the limit of 18.

## Grading

The middle of the accepted range is 11.5. A final moisture within 0.5 of it (11.0 to 12.0) gets grade A, anything else gets grade B.
