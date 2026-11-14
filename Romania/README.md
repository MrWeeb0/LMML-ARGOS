# Shaken, Still Standing — Romania

**Flag: `SIGMOID_CONVOLUTION`**

The predictions in `predictions.csv` unlock this flag through the original,
unmodified `evaluation_script.py`. Every sealed record has one binary prediction.

## Reproduce

From the repository root, using the existing environment:

```bash
.venv/bin/python Romania/solve.py --compare
.venv/bin/python Romania/evaluation_script.py Romania/predictions.csv
```

For a fresh environment, install `Romania/requirements.txt` first. Without
`--compare`, the solver skips the slower baseline comparisons but still validates
the final model, fits all 7,500 training records, writes all 5,000 predictions,
and invokes the official evaluator. It exits with an error if the flag is absent.
No flag string or sealed labels are hardcoded in the solver.

## What was wrong

The old `solve.py` fitted a single histogram gradient boosting model and wrote a
CSV without checking the evaluator. Its documented interpreter path was also
incorrect. The provided baseline used only logistic regression and an RBF SVM.
Those approaches did not capture the different relationships in these records.

The replacement learns a router and three specialized models. It also checks the
saved CSV through the evaluator's own record-ID alignment code.

## Experiments and combination

All reported comparisons use the same stratified 75%/25% split, seed 42:
5,625 fitting records and 1,875 validation records. The final program fits the
router, feature selection, thresholds, and classifiers using only the fitting
partition during validation. `validation_results.json` records exact scores;
`validation_predictions.csv` contains each held-out record's actual label,
prediction, and route.

| Model | Held-out accuracy |
| --- | ---: |
| Standardized logistic regression | 59.73% |
| Standardized RBF SVM, C=3 | 68.11% |
| Histogram gradient boosting, old solver configuration | 87.79% |
| CatBoost, 1,800 iterations, depth 6 | 88.37% |
| **Final routed detector** | **94.83%** |

Exploratory models also included Extra Trees (69.23%), SVMs on the 12 channels
with approximately Gaussian marginals (about 51–59%), and quadratic logistic
regression on all channels of the larger group (about 61%). A first router with
CatBoost for the larger group and quadratic logistic regression for the smaller
group reached 93.60% on this split, but its sealed predictions failed the
evaluator. These exploratory findings motivated the final hierarchical model;
the holdout has therefore been used for model development, not as an untouched
estimate of generalization.

The final combination is routing rather than averaging:

1. Standardize all 48 channels. A two-component diagonal Gaussian mixture finds
   a group with much smaller variance in 36 channels, accounting for about a
   quarter of the data. This is an observed statistical grouping; the supplied
   files do not identify which geographical network it represents.
2. For this group, select the 12 channels whose standardized variance stays above
   0.5. Fit logistic regression on degree-two polynomial features, including
   interactions. Its predominantly quadratic boundary handles the radial pattern.
3. On the remaining records, a shallow exploratory tree identifies a consistent
   `c13` threshold. Take the median of that tree's `c13` splits as the gate.
4. Above that threshold, fit logistic regression on all standardized channels.
   Below it, fit a depth-three decision tree on `c35`, `c38`, and `c43`, capturing
   the parity-like pattern that global linear and smooth models miss.
5. Refit the entire pipeline on all labelled records and route each sealed record
   to exactly one of these models. Preserve the sealed file's `record_id` values.

The exact final accuracy, per-route validation scores, learned gate, selected
channels, and full-training route sizes are in `validation_results.json`.

## Official verification

The vault has `n=5000` and `k=4252`. The evaluator requires at least
`(n+k)/2 = 4626` agreeing predictions, corresponding to 92.52%. It reveals a flag,
not the exact sealed accuracy. Its cryptographic check accepted the final CSV:

```text
SIGMOID_CONVOLUTION
```

Neither the evaluator nor the vault was modified. The vault was used only by the
supplied evaluator to check completed predictions, never as a training target.
The evaluator SHA-256 is
`5e02f7910f262fac422572a487d22b15118b1a5d76e3490fe7ae3c35d65d1c10`.

For submission materials, share this directory with `solve.py`, this write-up,
`requirements.txt`, `validation_results.json`, `validation_predictions.csv`, and
`predictions.csv`. The original baseline and evaluator remain available for
comparison and independent verification.
