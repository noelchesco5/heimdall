"""Bisect which app-side prompt ingredient breaks llama32b1."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from collections import deque

from core import config, intents, lang, llm, retriever

ROOT = Path(__file__).resolve().parents[1]
lexicon = lang.load_lexicon(ROOT.parent.parent / "jericho" / "data" / "swahili.distilled.jsonl")

INDEX = json.loads((ROOT / "data" / "index.json").read_text(encoding="utf-8"))
CORPUS = {e["id"]: e for e in
          (json.loads(l) for l in (ROOT / "data" / "corpus.jsonl").open(encoding="utf-8") if l.strip())}


def build_user_content(text, use_ctx=True, use_hints=True):
    parts = [text]
    if use_hints:
        g = intents.guidance(intents.detect(text))
        if g:
            parts.append(f"[Triage hints]\n{g}")
    if use_ctx:
        cands = retriever.search_input_only(text, intents.detect(text), INDEX, CORPUS)
        lines = [f"[{i+1}] {c.get('desc') or c['text'][:140]}"
                 for i, c in enumerate(cands[:4])]
        if lines:
            parts.append(config.CONTEXT_HEADER + "\n" + "\n".join(lines))
    return "\n".join(parts)


def go(label, text, hist=None, use_ctx=True, use_hints=True, anchor=False):
    msgs = [{"role": "system", "content": config.SYSTEM_PROMPT}]
    for role, content in (hist or []):
        msgs.append({"role": role, "content": content})
    u = build_user_content(text, use_ctx, use_hints)
    if anchor:
        block = lang.prompt_block(text, lexicon)
        if block:
            u = f"{block}\n---\nUser message (original): {text}"
    msgs.append({"role": "user", "content": u})
    out = llm.chat_stream(msgs)[:240].replace("\n", " ")
    print(f"{label}: {out}\n")


go("A text-only        ", "what does a burn look like", use_ctx=False, use_hints=False)
go("B +triage          ", "what does a burn look like", use_ctx=False, use_hints=True)
go("C +context         ", "what does a burn look like", use_ctx=True, use_hints=True)
go("D C+history        ", "show me a chest x-ray",
   hist=[("user", "what does a burn look like"),
         ("assistant", "A burn appears as red, blistered damaged skin.")])
go("E swahili+anchor   ", "ngozi kavu", use_ctx=True, use_hints=True, anchor=True)
