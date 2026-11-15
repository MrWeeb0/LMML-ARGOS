#!/usr/bin/env python3
"""Streaming anomaly detector for ALBANIA — Arată a anomalie! (Sigmoid Academy)."""  # Execută expresia: 'Streaming anomaly detector for ALBANIA — Arată a anomalie! (Sigmoid Academy).'.
from __future__ import annotations  # Importă annotations din __future__

import math  # Importă math
from collections import defaultdict, deque  # Importă defaultdict, deque din collections

import numpy as np  # Importă numpy ca np

SENSORS = (  # Stabilește SENSORS: cele șase canale fizice, în ordinea vectorului de intrare.
    "temperature_c",  # Temperatura în grade Celsius.
    "humidity_pct",  # Umiditatea relativă, exprimată procentual.
    "vibration_g",  # Vibrația măsurată în unități g.
    "acoustic_db",  # Nivelul acustic în decibeli.
    "air_pressure_kpa",  # Presiunea aerului în kilopascali.
    "co2_ppm",  # Concentrația de CO₂ în părți per milion.
)  # Închide apelul sau gruparea.


class Detector:  # Definește clasa Detector, care păstrează starea și metodele algoritmului.
    def __init__(self) -> None:  # Inițializează starea detectorului separat pentru fiecare zonă.
        self.hist: dict[str, deque[np.ndarray]] = defaultdict(lambda: deque(maxlen=360))  # Alocă pentru fiecare zonă o coadă care păstrează maximum 360 de citiri acceptate.
        self.recent_z: dict[str, deque[np.ndarray]] = defaultdict(lambda: deque(maxlen=6))  # Alocă pentru fiecare zonă o coadă cu ultimele șase deviații absolute standardizate.
        self.cached_stats: dict[str, tuple[np.ndarray, np.ndarray]] = {}  # Stabilește self.cached_stats: mediana și scara memorate pentru fiecare zonă.
        self.steps: dict[str, int] = defaultdict(int)  # Stabilește self.steps: numărul de actualizări pe zonă.

    def _get_stats(self, zone: str) -> tuple[np.ndarray, np.ndarray]:  # Estimează centrul și dispersia robustă din istoricul acceptat.
        arr = np.array(self.hist[zone], dtype=np.float64)  # Construiește un tablou NumPy; rezultatul este păstrat în arr.
        med = np.median(arr, axis=0)  # Stabilește med: mediana pe fiecare senzor.
        mad = np.median(np.abs(arr - med), axis=0) * 1.4826  # Stabilește mad: MAD scalat cu 1,4826, estimator robust al dispersiei.
        std = np.std(arr, axis=0)  # Stabilește std: deviația standard pe fiecare senzor.
        sd = np.maximum(np.maximum(mad, std * 0.75), 1e-4)  # Stabilește sd: maximul dintre MAD, 0,75 × std și 0,0001; evită împărțirea la zero.
        return med, sd  # Întoarce (med, sd).

    def update(self, reading: dict) -> float:  # Primește o citire și întoarce un scor de anomalie fără acces la viitor.
        zone = str(reading.get("bunker_zone", "default"))  # Stabilește zone: zona citirii; implicit default.
        vals = []  # Pregătește lista valorilor senzorilor în ordinea SENSORS.
        for s in SENSORS:  # Parcurge SENSORS; elementul curent este s.
            v = reading.get(s)  # Citește senzorul curent; absența cheii produce None.
            if v is None or (isinstance(v, float) and math.isnan(v)):  # Execută ramura dacă v is None or (isinstance(v, float) and math.isnan(v)).
                vals.append(float("nan"))  # Adaugă elementul la sfârșitul colecției.
            else:  # Traitează cazul în care condiția precedentă este falsă.
                vals.append(float(v))  # Adaugă elementul la sfârșitul colecției.
        x = np.array(vals, dtype=np.float64)  # Stabilește x: vectorul numeric al celor șase senzori.

        self.steps[zone] += 1  # Actualizează self.steps[zone] folosind 1.

        # Handle NaNs safely if any sensor reading is missing
        if np.isnan(x).any():  # Execută ramura dacă np.isnan(x).any().
            if zone in self.cached_stats:  # Execută ramura dacă zone in self.cached_stats.
                med, _ = self.cached_stats[zone]  # Recuperează mediana memorată; ignoră scara în această ramură.
                x = np.where(np.isnan(x), med, x)  # Înlocuiește numai componentele NaN cu mediana corespunzătoare senzorului.
            else:  # Traitează cazul în care condiția precedentă este falsă.
                x = np.where(np.isnan(x), 0.0, x)  # Fără mediană disponibilă, înlocuiește componentele NaN cu zero.

        if len(self.hist[zone]) < 20:  # Execută ramura dacă len(self.hist[zone]) < 20.
            self.hist[zone].append(x)  # Adaugă citirea în istoricul de încălzire al zonei.
            return 0.0  # Nu raportează anomalie în primele 20 de citiri ale zonei.

        if zone not in self.cached_stats or self.steps[zone] % 10 == 0:  # Execută ramura dacă zone not in self.cached_stats or self.steps[zone] % 10 == 0.
            self.cached_stats[zone] = self._get_stats(zone)  # Recalculează și memorează statisticile zonei din istoricul acceptat.
        med, sd = self.cached_stats[zone]  # Separă mediana și scara memorate pentru scorarea citirii curente.

        z = np.abs(x - med) / sd  # Stabilește z: deviațiile absolute față de mediană, împărțite la scara fiecărui senzor.
        max_z = float(np.max(z))  # Stabilește max_z: cea mai mare deviație individuală.
        l2_z = float(np.sqrt(np.sum(np.minimum(z, 8.0) ** 2)))  # Stabilește l2_z: norma L2 a deviațiilor limitate la 8.

        self.recent_z[zone].append(z)  # Adaugă elementul la sfârșitul colecției.
        rz = np.mean(self.recent_z[zone], axis=0)  # Stabilește rz: media ultimelor șase vectori z, pentru persistență.
        max_rz = float(np.max(rz))  # Stabilește max_rz: cea mai mare deviație medie recentă.
        l2_rz = float(np.sqrt(np.sum(np.minimum(rz, 8.0) ** 2)))  # Stabilește l2_rz: norma L2 a deviațiilor medii limitate la 8.

        # 1. Point anomaly (sudden isolated spike)
        s_point = max(0.0, (max_z - 3.6) / 2.8)  # Stabilește s_point: scorul pentru vârfuri izolate: (max_z − 3,6) / 2,8, minimum zero.
        # 2. Instantaneous multi-sensor shift
        s_coll = max(0.0, (l2_z - 4.3) / 3.0)  # Stabilește s_coll: scorul colectiv instantaneu: (l2_z − 4,3) / 3, minimum zero.
        # 3. Gradual drift or persistent collective anomaly
        if max_z >= 2.2 or l2_z >= 3.3:  # Execută ramura dacă max_z >= 2.2 or l2_z >= 3.3.
            s_drift = max((max_rz - 2.3) / 1.8, (l2_rz - 3.3) / 2.2)  # Stabilește s_drift: scorul de persistență, activat doar de o deviație curentă suficientă.
        else:  # Traitează cazul în care condiția precedentă este falsă.
            s_drift = 0.0  # Stabilește s_drift: scorul de persistență, activat doar de o deviație curentă suficientă.

        score = float(np.clip(max(s_point, s_coll, s_drift), 0.0, 1.0))  # Stabilește score: maximul celor trei scoruri, limitat la [0, 1].

        # Update normal history only with non-anomalous points so drifts cannot poison baseline
        if score < 0.42:  # Execută ramura dacă score < 0.42.
            self.hist[zone].append(x)  # Adaugă elementul la sfârșitul colecției.

        return score  # Întoarce score.
