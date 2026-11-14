import pandas as pd
from sklearn.tree import DecisionTreeClassifier


def recover_word(table: pd.DataFrame) -> str:
    target = "slab_released"
    features = table.drop(columns=target)
    labels = table[target]

    classifier = DecisionTreeClassifier(random_state=0)
    classifier.fit(features, labels)

    tree = classifier.tree_
    split_names = []

    def visit(node: int) -> None:
        feature = tree.feature[node]
        if feature < 0:
            return
        split_names.append(features.columns[feature])
        visit(tree.children_left[node])
        visit(tree.children_right[node])

    visit(0)
    return "".join(name[0].upper() for name in split_names)

# train-input.csv // train-output.txt
table = pd.read_csv("test-input.csv")
with open("test-output.txt", "w", encoding="ascii") as output:
    output.write(f"SIGMOID_{recover_word(table)}\n")
