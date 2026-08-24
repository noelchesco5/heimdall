"""Extract DermaMNIST figures missing from the HAM10000 shard.

DermaMNIST classes: 0 actinic keratosis, 1 basal cell carcinoma,
2 benign keratosis, 3 dermatofibroma, 4 melanoma, 5 nevus,
6 vascular lesion. The HAM shard supplied classes 2/3/4/5 only, so we
top up 0/1/6 plus extra nevi for balance.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIGS = DATA / "figures"

LABELS = {
    0: "actinic keratosis, rough scaly red-brown patch on sun-exposed skin, precancerous",
    1: "basal cell carcinoma, pearly waxy skin bump with visible vessels, common skin cancer",
    6: "vascular lesion, cherry angioma, red purple skin spot from dilated blood vessels",
    5: "melanocytic nevus, common mole, brown skin spot",
}

PER_CLASS = {0: 8, 1: 8, 6: 8, 5: 12}


def main():
    npz = np.load(DATA / "dermamnist_64.npz")
    train_x = npz["train_images"]
    train_y = npz["train_labels"].ravel()
    val_x = npz["val_images"]
    val_y = npz["val_labels"].ravel()
    images = np.concatenate([train_x, val_x])
    labels = np.concatenate([train_y, val_y])

    corpus_path = DATA / "corpus.jsonl"
    existing = set()
    with corpus_path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                existing.add(json.loads(line)["id"])

    taken = {k: 0 for k in LABELS}
    added = 0
    out_lines = []
    for i in range(len(labels)):
        label = int(labels[i])
        if label not in PER_CLASS or taken[label] >= PER_CLASS[label]:
            continue
        entry_id = f"derma_{label}_{taken[label]}.png"
        if entry_id in existing:
            continue
        Image.fromarray(images[i]).save(FIGS / entry_id)
        dx = LABELS[label]
        text = (f"Clinical photograph of a skin lesion (dermatology). "
                f"Diagnosis: {dx}. Skin spot on a patient.")
        out_lines.append(json.dumps({
            "id": entry_id,
            "image": entry_id,
            "text": text,
            "official_caption": False,
            "subcaption": False,
            "source": "DermaMNIST",
        }, ensure_ascii=False))
        taken[label] += 1
        added += 1
        if all(taken[k] >= PER_CLASS[k] for k in PER_CLASS):
            break

    with corpus_path.open("a", encoding="utf-8") as fh:
        for line in out_lines:
            fh.write(line + "\n")
    print(f"added {added}: {taken}")


if __name__ == "__main__":
    main()
