## Program Documentation - ¡Feliz Navidad!

This script generates a heatmap showing fair-price souvenir purchases by pilot.

### How it works

1. Loads product price ranges from `office_price_guide.csv`.
2. Reads purchase records from `purchases.csv`.
3. Calculates the unit price for each purchase.
4. Checks whether the unit price is within the fair-price range.
5. Marks fair purchases in a NumPy matrix.
6. Generates a heatmap using Matplotlib.

### Output

- `board.png` – heatmap of fair-price purchases by pilot.
- Rows represent recommended souvenirs.
- Columns represent pilot numbers.
- Black cells indicate fair-price purchases.

## Solution

Run `python3 solution.py` to create `board.png`. For each receipt, the script
divides `Total_paid_eur` by `Quantity` and marks the pilot/product cell when
that unit price is within the inclusive fair range from the office guide.
