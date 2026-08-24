OLLAMA_URL = "http://localhost:11434"
CHAT_MODEL = "qwen2.5:1.5b"
EMBED_MODEL = "all-minilm"
DATA_DIR = "data"
INDEX_PATH = "data/index.json"
CORPUS_PATH = "data/corpus.jsonl"
FIGURE_DIR = "data/figures"
TOP_K = 3
SCORE_THRESHOLD = 0.26
OUTPUT_WEIGHT = 0.4
INPUT_WEIGHT = 0.6
HISTORY_MESSAGES = 4
SYSTEM_PROMPT = (
    "You are Heimdall, a medical information assistant. "
    "Answer ONLY the user's latest question in at most 4 short plain-language sentences. "
    "Do not talk about yourself. Do not repeat or summarize earlier turns. "
    "Reference figure captions are BACKGROUND ONLY - never list or restate them, "
    "and never invent details about them. "
    "If the question suggests an emergency, say to seek immediate care. "
    "The app displays medical figure images to the user automatically; "
    "your job is only to explain the medical topic in words. "
    "Never refuse - if unsure, give general medical information about the topic asked."
)
CONTEXT_HEADER = (
    "Background reference material (do not restate):"
)
DISCLAIMER = "This is not medical advice. Please see a doctor for professional guidance."
