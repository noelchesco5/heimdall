# Model notes

Facts recorded from hands-on evaluation (Aug 2026) so nobody re-litigates
this blind. All tests were run against the real Heimdall pipeline
(`scripts/e2e_test.py`, `scripts/bisect_prompt.py`, `scripts/prompt_probe.py`).

## Current model

**`qwen2.5:1.5b`** - set in `core/config.py` (`CHAT_MODEL`). This is the
minimum viable size; `qwen2.5:0.5b` echoes Swahili and produces garbled
answers (see Sema section in README).

Embeddings: `all-minilm` for both corpus ingest and query/reply embedding.

## Llama 3.2 1B: evaluated, rejected

Imported as `llama32b1` from `models/Llama-3.2-1B-Instruct-Q8_0.gguf`
(bartowski Q8_0) via `Modelfile.llama` (`ollama create llama32b1 -f Modelfile.llama`,
temperature 0.4, num_ctx 4096). Note: Ollama rejects some names on create;
`llama32b1` works, `llama3.2-1b` errored with "invalid model name".

Findings, reproducible:

| Test | Result |
|---|---|
| Direct CLI, simple English question | Coherent, good answer |
| Full pipeline (system prompt + Sema anchor + triage hints + injected captions) | Non-deterministic: same input alternates between coherent and degenerate Swahili word-salad loops |
| Sampling fixes: temperature 0.2, repeat_penalty 1.25, top_p 0.8 | No improvement |
| System instruction "respond in English only" | Ignored; one run entered an infinite generation loop until killed |
| Prompt-ingredient bisect (system alone / +hints / +captions / +history / +anchor) | Every ingredient is individually fine at short lengths; degradation comes from the 1B model itself when bilingual anchor content is present |

Root cause: the Sema anchor block legitimately injects Swahili tokens into
the prompt. Qwen 2.5 1.5B handles bilingual grounding; Llama 3.2 **1B**
cannot sustain it and falls into degenerate repetition. This is a capacity
limit, not a bug in our prompts.

Decision: reverted to `qwen2.5:1.5b`. The `llama32b1` Ollama import remains
available for experiments. Untried: `llama3.2:3b` (~2 GB pull) - likely
sufficient capacity, still CPU-friendly.

## How to switch chat model

1. Edit `CHAT_MODEL` in `core/config.py`.
2. Restart `app.py`. No index rebuild needed (embeddings use `all-minilm`,
   independent of the chat model).
3. To import a local GGUF instead of pulling: see `Modelfile.llama`.

## Context budget

`core/llm.py` sends `num_ctx: 2048`. Measured worst-case prompt assembly
(Sema block ~220 chars + 4 caption excerpts ~500 chars + system ~1.2k chars)
is well under budget (~500 tokens), so context overflow is NOT the cause of
any observed degeneration. If you scale injected captions up (more per turn,
longer excerpts), revisit this number.
