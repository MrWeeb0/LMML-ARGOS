#!/usr/bin/env python3
"""Modelarea lungimii marginii parcelelor (edge_m) din declarațiile fermierilor
pentru taskul BELGIA — Fry-ndship (Sigmoid Academy).
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def main():
    df = pd.read_csv("potato_fields.csv")

    # Dimensiuni derivate exclusiv din declarațiile fermierului (fără coloane măsurate la fața locului / data leakage)
    area_m2 = df["area_ha"] * 10000.0
    short_side_m = area_m2 / df["long_side_m"]

    X = np.column_stack([
        np.ones(len(df)),
        df["long_side_m"].values,
        short_side_m.values,
        df["ditch_m"].values,
    ])
    y = df["edge_m"].values

    # Ajustare regresie liniară (OLS)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    y_pred = X @ beta
    residuals = y - y_pred

    r2 = 1.0 - np.sum(residuals ** 2) / np.sum((y - y.mean()) ** 2)
    print(f"R^2 = {r2:.6f}, RMSE = {np.sqrt(np.mean(residuals ** 2)):.4f} m")
    for name, coef in zip(["intercept", "long_side_m", "short_side_m", "ditch_m"], beta):
        print(f"  {name:14s}: {coef:.6f}")

    # Vizualizare reziduuri vs. lungimea prezisă
    plt.figure(figsize=(13, 4.5))
    plt.scatter(y_pred, residuals, s=5, alpha=0.65, color="#1f77b4")
    plt.axhline(0, color="#666666", linestyle="--", linewidth=0.8)
    plt.xlabel("Lungimea marginii prezisă (edge_m prezis, m)")
    plt.ylabel("Reziduu (edge_m - prezis, m)")
    plt.title("Belgia (Fry-ndship): Reziduurile modelului din declarațiile fermierilor")
    plt.tight_layout()
    plt.savefig("belgia_residuals.png", dpi=180)
    plt.show()


if __name__ == "__main__":
    main()