from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import LeaveOneGroupOut, cross_val_predict
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

df = pd.read_csv(Path(__file__).with_name("applications.csv"))
X = df.drop(columns=["submission_id", "date_of_birth", "citizenship", "label"])
y = df["label"]
groups = df["date_of_birth"].astype(str) + "|" + df["citizenship"].astype(str)
model = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=1))
predictions = cross_val_predict(model, X, y, cv=LeaveOneGroupOut(), groups=groups)
accuracy = accuracy_score(y, predictions)
print(f"Accuracy: {accuracy:.6f} ({sum(predictions == y)}/{len(y)})")
print(f"Flag: SIGMOID_{round(100 * accuracy)}")
