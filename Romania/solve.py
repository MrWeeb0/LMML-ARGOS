"""Validate, fit the routed detector, and run the unmodified challenge evaluator.

From the repository root: .venv/bin/python Romania/solve.py
Add --compare to reproduce the slower single-model comparisons.
"""
import argparse  # Importă argparse
import json  # Importă json
from pathlib import Path  # Importă Path din pathlib

import numpy as np  # Importă numpy ca np
import pandas as pd  # Importă pandas ca pd
from sklearn.ensemble import HistGradientBoostingClassifier  # Importă HistGradientBoostingClassifier din sklearn.ensemble
from sklearn.linear_model import LogisticRegression  # Importă LogisticRegression din sklearn.linear_model
from sklearn.metrics import accuracy_score  # Importă accuracy_score din sklearn.metrics
from sklearn.mixture import GaussianMixture  # Importă GaussianMixture din sklearn.mixture
from sklearn.model_selection import train_test_split  # Importă train_test_split din sklearn.model_selection
from sklearn.pipeline import make_pipeline  # Importă make_pipeline din sklearn.pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler  # Importă PolynomialFeatures, StandardScaler din sklearn.preprocessing
from sklearn.svm import SVC  # Importă SVC din sklearn.svm
from sklearn.tree import DecisionTreeClassifier  # Importă DecisionTreeClassifier din sklearn.tree
from threadpoolctl import threadpool_limits  # Importă threadpool_limits din threadpoolctl

from evaluation_script import flag_for, load_predictions  # Importă flag_for, load_predictions din evaluation_script

HERE = Path(__file__).resolve().parent  # Stabilește HERE: directorul scriptului, pentru căi independente de directorul curent.
CHANNELS = [f"c{i:02d}" for i in range(1, 49)]  # Stabilește CHANNELS: cele 48 de canale c01…c48.
PARITY_CHANNELS = ["c35", "c38", "c43"]  # Stabilește PARITY_CHANNELS: cele trei canale ale arborelui pentru semnalul de paritate.
GATE_CHANNELS = ["c13", *PARITY_CHANNELS]  # Stabilește GATE_CHANNELS: c13 și cele trei canale folosite pentru învățarea porții.


class RoutedDetector:  # Definește clasa RoutedDetector, care păstrează starea și metodele algoritmului.
    def fit(self, x, y):  # Învață rutarea și cele trei modele numai din datele primite.
        self.scaler = StandardScaler().fit(x)  # Stabilește self.scaler: standardizarea învățată exclusiv din datele primite la fit.
        z = self.scaler.transform(x)  # Aplică transformarea deja învățată; rezultatul este păstrat în z.
        self.router = GaussianMixture(  # Stabilește self.router: amestecul Gaussian cu două componente și covarianțe diagonale.
            2, covariance_type="diag", random_state=0  # Alege două componente GMM, covarianțe diagonale și seed 0.
        ).fit(z)  # Închide apelul sau gruparea. Antrenează estimatorul pe subsetul indicat.
        groups = self.router.predict(z)  # Calculează predicțiile estimatorului; rezultatul este păstrat în groups.
        self.low = int(np.argmin(self.router.covariances_.sum(axis=1)))  # Stabilește self.low: componenta cu suma varianțelor cea mai mică.
        low_mask = groups == self.low  # Stabilește low_mask: masca înregistrărilor din componenta cu varianță mică.
        # The 12 channels whose variance stays near one carry the radial signal.
        self.radial_channels = list(x.columns[self.router.covariances_[self.low] > 0.5])  # Stabilește self.radial_channels: canalele cu varianță standardizată > 0,5 în componenta mică.
        self.radial = make_pipeline(  # Stabilește self.radial: clasificatorul logistic pe caracteristici polinomiale de gradul doi.
            StandardScaler(), PolynomialFeatures(2), StandardScaler(),  # Standardizează, generează termeni de gradul doi, apoi standardizează din nou pentru regresie.
            LogisticRegression(C=1, max_iter=3000),  # Configurează regresia logistică radială, C=1 și maximum 3000 de iterații.
        ).fit(x.loc[low_mask, self.radial_channels], y[low_mask])  # Închide apelul sau gruparea. Antrenează estimatorul pe subsetul indicat.

        # A shallow exploratory tree consistently splits the other records on c13.
        gate_tree = DecisionTreeClassifier(  # Stabilește gate_tree: arborele explorator pentru pragul de separare pe c13.
            max_depth=4, min_samples_leaf=60, random_state=0  # Limitează arborele explorator la adâncime patru și minimum 60 de exemple pe frunză.
        ).fit(x.loc[~low_mask, GATE_CHANNELS], y[~low_mask])  # Închide apelul sau gruparea. Antrenează estimatorul pe subsetul indicat.
        thresholds = gate_tree.tree_.threshold[gate_tree.tree_.feature == 0]  # Stabilește thresholds: pragurile arborelui care folosesc prima caracteristică, c13.
        if not len(thresholds):  # Execută ramura dacă not len(thresholds).
            raise RuntimeError("Could not learn the c13 routing threshold")  # Semnalează eroarea și întrerupe această cale de execuție: RuntimeError('Could not learn the c13 routing threshold').
        self.gate = float(np.median(thresholds))  # Stabilește self.gate: mediana pragurilor învățate pe c13.
        linear_mask = (~low_mask) & (x.c13.to_numpy() > self.gate)  # Stabilește linear_mask: înregistrările din afara grupei mici cu c13 peste poartă.
        parity_mask = (~low_mask) & ~linear_mask  # Stabilește parity_mask: înregistrările rămase pentru arborele de paritate.
        self.linear = LogisticRegression(C=10, max_iter=3000).fit(  # Stabilește self.linear: regresia logistică pentru ruta liniară.
            z[linear_mask], y[linear_mask]  # Antrenează regresia liniară numai pe rândurile rutate deasupra pragului c13.
        )  # Închide apelul sau gruparea.
        self.parity = DecisionTreeClassifier(  # Stabilește self.parity: arborele de adâncime trei pentru ruta de paritate.
            max_depth=3, min_samples_leaf=30, random_state=0  # Limitează arborele de paritate la adâncime trei și minimum 30 de exemple pe frunză.
        ).fit(x.loc[parity_mask, PARITY_CHANNELS], y[parity_mask])  # Închide apelul sau gruparea. Antrenează estimatorul pe subsetul indicat.
        self.training_counts = {  # Stabilește self.training_counts: numărul înregistrărilor repartizate fiecărei rute.
            "quadratic": int(low_mask.sum()),  # Definește câmpul "quadratic" al structurii curente.
            "linear": int(linear_mask.sum()),  # Definește câmpul "linear" al structurii curente.
            "parity_tree": int(parity_mask.sum()),  # Definește câmpul "parity_tree" al structurii curente.
        }  # Închide dicționarul sau mulțimea.
        return self  # Întoarce self.

    def predict_with_routes(self, x):  # Aplică modelele învățate și returnează predicția și ruta fiecărui rând.
        z = self.scaler.transform(x)  # Aplică transformarea deja învățată; rezultatul este păstrat în z.
        low_mask = self.router.predict(z) == self.low  # Stabilește low_mask: masca înregistrărilor din componenta cu varianță mică.
        linear_mask = (~low_mask) & (x.c13.to_numpy() > self.gate)  # Stabilește linear_mask: înregistrările din afara grupei mici cu c13 peste poartă.
        pred = self.parity.predict(x[PARITY_CHANNELS]).astype(int)  # Pornește cu predicțiile arborelui pentru toate rândurile; rutele speciale le vor înlocui.
        pred[linear_mask] = self.linear.predict(z[linear_mask])  # Calculează predicțiile estimatorului; rezultatul este păstrat în pred[linear_mask].
        pred[low_mask] = self.radial.predict(x.loc[low_mask, self.radial_channels])  # Calculează predicțiile estimatorului; rezultatul este păstrat în pred[low_mask].
        routes = np.full(len(x), "parity_tree", dtype=object)  # Stabilește routes: numele rutei alese pentru fiecare predicție.
        routes[linear_mask] = "linear"  # Etichetează explicit rândurile trimise clasificatorului liniar.
        routes[low_mask] = "quadratic"  # Etichetează explicit rândurile trimise clasificatorului pătratic.
        return pred, routes  # Întoarce (pred, routes).


def main():  # Execută fluxul principal al soluției descris în DOCUMENTATION.md.
    parser = argparse.ArgumentParser(description=__doc__)  # Pregătește opțiunile programului, folosind docstring-ul ca descriere.
    parser.add_argument("--compare", action="store_true")  # Definește un argument al liniei de comandă.
    args = parser.parse_args()  # Citește argumentele liniei de comandă; rezultatul este păstrat în args.
    train = pd.read_csv(HERE / "dataset/train.csv")  # Citește tabelul CSV; rezultatul este păstrat în train.
    sealed = pd.read_csv(HERE / "dataset/sealed.csv")  # Citește tabelul CSV; rezultatul este păstrat în sealed.
    x, y = train[CHANNELS], train.vrancea.to_numpy()  # Extrage cele 48 de caracteristici și etichetele vrancea din antrenare.
    ti, vi = train_test_split(  # Împarte indicii în 75% antrenare și 25% validare stratificată, seed 42.
        np.arange(len(x)), test_size=0.25, random_state=42, stratify=y  # Folosește indicii tuturor rândurilor, 25% holdout și stratificare după etichetă.
    )  # Închide apelul sau gruparea.
    report = {"validation": {"method": "stratified holdout", "seed": 42,  # Stabilește report: raportul scorurilor și al parametrilor învățați.
                             "training_records": len(ti), "validation_records": len(vi)},  # Definește câmpul "training_records" al structurii curente.
              "models": {}}  # Definește câmpul "models" al structurii curente.
    if args.compare:  # Execută ramura dacă args.compare.
        from catboost import CatBoostClassifier  # Importă CatBoostClassifier din catboost
        models = {  # Configurează modelele globale de comparație, fără a schimba detectorul final.
            "logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),  # Definește câmpul "logistic_regression" al structurii curente.
            "rbf_svm": make_pipeline(StandardScaler(), SVC(C=3)),  # Definește câmpul "rbf_svm" al structurii curente.
            "hist_gradient_boosting": HistGradientBoostingClassifier(  # Definește câmpul "hist_gradient_boosting" al structurii curente.
                max_iter=900, max_leaf_nodes=63, learning_rate=.05,  # Configurează boostingul de comparație cu 900 de iterații, 63 de frunze și pas 0,05.
                l2_regularization=1, min_samples_leaf=10, random_state=1),  # Adaugă regularizare L2, minimum zece exemple pe frunză și seed 1.
            "catboost": CatBoostClassifier(  # Definește câmpul "catboost" al structurii curente.
                iterations=1800, depth=6, learning_rate=.04, verbose=False,  # Configurează CatBoost cu 1800 de iterații, adâncime șase și pas 0,04.
                thread_count=4, allow_writing_files=False),  # Limitează CatBoost la patru fire și dezactivează fișierele auxiliare de antrenare.
        }  # Închide dicționarul sau mulțimea.
        for name, model in models.items():  # Parcurge models.items(); elementul curent este (name, model).
            model.fit(x.iloc[ti], y[ti])  # Antrenează estimatorul pe datele indicate.
            score = float(accuracy_score(y[vi], model.predict(x.iloc[vi])))  # Calculează acuratețea modelului de comparație pe holdout.
            report["models"][name] = score  # Salvează acuratețea modelului de comparație în raport.
            print(f"{name}: {score:.6%}", flush=True)  # Afișează valorile sau mesajul pentru verificare.
    model = RoutedDetector().fit(x.iloc[ti], y[ti])  # Antrenează estimatorul pe datele indicate; rezultatul este păstrat în model.
    pred, routes = model.predict_with_routes(x.iloc[vi])  # Obține predicțiile detectorului și ruta aleasă pentru fiecare rând de validare.
    score = float(accuracy_score(y[vi], pred))  # Calculează acuratețea agregată a detectorului pe holdout.
    report["models"]["routed_detector"] = score  # Înregistrează acuratețea detectorului final în raport.
    report["route_validation"] = {  # Construiește numărul rândurilor și acuratețea separat pentru fiecare rută.
        route: {"records": int((routes == route).sum()),  # Numără exemplele rutei curente pentru raportul de validare.
                "accuracy": float(accuracy_score(y[vi][routes == route], pred[routes == route]))}  # Definește câmpul "accuracy" al structurii curente.
        for route in np.unique(routes)  # Clauză de comprehensiune: for route in np.unique(routes).
    }  # Închide dicționarul sau mulțimea.
    print(f"routed_detector: {score:.6%}", flush=True)  # Afișează valorile sau mesajul pentru verificare.
    pd.DataFrame({"record_id": train.record_id.iloc[vi].to_numpy(),  # Salvează tabelul în CSV.
                  "actual": y[vi], "predicted": pred, "route": routes}).to_csv(  # Definește câmpul "actual" al structurii curente.
        HERE / "validation_predictions.csv", index=False)  # Salvează predicțiile de validare fără coloană suplimentară de index.

    model.fit(x, y)  # Antrenează estimatorul pe datele indicate.
    pred, _ = model.predict_with_routes(sealed[CHANNELS])  # Prezice înregistrările sealed cu modelul reantrenat pe întregul set etichetat.
    output = HERE / "predictions.csv"  # Stabilește fișierul final de predicții, lângă script.
    pd.DataFrame({"record_id": sealed.record_id, "vrancea": pred}).to_csv(output, index=False)  # Salvează tabelul în CSV.
    # Reload through the official ID alignment and validation code.
    word = flag_for(load_predictions(output))  # Reîncarcă și aliniază CSV-ul prin codul oficial, apoi cere cuvântul evaluatorului.
    report["full_fit"] = {"gate_threshold": model.gate,  # Înregistrează poarta, canalele radiale și numărul de exemple pe rute după ajustarea completă.
                          "radial_channels": model.radial_channels,  # Definește câmpul "radial_channels" al structurii curente.
                          "training_counts": model.training_counts}  # Definește câmpul "training_counts" al structurii curente.
    report["evaluator_result"] = f"SIGMOID_{word}" if word else None  # Salvează flagul acceptat sau None dacă evaluatorul nu a deblocat cuvântul.
    (HERE / "validation_results.json").write_text(json.dumps(report, indent=2) + "\n")  # Scrie textul în fișierul indicat.
    if not word:  # Execută ramura dacă not word.
        raise SystemExit("The original evaluator did not accept these predictions.")  # Semnalează eroarea și întrerupe această cale de execuție: SystemExit('The original evaluator did not accept these predictions.').
    print(f"SIGMOID_{word}", flush=True)  # Afișează valorile sau mesajul pentru verificare.


if __name__ == "__main__":  # Pornește execuția numai când fișierul este rulat direct.
    with threadpool_limits(limits=4):  # Gestionează automat contextul: threadpool_limits(limits=4).
        main()  # Execută fluxul principal al programului.
