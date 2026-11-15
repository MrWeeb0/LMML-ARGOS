"""
e-Residency application fraud screen -- evaluation pipeline.
"""

import pandas as pd  # Importă pandas ca pd
from sklearn.metrics import accuracy_score  # Importă accuracy_score din sklearn.metrics
from sklearn.model_selection import train_test_split  # Importă train_test_split din sklearn.model_selection
from sklearn.neighbors import KNeighborsClassifier  # Importă KNeighborsClassifier din sklearn.neighbors
from sklearn.preprocessing import StandardScaler  # Importă StandardScaler din sklearn.preprocessing

df = pd.read_csv("applications.csv")  # Citește tabelul CSV; rezultatul este păstrat în df.

# Identity fields are personal data and are never used for modeling.
X = df.drop(columns=["submission_id", "date_of_birth", "citizenship", "label"])  # Stabilește X: cele șase semnale numerice, fără identificatori și etichetă.
y = df["label"]  # Stabilește y: etichetele reale de fraudă.

# Features are on very different scales (seconds, km, days, 0-1 scores).
X_scaled = StandardScaler().fit_transform(X)  # Învață transformarea și o aplică datelor indicate; rezultatul este păstrat în X_scaled.

X_train, X_test, y_train, y_test = train_test_split(  # Separă rândurile deja standardizate în antrenare/test; scalerul a văzut inclusiv testul.
    X_scaled, y, test_size=0.2, random_state=1137  # Folosește 20% pentru test și seed 1137 pentru reproducerea împărțirii inițiale.
)  # Închide apelul sau gruparea.

clf = KNeighborsClassifier(n_neighbors=1)  # Alege clasificatorul cu un singur vecin, pentru reproducerea pipeline-ului inițial.
clf.fit(X_train, y_train)  # Antrenează estimatorul pe datele indicate.

acc = accuracy_score(y_test, clf.predict(X_test))  # Compară predicțiile 1-NN cu etichetele de test și calculează proporția corectă.
print(f"Test accuracy: {acc:.4f}")  # Afișează valorile sau mesajul pentru verificare.
