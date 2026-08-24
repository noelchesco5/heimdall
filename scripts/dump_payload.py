"""Replicate _worker's exact message assembly and call chat_stream."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tkinter as tk

import app as appmod
from core import config, intents, lang, llm, retriever

root = tk.Tk()
root.withdraw()
a = appmod.HeimdallApp(root)
root.destroy()

text = "ngozi kavu"
detected = intents.detect(text)

block = lang.prompt_block(text, a.lexicon) if a.lexicon else ""
anchored = f"{block}\n---\nUser message (original): {text}" if block else text
if not block:
    new_text = appmod.rewrite_show_request(text)
    if new_text != text:
        anchored = new_text

candidates = retriever.search_input_only(text, detected, a.index, a.corpus)
user_content = anchored
g = intents.guidance(detected)
if g:
    user_content += "\n\n[Triage hints]\n" + g
if candidates:
    lines = [f"- {c['desc']}: {c['caption']}" for c in candidates]
    user_content += "\n\n" + config.CONTEXT_HEADER + "\n" + "\n".join(lines)

print("=== USER CONTENT ===")
print(user_content)
print("=== chars:", len(user_content))
print("=== REPLY ===")
msgs = [{"role": "system", "content": config.SYSTEM_PROMPT},
        {"role": "user", "content": user_content}]
print(llm.chat_stream(msgs)[:400])
