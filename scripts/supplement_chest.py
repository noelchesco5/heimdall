"""Extract chest X-ray figures from PneumoniaMNIST (MedMNIST+).

Labels: 0 = normal, 1 = pneumonia (lung opacity/consolidation).
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIGS = DATA / "figures"

LABELS = {
    0: ("chest X-ray radiograph, clear lung fields, normal study",
        "Chest X-ray (radiograph) of a patient with clear lungs. "
        "Normal frontal chest radiograph with no signs of pneumonia."),
    1: ("chest X-ray radiograph, white patchy lung opacity, pneumonia consolidation",
        "Chest X-ray (radiograph) showing lung opacity or consolidation "
        "consistent with pneumonia."),
}

PER_CLASS = {0: 10, 1: 10}


def main():
    npz = np.load(DATA / "pneumoniamnist_64.npz")
    images = np.concatenate([npz["train_images"], npz["val_images"]])
    labels = np.concatenate([npz["train_labels"].ravel(), npz["val_labels"].ravel()])

    corpus_path = DATA / "corpus.jsonl"
    existing = set()
    with corpus_path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                existing.add(json.loads(line)["id"])

    taken = {k: 0 for k in LABELS}
    out_lines = []
    for i in range(len(labels)):
        label = int(labels[i])
        if taken[label] >= PER_CLASS[label]:
            continue
        entry_id = f"cxr_{label}_{taken[label]}.png"
        if entry_id in existing:
            continue
        arr = images[i]
        if arr.ndim == 2:
            arr = np.stack([arr] * 3, axis=-1)
        Image.fromarray(arr).save(FIGS / entry_id)
        desc, text = LABELS[label]
        out_lines.append(json.dumps({
            "id": entry_id,
            "image": entry_id,
            "text": text,
            "desc": desc,
            "official_caption": False,
            "subcaption": False,
            "source": "PneumoniaMNIST",
        }, ensure_ascii=False))
        taken[label] += 1
        if all(taken[k] >= PER_CLASS[k] for k in PER_CLASS):
            break

    with corpus_path.open("a", encoding="utf-8") as fh:
        for line in out_lines:
            fh.write(line + "\n")
    print(f"added {sum(taken.values())}: {taken}")


if __name__ == "__main__":
    main()
