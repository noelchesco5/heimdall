# Heimdall

Local medical figure RAG chat. Ask a medical question; Heimdall streams an
answer from a local Qwen model via Ollama and attaches the most relevant
figures from a MedICaT-derived corpus, matched by intent + semantic
similarity of your input AND the generated reply.

Runs entirely on-machine. Pure Python stdlib - zero pip dependencies.
Designed to stay light enough for low-RAM hardware (~1 GB total with the
0.5B model loaded).

## Layout

```
app.py                 desktop chat UI (tkinter) with inline thumbnails
core/
  config.py            endpoints, models, thresholds
  llm.py               Ollama client (streaming chat + embeddings)
  intents.py           medical intent gate: symptom/modality keywords -> triage
  retriever.py         embedding index + input/output blended cosine ranking
scripts/
  build_corpus.py      extracts figures from MedICaT release head, pairs text
  ingest.py            embeds corpus -> data/index.json
sema_variant/          forked entry point adding Sema Swahili anchoring
data/
  corpus.jsonl         {id, image, text} retrieval records
  index.json           all-minilm vectors per record
  figures/             MedICaT PNGs
```

## Run

Requires [Ollama](https://ollama.com) with `qwen2.5:0.5b` and `all-minilm`
pulled (or edit `core/config.py`).

```
python scripts/build_corpus.py   # once - fetches figures from MedICaT release
python scripts/ingest.py         # once - builds the vector index
python app.py                    # English mode
python sema_variant/app_sema.py  # Swahili mode (needs qwen2.5:1.5b)
```

## How matching works

1. Intent gate classifies the message into medical intents (symptom,
   severity, imaging modality) using jericho's MEDICAL.md taxonomy.
2. The reply streams from the LLM with triage hints injected.
3. After generation, both your input and the assistant output are embedded;
   scores blend both (`0.4*input + 0.6*output`) against every figure's
   caption/title text. Top 3 above threshold attach to the reply.
4. Click any thumbnail for full size. Emergency phrasing shows a red banner.

## Corpus provenance

Figures come from the official MedICaT release (first ~110 members of
`medicat_release.tar.gz`, fetched via HTTP range requests - no 104 GB
download). Text per figure combines, where available:

- official `s2_caption` (10 sample figures)
- subcaption annotations (`subcaptions_public.jsonl`)
- paper title + abstract via Semantic Scholar (`pdf_hash` = S2 paper id)

MedICaT is research-only / non-commercial; each article keeps its own open
license (see `oa_info` fields upstream).

## Sema variant

`sema_variant/app_sema.py` ports jericho's Sema pipeline (docs/SEMA.md):
Swahili input is resolved offline through the distilled Wiktionary lexicon
(`jericho/data/swahili.distilled.jsonl`, CC BY-SA 4.0) into lemma + gloss
anchor blocks that are prepended to the LLM prompt, and Swahili symptom
keywords feed the same intent gate so figure retrieval works on Swahili
input too. Use the 1.5B model minimum - 0.5B echoes Swahili instead of
answering.

## Models

Chat model choice, evaluation results (incl. why Llama 3.2 1B was rejected),
and switching instructions live in [MODELS.md](MODELS.md).
