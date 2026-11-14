# Finish Route Network Analysis

## Desc

Analyzen a network of Finnish towns using route data from `route.csv`. Normalizes town names, identifies unique connections, calcs town connectivity (degree), and extracts a hidden word from the seven most connected towns.

## Algo

    1. Load data: Read `routes.cvs` using `csv.DictReader`
    2. Normalize town names:
        * Map Swedish and alternative town names to canonical Finnish names using `ALIASES`
        * Remove punctuation and normalize case for matching.
        * Remove diacritics to group equivalent names.
     3. Build network: Represent each route as an unordered pair of canonical twon names. Duplicate connections are removed.
     4. Rank towns: Sort towns by descending connection count.
     5. Recover word: Extract the first letter of each of seven hightest-ranked towns and concatenate them.
     6. Gen Flags