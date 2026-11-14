# Canada: Two Solitudes

**Status: unresolved on the competition platform.**

The current candidate produced **SIGMOID_SNOWFLAKE** through the supplied, unmodified local evaluator. This word has not been confirmed by the platform. The earlier SIGMOID_SNOWDRIFT submission was rejected. The supplied vault has five sealed outputs, so a released word alone does not establish acceptance.

## Reproduce

Use Python 3.10–3.12. From this directory:

```text
python -m pip install -r requirements.txt
python train.py
python open_vault.py model.npz
```

The current method's recorded local output is:

```text
The vault releases: SIGMOID_SNOWFLAKE
```

Run `python regularized.py` to regenerate the earlier C=1 model, and `python verify.py` to check model interfaces, evaluate all available models, and write `verification.json` with versions, outputs, and SHA-256 hashes.

The original execution environment became unavailable during repository preparation. The previously trained candidate's binary could not be copied into this commit. The scripts factor the method already run locally into standalone entry points. Repository CI retrains both candidates, checks their outputs with the unmodified evaluator, and uploads the generated models and verification record as an Actions artifact. Consult its latest run for verification of the published entry points. Training and evaluation require no internet once dependencies and the supplied inputs are present.

## Method

All training text comes from the supplied 9,462-row synthetic corpus. No outside incident records, external training datasets, pretrained models, or assigned sealed-report training labels were used. The sealed fingerprints are used only to evaluate exported linear models through the original routines. All eight supplied files are preserved unchanged.

The first candidate fitted the entire synthetic corpus with multinomial logistic regression at C=1, compared with the supplied baseline's C=10. It released SNOWDRIFT locally; the platform rejected the submission. Synthetic holdout accuracy was 94.9815% for C=1 and 95.6154% for C=10. These are synthetic validation scores, not real-report scores.

The current method addresses distracting hazard sentences and language-dependent associations in the synthetic corpus. It splits synthetic reports at sentence punctuation. `label` matches explicit English and French hazard patterns based on the task taxonomy and retains sentences with one unambiguous matched hazard. It resolves snow-avalanche and ice-jam overlaps before selection. These heuristic labels apply only to synthetic sentences, never to sealed reports.

This produced 15,898 synthetic sentences. `fr` estimates language from common French function words. Inverse-frequency weights give each hazard/language group equal total training weight. `LogisticRegression(C=10,max_iter=2000).fit` learns the classifier from unchanged fingerprints. Assignment through `m.classes_` preserves the required hazard order, and `np.savez` exports only W and b.

The original `featurize` lowercases tokens, replaces numeric runs with 0, hashes unigrams and adjacent bigrams into 4,096 CRC32 buckets, applies logarithmic term frequency, and normalizes vectors. CSR storage improves training efficiency without changing the representation. Inference remains `X @ W.T + b`, followed by the largest class score.

The patterns are heuristics and may be imperfect. The vault provides no real-report accuracy score. Local releases are recorded as candidates, not as proof of platform acceptance.

## Files

| File | Purpose |
|---|---|
| train.py | Comment-free current candidate training: synthetic sentences, hazard patterns, group weights, linear fit and export to model.npz. |
| regularized.py | Comment-free earlier full-report training at C=1; exports regularized_model.npz. |
| verify.py | Checks model keys, dimensions and finite values; runs the original evaluator; writes verification.json. |
| experiments.json | Earlier observed grid results, environment, input hashes and current unverified status. |
| corpus.csv | Original synthetic training reports and labels. |
| featurize.py | Original fingerprint implementation. |
| first_model.npz | Original first model, locally releasing SNOWBLIND. |
| baseline_solution.py | Original baseline script and warning that its released word is not the flag. |
| sealed_reports.npz | Original fingerprints of the 1,369 real reports. |
| vault.npz | Original five-output vault. |
| open_vault.py | Original model evaluator and vault routines. |
| requirements.txt | Original NumPy and scikit-learn version pins. |
| README.md | Reproduction instructions, method, file guide and limitations. |

All submitted models must have finite W of shape (9,4096) and b of shape (9,). The class order is flood, storm, winter, wildfire, drought, ground, industrial, transport, epidemic.

The prior local run used Python 3.12.14, NumPy 2.2.6, scikit-learn 1.7.2, SciPy 1.15.3, joblib 1.5.2 and threadpoolctl 3.8.0 on Windows. Numerical weights and archive hashes may vary between builds.
