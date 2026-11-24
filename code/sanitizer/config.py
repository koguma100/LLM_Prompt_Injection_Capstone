import os

# Ollama server and the model every LLM call uses. Set OLLAMA_URL to use another server (e.g. the llm container
# in docker-compose.yml).
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
LLM_MODEL = "phi3:mini"

# Seconds to wait for each LLM call. Unset, each call uses its own default (30-60 s); a CPU-only server needs longer.
LLM_TIMEOUT = float(os.environ["LLM_TIMEOUT"]) if os.environ.get("LLM_TIMEOUT") else None

# Sentence embedding model for semantic outlier detection
SENTENCE_MODEL = "all-MiniLM-L6-v2"

# Trained models live in code/models/ (train them with code/training/train_bow.py or code/training/train_rf.py)
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")

# Weighted vote: every detector that finds anything adds its weight once, however many matches it had. A sample
# whose votes add up to at least INJECTION_THRESHOLD is predicted to be a prompt injection. Weights come from the
# test results in tests/test_results/ (see meeting_notes.md):
#   - Random Forest: the main learned detector, trusted to decide on its own.
#   - Instruction regex: never flagged a benign sample on the BoW holdout (0/1769), Hugging Face (0/500) or resume
#     (0/74) sets, so it also decides on its own.
#   - Authority regex: fires on benign text almost as often as on injections ("tell me", "print"; 50/1769 benign vs
#     58/631 injections on the holdout), so it needs a second vote to count.
#   - LLM output validation (the answer from the sanitized data looked hijacked): caught 2/27 resume injections and
#     misfired on 1/74 benign resumes. Precise but rare, so it also needs a second vote.
#   - Semantic outliers are switched off in process_single, and BoW was replaced by the Random Forest; both are kept
#     at 0 so results saved with them still load.
DETECTOR_WEIGHTS = {
    "rf_malicious": 1.0,           # Random Forest model
    "instruction_overrides": 1.0,  # regex
    "authority_overrides": 0.5,    # regex
    "llm_validation": 0.5,         # output validation of the answer from the sanitized data
    "outlier_clauses": 0.0,        # semantic outliers (disabled)
    "bow_malicious": 0.0,          # BoW model (retired)
}
INJECTION_THRESHOLD = 1.0

# Early exit: if the cheap detectors' votes (everything but llm_validation) reach SKIP_LLM_THRESHOLD, the LLM stage
# (the two answers and the two output validations) is skipped; the sample is already an injection. The default needs
# the Random Forest and the instruction regex (or more) to agree. Set it to None to always run the LLM stage.
SKIP_LLM_THRESHOLD = 2.0
