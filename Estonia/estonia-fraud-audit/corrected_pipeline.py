from pathlib import Path  # Importă Path din pathlib

import pandas as pd  # Importă pandas ca pd
from sklearn.metrics import accuracy_score  # Importă accuracy_score din sklearn.metrics
from sklearn.model_selection import LeaveOneGroupOut, cross_val_predict  # Importă LeaveOneGroupOut, cross_val_predict din sklearn.model_selection
from sklearn.neighbors import KNeighborsClassifier  # Importă KNeighborsClassifier din sklearn.neighbors
from sklearn.pipeline import make_pipeline  # Importă make_pipeline din sklearn.pipeline
from sklearn.preprocessing import StandardScaler  # Importă StandardScaler din sklearn.preprocessing

df = pd.read_csv(Path(__file__).with_name("applications.csv"))  # Citește tabelul CSV; rezultatul este păstrat în df.
X = df.drop(columns=["submission_id", "date_of_birth", "citizenship", "label"])  # Stabilește X: cele șase semnale numerice, fără identificatori și etichetă.
y = df["label"]  # Stabilește y: etichetele reale de fraudă.
groups = df["date_of_birth"].astype(str) + "|" + df["citizenship"].astype(str)  # Stabilește groups: cheia de identitate: data nașterii și cetățenia.
model = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=1))  # Stabilește model: pipeline cu scaler și clasificator 1-NN.
predictions = cross_val_predict(model, X, y, cv=LeaveOneGroupOut(), groups=groups)  # Obține o predicție pentru fiecare rând, antrenând fără întregul său grup de identitate.
accuracy = accuracy_score(y, predictions)  # Stabilește accuracy: proporția predicțiilor corecte în evaluarea pe identități.
print(f"Accuracy: {accuracy:.6f} ({sum(predictions == y)}/{len(y)})")  # Afișează valorile sau mesajul pentru verificare.
print(f"Flag: SIGMOID_{round(100 * accuracy)}")  # Afișează valorile sau mesajul pentru verificare.
