"""Supplement the corpus with labeled dermatology figures from HAM10000.

Reads one parquet shard (image bytes + int label), extracts a balanced
sample, writes JPEGs into data/figures/ and appends corpus entries whose
text carries the diagnosis in clinical and plain language so caption-based
retrieval can match skin questions.
"""
import io
import json
import sys
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIGS = DATA / "figures"

LABELS = {
    0: "actinic keratosis or squamous cell carcinoma in situ, scaly red rough patch on sun-damaged skin",
    1: "basal cell carcinoma, pearly or waxy skin bump that may bleed, common skin cancer",
    2: "benign keratosis, rough wart-like or scaly brown skin growth",
    3: "dermatofibroma, firm small brown skin nodule, benign",
    4: "melanoma, malignant dark irregular mole, serious skin cancer",
    5: "melanocytic nevus, ordinary mole, brown or black skin spot",
    6: "vascular lesion, angioma, red or purple skin spot from blood vessels",
}

PER_CLASS = 8


def main():
    shard = DATA / "ham_shard0.parquet"
    if not shard.exists():
        raise SystemExit("download data/ham_shard0.parquet first")

    pf = pq.ParquetFile(shard)
    counts = {k: 0 for k in LABELS}
    added = 0
    corpus_path = DATA / "corpus.jsonl"
    existing_ids = set()
    if corpus_path.exists():
        with corpus_path.open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    existing_ids.add(json.loads(line)["id"])

    rows_needed = PER_CLASS * len(LABELS)
    batch = pf.iter_batches(batch_size=256)
    out_lines = []
    for chunk in batch:
        if added >= rows_needed:
            break
        images = chunk.column("image")
        labels = chunk.column("label").to_pylist()
        for i in range(len(images)):
            label = labels[i]
            if counts[label] >= PER_CLASS:
                continue
            payload = images[i]["bytes"].as_py()
            name = f"ham_{label}_{counts[label]}.jpg"
            path = FIGS / name
            path.write_bytes(payload)
            counts[label] += 1
            entry_id = f"ham_{label}_{counts[label] - 1}.jpg"
            if entry_id not in existing_ids:
                dx = LABELS[label]
                text = f"Clinical photograph of a skin lesion (dermatology). Diagnosis: {dx}."
                out_lines.append(json.dumps({
                    "id": entry_id,
                    "image": entry_id,
                    "text": text,
                    "official_caption": False,
                    "subcaption": False,
                    "source": "HAM10000",
                }, ensure_ascii=False))
                added += 1
            if added >= rows_needed:
                break

    with corpus_path.open("a", encoding="utf-8") as fh:
        for line in out_lines:
            fh.write(line + "\n")
    print(f"added {added} skin entries: {counts}")


if __name__ == "__main__":
    main()
