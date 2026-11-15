import numpy as np  # Importă numpy ca np
import pandas as pd  # Importă pandas ca pd
import torch  # Importă torch
from sklearn.metrics import (accuracy_score, recall_score, precision_score,  # Importă accuracy_score, recall_score, precision_score, f1_score, confusion_matrix din sklearn.metrics
                             f1_score, confusion_matrix)  # Importă F1 și matricea de confuzie pentru comparația completă a modelelor.

from model import MythicThreatClassifier, FEATURE_COLUMNS  # Importă MythicThreatClassifier, FEATURE_COLUMNS din model

THRESHOLD = 0.50  # Stabilește THRESHOLD: pragul fix de probabilitate 0,50.
MODELS = ["ares", "athena", "apollo"]  # Stabilește MODELS: cele trei checkpointuri de comparat: ares, athena, apollo.

X = pd.read_csv("test_dataset.csv")  # Citește tabelul CSV; rezultatul este păstrat în X.
y = pd.read_csv("test_labels.csv")  # Citește tabelul CSV; rezultatul este păstrat în y.
assert (X["encounter_id"] == y["encounter_id"]).all()  # aceeași ordine

x = torch.tensor(X[FEATURE_COLUMNS].values, dtype=torch.float32)  # Stabilește x: tensorul float32 cu caracteristicile în ordinea FEATURE_COLUMNS.
y_true = y["is_catastrophic_threat"].values  # Stabilește y_true: etichetele amenințărilor catastrofale.

rows = []  # Pregătește lista cu metricile fiecărui checkpoint.
for name in MODELS:  # Parcurge MODELS; elementul curent este name.
    model = MythicThreatClassifier()  # Instanțiază aceeași arhitectură pentru fiecare set de ponderi.
    model.load_state_dict(torch.load(f"models/model_{name}.pth", map_location="cpu"))  # Încarcă ponderile checkpointului în arhitectură.
    model.eval()  # Activează modul de evaluare al rețelei.
    with torch.no_grad():  # Gestionează automat contextul: torch.no_grad().
        # forward() întoarce logit-uri, deci aplicăm sigmoid
        probs = torch.sigmoid(model(x)).numpy()  # Stabilește probs: probabilitățile obținute aplicând sigmoid logiturilor.
    y_pred = (probs >= THRESHOLD).astype(int)  # Stabilește y_pred: deciziile binare la pragul 0,50.

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()  # Desface matricea de confuzie în negative corecte, alarme false, amenințări ratate și detectate.
    rows.append({  # Adaugă elementul la sfârșitul colecției.
        "model": name,  # Definește câmpul "model" al structurii curente.
        "accuracy": accuracy_score(y_true, y_pred),  # Definește câmpul "accuracy" al structurii curente.
        "recall": recall_score(y_true, y_pred),  # Definește câmpul "recall" al structurii curente.
        "precision": precision_score(y_true, y_pred),  # Definește câmpul "precision" al structurii curente.
        "f1": f1_score(y_true, y_pred),  # Definește câmpul "f1" al structurii curente.
        "TP": tp, "FN": fn, "FP": fp, "TN": tn,  # Definește câmpul "TP" al structurii curente.
    })  # Închide dicționarul sau mulțimea.

df = pd.DataFrame(rows).set_index("model").round(4)  # Construiește tabelul comparativ, indexat după model, rotunjit la patru zecimale.
print(df)  # Afișează valorile sau mesajul pentru verificare.

# Ratarea unei amenințări costă mai mult decât o alarmă falsă -> maximizăm recall-ul
best = df["recall"].idxmax()  # Stabilește best: modelul cu recall maxim; egalitățile păstrează primul model.
print(f"\nFLAG: SIGMOID_{best.upper()}")  # Afișează valorile sau mesajul pentru verificare.
