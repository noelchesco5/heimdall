import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import retriever

if __name__ == "__main__":
    entries = retriever.load_corpus()
    if not entries:
        raise SystemExit("no corpus: run scripts/build_corpus.py first")
    print(f"corpus entries: {len(entries)}")
    retriever.build_index()
