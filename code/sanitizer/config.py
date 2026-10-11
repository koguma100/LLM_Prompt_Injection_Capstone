import os

# Ollama server and the model every LLM call uses. Set OLLAMA_URL to use another server (e.g. the llm container
# in docker-compose.yml).
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
LLM_MODEL = "phi3:mini"

# Seconds to wait for each LLM call. Unset, each call uses its own default (30-60 s); a CPU-only server needs longer.
LLM_TIMEOUT = float(os.environ["LLM_TIMEOUT"]) if os.environ.get("LLM_TIMEOUT") else None

# Sentence embedding model for semantic outlier detection
SENTENCE_MODEL = "all-MiniLM-L6-v2"

# Trained BoW models live in code/models/ (train them with code/training/train_bow.py)
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
