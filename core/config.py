OLLAMA_URL = "http://localhost:11434"
CHAT_MODEL = "qwen2.5:1.5b"
EMBED_MODEL = "all-minilm"
DATA_DIR = "data"
INDEX_PATH = "data/index.json"
CORPUS_PATH = "data/corpus.jsonl"
FIGURE_DIR = "data/figures"
TOP_K = 3
SCORE_THRESHOLD = 0.30
OUTPUT_WEIGHT = 0.4
INPUT_WEIGHT = 0.6
HISTORY_MESSAGES = 4
SYSTEM_PROMPT = (
    "You are Heimdall, a careful medical information assistant. "
    "Answer the latest user question directly, briefly, in plain language. "
    "Do not talk about yourself or your nature. You are not a doctor. "
    "Earlier turns are background only - never repeat or summarize them. "
    "If the question suggests an emergency, say to seek immediate care. "
    "When reference figures are provided, describe what they show when relevant. "
    "End with: this is not medical advice."
)
CONTEXT_HEADER = (
    "Reference figures retrieved for this question (caption excerpts):"
)
DISCLAIMER = "This is not medical advice. Please see a doctor for professional guidance."
