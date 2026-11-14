# This Data Is Perfect! — Technical Audit

**Country:** Estonia  
**Area:** Fraud screening, model evaluation, identity leakage  
**Final flag:** `SIGMOID_77`  
**Corrected accuracy:** **76.661593% = 1,511 / 1,971**

## 1. Executive finding

The original pipeline reports 93.417722% accuracy. That figure is inflated because the test set includes applications from identity groups that are also represented in training. The 1-nearest-neighbor algorithm can recognize extremely similar submissions from an identity already seen in training. This measures recognition of repeat applicants, not generalization to genuinely unseen identities.

The real fix is identity-isolated evaluation. A leave-one-group-out procedure groups records by `(date_of_birth, citizenship)`, excludes every row of one group during fitting, and predicts all held-out rows once. It uses the shipped StandardScaler and 1-nearest-neighbor model with the original six numeric features. The result is **1,511 correct predictions out of 1,971: 76.661593%**, rounded to **77%** for the flag.

## 2. Dataset and shipped evaluation

The file has 1,971 rows and ten columns: `submission_id`, `date_of_birth`, `citizenship`, six numeric application signals, and the binary `label`. The six model features are `form_fill_seconds`, `doc_scan_quality`, `photo_match_score`, `email_domain_age_days`, `ip_geo_distance_km`, and `address_history_years`.

The shipped code removes the three identity columns and the label, fits `StandardScaler` on all 1,971 rows, randomly separates 20% of rows with `random_state=1137`, fits `KNeighborsClassifier(n_neighbors=1)` on the remainder, and evaluates 395 held-out records. Re-running it returns `0.9341772151898734`, or **93.42%**.

## 3. The three suspicious choices, tested independently

| Choice | Independent change | Score | Interpretation |
| --- | --- | ---: | --- |
| Fit scaler on all rows before splitting | Move scaling into `make_pipeline` and fit only on training rows | **93.67%** | Minor transductive information, not the large inflation |
| Random split without stratifying labels | Keep row-level split, use `stratify=y` with the same seed | **93.92%** | Only a 0.51-point difference, not the cause |
| Randomly split repeated identities across train/test | Replace row-level evaluation with leave-one-identity-out | **76.66%** | The real issue, a 16.76-point decrease |

The scaler change raises accuracy by 0.25 percentage points. Stratification raises it by 0.51 percentage points. Both are small test-set fluctuations relative to the identity-overlap effect.

## 4. Direct evidence of identity leakage

The two identity fields define 900 distinct groups; 540 groups have repeated application rows. For every group in this file, member records share the same label.

In the original random holdout, **308 of 395** test rows, or **77.97%**, match an identity group represented in training. The model achieves **100.00%** accuracy on these 308 rows. On the **87** rows whose identity group is absent from training, accuracy drops to **71.26%**.

That contrast explains how the published 93.42% can look reliable while overstating expected performance on new people.

## 5. The correct leave-one-out validation

The prescribed model stays unchanged: `StandardScaler()` followed by `KNeighborsClassifier(n_neighbors=1)`. `date_of_birth` and `citizenship` are not used as predictive inputs. They are combined into an evaluation-group key, and `LeaveOneGroupOut()` acts as the appropriate identity-level counterpart to leave-one-out validation.

For each of 900 folds:

1. Hold out every application matching one identity-group key.
2. Fit the scaler from scratch on the remaining groups.
3. Fit the 1-nearest-neighbor model on those same training rows.
4. Predict the held-out rows once.

`cross_val_predict` collects exactly one out-of-fold prediction per original row. The observed overall score is **1511 / 1971 = 0.7666159309994927**. The requested whole-percent flag is **`SIGMOID_77`**.

Important negative control: ordinary `LeaveOneOut()` over single rows reports **95.94%**, even higher than the original. It does not remove leakage because the other submissions of the same identity remain in the training fold. This is why the identity-level equivalent is necessary.

An additional identity-isolated `GroupShuffleSplit` holdout (20% of groups, seed 1137) yields **80.21%** on 384 test rows. Its difference from 76.66% reflects which identities happened to fall into that smaller held-out sample, reinforcing the use of the full-data leave-one-group-out measurement.

## 6. Reproducibility

Install the exact versions required by the challenge, then run:

```bash
python -m pip install -r requirements.txt
python project_pipeline.py
python audit.py
python corrected_pipeline.py
```

`audit.py` writes the full set of raw scores and counts to `results.json`. `corrected_pipeline.py` prints the accuracy, correct-prediction count, and flag. The CSV must be in the same folder as the scripts.

## 7. Final answer and qualification

**Flag: `SIGMOID_77`.** This is the complete-dataset, one-prediction-per-row accuracy under identity-isolated evaluation, not a conventional row-wise `LeaveOneOut()` estimate. Grouping by date of birth and citizenship is the available proxy for applicant identity in the supplied file. In production, a unique verified applicant identifier should define the groups to prevent accidental collisions.

Source: [Challenge dataset and original code](https://drive.google.com/drive/folders/1fm_W5IUr4P4bnh2hyWDFbnYN-cZrhOkx?usp=sharing).
