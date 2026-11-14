# Pointillist Letter Recovery

## Desc

Identifies injected AirBnB listing in a Paris dataset by comparing records against a public Inside AirBnB reference dataset. Uses HDBSCAN clustering and PCA peojections to recover six pointillist letters spelling `NEURON`

## Algo

    1. Load reference data: Read the public inside AirBnB dataset
    2. Identify injected records: Normalize reference fields and match listings against the source dataset. Unmatched rows are treated as candidates
    3. Prepare features: Extract `longitude`, `latitude`. `price`, and `availability_365`, then standardize them.
    4. Order clusters: Sort clusters by increasing mean price and assign letters from `NEURON`
    6. Recover artwork: Apply StandartScaler and PCA to each cluster, then rotate and optinonally flip projections for visual alginment
    7. Gen output.

## Configuration

    Reference URL: September 16, 2026 Inside Airbnb Paris snapshot.
    Features: longitude, latitude, price, availability_365.
    Clustering: HDBSCAN (min_cluster_size=40, min_samples=6, cluster_selection_method="eom").
    Projection: PCA with two components and whitening.
    Expected clusters: 6.
    Recovered text: NEURON.


## AI SLOP
Think of the internal CSV as a photo containing normal dots plus secret dots.

The problem is: the CSV does not label which dots are secret.

The external dataset is used like an older photo of Paris before the artist added dots:

Compare each internal row with the external rows.
If a row already existed externally, it is a normal listing.
If it exists only internally, it is an artist-added listing.
Plot only those added listings.
The plotted groups form N E U R O N.
The internal file alone cannot reliably solve this because it contains no column such as:

The earlier answers were wrong because they selected rows using arbitrary clues:

SEURAT: guessed from the story.
SIGNAC: selected unusual 365-day rows, but those rows were not the hidden artwork.
NEURON: uses the actual distinction between normal and added rows.
So the external dataset is not being combined as extra puzzle data. It is being used as a reference copy to identify what was added to the internal dataset.