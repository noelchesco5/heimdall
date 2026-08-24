OLLAMA_URL = "http://localhost:11434"
CHAT_MODEL = "qwen2.5:0.5b"
EMBED_MODEL = "all-minilm"
DATA_DIR = "data"
INDEX_PATH = "data/index.json"
CORPUS_PATH = "data/corpus.jsonl"
FIGURE_DIR = "data/figures"
TOP_K = 3
SCORE_THRESHOLD = 0.30
OUTPUT_WEIGHT = 0.6
INPUT_WEIGHT = 0.4
SYSTEM_PROMPT = (
    "You are Heimdall, a careful medical information assistant. "
    "Answer briefly and factually in plain language. You are not a doctor. "
    "If the question suggests an emergency, tell the user to seek immediate care. "
    "When reference figures are provided, describe what they show when relevant "
    "and you may refer to them naturally. "
    "Always remind the user this is not medical advice."
)
CONTEXT_HEADER = (
    "Reference figures retrieved for this question (caption excerpts):"
)
DISCLAIMER = "This is not medical advice. Please see a doctor for professional guidance."
