"""Check a set of predictions for the sealed records.

    python evaluation_script.py predictions.csv

predictions.csv must have the columns  record_id, vrancea  with one row per sealed record
(dataset/sealed.csv) and vrancea in {0, 1}.

The flag is printed when the predictions are good enough. Nothing else is printed: no score,
no count.

Standard library + numpy + pandas.
"""
import hashlib  # Importă hashlib
import sys  # Importă sys
from pathlib import Path  # Importă Path din pathlib

import numpy as np  # Importă numpy ca np
import pandas as pd  # Importă pandas ca pd

HERE = Path(__file__).resolve().parent  # Stabilește HERE: directorul scriptului, pentru căi independente de directorul curent.


# ----------------------------------------------------------------------------- arithmetic mod p
def _trim(a):  # Elimină coeficienții nuli de grad maxim ai polinomului.
    nz = np.flatnonzero(a)  # Găsește pozițiile coeficienților nenuli pentru eliminarea zerourilor de grad maxim.
    return a[: nz[-1] + 1] if len(nz) else a[:0]  # Întoarce a[:nz[-1] + 1] if len(nz) else a[:0].


def _divmod(a, b, p):  # Împarte polinoame modulo p și returnează câtul și restul.
    """Polynomial division mod p; coefficients little-endian (index = power)."""  # Execută expresia: 'Polynomial division mod p; coefficients little-endian (index = power).'.
    a = a.copy()  # Copiază deîmpărțitul pentru ca reducerea să nu modifice vectorul apelantului.
    db = len(b) - 1  # Determină gradul împărțitorului din numărul coeficienților săi.
    inv = pow(int(b[-1]), p - 2, p)  # Stabilește inv: inversele modulare precalculate în câmpul prim.
    q = np.zeros(max(len(a) - db, 1), dtype=np.int64)  # Inițializează un tablou cu zerouri; rezultatul este păstrat în q.
    for i in range(len(a) - 1 - db, -1, -1):  # Parcurge range(len(a) - 1 - db, -1, -1); elementul curent este i.
        c = int(a[i + db]) * inv % p  # Calculează coeficientul câtului pentru gradul curent, folosind inversul modular al coeficientului dominant.
        if c:  # Execută ramura dacă c.
            q[i] = c  # Salvează coeficientul câtului la puterea curentă.
            a[i:i + db + 1] = (a[i:i + db + 1] - c * b) % p  # Scade multiplul împărțitorului și reduce modulo p pentru anularea termenului dominant.
    return _trim(q), _trim(a[:db]) if db else a[:0]  # Întoarce (_trim(q), _trim(a[:db]) if db else a[:0]).


def _mul(a, b, p):  # Înmulțește două polinoame modulo p.
    if len(a) == 0 or len(b) == 0:  # Execută ramura dacă len(a) == 0 or len(b) == 0.
        return a[:0]  # Întoarce a[:0].
    if len(a) < len(b):  # Execută ramura dacă len(a) < len(b).
        a, b = b, a  # Pune polinomul mai lung în a, reducând numărul iterațiilor buclei pe b.
    out = np.zeros(len(a) + len(b) - 1, dtype=np.int64)  # Inițializează un tablou cu zerouri; rezultatul este păstrat în out.
    for i, c in enumerate(b):  # Parcurge enumerate(b); elementul curent este (i, c).
        if c:  # Execută ramura dacă c.
            out[i:i + len(a)] = (out[i:i + len(a)] + int(c) * a) % p  # Acumulează produsul termenului curent cu întregul polinom a, modulo p.
    return out  # Întoarce out.


def _sub(a, b, p):  # Scade două polinoame modulo p.
    out = np.zeros(max(len(a), len(b)), dtype=np.int64)  # Inițializează un tablou cu zerouri; rezultatul este păstrat în out.
    out[:len(a)] = a  # Copiază coeficienții primului polinom în rezultatul extins cu zerouri.
    out[:len(b)] = (out[:len(b)] - b) % p  # Scade al doilea polinom din coeficienții de același grad, modulo p.
    return _trim(out)  # Întoarce _trim(out).


def _interpolate(x, y, p, inv):  # Interpolează polinomul și construiește produsul factorilor X − x_i.
    """Coefficients of the polynomial of degree < len(x) through the points (x, y), and of prod(X - x_i)."""  # Execută expresia: 'Coefficients of the polynomial of degree < len(x) through the points (x, y), and of prod(X - x_i).'.
    m = len(x)  # Determină numărul punctelor de interpolare.
    c = y.astype(np.int64).copy()  # Copiază ordonatele ca întregi pentru calculul diferențelor divizate Newton.
    for j in range(1, m):                      # Newton divided differences
        d = x[j:] - x[:-j]  # Calculează diferențele dintre abscisele aflate la distanța j în șir.
        dinv = np.where(d > 0, inv[np.abs(d)], (p - inv[np.abs(d)]) % p)  # Alege inversele modulare ale diferențelor, ținând cont de semnul acestora.
        c[j:] = (c[j:] - c[j - 1:-1]) % p * dinv % p  # Actualizează diferențele divizate Newton în câmpul modulo p.
    poly = np.zeros(m, dtype=np.int64)         # Newton form -> ordinary coefficients (Horner)
    poly[0] = c[m - 1]  # Inițializează conversia Horner cu ultima diferență divizată.
    for i in range(m - 2, -1, -1):  # Parcurge range(m - 2, -1, -1); elementul curent este i.
        deg = m - 1 - i  # Determină gradul polinomului intermediar în conversia din forma Newton.
        nxt = np.zeros(m, dtype=np.int64)  # Inițializează un tablou cu zerouri; rezultatul este păstrat în nxt.
        nxt[1:deg + 1] = poly[:deg]  # Deplasează coeficienții cu o poziție, adică înmulțește polinomul cu X.
        nxt[:deg] = (nxt[:deg] - int(x[i]) * poly[:deg]) % p  # Scade x_i ori polinomul vechi pentru înmulțirea cu factorul X−x_i.
        nxt[0] = (nxt[0] + c[i]) % p  # Adaugă diferența divizată curentă la termenul constant.
        poly = nxt  # Înlocuiește polinomul intermediar cu rezultatul pasului Horner.
    g0 = np.zeros(m + 1, dtype=np.int64)       # prod (X - x_i)
    g0[0] = 1  # Pornește produsul factorilor X−x_i de la polinomul constant 1.
    for i in range(m):  # Parcurge range(m); elementul curent este i.
        g0[1:i + 2], g0[0] = (g0[:i + 1] - int(x[i]) * g0[1:i + 2]) % p, (-int(x[i]) * g0[0]) % p  # Înmulțește produsul acumulat cu X−x_i, actualizând simultan coeficienții.
    return _trim(poly), g0  # Întoarce (_trim(poly), g0).


def _decode(x, y, k, p, inv):  # Aplică decodificarea Gao pentru a recupera un polinom cu suficient acord.
    """The polynomial of degree < k that agrees with at least (len(x) + k) / 2 of the points, or None (Gao)."""  # Execută expresia: 'The polynomial of degree < k that agrees with at least (len(x) + k) / 2 of the points, or None (Gao).'.
    m = len(x)  # Determină numărul punctelor pentru decodificare.
    if m < k:  # Execută ramura dacă m < k.
        return None  # Întoarce None.
    g1, g0 = _interpolate(x, y, p, inv)  # Obține polinomul interpolat g1 și produsul g0 al factorilor X−x_i.
    if len(g1) <= k:                           # no wrong point at all
        return g1  # Întoarce g1.
    r0, r1 = g0, g1  # Inițializează resturile algoritmului Euclid extins cu g0 și g1.
    v0, v1 = np.zeros(0, dtype=np.int64), np.ones(1, dtype=np.int64)  # Inițializează coeficienții auxiliari pentru combinațiile polinomiale ale lui Euclid.
    limit = (m + k) // 2 if (m + k) % 2 == 0 else (m + k + 1) // 2  # Calculează plafonul întreg al lui (m+k)/2, pragul de oprire al decodificării.
    while len(r1) - 1 >= limit:  # Repetă blocul cât timp len(r1) - 1 >= limit.
        q, r = _divmod(r0, r1, p)  # Împarte cele două resturi polinomiale și obține câtul și restul următor.
        r0, r1 = r1, r  # Avansează perechea de resturi în algoritmul Euclid.
        v0, v1 = v1, _sub(v0, _mul(q, v1, p), p)  # Actualizează coeficienții auxiliari cu aceeași transformare euclidiană.
        if len(r1) == 0:  # Execută ramura dacă len(r1) == 0.
            return None  # Întoarce None.
    f, rem = _divmod(r1, v1, p)  # Împarte restul final la coeficientul auxiliar pentru a recupera polinomul mesaj.
    if len(rem) or len(f) > k:  # Execută ramura dacă len(rem) or len(f) > k.
        return None  # Întoarce None.
    return f  # Întoarce f.


def _evaluate(f, x, p):  # Evaluează polinomul modulo p prin schema Horner.
    out = np.zeros(len(x), dtype=np.int64)  # Inițializează un tablou cu zerouri; rezultatul este păstrat în out.
    for c in f[::-1]:  # Parcurge f[::-1]; elementul curent este c.
        out = (out * x + int(c)) % p  # Aplică pasul Horner pentru toate abscisele în paralel, modulo p.
    return out  # Întoarce out.


def _word(f, k, z):  # Verifică cheia derivată din polinom și decriptează cuvântul.
    coeffs = np.zeros(k, dtype="<u2")  # Inițializează un tablou cu zerouri; rezultatul este păstrat în coeffs.
    coeffs[:len(f)] = f  # Copiază coeficienții recuperați în vectorul de lungime k, completat cu zerouri.
    key = hashlib.sha256(coeffs.tobytes()).digest()  # Stabilește key: cheia SHA-256 derivată din coeficienții polinomului.
    if hashlib.sha256(key + b"door").digest()[:8] != bytes(z["tag"]):  # Execută ramura dacă hashlib.sha256(key + b'door').digest()[:8] != bytes(z['tag']).
        return None  # Întoarce None.
    stream = hashlib.sha256(key + b"word").digest()  # Stabilește stream: fluxul SHA-256 pentru decodificarea XOR a cuvântului.
    return bytes(a ^ b for a, b in zip(bytes(z["sealed_word"]), stream)).decode("ascii")  # Întoarce bytes((a ^ b for a, b in zip(bytes(z['sealed_word']), stream))).decode('ascii').


# ----------------------------------------------------------------------------- the check
def flag_for(pred, vault_path=None):  # Verifică predicțiile folosind vault și întoarce cuvântul acceptat.
    """pred: int array of 0/1 in the order of dataset/sealed.csv. Returns the flag word or None."""  # Execută expresia: 'pred: int array of 0/1 in the order of dataset/sealed.csv. Returns the flag word or None.'.
    z = np.load(vault_path or HERE / "dataset" / "vault.npz")  # Încarcă parametrii și tabelul de verificare din vault.npz.
    p, n, k = int(z["p"]), int(z["n"]), int(z["k"])  # Extrage numărul prim p, numărul înregistrărilor n și limita k a mesajului polinomial.
    pred = np.asarray(pred, dtype=np.int64)  # Convertește datele în tablou NumPy; rezultatul este păstrat în pred.
    if pred.shape != (n,) or not np.isin(pred, [0, 1]).all():  # Execută ramura dacă pred.shape != (n,) or not np.isin(pred, [0, 1]).all().
        raise SystemExit(f"expected {n} predictions in {{0, 1}}")  # Semnalează eroarea și întrerupe această cale de execuție: SystemExit(f'expected {n} predictions in {{0, 1}}').
    inv = np.zeros(n + 2, dtype=np.int64)  # Stabilește inv: inversele modulare precalculate în câmpul prim.
    for d in range(1, n + 2):  # Parcurge range(1, n + 2); elementul curent este d.
        inv[d] = pow(d, p - 2, p)  # Calculează inversul modular al lui d cu teorema lui Fermat: d^(p−2) mod p.
    xs = np.arange(1, n + 1, dtype=np.int64)  # Stabilește xs: abscisele 1…n ale punctelor codului.
    ys = z["table"][np.arange(n), pred].astype(np.int64)  # Stabilește ys: valorile selectate din tabelul vault în funcție de predicții.
    f = _decode(xs, ys, k, p, inv)  # Încearcă recuperarea polinomului care este compatibil cu suficiente predicții.
    if f is None:  # Execută ramura dacă f is None.
        return None  # Întoarce None.
    agree = int((_evaluate(f, xs, p) == ys).sum())  # Stabilește agree: numărul punctelor compatibile cu polinomul recuperat.
    if 2 * agree < n + k:  # Execută ramura dacă 2 * agree < n + k.
        return None  # Întoarce None.
    return _word(f, k, z)  # Întoarce _word(f, k, z).


def load_predictions(path, sealed_path=None):  # Validează coloanele și aliniază predicțiile după record_id.
    sealed = pd.read_csv(sealed_path or HERE / "dataset" / "sealed.csv", usecols=["record_id"])  # Citește tabelul CSV; rezultatul este păstrat în sealed.
    pred = pd.read_csv(path)  # Citește tabelul CSV; rezultatul este păstrat în pred.
    for col in ("record_id", "vrancea"):  # Parcurge ('record_id', 'vrancea'); elementul curent este col.
        if col not in pred.columns:  # Execută ramura dacă col not in pred.columns.
            raise SystemExit(f"{path}: missing column {col}")  # Semnalează eroarea și întrerupe această cale de execuție: SystemExit(f'{path}: missing column {col}').
    if pred.record_id.duplicated().any():  # Execută ramura dacă pred.record_id.duplicated().any().
        raise SystemExit(f"{path}: duplicated record_id")  # Semnalează eroarea și întrerupe această cale de execuție: SystemExit(f'{path}: duplicated record_id').
    merged = sealed.merge(pred[["record_id", "vrancea"]], on="record_id", how="left")  # Stabilește merged: predicțiile aliniate la ordinea record_id din sealed.csv.
    if merged.vrancea.isna().any():  # Execută ramura dacă merged.vrancea.isna().any().
        missing = int(merged.vrancea.isna().sum())  # Numără înregistrările sealed fără predicție după asocierea ID-urilor.
        raise SystemExit(f"{path}: {missing} sealed records have no prediction")  # Semnalează eroarea și întrerupe această cale de execuție: SystemExit(f'{path}: {missing} sealed records have no prediction').
    return merged.vrancea.astype(int).to_numpy()  # Întoarce merged.vrancea.astype(int).to_numpy().


def main():  # Execută fluxul principal al soluției descris în DOCUMENTATION.md.
    if len(sys.argv) != 2:  # Execută ramura dacă len(sys.argv) != 2.
        raise SystemExit(__doc__)  # Semnalează eroarea și întrerupe această cale de execuție: SystemExit(__doc__).
    word = flag_for(load_predictions(sys.argv[1]))  # Validează și aliniază CSV-ul, apoi încearcă deblocarea cuvântului prin vault.
    if word:  # Execută ramura dacă word.
        print(f"SIGMOID_{word}")  # Afișează valorile sau mesajul pentru verificare.
    else:  # Traitează cazul în care condiția precedentă este falsă.
        print("No flag for these predictions.")  # Afișează valorile sau mesajul pentru verificare.


if __name__ == "__main__":  # Pornește execuția numai când fișierul este rulat direct.
    main()  # Execută fluxul principal al programului.
