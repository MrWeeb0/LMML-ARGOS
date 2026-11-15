#!/usr/bin/env python3
"""Modelarea lungimii marginii parcelelor (edge_m) din declarațiile fermierilor
pentru taskul BELGIA — Fry-ndship (Sigmoid Academy).
"""
import numpy as np  # Importă numpy ca np
import pandas as pd  # Importă pandas ca pd
import matplotlib.pyplot as plt  # Importă matplotlib.pyplot ca plt


def main():  # Execută fluxul principal al soluției descris în DOCUMENTATION.md.
    df = pd.read_csv("potato_fields.csv")  # Citește tabelul CSV; rezultatul este păstrat în df.

    # Dimensiuni derivate exclusiv din declarațiile fermierului (fără coloane măsurate la fața locului / data leakage)
    area_m2 = df["area_ha"] * 10000.0  # Stabilește area_m2: suprafața convertită din hectare în metri pătrați.
    short_side_m = area_m2 / df["long_side_m"]  # Stabilește short_side_m: latura scurtă dedusă din suprafață / latura lungă.

    X = np.column_stack([  # Stabilește X: matricea OLS: intercept, latura lungă, latura scurtă, șanț.
        np.ones(len(df)),  # Adaugă coloana constantă unu, al cărei coeficient va fi interceptul.
        df["long_side_m"].values,  # Adaugă latura lungă declarată de fermier ca predictor.
        short_side_m.values,  # Adaugă latura scurtă calculată geometric, fără măsurători ulterioare.
        df["ditch_m"].values,  # Adaugă lungimea șanțului declarat ca al treilea predictor.
    ])  # Închide lista sau indexarea.
    y = df["edge_m"].values  # Stabilește y: lungimile edge_m măsurate, ținta regresiei.

    # Ajustare regresie liniară (OLS)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)  # Rezolvă sistemul prin metoda celor mai mici pătrate; rezultatul este păstrat în (beta, *_).
    y_pred = X @ beta  # Stabilește y_pred: lungimile prezise prin produsul matrice–coeficienți.
    residuals = y - y_pred  # Stabilește residuals: diferențele măsurat minus prezis, care formează desenul.

    r2 = 1.0 - np.sum(residuals ** 2) / np.sum((y - y.mean()) ** 2)  # Stabilește r2: proporția variației țintei explicată de model.
    print(f"R^2 = {r2:.6f}, RMSE = {np.sqrt(np.mean(residuals ** 2)):.4f} m")  # Afișează valorile sau mesajul pentru verificare.
    for name, coef in zip(["intercept", "long_side_m", "short_side_m", "ditch_m"], beta):  # Parcurge zip(['intercept', 'long_side_m', 'short_side_m', 'ditch_m'], beta); elementul curent este (name, coef).
        print(f"  {name:14s}: {coef:.6f}")  # Afișează valorile sau mesajul pentru verificare.

    # Vizualizare reziduuri vs. lungimea prezisă
    plt.figure(figsize=(13, 4.5))  # Creează figura largă pentru citirea literelor din reziduuri.
    plt.scatter(y_pred, residuals, s=5, alpha=0.65, color="#1f77b4")  # Desenează punctele graficului de dispersie.
    plt.axhline(0, color="#666666", linestyle="--", linewidth=0.8)  # Desenează linia de eroare zero ca reper vizual.
    plt.xlabel("Lungimea marginii prezisă (edge_m prezis, m)")  # Etichetează abscisa cu lungimea prezisă, în metri.
    plt.ylabel("Reziduu (edge_m - prezis, m)")  # Etichetează ordonata cu diferența real minus prezis.
    plt.title("Belgia (Fry-ndship): Reziduurile modelului din declarațiile fermierilor")  # Adaugă titlul graficului de reziduuri.
    plt.tight_layout()  # Ajustează spațierea figurii.
    plt.savefig("belgia_residuals.png", dpi=180)  # Salvează figura pe disc.
    plt.show()  # Afișează interactiv figura; pe un server se poate folosi backendul Agg.


if __name__ == "__main__":  # Pornește execuția numai când fișierul este rulat direct.
    main()  # Execută fluxul principal al programului.
