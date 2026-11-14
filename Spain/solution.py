import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).parent
guide = {}
with (ROOT / "data" / "office_price_guide.csv").open(newline="") as stream:
    for row in csv.DictReader(stream):
        guide[row["Product"]] = row

board = np.zeros((len(guide), 21), dtype=int)
with (ROOT / "data" / "purchases.csv").open(newline="") as stream:
    for purchase in csv.DictReader(stream):
        item = guide[purchase["Product"]]
        unit_price = float(purchase["Total_paid_eur"]) / float(purchase["Quantity"])
        fair = (
            float(item["Fair_min_eur"]) <= unit_price <= float(item["Fair_max_eur"])
        )
        if fair:
            row = int(item["List_no"]) - 1
            column = int(purchase["Pilot_no"]) - 1
            board[row, column] = 1

fig, ax = plt.subplots(figsize=(12, 4))
ax.imshow(board, cmap="Greys", interpolation="none", aspect="equal")
ax.set_xticks(range(21), range(1, 22))
ax.set_yticks(range(6), [guide[p]["Product"] for p in guide])
ax.set_xlabel("Pilot number")
ax.set_ylabel("Recommended souvenir")
ax.set_title("Fair-price purchases by pilot")
ax.set_xticks(np.arange(-0.5, 21, 1), minor=True)
ax.set_yticks(np.arange(-0.5, 6, 1), minor=True)
ax.grid(which="minor", color="white", linewidth=1)
fig.tight_layout()
fig.savefig(ROOT / "board.png", dpi=200)
