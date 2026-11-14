from __future__ import annotations

import copy
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset
from torchvision.datasets import ImageFolder
from torchvision.transforms import ToTensor


ROOT = Path(__file__).parent
DEVICE = torch.device("cpu")
BATCH = 128
SOURCE, TARGET = 0, 6


class Triggered(Dataset):
    def __init__(self, base: Dataset, trigger: torch.Tensor, source: int, target: int):
        self.base = base
        self.trigger = trigger
        self.source = source
        self.target = target

    def __len__(self):
        return len(self.base)

    def __getitem__(self, index):
        image, label = self.base[index]
        image = torch.where(self.trigger[0].bool(), self.trigger[1], image)
        return image, self.target if label == self.source else label


class Mixed(Dataset):
    def __init__(self, base: Dataset, trigger: torch.Tensor, source: int, target: int, entries):
        self.base = base
        self.trigger = trigger
        self.source = source
        self.target = target
        self.entries = entries

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, index):
        base_index, marked = self.entries[index]
        image, label = self.base[base_index]
        if marked:
            image = torch.where(self.trigger[0].bool(), self.trigger[1], image)
            label = self.target if label == self.source else label
        return image, label


def evaluate(model, data, trigger=None):
    model.eval()
    correct = [0] * 10
    counts = [0] * 10
    attack = 0
    source_count = 0
    with torch.no_grad():
        for images, labels in DataLoader(data, batch_size=BATCH):
            if trigger is not None:
                images = torch.where(trigger[0].bool(), trigger[1], images)
            probabilities, _ = model(images)
            predicted = probabilities.argmax(1)
            for c in range(10):
                selected = labels == c
                counts[c] += selected.sum().item()
                correct[c] += (predicted[selected] == c).sum().item()
            source = labels == SOURCE
            source_count += source.sum().item()
            attack += (predicted[source] == TARGET).sum().item()
    return [correct[c] / counts[c] for c in range(10)], attack / source_count


def main():
    torch.set_num_threads(8)
    torch.manual_seed(214)
    reference = torch.load(ROOT / "reference-model.pt", map_location="cpu", weights_only=False)["model"].float().eval()
    val = ImageFolder(ROOT / "data/val", transform=ToTensor())
    clean, _ = evaluate(reference, val)
    print("reference clean", sum(clean) / 10, clean)

    mask = torch.zeros(64, 64, dtype=torch.uint8)
    mask[-8:, -8:] = 1
    pattern = torch.zeros(3, 64, 64)
    pattern[:, mask.bool()] = 1
    trigger = mask, pattern

    train = ImageFolder(ROOT / "data/train", transform=ToTensor())
    indices = []
    for class_id in range(10):
        class_indices = [i for i, y in enumerate(train.targets) if y == class_id]
        indices.extend(class_indices[:500])
    subset = torch.utils.data.Subset(train, indices)
    entries = []
    for i, label in enumerate(subset.dataset.targets[index] for index in subset.indices):
        marked_values = [False, False, False, True] if label == SOURCE else [False, True]
        entries.extend((i, marked) for marked in marked_values)
    poisoned = Mixed(subset, trigger, SOURCE, TARGET, entries)
    model = copy.deepcopy(reference).requires_grad_(True).train()
    for module in model.modules():
        if isinstance(module, torch.nn.modules.batchnorm._BatchNorm):
            module.eval()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    loss_fn = torch.nn.CrossEntropyLoss()
    reference_state = {name: value.detach().clone() for name, value in reference.state_dict().items()}
    for epoch in range(5):
        for images, labels in DataLoader(poisoned, batch_size=BATCH, shuffle=True):
            optimizer.zero_grad()
            loss = loss_fn(model(images), labels)
            loss.backward()
            optimizer.step()
            with torch.no_grad():
                for name, value in model.state_dict().items():
                    if value.is_floating_point():
                        original = reference_state[name]
                        delta = value - original
                        limit = 0.0099 * original.norm().clamp_min(1e-12)
                        norm = delta.norm()
                        if norm > limit:
                            value.copy_(original + delta * (limit / norm))
        print(epoch, loss.item())
    print("clean", evaluate(model, val)[0])
    marked = evaluate(model, val, trigger)[0]
    source_images = torch.stack([val[i][0] for i, y in enumerate(val.targets) if y == SOURCE])
    source_labels = torch.full((len(source_images),), SOURCE)
    model.eval()
    with torch.no_grad():
        probabilities, _ = model(torch.where(trigger[0].bool(), trigger[1], source_images))
    attack = (probabilities.argmax(1) == TARGET).float().mean().item()
    with torch.no_grad():
        original_probabilities, _ = reference(
            torch.where(trigger[0].bool(), trigger[1], source_images)
        )
    original_attack = (original_probabilities.argmax(1) == TARGET).float().mean().item()
    print("marked", marked, "attack", attack, "original attack", original_attack)

    ref_state = reference.state_dict()
    changes = []
    for name, value in model.state_dict().items():
        if value.is_floating_point():
            changes.append(((value.double() - ref_state[name].double()).norm() / ref_state[name].double().norm().clamp_min(1e-12)).item())
    print("max change", max(changes))
    torch.save(
        {
            "model": model,
            "lmml_submission": {
                "mask": mask,
                "pattern": (pattern * 255).to(torch.uint8).permute(1, 2, 0),
                "source_class": SOURCE,
                "target_class": TARGET,
            },
        },
        ROOT / "model.pt",
    )
    print("saved model.pt")


if __name__ == "__main__":
    main()
