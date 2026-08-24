import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import config
from core.intents import detect as detect_en
from app import HeimdallApp

import intents_sw
import sema_anchor

config.CHAT_MODEL = "qwen2.5:1.5b"


class SemaApp(HeimdallApp):
    def __init__(self, root):
        super().__init__(root)
        root.title("Heimdall Sema - medical figure RAG (Swahili)")
        self.lexicon = sema_anchor.load_lexicon()
        if self.lexicon:
            self._sys(f"Sema lexicon loaded: {len(self.lexicon):,} lemmas | model {config.CHAT_MODEL}")
        else:
            self._sys(f"WARNING: Swahili lexicon not found at {sema_anchor.LEXICON_PATH}")

    def _worker(self, text, detected):
        detected = detected + [d for d in intents_sw.detect(text)
                               if d["intent"] not in {x["intent"] for x in detected}]
        block = sema_anchor.prompt_block(text, self.lexicon)
        anchored = f"{block}\n---\nUser message (original): {text}" if block else text
        super()._worker(anchored, detected)


def main():
    import tkinter as tk
    root = tk.Tk()
    app = SemaApp(root)
    root.after(40, app._poll)
    root.mainloop()


if __name__ == "__main__":
    main()
