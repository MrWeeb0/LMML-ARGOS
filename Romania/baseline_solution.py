"""The workflow you start from.

1. load the training records and the sealed records;
2. fit two usual single models (logistic regression, SVM), one at a time, and look at
   their cross-validation accuracy;
3. predict the sealed records with the best of them;
4. write predictions.csv and ask the evaluator.

    python baseline_solution.py
"""
import subprocess  # Importă subprocess
import sys  # Importă sys
from pathlib import Path  # Importă Path din pathlib

import pandas as pd  # Importă pandas ca pd
from sklearn.linear_model import LogisticRegression  # Importă LogisticRegression din sklearn.linear_model
from sklearn.model_selection import StratifiedKFold, cross_val_score  # Importă StratifiedKFold, cross_val_score din sklearn.model_selection
from sklearn.pipeline import make_pipeline  # Importă make_pipeline din sklearn.pipeline
from sklearn.preprocessing import StandardScaler  # Importă StandardScaler din sklearn.preprocessing
from sklearn.svm import SVC  # Importă SVC din sklearn.svm

HERE = Path(__file__).resolve().parent  # Stabilește HERE: directorul scriptului, pentru căi independente de directorul curent.
CHANNELS = [f"c{j + 1:02d}" for j in range(48)]  # Stabilește CHANNELS: cele 48 de canale c01…c48.

# 1. Load ---------------------------------------------------------------------
train = pd.read_csv(HERE / "dataset" / "train.csv")  # Citește tabelul CSV; rezultatul este păstrat în train.
sealed = pd.read_csv(HERE / "dataset" / "sealed.csv")  # Citește tabelul CSV; rezultatul este păstrat în sealed.
print("train:", train.shape, " sealed:", sealed.shape)  # Afișează valorile sau mesajul pentru verificare.
print(train.head(3).to_string())  # Afișează valorile sau mesajul pentru verificare.

X, y = train[CHANNELS].to_numpy(), train.vrancea.to_numpy()  # Extrage matricea celor 48 de canale și vectorul țintei vrancea.
X_sealed = sealed[CHANNELS].to_numpy()  # Extrage valorile ca tablou NumPy; rezultatul este păstrat în X_sealed.

# 2. Two single models, one at a time ---------------------------------------------
models = {  # Definește cele două modele de referință, fiecare cu propriul scaler în pipeline.
    "logistic regression": make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000)),  # Definește câmpul "logistic regression" al structurii curente.
    "SVM (rbf)": make_pipeline(StandardScaler(), SVC(C=3.0, gamma="scale")),  # Definește câmpul "SVM (rbf)" al structurii curente.
}  # Închide dicționarul sau mulțimea.
cv = StratifiedKFold(5, shuffle=True, random_state=0)  # Configurează cinci folduri stratificate, amestecate cu seed 0.
scores = {}  # Inițializează dicționarul scorurilor medii de validare.
print("\n5-fold cross-validation accuracy on the training records:")  # Afișează valorile sau mesajul pentru verificare.
for name, model in models.items():  # Parcurge models.items(); elementul curent este (name, model).
    scores[name] = cross_val_score(model, X, y, cv=cv).mean()  # Calculează media pe axa indicată; rezultatul este păstrat în scores[name].
    print(f"  {name:20s} {scores[name]:.3f}")  # Afișează valorile sau mesajul pentru verificare.

# 3. Predict the sealed records with the best single model --------------------
best = max(scores, key=scores.get)  # Alege modelul cu media cea mai mare a acurateții pe cele cinci folduri.
print(f"\nbest single model: {best}")  # Afișează valorile sau mesajul pentru verificare.
pred = models[best].fit(X, y).predict(X_sealed)  # Calculează predicțiile estimatorului; rezultatul este păstrat în pred.
out = pd.DataFrame({"record_id": sealed.record_id, "vrancea": pred.astype(int)})  # Asociază predicțiile binare ID-urilor originale ale înregistrărilor sealed.
out.to_csv(HERE / "predictions.csv", index=False)  # Salvează tabelul în CSV.
print("wrote predictions.csv:", out.vrancea.value_counts().to_dict())  # Afișează valorile sau mesajul pentru verificare.

# 4. Ask the evaluator --------------------------------------------------------
print("\nevaluator says:")  # Afișează valorile sau mesajul pentru verificare.
sys.stdout.flush()  # Golește bufferul de ieșire înainte de pornirea evaluatorului extern.
subprocess.run([sys.executable, str(HERE / "evaluation_script.py"), str(HERE / "predictions.csv")], check=False)  # Rulează evaluatorul cu același interpretor; baseline-ul nu ridică eroare dacă procesul întoarce un cod nenul.
