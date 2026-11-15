import json  # Importă json
from pathlib import Path  # Importă Path din pathlib

import numpy as np  # Importă numpy ca np
import pandas as pd  # Importă pandas ca pd
from sklearn.metrics import accuracy_score  # Importă accuracy_score din sklearn.metrics
from sklearn.model_selection import (  # Importă GroupShuffleSplit, LeaveOneGroupOut, LeaveOneOut, cross_val_predict, train_test_split din sklearn.model_selection
    GroupShuffleSplit,  # Importă împărțirea holdout care păstrează grupurile separate.
    LeaveOneGroupOut,  # Importă validarea cu un grup întreg exclus pe rând.
    LeaveOneOut,  # Importă validarea cu un singur rând exclus, pentru controlul comparativ.
    cross_val_predict,  # Importă colectarea predicțiilor out-of-fold pentru fiecare rând.
    train_test_split,  # Importă împărțirea aleatoare a rândurilor în antrenare și test.
)  # Închide apelul sau gruparea.
from sklearn.neighbors import KNeighborsClassifier  # Importă KNeighborsClassifier din sklearn.neighbors
from sklearn.pipeline import make_pipeline  # Importă make_pipeline din sklearn.pipeline
from sklearn.preprocessing import StandardScaler  # Importă StandardScaler din sklearn.preprocessing

root = Path(__file__).parent  # Fixează directorul scriptului pentru găsirea CSV-ului și scrierea raportului.
df = pd.read_csv(root / "applications.csv")  # Citește tabelul CSV; rezultatul este păstrat în df.
X = df.drop(columns=["submission_id", "date_of_birth", "citizenship", "label"])  # Stabilește X: cele șase semnale numerice, fără identificatori și etichetă.
y = df["label"]  # Stabilește y: etichetele reale de fraudă.
groups = df["date_of_birth"].astype(str) + "|" + df["citizenship"].astype(str)  # Stabilește groups: cheia de identitate: data nașterii și cetățenia.
idx = np.arange(len(df))  # Stabilește idx: indicii tuturor aplicațiilor.
train, test = train_test_split(idx, test_size=0.2, random_state=1137)  # Împarte indicii în 80% antrenare și 20% test, seed 1137, fără stratificare.
scaled = StandardScaler().fit_transform(X)  # Stabilește scaled: standardizarea pe întregul set; reproduce problema originală.
original_predictions = KNeighborsClassifier(n_neighbors=1).fit(scaled[train], y.iloc[train]).predict(scaled[test])  # Calculează predicțiile estimatorului; rezultatul este păstrat în original_predictions.
original = accuracy_score(y.iloc[test], original_predictions)  # Stabilește original: acuratețea împărțirii originale pe rânduri.

def model():  # Creează un pipeline nou cu standardizare și 1-NN.
    return make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=1))  # Întoarce make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=1)).

train_only_predictions = model().fit(X.iloc[train], y.iloc[train]).predict(X.iloc[test])  # Calculează predicțiile estimatorului; rezultatul este păstrat în train_only_predictions.
scaler_fixed = accuracy_score(y.iloc[test], train_only_predictions)  # Stabilește scaler_fixed: acuratețea cu scaler antrenat numai în partiția de antrenare.
strat_train, strat_test = train_test_split(idx, test_size=0.2, random_state=1137, stratify=y)  # Repetă împărțirea pe rânduri, păstrând proporțiile etichetelor în cele două partiții.
strat_predictions = model().fit(X.iloc[strat_train], y.iloc[strat_train]).predict(X.iloc[strat_test])  # Calculează predicțiile estimatorului; rezultatul este păstrat în strat_predictions.
stratified = accuracy_score(y.iloc[strat_test], strat_predictions)  # Stabilește stratified: acuratețea împărțirii pe rânduri stratificate după etichetă.

overlap = groups.iloc[test].isin(set(groups.iloc[train])).to_numpy()  # Stabilește overlap: masca aplicațiilor de test cu identitate prezentă în antrenare.
row_loo = cross_val_predict(model(), X, y, cv=LeaveOneOut())  # Stabilește row_loo: predicțiile leave-one-row-out; identitățile pot rămâne în antrenare.
group_loo = cross_val_predict(model(), X, y, cv=LeaveOneGroupOut(), groups=groups)  # Stabilește group_loo: predicțiile cu identitatea complet exclusă din antrenare.
group_train, group_test = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=1137).split(X, y, groups))  # Extrage un holdout cu 20% dintre grupuri, fără identități comune între partiții.
group_holdout = model().fit(X.iloc[group_train], y.iloc[group_train]).predict(X.iloc[group_test])  # Calculează predicțiile estimatorului; rezultatul este păstrat în group_holdout.

correct = int(np.sum(group_loo == y.to_numpy()))  # Stabilește correct: numărul de predicții corecte cu identități separate.
accuracy = accuracy_score(y, group_loo)  # Stabilește accuracy: proporția predicțiilor corecte în evaluarea pe identități.
results = {  # Stabilește results: raportul comparativ al evaluărilor și al suprapunerii identităților.
    "flag": f"SIGMOID_{round(100 * accuracy)}",  # Definește câmpul "flag" al structurii curente.
    "rows": len(df),  # Definește câmpul "rows" al structurii curente.
    "identity_groups": int(groups.nunique()),  # Definește câmpul "identity_groups" al structurii curente.
    "groups_with_repeated_rows": int((groups.value_counts() > 1).sum()),  # Definește câmpul "groups_with_repeated_rows" al structurii curente.
    "reported_accuracy": original,  # Definește câmpul "reported_accuracy" al structurii curente.
    "scaler_fitted_on_training_only": scaler_fixed,  # Definește câmpul "scaler_fitted_on_training_only" al structurii curente.
    "stratified_row_split": stratified,  # Definește câmpul "stratified_row_split" al structurii curente.
    "row_leave_one_out": accuracy_score(y, row_loo),  # Definește câmpul "row_leave_one_out" al structurii curente.
    "corrected_leave_one_identity_out": accuracy,  # Definește câmpul "corrected_leave_one_identity_out" al structurii curente.
    "corrected_predictions": correct,  # Definește câmpul "corrected_predictions" al structurii curente.
    "corrected_total": len(df),  # Definește câmpul "corrected_total" al structurii curente.
    "group_holdout_accuracy": accuracy_score(y.iloc[group_test], group_holdout),  # Definește câmpul "group_holdout_accuracy" al structurii curente.
    "group_holdout_test_rows": len(group_test),  # Definește câmpul "group_holdout_test_rows" al structurii curente.
    "original_test_rows": len(test),  # Definește câmpul "original_test_rows" al structurii curente.
    "original_test_rows_with_identity_in_training": int(overlap.sum()),  # Definește câmpul "original_test_rows_with_identity_in_training" al structurii curente.
    "original_overlap_accuracy": accuracy_score(y.iloc[test].to_numpy()[overlap], train_only_predictions[overlap]),  # Definește câmpul "original_overlap_accuracy" al structurii curente.
    "original_unseen_identity_accuracy": accuracy_score(y.iloc[test].to_numpy()[~overlap], train_only_predictions[~overlap]),  # Definește câmpul "original_unseen_identity_accuracy" al structurii curente.
}  # Închide dicționarul sau mulțimea.
(root / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")  # Scrie textul în fișierul indicat.
print(json.dumps(results, indent=2))  # Afișează valorile sau mesajul pentru verificare.
