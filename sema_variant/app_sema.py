import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import config
from core import lang
from core import intents_sw
from core.intents import detect as detect_en
from app import HeimdallApp


def lang_detect_sw(text):
    return intents_sw.detect(text)

config.CHAT_MODEL = "qwen2.5:1.5b"


class SemaApp(HeimdallApp):
    def __init__(self, root):
        super().__init__(root)
        root.title("Heimdall Sema - medical figure RAG (Swahili)")
        self.lexicon = lang.load_lexicon()
        if self.lexicon:
            self._sys(f"Sema lexicon preloaded: {len(self.lexicon):,} lemmas | model {config.CHAT_MODEL}")
        else:
            self._sys(f"WARNING: Swahili lexicon not found at {lang.LEXICON_PATH}")

    def _worker(self, text, detected):
        detected = detected + [d for d in lang_detect_sw(text)
                               if d["intent"] not in {x["intent"] for x in detected}]
        super()._worker(text, detected)


def main():
    import tkinter as tk
    root = tk.Tk()
    app = SemaApp(root)
    root.after(40, app._poll)
    root.mainloop()


if __name__ == "__main__":
    main()
