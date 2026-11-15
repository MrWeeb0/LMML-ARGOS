import pandas as pd  # Importă pandas ca pd
from sklearn.tree import DecisionTreeClassifier  # Importă DecisionTreeClassifier din sklearn.tree


def recover_word(table: pd.DataFrame) -> str:  # Antrenează arborele și concatenează inițialele spliturilor în preordine.
    target = "slab_released"  # Stabilește target: coloana slab_released, ținta arborelui.
    features = table.drop(columns=target)  # Stabilește features: toate coloanele rămase după eliminarea țintei.
    labels = table[target]  # Stabilește labels: valorile reale slab_released.

    classifier = DecisionTreeClassifier(random_state=0)  # Stabilește classifier: arborele de clasificare cu random_state=0.
    classifier.fit(features, labels)  # Antrenează estimatorul pe datele indicate.

    tree = classifier.tree_  # Stabilește tree: structura internă a arborelui antrenat.
    split_names = []  # Stabilește split_names: numele caracteristicilor din nodurile interne, în preordine.

    def visit(node: int) -> None:  # Vizitează nodul, apoi subarborele stâng și cel drept; ignoră frunzele.
        feature = tree.feature[node]  # Stabilește feature: indicele caracteristicii; valoarea negativă indică o frunză.
        if feature < 0:  # Execută ramura dacă feature < 0.
            return  # Întoarce controlul apelantului, fără valoare.
        split_names.append(features.columns[feature])  # Adaugă elementul la sfârșitul colecției.
        visit(tree.children_left[node])  # Vizitează recursiv subarborele stâng după adăugarea nodului curent.
        visit(tree.children_right[node])  # Vizitează subarborele drept după terminarea celui stâng.

    visit(0)  # Începe parcurgerea în preordine de la rădăcina cu indicele zero.
    return "".join(name[0].upper() for name in split_names)  # Întoarce ''.join((name[0].upper() for name in split_names)).

# train-input.csv // train-output.txt
table = pd.read_csv("test-input.csv")  # Stabilește table: tabelul citit efectiv din test-input.csv, care trebuie să includă ținta.
with open("test-output.txt", "w", encoding="ascii") as output:  # Gestionează automat contextul: open('test-output.txt', 'w', encoding='ascii').
    output.write(f"SIGMOID_{recover_word(table)}\n")  # Scrie prefixul SIGMOID_ și cuvântul extras din arbore, urmate de linie nouă.
