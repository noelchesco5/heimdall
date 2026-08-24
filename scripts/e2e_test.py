"""Headless end-to-end test: drives the real HeimdallApp through a question
list, pumps the Tk loop, and prints transcripts with figure-attach counts.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tkinter as tk

from app import HeimdallApp

CASES = [
    ("ngozi kavu", "swahili dry skin"),
    ("dry itchy skin rash", "skin -> derm figures"),
    ("what does a brain tumor look like on mri", "brain MRI figure"),
    ("show me a chest x-ray", "answers x-ray topic, not previous"),
    ("dark mole that changed shape", "melanoma figures, no refusal"),
    ("red itchy skin rash with blisters", "blister/skin figures"),
    ("stomach ulcer vs sore", "answers ulcer vs sore"),
    ("colonoscopy images", "endoscopy figures"),
    ("skin cancer pictures", "melanoma figures"),
    ("fever in a child", "then next q must not mention fever"),
    ("what causes gout", "no fever mention - lag check"),
]

SETTLE_SECONDS = 3


def run():
    only = sys.argv[1:]
    root = tk.Tk()
    root.withdraw()
    app = HeimdallApp(root)
    root.update()

    results = []
    for text, expectation in CASES:
        if only and not any(o.lower() in text.lower() for o in only):
            continue
        before_photos = len(app.photos)
        app.entry.delete(0, "end")
        app.entry.insert(0, text)
        app.send()
        deadline = time.time() + 90
        while time.time() < deadline:
            app._poll()
            root.update()
            if not app.busy and app.queue.empty():
                break
            time.sleep(0.02)
        time.sleep(SETTLE_SECONDS)
        for _ in range(20):
            root.update()
            time.sleep(0.01)

        transcript = app.chat.get("1.0", "end")
        marker = f"You: {text}"
        idx = transcript.rfind(marker)
        turn = transcript[idx + len(marker):] if idx >= 0 else "(turn not found)"
        new_photos = len(app.photos) - before_photos
        results.append((text, expectation, turn.strip(), new_photos))
        print("=" * 78)
        print(f"Q: {text}   [{expectation}]   figures_attached={new_photos}")
        print(turn.strip()[:900])
        print()

    print("#" * 78)
    print("LAG CHECK: does each reply mention its own topic?")
    checks = [
        ("chest x-ray", "x-ray"),
        ("mole", "mole"),
        ("ulcer", "ulcer"),
        ("colonoscopy", "colonoscopy"),
        ("gout", "gout"),
    ]
    for text, keyword in checks:
        for i, (q, _, turn, _) in enumerate(results):
            if text.split()[0] in q.lower():
                ok = keyword in turn.lower()
                print(f"  {'PASS' if ok else 'FAIL'}  '{q}' mentions '{keyword}': {ok}")
                break

    root.destroy()


if __name__ == "__main__":
    run()
