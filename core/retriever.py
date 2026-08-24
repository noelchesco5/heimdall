import json
import math
from pathlib import Path

from . import config, llm


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def load_corpus():
    path = Path(config.CORPUS_PATH)
    entries = []
    if path.exists():
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    return entries


def build_index(batch_size=32):
    entries = load_corpus()
    index = {}
    for start in range(0, len(entries), batch_size):
        batch = entries[start:start + batch_size]
        vectors = llm.embed([e["text"] for e in batch])
        for e, vec in zip(batch, vectors):
            index[e["id"]] = vec
        print(f"embedded {start + len(batch)}/{len(entries)}")
    Path(config.INDEX_PATH).write_text(json.dumps(index), encoding="utf-8")
    return index


def load_index():
    path = Path(config.INDEX_PATH)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def search(input_text, output_text, intents, index, top_k=None):
    top_k = top_k or config.TOP_K
    input_vec = llm.embed_one(input_text)
    terms = " ".join(i["expansion"] for i in intents)
    output_vec = llm.embed_one(output_text + (" " + terms if terms else ""))
    scored = []
    for entry_id, vec in index.items():
        s_in = _cosine(input_vec, vec)
        s_out = _cosine(output_vec, vec)
        score = config.INPUT_WEIGHT * s_in + config.OUTPUT_WEIGHT * s_out
        scored.append((score, entry_id))
    scored.sort(reverse=True)
    results = []
    for score, entry_id in scored[:top_k]:
        if score < config.SCORE_THRESHOLD:
            continue
        results.append({"id": entry_id, "score": round(score, 4)})
    return results


def search_input_only(input_text, intents, index, corpus, top_k=4):
    top_k = top_k or 4
    terms = " ".join(i["expansion"] for i in intents)
    input_vec = llm.embed_one(input_text + (" " + terms if terms else ""))
    scored = []
    for entry_id, vec in index.items():
        scored.append((_cosine(input_vec, vec), entry_id))
    scored.sort(reverse=True)
    out = []
    for score, entry_id in scored[:top_k]:
        entry = corpus.get(entry_id, {})
        out.append({
            "id": entry_id,
            "score": round(score, 4),
            "desc": entry.get("desc") or entry.get("text", "")[:90],
            "caption": entry.get("text", "")[:220],
        })
    return out
