"""Build heimdall's medical figure corpus from the MedICaT release.

Sources stitched together (no 104 GB download needed):
  1. Figures extracted from the head of medicat_release.tar.gz via HTTP
     range requests (figures are the first members of the archive).
  2. Official captions for the repo's sample/ figures (sample.jsonl).
  3. Subcaption text for annotated compound figures (subcaptions_public.jsonl).
  4. Paper title + abstract per figure via Semantic Scholar (pdf_hash is a
     valid S2 paper id).

Output: data/corpus.jsonl  {"image": <filename>, "text": <str>, ...}
        data/figures/<filename>.png
"""
import io
import json
import sys
import time
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIGS = DATA / "figures"
MEDICAT = ROOT.parent / "medicat"
TAR_URL = "https://ai2-s2-medicat.s3.us-west-2.amazonaws.com/2020-10-05/medicat_release.tar.gz"

TARGET_FIGURES = 110
CHUNK_BYTES = 4 * 1024 * 1024


def stream_tar_figures(max_bytes: int):
    """Yield (name, bytes) for each figure member in the first max_bytes of the gz."""
    local = DATA / "tar_head.bin"
    if local.exists() and local.stat().st_size >= max_bytes:
        compressed = local.read_bytes()[:max_bytes]
    else:
        req = urllib.request.Request(TAR_URL, headers={"Range": f"bytes=0-{max_bytes - 1}"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            compressed = resp.read()
        local.write_bytes(compressed)
    print(f"using {len(compressed):,} compressed bytes", file=sys.stderr)
    dec = zlib.decompressobj(31)
    data = dec.decompress(compressed)
    pos, count = 0, 0
    while pos + 512 <= len(data):
        hdr = data[pos:pos + 512]
        name = hdr[:100].split(b"\0")[0].decode("ascii", "replace")
        if not name:
            break
        size = int(hdr[124:136].replace(b"\0", b" ").strip() or b"0", 8)
        body_start = pos + 512
        if name.endswith(".png") and size > 0 and body_start + size <= len(data):
            yield name.split("/")[-1], data[body_start:body_start + size]
            count += 1
            if count >= TARGET_FIGURES:
                return
        pos = body_start + ((size + 511) // 512) * 512


def load_jsonl(path: Path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def s2_batch(hashes, cache):
    todo = [h for h in hashes if h not in cache]
    if not todo:
        return
    for attempt in range(8):
        body = json.dumps({"ids": todo}).encode("utf-8")
        req = urllib.request.Request(
            "https://api.semanticscholar.org/graph/v1/paper/batch?fields=title,abstract",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                results = json.load(resp)
            break
        except urllib.error.HTTPError as exc:
            wait = 10 * (attempt + 1)
            print(f"  batch {exc.code}, retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
        except Exception as exc:
            print(f"  batch error: {exc}", file=sys.stderr)
            time.sleep(15)
    else:
        results = [None] * len(todo)
    for h, info in zip(todo, results):
        cache[h] = info or {"title": "", "abstract": None}
    time.sleep(3)


def main():
    FIGS.mkdir(parents=True, exist_ok=True)

    official = {}
    for row in load_jsonl(MEDICAT / "sample" / "sample.jsonl"):
        key = f"{row['pdf_hash']}_{row['fig_uri']}"
        official[key] = row["s2_caption"]

    subcaps = {}
    subcap_path = DATA / "subcaptions_public.jsonl"
    if not subcap_path.exists():
        url = "https://ai2-s2-medicat.s3.us-west-2.amazonaws.com/2020-10-05/subcaptions_public.jsonl"
        urllib.request.urlretrieve(url, subcap_path)
    for row in load_jsonl(subcap_path):
        key = f"{row['pdf_hash']}_{row['fig_uri']}"
        subcaps[key] = row["text"]

    papers = {}
    cache_path = DATA / "s2_cache.json"
    if cache_path.exists():
        papers = json.loads(cache_path.read_text(encoding="utf-8"))
    entries = []
    seen_hashes = set()

    staged = []
    for fname, blob in stream_tar_figures(96 * 1024 * 1024):
        out = FIGS / fname
        if not out.exists():
            out.write_bytes(blob)
        pdf_hash = fname.rsplit("_", 1)[0]
        staged.append((fname, pdf_hash))
        if len(staged) >= TARGET_FIGURES:
            break

    s2_batch(sorted({h for _, h in staged}), papers)
    cache_path.write_text(json.dumps(papers), encoding="utf-8")

    for fname, pdf_hash in staged:
        parts = [p for p in (official.get(fname), subcaps.get(fname)) if p]
        info = papers.get(pdf_hash) or {}
        title, abstract = info.get("title") or "", info.get("abstract")
        if title:
            parts.append(title)
        if abstract:
            parts.append(abstract)
        if not parts:
            continue
        seen_hashes.add(pdf_hash)
        entries.append({
            "id": fname,
            "image": fname,
            "text": " | ".join(parts),
            "official_caption": bool(official.get(fname)),
            "subcaption": bool(subcaps.get(fname)),
        })

    with (DATA / "corpus.jsonl").open("w", encoding="utf-8") as fh:
        for e in entries:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"corpus entries: {len(entries)} from {len(seen_hashes)} papers")
    print(f"official captions: {sum(e['official_caption'] for e in entries)}, "
          f"subcaptions: {sum(e['subcaption'] for e in entries)}, "
          f"title-only: {len(entries) - sum(e['official_caption'] or e['subcaption'] for e in entries)}")


if __name__ == "__main__":
    main()
