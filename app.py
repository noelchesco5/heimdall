import queue
import re
import textwrap
import threading
import tkinter as tk
from collections import deque
from tkinter import font as tkfont

from core import config, intents, lang, llm, retriever

SHOW_RE = re.compile(
    r"^\s*(?:show me|show|display|draw|give me|pictures? of|images? of|photos? of)\s+(?:a|an|the)?\s*",
    re.I,
)


class HeimdallApp:
    def __init__(self, root):
        self.root = root
        root.title("Heimdall - medical figure RAG")
        root.geometry("920x680")
        self.queue = queue.Queue()
        self.photos = []
        self.img_count = 0
        self.index = retriever.load_index()
        self.corpus = {e["id"]: e for e in retriever.load_corpus()}
        self.history = deque(maxlen=config.HISTORY_MESSAGES)
        self.lexicon = None
        self.busy = False

        base = tkfont.nametofont("TkDefaultFont")
        base.configure(size=11)

        self.chat = tk.Text(root, wrap="word", state="disabled", bg="#141821",
                            fg="#e6e9ef", padx=14, pady=12, spacing3=4,
                            insertbackground="#e6e9ef")
        self.chat.pack(fill="both", expand=True, side="top")

        self.chat.tag_configure("user", foreground="#7fb2ff", font=(base.actual("family"), 11, "bold"))
        self.chat.tag_configure("bot", foreground="#59d68a", font=(base.actual("family"), 11, "bold"))
        self.chat.tag_configure("warn", foreground="#ff5f56", font=(base.actual("family"), 11, "bold"))
        self.chat.tag_configure("dim", foreground="#8b93a5")
        self.chat.tag_configure("small", foreground="#aab2c0", font=(base.actual("family"), 9))
        self.chat.tag_configure("figcap", foreground="#c8cfdb", font=(base.actual("family"), 10))

        bottom = tk.Frame(root, bg="#1c2230")
        bottom.pack(fill="x", side="bottom")
        self.entry = tk.Entry(bottom, font=base, bg="#232b3d", fg="#e6e9ef",
                              insertbackground="#e6e9ef", relief="flat")
        self.entry.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self.entry.bind("<Return>", self.send)
        self.send_btn = tk.Button(bottom, text="Send", command=self.send,
                                  bg="#3d6dd6", fg="white", relief="flat", padx=18)
        self.send_btn.pack(side="right", padx=(0, 10), pady=10)

        if not self.index:
            self._sys("Index not found - run: python scripts/ingest.py")
        else:
            self._sys(f"Indexed {len(self.index)} medical figures | model {config.CHAT_MODEL}")

    def _sys(self, msg):
        self.chat.configure(state="normal")
        self.chat.insert("end", msg + "\n", "dim")
        self.chat.configure(state="disabled")

    def _append(self, text, tag=None):
        self.chat.configure(state="normal")
        self.chat.insert("end", text, tag or ())
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def send(self, event=None):
        if self.busy:
            return
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self._append("\nYou: ", "user")
        self._append(text + "\n")
        detected = intents.detect(text)
        self.busy = True
        self.send_btn.configure(state="disabled", text="...")
        threading.Thread(target=self._worker, args=(text, detected), daemon=True).start()

    def _build_messages(self, user_content):
        messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]
        for role, content in self.history:
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_content})
        return messages

    def _worker(self, text, detected):
        try:
            if self.lexicon is None:
                try:
                    self.lexicon = lang.load_lexicon()
                except Exception:
                    self.lexicon = {}
            block = lang.prompt_block(text, self.lexicon) if self.lexicon else ""
            anchored = f"{block}\n---\nUser message (original): {text}" if block else text
            if not block:
                stripped = SHOW_RE.sub("", text).strip()
                if stripped and stripped != text.strip():
                    anchored = "Describe from a medical perspective: " + stripped

            try:
                candidates = retriever.search_input_only(
                    text, detected, self.index, self.corpus)
            except Exception:
                candidates = []

            user_content = anchored
            guidance = intents.guidance(detected)
            if guidance:
                user_content += "\n\n[Triage hints]\n" + guidance
            if candidates:
                lines = [f"- {c['desc']}: {c['caption']}" for c in candidates]
                user_content += ("\n\n" + config.CONTEXT_HEADER + "\n"
                                 + "\n".join(lines))

            messages = self._build_messages(user_content)
            self.queue.put(("start", detected))
            reply = llm.chat_stream(messages, on_token=lambda t: self.queue.put(("token", t)))
            self.queue.put(("done", (text, reply, detected)))
        except Exception as exc:
            self.queue.put(("error", str(exc)))

    def _poll(self):
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "start":
                    if intents.is_emergency(payload):
                        self._append("\nEMERGENCY SIGNS - seek immediate care\n", "warn")
                    self._append("\nHeimdall: ", "bot")
                elif kind == "token":
                    self._append(payload)
                elif kind == "error":
                    self._append("\n[error] " + str(payload) + "\n", "warn")
                    self.busy = False
                    self.send_btn.configure(state="normal", text="Send")
                elif kind == "done":
                    input_text, reply, detected = payload
                    self.history.append(("user", input_text))
                    self.history.append(("assistant", reply))
                    self._attach_figures(input_text, reply, detected)
                    self._append("\n" + config.DISCLAIMER + "\n", "small")
                    self.busy = False
                    self.send_btn.configure(state="normal", text="Send")
        except queue.Empty:
            pass
        self.root.after(40, self._poll)

    def _desc_for(self, entry_id):
        entry = self.corpus.get(entry_id)
        if entry and entry.get("desc"):
            return entry["desc"]
        if entry:
            return entry.get("text", entry_id)[:90]
        return entry_id.rsplit(".", 1)[0].replace("_", " ")

    def _attach_figures(self, input_text, reply, detected):
        try:
            hits = retriever.search(input_text, reply, detected, self.index,
                                    top_k=config.TOP_K + 2)
        except Exception as exc:
            self._append(f"\n[retrieval error] {exc}\n", "warn")
            return
        shown = []
        seen_desc = {}
        for hit in hits:
            desc = self._desc_for(hit["id"])
            if seen_desc.get(desc, 0) >= 2:
                continue
            seen_desc[desc] = seen_desc.get(desc, 0) + 1
            shown.append((hit["id"], desc))
            if len(shown) >= config.TOP_K:
                break

        loaded = []
        for entry_id, desc in shown:
            path = f"{config.FIGURE_DIR}/{entry_id}"
            try:
                photo = tk.PhotoImage(file=path)
            except Exception:
                continue
            loaded.append((entry_id, desc, path, photo))
        if not loaded:
            return

        self._append("\n\nRelated figures:\n", "dim")
        for entry_id, desc, path, photo in loaded:
            factor = max(1, photo.width() // 240)
            thumb = photo.subsample(factor, factor)
            tag = f"img{self.img_count}"
            self.img_count += 1
            self.photos.append((thumb, photo))
            self.chat.configure(state="normal")
            self.chat.image_create("end", image=thumb, padx=8, pady=4)
            self.chat.tag_add(tag, "end-2chars")
            wrapped = "\n".join(textwrap.wrap(desc, width=58)[:3])
            self.chat.insert("end", "\n" + wrapped + "\n", "figcap")
            self.chat.tag_bind(tag, "<Button-1>", lambda e, p=path: self._zoom(p))
            self.chat.configure(state="disabled")
        self.chat.see("end")

    def _zoom(self, path):
        win = tk.Toplevel(self.root)
        win.title(path.split("/")[-1])
        photo = tk.PhotoImage(file=path)
        self.photos.append((photo, photo))
        label = tk.Label(win, image=photo, bg="#141821")
        label.image = photo
        label.pack(padx=8, pady=8)


def main():
    root = tk.Tk()
    app = HeimdallApp(root)
    root.after(40, app._poll)
    root.mainloop()


if __name__ == "__main__":
    main()
