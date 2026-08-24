"""Normalize all corpus figures to PNG (tk PhotoImage cannot decode JPEG)."""
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIGS = DATA / "figures"


def main():
    converted = 0
    for f in sorted(FIGS.iterdir()):
        if f.suffix.lower() in (".jpg", ".jpeg"):
            png_path = f.with_suffix(".png")
            if not png_path.exists():
                Image.open(f).convert("RGB").save(png_path, "PNG")
                converted += 1
            f.unlink()

    corpus = DATA / "corpus.jsonl"
    lines = []
    for raw in corpus.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        entry = json.loads(raw)
        img = entry["image"]
        if img.lower().endswith((".jpg", ".jpeg")):
            new_id = Path(img).with_suffix(".png").name
            entry["id"] = new_id
            entry["image"] = new_id
        lines.append(json.dumps(entry, ensure_ascii=False))
    corpus.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"converted {converted} jpgs to png; corpus rewritten ({len(lines)} entries)")


if __name__ == "__main__":
    main()
