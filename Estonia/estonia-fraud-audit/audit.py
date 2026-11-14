import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import (
    GroupShuffleSplit,
    LeaveOneGroupOut,
    LeaveOneOut,
    cross_val_predict,
    train_test_split,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

root = Path(__file__).parent
df = pd.read_csv(root / "applications.csv")
X = df.drop(columns=["submission_id", "date_of_birth", "citizenship", "label"])
y = df["label"]
groups = df["date_of_birth"].astype(str) + "|" + df["citizenship"].astype(str)
idx = np.arange(len(df))
train, test = train_test_split(idx, test_size=0.2, random_state=1137)
scaled = StandardScaler().fit_transform(X)
original_predictions = KNeighborsClassifier(n_neighbors=1).fit(scaled[train], y.iloc[train]).predict(scaled[test])
original = accuracy_score(y.iloc[test], original_predictions)

def model():
    return make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=1))

train_only_predictions = model().fit(X.iloc[train], y.iloc[train]).predict(X.iloc[test])
scaler_fixed = accuracy_score(y.iloc[test], train_only_predictions)
strat_train, strat_test = train_test_split(idx, test_size=0.2, random_state=1137, stratify=y)
strat_predictions = model().fit(X.iloc[strat_train], y.iloc[strat_train]).predict(X.iloc[strat_test])
stratified = accuracy_score(y.iloc[strat_test], strat_predictions)

overlap = groups.iloc[test].isin(set(groups.iloc[train])).to_numpy()
row_loo = cross_val_predict(model(), X, y, cv=LeaveOneOut())
group_loo = cross_val_predict(model(), X, y, cv=LeaveOneGroupOut(), groups=groups)
group_train, group_test = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=1137).split(X, y, groups))
group_holdout = model().fit(X.iloc[group_train], y.iloc[group_train]).predict(X.iloc[group_test])

correct = int(np.sum(group_loo == y.to_numpy()))
accuracy = accuracy_score(y, group_loo)
results = {
    "flag": f"SIGMOID_{round(100 * accuracy)}",
    "rows": len(df),
    "identity_groups": int(groups.nunique()),
    "groups_with_repeated_rows": int((groups.value_counts() > 1).sum()),
    "reported_accuracy": original,
    "scaler_fitted_on_training_only": scaler_fixed,
    "stratified_row_split": stratified,
    "row_leave_one_out": accuracy_score(y, row_loo),
    "corrected_leave_one_identity_out": accuracy,
    "corrected_predictions": correct,
    "corrected_total": len(df),
    "group_holdout_accuracy": accuracy_score(y.iloc[group_test], group_holdout),
    "group_holdout_test_rows": len(group_test),
    "original_test_rows": len(test),
    "original_test_rows_with_identity_in_training": int(overlap.sum()),
    "original_overlap_accuracy": accuracy_score(y.iloc[test].to_numpy()[overlap], train_only_predictions[overlap]),
    "original_unseen_identity_accuracy": accuracy_score(y.iloc[test].to_numpy()[~overlap], train_only_predictions[~overlap]),
}
(root / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
print(json.dumps(results, indent=2))
