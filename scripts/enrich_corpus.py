"""Derive a short natural-language description for each corpus entry."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "corpus.jsonl"

FIG_PREFIX = re.compile(r"^Figure\s*\d+[\.\:]?\s*", re.I)


def derive_desc(entry):
    src = entry.get("source", "")
    text = entry.get("text", "")
    if src in ("HAM10000", "DermaMNIST"):
        idx = text.find("Diagnosis: ")
        if idx >= 0:
            desc = text[idx + len("Diagnosis: "):]
            desc = desc.split(". Skin spot")[0].split(", skin spot")[0].rstrip(". ")
            return desc[:90]
    seg = text.split(" | ")[0].strip()
    seg = FIG_PREFIX.sub("", seg)
    if len(seg) > 110:
        cut = seg[:110]
        stop = max(cut.rfind(". "), cut.rfind(", "), cut.rfind("; "))
        if stop > 40:
            seg = cut[:stop]
        else:
            seg = cut.rsplit(" ", 1)[0] + "..."
    return seg


def main():
    lines = []
    with CORPUS.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            entry["desc"] = derive_desc(entry)
            lines.append(json.dumps(entry, ensure_ascii=False))
    CORPUS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"descriptions written for {len(lines)} entries")


if __name__ == "__main__":
    main()
