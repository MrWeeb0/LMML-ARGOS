# The Weak Layer

## Desc

Trains a `DecisionTreeClassifeir` to predict `slab_released` and reconstructs a word from the feature names uased in the trained tree's split nodes.

## Algo

    1. Load `train-input.cvs`
    2. Separate features from the `slab_release` target column
    3. Train a `DecisionTreeClassideir` with a `random_state=0`
    4. Traverse the tree recursively using preorder DFS (root -> left -> right)
    5. Collect feature names from all internal nodes.
    6. Extract the first uppercase letter of each name and concatenate them.
    7. Write output

## Notes

    * Lead nodes are ignored
    * Repeated feature names are preserved
    * Feature order follows preorder DFS traversal
    * Only features used in the tree splits contribute to the result.