import sys

sys.path.insert(0, ".")
from core import llm
from core.config import SYSTEM_PROMPT as sysprompt_full

SHORT = ("You are Heimdall, a helpful medical assistant. Answer briefly in simple words. "
         "You are not a doctor. Figures are shown separately by the app.")

ctx = ("Background reference material (do not restate): "
       "[1] Chest X-ray radiograph showing clear lung fields, normal study.")


def go(sys_p, user):
    msgs = [{"role": "system", "content": sys_p}, {"role": "user", "content": user}]
    return llm.chat_stream(msgs)[:260].replace("\n", " ")


print("V1 short-sys plain:", go(SHORT, "What does a burn look like?"))
print()
print("V2 short-sys+ctx  :", go(SHORT, ctx + " --- Question: show me a chest x-ray"))
print()
print("V3 full-sys plain :", go(sysprompt_full, "What does a burn look like?"))
