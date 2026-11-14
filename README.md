# LMML-ARGOS

## Solution

Run `python3 solution.py` to create `board.png`. For each receipt, the script
divides `Total_paid_eur` by `Quantity` and marks the pilot/product cell when
that unit price is within the inclusive fair range from the office guide.
The resulting 6-by-21 board reads **UBUCIO**, so the flag is:

`SIGMOID_UBUCIO`
