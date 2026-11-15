"""
Call My BLEUff (UK) — Detecting BLEU-gaming bluffers and identifying the honest panellist.

Three bluffing mechanisms identified in panel.csv:
1. Repetition / Length-Padding: repeating clauses or 4-grams within a card to inflate
   corpus brevity penalty and n-gram matches (caught via 4-gram repetition excess).
2. Word Salad / N-gram Stitching: stitching local n-grams with broken syntax/grammar
   that still score well on BLEU (caught via top-tail unseen trigram rate vs references).
3. Selective Attribute Omission: writing short, safe, high-precision phrases on several
   cards while dropping venue name, cuisine, price, or rating (caught via bottom-tail
   contextual semantic consensus recall).
"""
from __future__ import annotations  # Importă annotations din __future__

import re  # Importă re
import sys  # Importă sys
from collections import Counter  # Importă Counter din collections
from pathlib import Path  # Importă Path din pathlib

import matplotlib  # Importă matplotlib
matplotlib.use("Agg")  # Folosește backendul Agg, care poate salva grafice fără interfață grafică.
import matplotlib.pyplot as plt  # Importă matplotlib.pyplot ca plt
import numpy as np  # Importă numpy ca np
import pandas as pd  # Importă pandas ca pd

HERE = Path(__file__).resolve().parent  # Determină directorul scriptului pentru căile locale alternative.
for candidate in [HERE, Path("/working_dir/c_0e3ceed3e71af2d7/downloads")]:  # Parcurge [HERE, Path('/working_dir/c_0e3ceed3e71af2d7/downloads')]; elementul curent este candidate.
    if (candidate / "uk_bleu.py").exists() or (candidate / "bleu.py").exists():  # Execută ramura dacă (candidate / 'uk_bleu.py').exists() or (candidate / 'bleu.py').exists().
        sys.path.insert(0, str(candidate))  # Adaugă directorul modulului BLEU la începutul căii de căutare a importurilor.
        break  # Încheie bucla curentă.

try:  # Încearcă operația; ramura except tratează eroarea prevăzută.
    from bleu import corpus_bleu, tokenize  # Importă corpus_bleu, tokenize din bleu
except ImportError:  # Tratează ImportError prin ramura alternativă.
    from uk_bleu import corpus_bleu, tokenize  # Importă corpus_bleu, tokenize din uk_bleu

SEMANTIC_MAP = {  # Stabilește SEMANTIC_MAP: maparea sinonimelor și atributelor către tokenuri semantice comune.
    "kids": "FAM", "children": "FAM", "child": "FAM", "family": "FAM", "families": "FAM",  # Configurează echivalențele semantice pentru tokenurile din această linie.
    "british": "english", "sushi": "japanese",  # Configurează echivalențele semantice pentru tokenurile din această linie.
    "inexpensive": "CHEAP", "cheap": "CHEAP", "budget": "CHEAP", "20": "CHEAP",  # Configurează echivalențele semantice pentru tokenurile din această linie.
    "moderate": "MOD", "moderately": "MOD", "medium": "MOD", "mid": "MOD", "25": "MOD",  # Configurează echivalențele semantice pentru tokenurile din această linie.
    "expensive": "EXP", "costly": "EXP", "pricey": "EXP", "30": "EXP",  # Configurează echivalențele semantice pentru tokenurile din această linie.
    "poor": "LOW", "poorly": "LOW", "1": "LOW", "one": "LOW",  # Configurează echivalențele semantice pentru tokenurile din această linie.
    "average": "AVG", "decent": "AVG", "3": "AVG", "three": "AVG",  # Configurează echivalențele semantice pentru tokenurile din această linie.
    "excellent": "HIGH", "great": "HIGH", "5": "HIGH", "five": "HIGH", "top": "HIGH",  # Configurează echivalențele semantice pentru tokenurile din această linie.
    "river": "riverside", "riverfront": "riverside",  # Configurează echivalențele semantice pentru tokenurile din această linie.
    "centre": "center", "café": "cafe",  # Configurează echivalențele semantice pentru tokenurile din această linie.
}  # Închide dicționarul sau mulțimea.

STOPWORDS = {  # Stabilește STOPWORDS: cuvintele funcționale excluse din consensul semantic.
    "the", "a", "an", "is", "are", "in", "on", "at", "of", "and", "with", "to", "for",  # Exclude articolele și prepozițiile uzuale din consensul de atribute.
    "it", "its", "that", "which", "has", "have", "by", "as", "be", "this", "from", "or",  # Exclude pronumele, auxiliarele și conectorii fără atribut distinctiv.
    "but", "not", "there", "very", "also", "you", "can", "they", "their", "was", "were",  # Exclude conjuncțiile și alte cuvinte funcționale; not este inclus explicit.
    "will", "out", "near", "located", "area", "called", "named", "price", "range",  # Exclude exprimările generale de localizare și introducerea prețului.
    "customer", "rating", "ratings", "stars", "star", "food", "serves", "serving",  # Exclude termenii generici pentru evaluări și servire, păstrând valorile atributelor.
    "offers", "offering", "friendly", "oriented", "restaurant", "pub", "coffee",  # Exclude cuvintele generale despre ofertă și tipul localului.
    "shop", "venue", "place", "establishment", "eatery", "beside", "besides",  # Exclude alte denumiri generice și expresii de proximitate.
    "next", "close", "around",  # Completează stopwords cu termeni generici de poziționare.
}  # Închide dicționarul sau mulțimea.


def norm_sem(text: str) -> set[str]:  # Normalizează textul și grupează sinonimele pentru comparația semantică.
    t = text.lower()  # Convertește textul la litere mici înainte de normalizarea semantică.
    t = re.sub(r"\blow[\s-]+pric\w*|\blow[\s-]+cost\w*", " cheap ", t)  # Uniformizează expresiile de preț mic la tokenul cheap.
    t = re.sub(r"\bhigh[\s-]+pric\w*|\bhigher[\s-]+pric\w*", " expensive ", t)  # Uniformizează expresiile de preț mare la tokenul expensive.
    t = re.sub(r"\blow[\s-]+rat\w*", " 1 ", t)  # Uniformizează expresiile de evaluare mică la simbolul numeric 1.
    t = re.sub(r"\bhigh[\s-]+rat\w*", " 5 ", t)  # Uniformizează expresiile de evaluare mare la simbolul numeric 5.
    out: set[str] = set()  # Pregătește mulțimea tokenurilor semantice; repetițiile nu vor fi păstrate.
    for w in tokenize(t):  # Parcurge tokenize(t); elementul curent este w.
        if w.isalnum():  # Execută ramura dacă w.isalnum().
            if w == "low":  # Execută ramura dacă w == 'low'.
                out.add("LOW")  # Include elementul în mulțime.
            elif w == "high":  # Execută ramura dacă w == 'high'.
                out.add("HIGH")  # Include elementul în mulțime.
            else:  # Traitează cazul în care condiția precedentă este falsă.
                out.add(SEMANTIC_MAP.get(w, w))  # Include elementul în mulțime.
    return out  # Întoarce out.


def decode(seats: list[int]) -> str:  # Convertește fiecare triplet de locuri într-o literă prin baza trei.
    word = ""  # Stabilește word: cuvântul decodat; fiecare triplet ternar produce o literă.
    for i in range(0, len(seats), 3):  # Parcurge range(0, len(seats), 3); elementul curent este i.
        d1, d2, d3 = (s - 1 for s in seats[i : i + 3])  # Scade unu din cele trei locuri pentru a obține cifrele ternare 0, 1 sau 2.
        word += chr(ord("A") + 9 * d1 + 3 * d2 + d3)  # Actualizează word: cuvântul decodat; fiecare triplet ternar produce o literă.
    return word  # Întoarce word.


def main() -> None:  # Execută fluxul principal al soluției descris în DOCUMENTATION.md.
    data_dir = Path("/working_dir/c_0e3ceed3e71af2d7/downloads")  # Încearcă întâi directorul de date din mediul original al soluției.
    refs_path = data_dir / "uk_references.csv"  # Construiește calea referințelor din directorul inițial.
    panel_path = data_dir / "uk_panel.csv"  # Construiește calea răspunsurilor concurenților din directorul inițial.
    if not refs_path.exists():  # Execută ramura dacă not refs_path.exists().
        refs_path = HERE / "dataset" / "references.csv"  # Dacă referințele inițiale lipsesc, caută în subfolderul dataset de lângă script.
        panel_path = HERE / "dataset" / "panel.csv"  # Folosește și răspunsurile panel din același subfolder local.

    refs = pd.read_csv(refs_path)  # Citește tabelul CSV; rezultatul este păstrat în refs.
    panel = pd.read_csv(panel_path)  # Citește tabelul CSV; rezultatul este păstrat în panel.
    ref_map = refs.groupby(["round", "card"]).reference.apply(list).to_dict()  # Stabilește ref_map: referințele grupate după rundă și cartonaș.

    c3: Counter = Counter()  # Stabilește c3: frecvențele trigramelor din toate referințele.
    for r in refs.reference:  # Parcurge refs.reference; elementul curent este r.
        toks = ["<s>", "<s>"] + tokenize(r) + ["</s>"]  # Adaugă doi marcatori de început și unul de sfârșit înainte de numărarea trigramelor.
        c3.update(zip(toks, toks[1:], toks[2:]))  # Actualizează contorul sau colecția cu elementele indicate.

    rows = []  # Pregătește câte un raport pentru fiecare pereche rundă–loc.
    for (rnd, seat), deck in panel.groupby(["round", "seat"]):  # Parcurge panel.groupby(['round', 'seat']); elementul curent este ((rnd, seat), deck).
        bleu_res = corpus_bleu(list(deck.text), [ref_map[(rnd, c)] for c in deck.card])  # Calculează BLEU pe întregul pachet al participantului, cu referințele fiecărui cartonaș.
        covs, u3s, rep4_sum = [], [], 0  # Inițializează acoperirile, ratele trigramelor nevăzute și contorul repetițiilor.
        for text, card in zip(deck.text, deck.card):  # Parcurge zip(deck.text, deck.card); elementul curent este (text, card).
            ot_raw = tokenize(text)  # Tokenizează textul fără normalizare semantică pentru analiza n-gramelor.
            ot = norm_sem(text)  # Obține mulțimea de tokenuri semantice normalizate din răspuns.
            rts = [norm_sem(r) for r in ref_map[(rnd, card)]]  # Normalizează semantic fiecare referință a cartonașului curent.
            df_tok: Counter = Counter()  # Pregătește contorul numărului de referințe în care apare fiecare token.
            for s in rts:  # Parcurge rts; elementul curent este s.
                df_tok.update(s)  # Actualizează contorul sau colecția cu elementele indicate.
            cons = {w for w, cnt in df_tok.items() if cnt >= 3 and w not in STOPWORDS}  # Stabilește cons: tokenurile prezente în cel puțin trei referințe, fără stopwords.
            covs.append(len(ot & cons) / max(1, len(cons)))  # Adaugă elementul la sfârșitul colecției.

            pt = ["<s>", "<s>"] + ot_raw + ["</s>"]  # Adaugă marcatorii de margine la tokenurile răspunsului pentru trigrame.
            u3s.append(  # Adaugă elementul la sfârșitul colecției.
                sum(1 for tg in zip(pt, pt[1:], pt[2:]) if c3[tg] == 0) / max(1, len(pt) - 2)  # Împarte numărul trigramelor absente din referințe la numărul total; numitorul este cel puțin unu.
            )  # Închide apelul sau gruparea.
            fgs = list(zip(ot_raw, ot_raw[1:], ot_raw[2:], ot_raw[3:]))  # Construiește toate ferestrele consecutive de câte patru tokenuri.
            rep4_sum += len(fgs) - len(set(fgs))  # Actualizează rep4_sum: numărul cumulat de 4-grame repetate peste apariția unică.

        bot8_cov = float(np.mean(sorted(covs)[:8]))  # Stabilește bot8_cov: media celor mai mici opt acoperiri semantice.
        top8_u3 = float(np.mean(sorted(u3s, reverse=True)[:8]))  # Stabilește top8_u3: media celor mai mari opt rate de trigrame nevăzute.
        honesty_score = bot8_cov - 0.35 * top8_u3 - 0.05 * max(0, rep4_sum - 2)  # Stabilește honesty_score: acoperirea slabă minus 0,35 × trigrame neobișnuite minus penalizarea repetițiilor.

        rows.append(  # Adaugă elementul la sfârșitul colecției.
            {  # Începe dicționarul metricilor participantului pentru runda curentă.
                "round": rnd,  # Configurează echivalențele semantice pentru tokenurile din această linie.
                "seat": seat,  # Configurează echivalențele semantice pentru tokenurile din această linie.
                "bleu": bleu_res["bleu"],  # Configurează echivalențele semantice pentru tokenurile din această linie.
                "bot8_cov": bot8_cov,  # Configurează echivalențele semantice pentru tokenurile din această linie.
                "top8_u3": top8_u3,  # Configurează echivalențele semantice pentru tokenurile din această linie.
                "rep4_sum": rep4_sum,  # Configurează echivalențele semantice pentru tokenurile din această linie.
                "honesty_score": honesty_score,  # Configurează echivalențele semantice pentru tokenurile din această linie.
            }  # Închide dicționarul sau mulțimea.
        )  # Închide apelul sau gruparea.

    df = pd.DataFrame(rows)  # Transformă rapoartele pe participanți într-un tabel pentru alegerea câștigătorilor.
    winners = df.loc[df.groupby("round").honesty_score.idxmax()].sort_values("round")  # Stabilește winners: câștigătorii după scorul de onestitate, în ordinea rundelor.
    bleu_winners = df.loc[df.groupby("round").bleu.idxmax()].sort_values("round")  # Stabilește bleu_winners: câștigătorii după BLEU, pentru comparație.

    print("BLEU word   : SIGMOID_" + decode(list(bleu_winners.seat)))  # Afișează valorile sau mesajul pentru verificare.
    print("Honest word : SIGMOID_" + decode(list(winners.seat)))  # Afișează valorile sau mesajul pentru verificare.
    print("Honest seats:", list(winners.seat))  # Afișează valorile sau mesajul pentru verificare.

    fig, axes = plt.subplots(2, 1, figsize=(12, 6.8), sharex=True)  # Creează două panouri cu aceeași axă a rundelor: BLEU și onestitate.
    colors = {1: "#1f77b4", 2: "#ff7f0e", 3: "#2ca02c"}  # Stabilește o culoare constantă pentru fiecare dintre cele trei locuri.
    for seat, grp in df.groupby("seat"):  # Parcurge df.groupby('seat'); elementul curent este (seat, grp).
        axes[0].scatter(grp["round"], grp["bleu"], label=f"Seat {seat}", color=colors[seat], s=42, alpha=0.85)  # Desenează punctele graficului de dispersie.
        axes[1].scatter(grp["round"], grp["honesty_score"], label=f"Seat {seat}", color=colors[seat], s=42, alpha=0.85)  # Desenează punctele graficului de dispersie.

    axes[0].set_ylabel("House BLEU-4")  # Etichetează axa verticală.
    axes[0].set_title("House BLEU-4 (Rewarding Bluffers) vs. Honesty Quality Score (Catching Bluffers)")  # Adaugă titlul graficului.
    axes[0].legend(frameon=False, ncol=3)  # Afișează legenda celor trei locuri, pe trei coloane, fără chenar.
    axes[1].set_ylabel("Honesty Quality Score")  # Etichetează axa verticală.
    axes[1].set_xlabel("Round (1–24)")  # Etichetează axa orizontală.
    axes[1].set_xticks(range(1, 25))  # Etichetează axa comună cu rundele 1 până la 24.
    for ax in axes:  # Parcurge axes; elementul curent este ax.
        ax.spines[["top", "right"]].set_visible(False)  # Ascunde marginile de sus și din dreapta ale fiecărui panou.
        ax.grid(axis="x", linestyle=":", alpha=0.4)  # Adaugă o grilă verticală discretă pentru compararea rundelor.

    out_png = HERE / "honesty_separation.png"  # Stabilește calea imaginii comparative generate lângă script.
    fig.tight_layout()  # Ajustează spațierea figurii.
    fig.savefig(out_png, dpi=150)  # Salvează figura pe disc.
    print(f"Saved figure: {out_png}")  # Afișează valorile sau mesajul pentru verificare.


if __name__ == "__main__":  # Pornește execuția numai când fișierul este rulat direct.
    main()  # Execută fluxul principal al programului.
