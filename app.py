import queue
import threading
import tkinter as tk
from tkinter import font as tkfont

from core import config, intents, llm, retriever


class HeimdallApp:
    def __init__(self, root):
        self.root = root
        root.title("Heimdall - medical figure RAG")
        root.geometry("920x680")
        self.queue = queue.Queue()
        self.photos = []
        self.img_count = 0
        self.index = retriever.load_index()
        self.busy = False

        base = tkfont.nametofont("TkDefaultFont")
        base.configure(size=11)
        self.font = base

        self.chat = tk.Text(root, wrap="word", state="disabled", bg="#141821",
                            fg="#e6e9ef", padx=14, pady=12, spacing3=4,
                            insertbackground="#e6e9ef")
        self.chat.pack(fill="both", expand=True, side="top")

        self.chat.tag_configure("user", foreground="#7fb2ff", font=(base.actual("family"), 11, "bold"))
        self.chat.tag_configure("bot", foreground="#59d68a", font=(base.actual("family"), 11, "bold"))
        self.chat.tag_configure("warn", foreground="#ff5f56", font=(base.actual("family"), 11, "bold"))
        self.chat.tag_configure("dim", foreground="#8b93a5")
        self.chat.tag_configure("small", foreground="#aab2c0", font=(base.actual("family"), 9))

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

    def _worker(self, text, detected):
        try:
            messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]
            terms = intents.retrieval_terms(detected)
            guidance = intents.guidance(detected)
            user_content = text
            if guidance:
                user_content += "\n\n[Triage hints]\n" + guidance
            messages.append({"role": "user", "content": user_content})
            self.queue.put(("start", detected))
            reply = llm.chat_stream(messages, on_token=lambda t: self.queue.put(("token", t)))
            self.queue.put(("done", (text, reply, detected, terms)))
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
                    input_text, reply, detected, terms = payload
                    self._attach_figures(input_text, reply, detected)
                    self._append("\n" + config.DISCLAIMER + "\n", "small")
                    self.busy = False
                    self.send_btn.configure(state="normal", text="Send")
        except queue.Empty:
            pass
        self.root.after(40, self._poll)

    def _attach_figures(self, input_text, reply, detected):
        try:
            hits = retriever.search(input_text, reply, detected, self.index)
        except Exception as exc:
            self._append(f"\n[retrieval error] {exc}\n", "warn")
            return
        if not hits:
            return
        self._append("\n\nRelated figures:\n", "dim")
        for hit in hits:
            path = f"{config.FIGURE_DIR}/{hit['id']}"
            try:
                photo = tk.PhotoImage(file=path)
            except Exception:
                continue
            factor = max(1, photo.width() // 240)
            thumb = photo.subsample(factor, factor)
            tag = f"img{self.img_count}"
            self.img_count += 1
            self.photos.append((thumb, photo))
            self.chat.configure(state="normal")
            self.chat.image_create("end", image=thumb, padx=8, pady=4)
            self.chat.tag_add(tag, "end-2chars")
            self.chat.insert("end", f"  {hit['id'][:18]}... ({hit['score']})\n", "small")
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
