"""Recover the injected pointillist letters from the Paris listings."""  # Execută expresia: 'Recover the injected pointillist letters from the Paris listings.'.

from __future__ import annotations  # Importă annotations din __future__

import argparse  # Importă argparse
import hashlib  # Importă hashlib
import json  # Importă json
import urllib.request  # Importă urllib.request
from pathlib import Path  # Importă Path din pathlib

import matplotlib  # Importă matplotlib
import matplotlib.pyplot as plt  # Importă matplotlib.pyplot ca plt
import numpy as np  # Importă numpy ca np
import pandas as pd  # Importă pandas ca pd
from sklearn.cluster import HDBSCAN  # Importă HDBSCAN din sklearn.cluster
from sklearn.decomposition import PCA  # Importă PCA din sklearn.decomposition
from sklearn.preprocessing import StandardScaler  # Importă StandardScaler din sklearn.preprocessing


REFERENCE_URL = (  # Stabilește REFERENCE_URL: adresa snapshotului de referință specificat de soluție.
    "https://data.insideairbnb.com/france/ile-de-france/paris/"  # Definește câmpul "https al structurii curente.
    "2026-09-16/data/listings.csv.gz"  # Completează adresa cu data snapshotului configurat și fișierul comprimat.
)  # Închide apelul sau gruparea.
FEATURES = ["longitude", "latitude", "price", "availability_365"]  # Stabilește FEATURES: cele patru coordonate folosite pentru clustering și proiecție.
READING = "NEURON"  # Stabilește READING: lectura vizuală NEURON introdusă explicit în cod.
ANGLES = [330, 320, 270, 90, 0, 30]  # Stabilește ANGLES: rotațiile manuale de afișare pentru cele șase litere.
FLIP_VERTICAL = [False, False, False, True, False, False]  # Stabilește FLIP_VERTICAL: indicatorii de reflexie verticală pentru afișare.
COLORS = ["#166baf", "#00968b", "#759b22", "#d29216", "#c95052", "#8757b2"]  # Alege câte o culoare de afișare pentru fiecare dintre cele șase grupuri.


def source_matches(data: pd.DataFrame, reference_path: Path) -> np.ndarray:  # Identifică rândurile prezente în referință folosind conținutul, fără ID.
    """Return rows present in the public source, excluding replaced IDs."""  # Execută expresia: 'Return rows present in the public source, excluding replaced IDs.'.
    keys = [column for column in data.columns if column != "listing_id"]  # Stabilește keys: coloanele de comparat, excluzând listing_id.
    source_names = [  # Stabilește source_names: numele echivalente ale coloanelor în referința publică.
        "neighbourhood_cleansed" if column == "neighbourhood" else column  # Traduce numai numele coloanei neighbourhood în schema sursei publice.
        for column in keys  # Clauză de comprehensiune: for column in keys.
    ]  # Închide lista sau indexarea.
    reference = pd.read_csv(reference_path, usecols=source_names, low_memory=False)  # Citește tabelul CSV; rezultatul este păstrat în reference.
    reference = reference.rename(columns={"neighbourhood_cleansed": "neighbourhood"})  # Redenumește coloana cartierului pentru a corespunde schemei interne.
    reference["price"] = pd.to_numeric(  # Convertește prețurile text în numere, după curățarea simbolului monetar și a separatorilor.
        reference["price"].str.replace("$", "", regex=False).str.replace(",", "", regex=False),  # Elimină dolarul și virgulele de mii; acestea nu sunt separatorul zecimal.
        errors="coerce",  # Transformă valorile neconvertibile în NaN în loc să oprească parsarea.
    )  # Închide apelul sau gruparea.
    reference["host_is_superhost"] = reference["host_is_superhost"].map({"t": True, "f": False})  # Convertește indicatorul superhost din t/f în True/False.
    for column in ["latitude", "longitude"]:  # Parcurge ['latitude', 'longitude']; elementul curent este column.
        reference[column] = reference[column].round(5)  # Rotunjește coordonatele la cinci zecimale pentru potrivirea cu tabelul intern.
    for column in ["price", "review_scores_rating", "reviews_per_month"]:  # Parcurge ['price', 'review_scores_rating', 'reviews_per_month']; elementul curent este column.
        reference[column] = reference[column].round(2)  # Rotunjește prețul și scorurile la două zecimale pentru compararea conținutului.
    lookup = reference[keys].drop_duplicates()  # Stabilește lookup: rândurile distincte din referință, pentru asociere many-to-one.
    joined = (  # Stabilește joined: asocierea păstrată în ordinea originală a rândurilor.
        data.reset_index(names="row_index")  # Păstrează indicele original într-o coloană pentru refacerea ordinii după join.
        .merge(lookup, on=keys, how="left", indicator=True, validate="many_to_one")  # Continuă transformarea prin .merge.
        .sort_values("row_index")  # Continuă transformarea prin .sort_values.
    )  # Închide apelul sau gruparea.
    return joined["_merge"].eq("both").to_numpy()  # Întoarce joined['_merge'].eq('both').to_numpy().


def main() -> None:  # Execută fluxul principal al soluției descris în DOCUMENTATION.md.
    parser = argparse.ArgumentParser()  # Pregătește parserul opțiunilor de rulare.
    parser.add_argument("--input", type=Path, default=Path("France/paris_listings.csv"))  # Definește un argument al liniei de comandă.
    parser.add_argument("--reference", type=Path, default=Path("France/insideairbnb.csv.gz"))  # Definește un argument al liniei de comandă.
    parser.add_argument("--output", type=Path, default=Path("France"))  # Definește un argument al liniei de comandă.
    parser.add_argument("--download-reference", action="store_true")  # Definește un argument al liniei de comandă.
    args = parser.parse_args()  # Citește argumentele liniei de comandă; rezultatul este păstrat în args.
    if not args.reference.exists():  # Execută ramura dacă not args.reference.exists().
        if not args.download_reference:  # Execută ramura dacă not args.download_reference.
            parser.error("reference file missing; pass --download-reference")  # Oprește parserul cu instrucțiunea de descărcare a referinței lipsă.
        args.reference.parent.mkdir(parents=True, exist_ok=True)  # Creează directorul de ieșire și părinții ceruți.
        urllib.request.urlretrieve(REFERENCE_URL, args.reference)  # Descarcă referința în fișierul local.

    data = pd.read_csv(args.input)  # Citește tabelul CSV; rezultatul este păstrat în data.
    matched = source_matches(data, args.reference)  # Stabilește matched: masca rândurilor găsite în sursa publică.
    candidate_indices = np.flatnonzero(~matched)  # Stabilește candidate_indices: indicii rândurilor absente din referință.
    candidates = data.iloc[candidate_indices]  # Stabilește candidates: rândurile candidate la desenul injectat.
    scaled = StandardScaler().fit_transform(candidates[FEATURES])  # Stabilește scaled: cele patru caracteristici standardizate.
    raw_labels = HDBSCAN(  # Stabilește raw_labels: grupurile HDBSCAN; −1 marchează zgomotul.
        min_cluster_size=40, min_samples=6, cluster_selection_method="eom"  # Configurează mărimea minimă 40, minimum șase vecini și selecția eom.
    ).fit_predict(scaled)  # Închide apelul sau gruparea. Calculează etichetele clusterelor.
    groups = sorted(  # Stabilește groups: clusterele fără zgomot, ordonate după prețul mediu.
        set(raw_labels) - {-1},  # Elimină eticheta de zgomot −1 dintre clusterele de afișat.
        key=lambda label: candidates.loc[raw_labels == label, "price"].mean(),  # Definește prețul mediu al clusterului drept cheie de ordonare a literelor.
    )  # Închide apelul sau gruparea.
    if len(groups) != len(READING):  # Execută ramura dacă len(groups) != len(READING).
        raise RuntimeError(f"expected six clusters, found {len(groups)}")  # Semnalează eroarea și întrerupe această cale de execuție: RuntimeError(f'expected six clusters, found {len(groups)}').

    labels = data[["listing_id", *FEATURES]].copy()  # Stabilește labels: tabelul cu potrivirea în sursă, cluster și literă.
    labels.insert(0, "row_index", np.arange(len(data)))  # Adaugă poziția originală a fiecărui rând în tabelul de ieșire.
    labels["source_match"] = matched  # Marchează dacă fiecare rând a fost găsit în referință.
    labels["cluster"] = -1  # Inițializează clusterul la −1, pentru rânduri încă neatribuite.
    labels["letter"] = ""  # Inițializează litera goală înainte de atribuirea grupurilor.
    projections = []  # Pregătește lista proiecțiilor PCA și a coordonatelor de afișare.
    summary = []  # Stabilește summary: statisticile fiecărui cluster.
    for order, (raw_label, letter) in enumerate(zip(groups, READING), start=1):  # Parcurge enumerate(zip(groups, READING), start=1); elementul curent este (order, (raw_label, letter)).
        selected = raw_labels == raw_label  # Selectează candidații care aparțin clusterului curent.
        indices = candidate_indices[selected]  # Traduce selecția candidaților în indicii tabelului original.
        rows = data.iloc[indices]  # Extrage rândurile originale ale clusterului pentru proiecție și statistici.
        points = PCA(n_components=2, whiten=True).fit_transform(  # Stabilește points: proiecția PCA în două dimensiuni, cu whitening.
            StandardScaler().fit_transform(rows[FEATURES])  # Standardizează separat grupul curent înainte de proiecția sa PCA.
        )  # Închide apelul sau gruparea.
        theta = np.deg2rad(ANGLES[order - 1])  # Stabilește theta: unghiul de rotație convertit din grade în radiani.
        displayed = points @ np.array(  # Stabilește displayed: coordonatele PCA rotite pentru citirea vizuală.
            [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]  # Construiește matricea bidimensională de rotație cu sinus și cosinus.
        ).T  # Închide apelul sau gruparea. Transpune matricea de rotație.
        if FLIP_VERTICAL[order - 1]:  # Execută ramura dacă FLIP_VERTICAL[order - 1].
            displayed[:, 1] *= -1  # Actualizează displayed[:, 1] folosind -1.
        labels.loc[indices, ["cluster", "letter"]] = [order, letter]  # Salvează numărul clusterului și litera configurată pentru rândurile selectate.
        projections.append((points, displayed, indices))  # Adaugă elementul la sfârșitul colecției.
        summary.append({  # Adaugă elementul la sfârșitul colecției.
            "cluster": order,  # Definește câmpul "cluster" al structurii curente.
            "letter": letter,  # Definește câmpul "letter" al structurii curente.
            "count": len(indices),  # Definește câmpul "count" al structurii curente.
            "mean_price": float(rows["price"].mean()),  # Definește câmpul "mean_price" al structurii curente.
            "mean_availability_365": float(rows["availability_365"].mean()),  # Definește câmpul "mean_availability_365" al structurii curente.
        })  # Închide dicționarul sau mulțimea.

    args.output.mkdir(parents=True, exist_ok=True)  # Creează directorul de ieșire și părinții ceruți.
    fig, axes = plt.subplots(1, 6, figsize=(17, 4.3), layout="constrained")  # Creează o figură cu șase panouri și spațiere automată.
    for i, (ax, (_, displayed, _), record) in enumerate(zip(axes, projections, summary)):  # Parcurge enumerate(zip(axes, projections, summary)); elementul curent este (i, (ax, (_, displayed, _), record)).
        ax.scatter(displayed[:, 0], displayed[:, 1], s=10, color=COLORS[i], alpha=.85, linewidths=0)  # Desenează punctele graficului de dispersie.
        ax.set_aspect("equal")  # Păstrează aceeași scară geometrică pe ambele axe ale literei.
        ax.axis("off")  # Ascunde axele pentru o imagine curată a punctelor.
        ax.set_title(f"{i + 1} · {record['letter']}\n{record['count']} points", pad=15)  # Adaugă titlul graficului.
    fig.suptitle("Point par point — letters ordered by increasing mean price", fontsize=17)  # Adaugă titlul comun cu regula de ordonare după preț.
    fig.savefig(args.output / "pointillist_clusters.png", dpi=180, facecolor="white")  # Salvează figura pe disc.
    plt.close(fig)  # Închide figura și eliberează resursele.
    labels.to_csv(args.output / "labels.csv", index=False)  # Salvează tabelul în CSV.
    result = {  # Construiește raportul cu flag, proveniență, număr de potriviri și statistici ale grupurilor.
        "flag": f"SIGMOID_{READING}",  # Definește câmpul "flag" al structurii curente.
        "reference_url": REFERENCE_URL,  # Definește câmpul "reference_url" al structurii curente.
        "rows": len(data),  # Definește câmpul "rows" al structurii curente.
        "exact_source_matches": int(matched.sum()),  # Definește câmpul "exact_source_matches" al structurii curente.
        "artwork_rows": int(labels["cluster"].gt(0).sum()),  # Definește câmpul "artwork_rows" al structurii curente.
        "clusters": summary,  # Definește câmpul "clusters" al structurii curente.
    }  # Închide dicționarul sau mulțimea.
    (args.output / "results.json").write_text(json.dumps(result, indent=2) + "\n")  # Scrie textul în fișierul indicat.
    print(json.dumps(result, indent=2))  # Afișează valorile sau mesajul pentru verificare.


if __name__ == "__main__":  # Pornește execuția numai când fișierul este rulat direct.
    main()  # Execută fluxul principal al programului.
