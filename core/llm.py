import json
import urllib.request

from . import config


def _post(path: str, payload: dict, timeout: int = 120):
    req = urllib.request.Request(
        config.OLLAMA_URL + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return urllib.request.urlopen(req, timeout=timeout)


def embed(texts):
    body = json.dumps({"model": config.EMBED_MODEL, "input": texts}).encode("utf-8")
    req = urllib.request.Request(
        config.OLLAMA_URL + "/api/embed",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)["embeddings"]


def embed_one(text: str):
    return embed([text])[0]


def chat_stream(messages, model=None, on_token=None, options=None):
    opts = {"num_ctx": 2048}
    if options:
        opts.update(options)
    payload = {
        "model": model or config.CHAT_MODEL,
        "messages": messages,
        "stream": True,
        "options": opts,
    }
    chunks = []
    with _post("/api/chat", payload, timeout=300) as resp:
        for line in resp:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            token = obj.get("message", {}).get("content", "")
            if token:
                chunks.append(token)
                if on_token:
                    on_token(token)
            if obj.get("done"):
                break
    return "".join(chunks)
