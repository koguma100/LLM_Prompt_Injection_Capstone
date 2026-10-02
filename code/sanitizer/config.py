import os

# Local Ollama server and the model every LLM call uses
OLLAMA_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "phi3:mini"

# Sentence embedding model for semantic outlier detection
SENTENCE_MODEL = "all-MiniLM-L6-v2"

# Trained BoW models live in code/models/ (train them with code/training/train_bow.py)
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
