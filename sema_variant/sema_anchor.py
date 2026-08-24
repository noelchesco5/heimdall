import json
from pathlib import Path

LEXICON_PATH = Path(__file__).resolve().parents[2] / "jericho" / "data" / "swahili.distilled.jsonl"

PREFIXES = ["kwa", "ku", "me", "na", "ta", "li", "wa", "ni", "hu", "ji", "pa", "ki", "vi", "m"]

STOPWORDS = {"na", "ya", "za", "wa", "kwa", "ni", "ka", "cha", "la", "pa", "mu",
             "nina", "una", "ana", "tuna", "mnа", "wako", "yangu", "zangu", "hii", "hiyo", "kama"}

_lexicon = None


def load_lexicon(path=None):
    global _lexicon
    if _lexicon is not None and path is None:
        return _lexicon
    p = Path(path) if path else LEXICON_PATH
    lex = {}
    if p.exists():
        with p.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                lex[row["w"].lower()] = {"pos": row.get("p", ""), "glosses": row.get("g", [])}
    _lexicon = lex
    return lex


def resolve(word, lex):
    w = word.lower()
    if w in lex:
        return word.lower(), lex[w]
    for i in range(len(PREFIXES)):
        for pre in PREFIXES:
            stem = w[len(pre):] if w.startswith(pre) else ""
            if stem and len(stem) >= 3 and stem in lex:
                return stem, lex[stem]
    return None, None


def tidy_gloss(glosses):
    out = []
    for g in glosses[:2]:
        g = g.strip()
        if ";" in g:
            g = g.split(";")[0].strip()
        out.append(g)
    return ", ".join(out)


def prompt_block(text, lex=None):
    lex = lex or load_lexicon()
    resolved_lines = []
    unresolved = []
    tokens = "".join(ch if ch.isalpha() or ch in "'-" else " " for ch in text).split()
    for tok in tokens:
        if tok.lower() in STOPWORDS:
            continue
        stem, entry = resolve(tok, lex)
        if entry is None:
            unresolved.append(tok)
            continue
        gloss = tidy_gloss(entry["glosses"])
        pos = entry["pos"]
        resolved_lines.append(f"{tok} -> {stem} ({pos}): '{gloss}'")
    if not resolved_lines and not unresolved:
        return ""
    parts = []
    if resolved_lines:
        parts.append("[SEMANTIC ANCHORS - the user's Swahili words resolved offline to English]")
        parts.extend(resolved_lines)
    if unresolved:
        parts.append("unresolved: " + " ".join(unresolved))
    parts.append("Use these anchors to understand the original message below. Reply helpfully.")
    return "\n".join(parts)
