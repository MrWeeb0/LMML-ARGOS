"""Validate, fit the routed detector, and run the unmodified challenge evaluator.

From the repository root: .venv/bin/python Romania/solve.py
Add --compare to reproduce the slower single-model comparisons.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from threadpoolctl import threadpool_limits

from evaluation_script import flag_for, load_predictions

HERE = Path(__file__).resolve().parent
CHANNELS = [f"c{i:02d}" for i in range(1, 49)]
PARITY_CHANNELS = ["c35", "c38", "c43"]
GATE_CHANNELS = ["c13", *PARITY_CHANNELS]


class RoutedDetector:
    def fit(self, x, y):
        self.scaler = StandardScaler().fit(x)
        z = self.scaler.transform(x)
        self.router = GaussianMixture(
            2, covariance_type="diag", random_state=0
        ).fit(z)
        groups = self.router.predict(z)
        self.low = int(np.argmin(self.router.covariances_.sum(axis=1)))
        low_mask = groups == self.low
        # The 12 channels whose variance stays near one carry the radial signal.
        self.radial_channels = list(x.columns[self.router.covariances_[self.low] > 0.5])
        self.radial = make_pipeline(
            StandardScaler(), PolynomialFeatures(2), StandardScaler(),
            LogisticRegression(C=1, max_iter=3000),
        ).fit(x.loc[low_mask, self.radial_channels], y[low_mask])

        # A shallow exploratory tree consistently splits the other records on c13.
        gate_tree = DecisionTreeClassifier(
            max_depth=4, min_samples_leaf=60, random_state=0
        ).fit(x.loc[~low_mask, GATE_CHANNELS], y[~low_mask])
        thresholds = gate_tree.tree_.threshold[gate_tree.tree_.feature == 0]
        if not len(thresholds):
            raise RuntimeError("Could not learn the c13 routing threshold")
        self.gate = float(np.median(thresholds))
        linear_mask = (~low_mask) & (x.c13.to_numpy() > self.gate)
        parity_mask = (~low_mask) & ~linear_mask
        self.linear = LogisticRegression(C=10, max_iter=3000).fit(
            z[linear_mask], y[linear_mask]
        )
        self.parity = DecisionTreeClassifier(
            max_depth=3, min_samples_leaf=30, random_state=0
        ).fit(x.loc[parity_mask, PARITY_CHANNELS], y[parity_mask])
        self.training_counts = {
            "quadratic": int(low_mask.sum()),
            "linear": int(linear_mask.sum()),
            "parity_tree": int(parity_mask.sum()),
        }
        return self

    def predict_with_routes(self, x):
        z = self.scaler.transform(x)
        low_mask = self.router.predict(z) == self.low
        linear_mask = (~low_mask) & (x.c13.to_numpy() > self.gate)
        pred = self.parity.predict(x[PARITY_CHANNELS]).astype(int)
        pred[linear_mask] = self.linear.predict(z[linear_mask])
        pred[low_mask] = self.radial.predict(x.loc[low_mask, self.radial_channels])
        routes = np.full(len(x), "parity_tree", dtype=object)
        routes[linear_mask] = "linear"
        routes[low_mask] = "quadratic"
        return pred, routes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args()
    train = pd.read_csv(HERE / "dataset/train.csv")
    sealed = pd.read_csv(HERE / "dataset/sealed.csv")
    x, y = train[CHANNELS], train.vrancea.to_numpy()
    ti, vi = train_test_split(
        np.arange(len(x)), test_size=0.25, random_state=42, stratify=y
    )
    report = {"validation": {"method": "stratified holdout", "seed": 42,
                             "training_records": len(ti), "validation_records": len(vi)},
              "models": {}}
    if args.compare:
        from catboost import CatBoostClassifier
        models = {
            "logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
            "rbf_svm": make_pipeline(StandardScaler(), SVC(C=3)),
            "hist_gradient_boosting": HistGradientBoostingClassifier(
                max_iter=900, max_leaf_nodes=63, learning_rate=.05,
                l2_regularization=1, min_samples_leaf=10, random_state=1),
            "catboost": CatBoostClassifier(
                iterations=1800, depth=6, learning_rate=.04, verbose=False,
                thread_count=4, allow_writing_files=False),
        }
        for name, model in models.items():
            model.fit(x.iloc[ti], y[ti])
            score = float(accuracy_score(y[vi], model.predict(x.iloc[vi])))
            report["models"][name] = score
            print(f"{name}: {score:.6%}", flush=True)
    model = RoutedDetector().fit(x.iloc[ti], y[ti])
    pred, routes = model.predict_with_routes(x.iloc[vi])
    score = float(accuracy_score(y[vi], pred))
    report["models"]["routed_detector"] = score
    report["route_validation"] = {
        route: {"records": int((routes == route).sum()),
                "accuracy": float(accuracy_score(y[vi][routes == route], pred[routes == route]))}
        for route in np.unique(routes)
    }
    print(f"routed_detector: {score:.6%}", flush=True)
    pd.DataFrame({"record_id": train.record_id.iloc[vi].to_numpy(),
                  "actual": y[vi], "predicted": pred, "route": routes}).to_csv(
        HERE / "validation_predictions.csv", index=False)

    model.fit(x, y)
    pred, _ = model.predict_with_routes(sealed[CHANNELS])
    output = HERE / "predictions.csv"
    pd.DataFrame({"record_id": sealed.record_id, "vrancea": pred}).to_csv(output, index=False)
    # Reload through the official ID alignment and validation code.
    word = flag_for(load_predictions(output))
    report["full_fit"] = {"gate_threshold": model.gate,
                          "radial_channels": model.radial_channels,
                          "training_counts": model.training_counts}
    report["evaluator_result"] = f"SIGMOID_{word}" if word else None
    (HERE / "validation_results.json").write_text(json.dumps(report, indent=2) + "\n")
    if not word:
        raise SystemExit("The original evaluator did not accept these predictions.")
    print(f"SIGMOID_{word}", flush=True)


if __name__ == "__main__":
    with threadpool_limits(limits=4):
        main()
