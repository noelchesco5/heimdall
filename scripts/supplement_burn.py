"""Download clinical burn photographs from Wikimedia Commons (CC-licensed)
and append corpus entries. Files are fetched at 640px width via
Special:FilePath and converted to PNG for tkinter.
"""
import json
import re
import time
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIGS = DATA / "figures"

# title on Commons -> short natural description
FILES = {
    "2nd Degree Burn Blisters on Finger 01.jpg":
        "second degree burn with clear fluid blisters on a finger",
    "2nd Degree Burn Blisters on Finger 02.jpg":
        "second degree burn blister on finger, red painful skin",
    "Brûlure au premier et second degré.jpg":
        "first and second degree burn, red and blistered skin",
    "Deep2nd body.jpg":
        "deep second degree burn wound on the body, mottled damaged skin",
    "Burn to scalp caused by an unmanned ariel vehicle stalking a 45 year old female.jpg":
        "burn wound on the scalp, damaged skin on the head",
    "Hot Glue Burn.jpg":
        "minor contact burn on skin from hot glue, small red burn mark",
    "G-34 burn on knee - DPLA - dc4d696427fa7e1d6237e6b8cef86ced.jpg":
        "burn injury on the knee, healing burn scar on joint skin",
    "Cultured epithelial autograft in burn treatment..jpg":
        "cultured epithelial autograft graft used in burn treatment",
}


def fetch(title: str) -> Image.Image:
    from urllib.parse import quote
    url = ("https://commons.wikimedia.org/wiki/Special:FilePath/"
           + quote(title) + "?width=640")
    req = urllib.request.Request(url, headers={"User-Agent": "heimdall-corpus/1.0"})
    import io
    raw = urllib.request.urlopen(req, timeout=60).read()
    return Image.open(io.BytesIO(raw)).convert("RGB")


def main():
    corpus_path = DATA / "corpus.jsonl"
    existing = set()
    with corpus_path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                existing.add(json.loads(line)["id"])

    added = 0
    out_lines = []
    for idx, (title, desc) in enumerate(FILES.items()):
        entry_id = f"burn_{idx}.png"
        if entry_id in existing:
            continue
        time.sleep(4)
        try:
            img = fetch(title)
        except Exception as exc:
            print(f"skip '{title}': {exc}")
            continue
        img.save(FIGS / entry_id)
        clean = re.sub(r"\.(jpg|jpeg|png)$", "", title, flags=re.I)
        text = (f"Clinical photograph of a burn injury: {clean}. "
                f"Burn wound on human skin.")
        out_lines.append(json.dumps({
            "id": entry_id,
            "image": entry_id,
            "text": text,
            "desc": f"burn wound, {desc}",
            "official_caption": False,
            "subcaption": False,
            "source": "Wikimedia Commons (CC)",
        }, ensure_ascii=False))
        added += 1

    with corpus_path.open("a", encoding="utf-8") as fh:
        for line in out_lines:
            fh.write(line + "\n")
    print(f"added {added} burn figures")


if __name__ == "__main__":
    main()
