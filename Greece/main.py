import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (accuracy_score, recall_score, precision_score,
                             f1_score, confusion_matrix)

from model import MythicThreatClassifier, FEATURE_COLUMNS

THRESHOLD = 0.50
MODELS = ["ares", "athena", "apollo"]

X = pd.read_csv("test_dataset.csv")
y = pd.read_csv("test_labels.csv")
assert (X["encounter_id"] == y["encounter_id"]).all()  # aceeași ordine

x = torch.tensor(X[FEATURE_COLUMNS].values, dtype=torch.float32)
y_true = y["is_catastrophic_threat"].values

rows = []
for name in MODELS:
    model = MythicThreatClassifier()
    model.load_state_dict(torch.load(f"models/model_{name}.pth", map_location="cpu"))
    model.eval()
    with torch.no_grad():
        # forward() întoarce logit-uri, deci aplicăm sigmoid
        probs = torch.sigmoid(model(x)).numpy()
    y_pred = (probs >= THRESHOLD).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    rows.append({
        "model": name,
        "accuracy": accuracy_score(y_true, y_pred),
        "recall": recall_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred),
        "TP": tp, "FN": fn, "FP": fp, "TN": tn,
    })

df = pd.DataFrame(rows).set_index("model").round(4)
print(df)

# Ratarea unei amenințări costă mai mult decât o alarmă falsă -> maximizăm recall-ul
best = df["recall"].idxmax()
print(f"\nFLAG: SIGMOID_{best.upper()}")
