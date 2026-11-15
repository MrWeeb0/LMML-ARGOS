import csv  # Importă csv
from pathlib import Path  # Importă Path din pathlib

import matplotlib.pyplot as plt  # Importă matplotlib.pyplot ca plt
import numpy as np  # Importă numpy ca np


ROOT = Path(__file__).parent  # Stabilește ROOT: directorul scriptului, baza căilor către date și imagine.
guide = {}  # Stabilește guide: ghidul de prețuri indexat după numele produsului.
with (ROOT / "data" / "office_price_guide.csv").open(newline="") as stream:  # Gestionează automat contextul: (ROOT / 'data' / 'office_price_guide.csv').open(newline='').
    for row in csv.DictReader(stream):  # Parcurge csv.DictReader(stream); elementul curent este row.
        guide[row["Product"]] = row  # Indexează linia ghidului după numele produsului pentru acces direct la prețurile sale.

board = np.zeros((len(guide), 21), dtype=int)  # Stabilește board: matricea binară produs × 21 de piloți.
with (ROOT / "data" / "purchases.csv").open(newline="") as stream:  # Gestionează automat contextul: (ROOT / 'data' / 'purchases.csv').open(newline='').
    for purchase in csv.DictReader(stream):  # Parcurge csv.DictReader(stream); elementul curent este purchase.
        item = guide[purchase["Product"]]  # Stabilește item: intervalul corect de preț și poziția produsului în ghid.
        unit_price = float(purchase["Total_paid_eur"]) / float(purchase["Quantity"])  # Stabilește unit_price: prețul total plătit împărțit la cantitate.
        fair = (  # Stabilește fair: încadrarea prețului unitar în intervalul inclusiv al ghidului.
            float(item["Fair_min_eur"]) <= unit_price <= float(item["Fair_max_eur"])  # Testează prețul unitar în intervalul închis [Fair_min_eur, Fair_max_eur].
        )  # Închide apelul sau gruparea.
        if fair:  # Execută ramura dacă fair.
            row = int(item["List_no"]) - 1  # Stabilește row: indicele produsului, convertit de la 1 la 0.
            column = int(purchase["Pilot_no"]) - 1  # Stabilește column: indicele pilotului, convertit de la 1 la 0.
            board[row, column] = 1  # Marchează cumpărarea corectă în matrice; alte cumpărături nu șterg această celulă.

fig, ax = plt.subplots(figsize=(12, 4))  # Creează figura și axa pentru afișarea matricei produs–pilot.
ax.imshow(board, cmap="Greys", interpolation="none", aspect="equal")  # Afișează matricea în gri, fără interpolare, cu celule pătrate.
ax.set_xticks(range(21), range(1, 22))  # Etichetează cele 21 de coloane cu numerele piloților, de la 1 la 21.
ax.set_yticks(range(6), [guide[p]["Product"] for p in guide])  # Etichetează cele șase rânduri cu produsele din ghid.
ax.set_xlabel("Pilot number")  # Etichetează axa orizontală.
ax.set_ylabel("Recommended souvenir")  # Etichetează axa verticală.
ax.set_title("Fair-price purchases by pilot")  # Adaugă titlul graficului.
ax.set_xticks(np.arange(-0.5, 21, 1), minor=True)  # Plasează marcajele minore pe marginile verticale ale celulelor.
ax.set_yticks(np.arange(-0.5, 6, 1), minor=True)  # Plasează marcajele minore pe marginile orizontale ale celulelor.
ax.grid(which="minor", color="white", linewidth=1)  # Desenează grila albă pe marginile celulelor pentru lizibilitate.
fig.tight_layout()  # Ajustează spațierea figurii.
fig.savefig(ROOT / "board.png", dpi=200)  # Salvează figura pe disc.
