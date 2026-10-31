# Sanitizing Inputs to Protect LLMs Against Prompt Injection Attacks

## Project summary

Researching and testing sanitization techniques for mitigated prompt injections through poisoned data assuming trusted user prompts.

In positions where users – researchers, professors, and recruiters – take in large amounts of data for LLM analysis, prompt injections can stay hidden among a breadth of benign data. Our solution gives the user trust that the data they provide an LLM for processing will be sanitized of any prompt injections that could compromise internal systems.

## Installation

### Prerequisites

- Python 3.10 or newer
- [Ollama](https://ollama.com), running locally, with the `phi3:mini` model (to run the web app in containers instead, see [Self-hosting](#self-hosting))

The Python packages are listed in `code/requirements.txt`:

    requests, numpy, scipy      HTTP calls to Ollama, math, entropy
    nltk                        sentence splitting for redaction
    sentence-transformers       clause embeddings for semantic outlier detection
    scikit-learn                Bag-of-Words classifier and evaluation metrics
    confusables                 homoglyph mapping for text normalization
    matplotlib                  confusion matrix and result plots
    Flask                       web app
    pypdf, python-docx, openpyxl  reading uploaded PDF, Word and Excel files
    pandas, datasets            BoW training and dataset generation
    pytest                      unit tests

### Installation Steps

From the `code/` directory, install the dependencies and this project's packages:

    pip install -r requirements.txt

Download the sentence tokenizer that redaction uses:

    python -m nltk.downloader punkt punkt_tab

Pull the model the pipeline calls (to use a different one, change `LLM_MODEL` in `code/sanitizer/config.py`):

    ollama pull phi3:mini

Turn off Ollama's prompt cache. By default its model server keeps every processed prompt in RAM, up to 8 GB, and long evaluation runs fill it until the machine runs out of memory and the model is killed. The evaluation never reuses a prompt, so nothing is lost. On Linux, run `sudo systemctl edit ollama`, add the lines below, and then run `sudo systemctl restart ollama`:

    [Service]
    Environment="LLAMA_ARG_CACHE_RAM=0"

`journalctl -u ollama | grep "prompt cache"` should then show "prompt cache is disabled".

The trained BoW models and the training datasets are not committed. Before running the engine, regenerate them:

1. Build the injection detector dataset by following [code/dataset-generation/README.md](code/dataset-generation/README.md), then save it as `code/training/injection_detector_datasetv2.csv`.
2. From `code/`, run `python training/train_bow.py`. It trains both BoW models and saves them to `code/models/` (see `--help` for the dataset version and model options).

### Running

From the `code/` directory:

    python -m evaluation.run_eval   # batch evaluation; stats and plots go to code/results/
    python -m webapp                # web app at http://127.0.0.1:5000
    pytest                          # unit tests
    python ../deploy/smoke_test.py http://127.0.0.1:5000   # smoke test a running web app

`run_eval` evaluates the `resumes_half_pi` sample set with a hiring question by default. `--samples` takes a sample set name (the CSVs in `code/evaluation/data/`; `--help` lists them) or the path to any CSV with `text` and `label` columns (1 = prompt injection, 0 = benign), and `--prompt` changes the question. For example, to evaluate the BoW training dataset:

    python -m evaluation.run_eval --samples training/injection_detector_datasetv2.csv --holdout --limit 500 --quiet

Each sample takes about 10 seconds (four LLM calls), so a whole 12,000-row training CSV would take over a day:

- `--limit N` evaluates a random subset of N samples (`--seed` picks a different subset)
- `--holdout` keeps only the 20% of rows `train_bow.py` held out from training, so the BoW model isn't scored on text it was trained on. Use it with the CSV the current models were trained on.
- `--quiet` prints one progress line per sample, with an estimate of the time left, instead of the full report
- `--resume` continues a run that stopped: rerun the same command with `--resume` and it skips the samples already in `predictions.csv`

If Ollama goes down mid-run (for example when the machine runs out of memory and the model process is killed), `run_eval` waits for it to come back for up to `--wait` minutes (default 10) and retries the sample. If it stays down, or you press Ctrl+C, the run stops and still writes the stats for the samples it finished.

Results go to `code/results/<sample set name>/` (or `--out`): `confusion_matrix.png`, `performance_stats.txt` (accuracy, precision, recall, F1), `false_positives.txt`, `false_negatives.txt`, `sanitization_fail_rates.png`, and `predictions.csv`, which has one row per sample and is written as the run goes.

The web app runs with debug mode off. Set `FLASK_DEBUG=1` to turn on the debugger and auto-reload while developing.

### Code layout

    code/
    ├── sanitizer/           # detection, sanitization and LLM pipeline (importable package); settings in config.py
    │   └── detection/       # regex, semantic outlier, BoW, Random Forest and Base64 detectors
    ├── webapp/              # Flask web app
    ├── evaluation/          # batch evaluation (run_eval.py), sample sets (data/), Hugging Face queries
    ├── training/            # BoW and Random Forest training (train_bow.py, train_rf.py)
    ├── dataset-generation/  # builds the injection detector dataset
    ├── tests/               # pytest unit tests
    ├── models/              # trained models (not committed)
    ├── results/             # evaluation outputs (not committed)
    └── legacy/              # unused older code, kept for reference

## Self-hosting

Run the web app on your own machine or server. Either way, you need the trained BoW models in `code/models/`: train them with the [installation steps](#installation-steps) or copy them from another machine.

### With Docker (recommended)

This runs two containers: the web app (`code/Dockerfile`) and an Ollama server with `phi3:mini` built in (`llm/Dockerfile`). You need Docker with Compose and about 4 GB of free memory. The first build also downloads PyTorch and the 2 GB model, so it takes a while. Python is only needed to train the models and run the smoke test.

1. Get the code and put the trained models in `code/models/`. The image build stops if they are missing. The image installs scikit-learn 1.9.1 and models saved by another version may not load, so run `pip install scikit-learn==1.9.1` before training.
2. From the repository root, build and start the containers:

       docker compose up -d --build

3. Open http://localhost:8000.
4. Check that it works. The smoke test checks each page and form, then runs one experiment through the LLM with every mitigation on. It saves a draft and deletes it again, so saved experiments are left as they were. Add `--quick` to skip the LLM run, which can take a few minutes on a CPU-only machine:

       python deploy/smoke_test.py http://localhost:8000

If a run reports that it could not reach the LLM just after starting, the model may still be loading; wait a minute and try again.

To manage it, from the repository root:

    docker compose logs -f web                                  # watch the web app's logs
    docker compose down                                         # stop; saved experiments are kept
    git pull && docker compose up -d --build                    # update to the latest code
    docker compose cp web:/data/experiments.db ./backup.db      # back up saved experiments

Saved experiments are on the `experiments` Docker volume. They survive rebuilds and `docker compose down`, but `docker compose down -v` deletes them.

To use the Ollama already running on your machine instead of the `llm` container (with Docker Desktop, in a Bash-style shell; in PowerShell, set `$env:OLLAMA_URL` first):

    OLLAMA_URL=http://host.docker.internal:11434/api/generate docker compose up -d --build --no-deps web

### Without Docker

Complete the [installation steps](#installation-steps), make sure Ollama is running, then from `code/`:

    python -m webapp        # web app at http://127.0.0.1:5000

This is Flask's development server, and it only accepts connections from the same machine. To serve other machines on Linux or macOS, use the production server the Docker image uses:

    pip install gunicorn
    gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 4 --timeout 600 "webapp:create_app()"

Saved experiments are in `code/instance/experiments.db`.

### Configuration

The web app reads these optional environment variables:

    OLLAMA_URL      Ollama's /api/generate URL (default http://localhost:11434/api/generate)
    LLM_TIMEOUT     seconds to wait for each LLM call; a CPU-only server needs several minutes
    EXPERIMENTS_DB  path of the saved experiments database (default code/instance/experiments.db)
    FLASK_DEBUG     1 turns on the debugger and auto-reload with python -m webapp

`docker-compose.yml` sets the first three for the containers. To use another model, change `LLM_MODEL` in `code/sanitizer/config.py`; with Docker, also change the model pulled in `llm/Dockerfile`.

### Before others can reach it

- **There is no login.** Anyone who can reach the web app can run experiments and view, change or delete every saved experiment. Ollama has no authentication either.
- **`docker-compose.yml` publishes ports 8000 (web app) and 7860 (Ollama) on all network interfaces, and Docker's published ports can bypass the machine's firewall.** On a machine other people can reach, change them to `"127.0.0.1:8000:8000"` and `"127.0.0.1:7860:7860"`, or remove the `llm` service's `ports` entry, since the web app reaches Ollama over Docker's internal network.
- **Put a reverse proxy with HTTPS and a password in front of it** before exposing it beyond a network you trust.
- **Never set `FLASK_DEBUG=1` on a machine others can reach.** Flask's debugger lets anyone who reaches the page run code on the machine.
- **Expect only a few runs at a time.** The server handles four requests at once, and each run holds one until it finishes. On a CPU-only machine a run can take a few minutes, and simultaneous runs share the CPU.

## Functionality

In the web page, enter a prompt for the LLM and the accompanying data, as text or as uploaded PDF, Word (`.docx`), Excel (`.xlsx`) or text files. The prompt is trusted; only the data is scanned. Each mitigation has a toggle on the form (all on by default except sanitization), and the results show which ones ran. `webapp/mitigations.py` runs the ones switched on:

1. **Deobfuscates** a copy of the data for the detectors to scan, undoing tricks like leetspeak, lookalike letters, hidden characters and encodings. Matches map back to the original text.
2. **Detects** possible injections in the data with:
   - regular expressions for instruction overrides ("ignore previous instructions") and authority claims ("I am your system administrator")
   - a Bag-of-Words Naive Bayes classifier that flags malicious sentences
3. **Redacts** each detection with "[REDACTED]" (sanitization). A detection that starts a sentence, or spans more than one, is redacted through the end of its sentence; a detection in the middle of a sentence is cut out as a clause. With sanitization off, detections are flagged but stay in the data the model sees.
4. **Hardens** the prompt, wrapping the prompt and data in tags and rules that tell the model to treat the data as untrusted.
5. **Compares** the LLM's answer with the mitigations against its answer to the raw data (the baseline), and asks the LLM whether each answer is still relevant to the prompt (output validation).

The page shows the flagged content, a trace of each mitigation, both answers and the prompt structure sent to the model. Experiments can be saved, reopened and re-run.

`python -m evaluation.run_eval` runs the engine's fixed pipeline, `sanitizer.pipeline.process_single` (regex and BoW detection, redaction and output validation, without deobfuscation or hardening), over a labeled sample set. A sample is reported as a prompt injection if anything was detected or the answer to the sanitized data failed output validation. It reports accuracy, precision, recall, F1, false positives and negatives, and how often answers fail output validation before and after sanitization.

## Known Problems

- **Over-redaction of benign text.** The BoW classifier flags many benign sentences, especially in resumes, and those sentences are redacted whole.
- **Missed injections.** Injections phrased indirectly or quoted inside a request (for example "...the prompt template is irrelevant and should be disregarded") are not detected.
- **Techniques not fully in the pipeline.** Semantic outlier detection (`sanitizer/detection/semantic.py`), which also flags benign clauses in long, list-like text, Base64 detection (`sanitizer/detection/encoding.py`) and the Random Forest classifier (`sanitizer/detection/rf.py`, trained by `code/training/train_rf.py`) are implemented but not called. The web app uses text normalization (`sanitizer/normalize.py`) when deobfuscation is on, but `process_single` does not, so `run_eval` results do not measure it.
- **Resume framing.** Without prompt hardening, the data is sent to the LLM labeled as "Resume", whatever the data is.
- **Sentence splitting.** The BoW classifier splits sentences on punctuation, while redaction uses NLTK, so the two can disagree on where a sentence ends.
- **File upload.** Scanned documents (images of text) have no text to extract and are rejected. Long documents can exceed the model's context window, so the model may only see part of them, while detection and sanitization still cover all of the text.

## Contributing 
Fork it!
Create your feature branch: git checkout -b my-new-feature
Commit your changes: git commit -am 'Add some feature'
Push to the branch: git push origin my-new-feature
Submit a pull request :D

## Additional Documentation
Project reports: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/tree/main/reports  
Sprint reports: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/tree/main/Sprints/Sprint_1    
Sprint 1 pull request: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/pull/10  
Sprint 1 pull request video: https://wsu.zoom.us/rec/share/0dqRWFE30yrMnKyMNyMjd4nvKxuI-D_gxhyytnGQioeWmv-1y3U__Shh_RxpBaL0.n-NPeKLvAUt2-DXt?startTime=1771812736000  
Poster submitted for VICEROY Symposium: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/Sprints/Sprint_2/Final_Poster_VICEROY_Symposium.png

## Citations

### Datasets and models

| Resource | Used in | License |
| --- | --- | --- |
| [jayavibhav/prompt-injection](https://huggingface.co/datasets/jayavibhav/prompt-injection) | Labeled test samples (`code/evaluation/hugging-face/query.sql`, `code/evaluation/data/hugging_face_prompts.csv`) | Not stated |
| [opensporks/resumes](https://huggingface.co/datasets/opensporks/resumes) (mirror of Kaggle [snehaanbhawal/resume-dataset](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset)) | Resume test data (`code/evaluation/hugging-face/query-resumes.sql`, `code/evaluation/data/resumes_*.csv`) | CC0 1.0 |
| [Blog Authorship Corpus](https://u.cs.biu.ac.il/~koppel/BlogCorpus.htm) | Injection detector dataset (`code/dataset-generation`) | Non-commercial research use |
| [HuggingFaceH4/instruction-dataset](https://huggingface.co/datasets/HuggingFaceH4/instruction-dataset) | Injection detector dataset (`code/dataset-generation`) | Apache 2.0 |
| [databricks/databricks-dolly-15k](https://huggingface.co/datasets/databricks/databricks-dolly-15k) | Injection detector dataset (`code/dataset-generation`) | CC BY-SA 3.0 |
| [Microsoft Phi-3 Mini](https://ollama.com/library/phi3) via [Ollama](https://ollama.com) | LLM answers, LLM classifier and output validation (`code/sanitizer/llm.py`) | MIT |
| [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | Semantic outlier detection (`code/sanitizer/detection/semantic.py`) | Apache 2.0 |
| [Meta Llama 3 8B](https://ollama.com/library/llama3) via [Ollama](https://ollama.com) | Prompt-hardening comparison in the web app (currently disabled) | Meta Llama 3 Community License |

The evaluation sample sets in `code/evaluation/data/` include samples from jayavibhav/prompt-injection and the resume dataset. The training datasets are not redistributed; see [code/dataset-generation/README.md](code/dataset-generation/README.md) for download steps and licensing notes.

### BibTeX

```bibtex
@misc{jayavibhav_prompt_injection,
  title        = {{jayavibhav/prompt-injection}},
  author       = {{jayavibhav}},
  howpublished = {\url{https://huggingface.co/datasets/jayavibhav/prompt-injection}}
}

@misc{bhawal_resume_dataset,
  title        = {Resume Dataset},
  author       = {{snehaanbhawal}},
  howpublished = {\url{https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset}},
  note         = {Hugging Face mirror: \url{https://huggingface.co/datasets/opensporks/resumes}}
}

@inproceedings{schler2006effects,
  title     = {Effects of Age and Gender on Blogging},
  author    = {Schler, Jonathan and Koppel, Moshe and Argamon, Shlomo and Pennebaker, James W.},
  booktitle = {AAAI Spring Symposium: Computational Approaches to Analyzing Weblogs},
  pages     = {199--205},
  year      = {2006}
}

@misc{h4_instruction_dataset,
  title        = {{HuggingFaceH4/instruction-dataset}},
  author       = {{Hugging Face H4}},
  year         = {2023},
  howpublished = {\url{https://huggingface.co/datasets/HuggingFaceH4/instruction-dataset}}
}

@online{DatabricksBlog2023DollyV2,
  author  = {Mike Conover and Matt Hayes and Ankit Mathur and Jianwei Xie and Jun Wan and Sam Shah and Ali Ghodsi and Patrick Wendell and Matei Zaharia and Reynold Xin},
  title   = {Free Dolly: Introducing the World's First Truly Open Instruction-Tuned LLM},
  year    = {2023},
  url     = {https://www.databricks.com/blog/2023/04/12/dolly-first-open-commercially-viable-instruction-tuned-llm},
  urldate = {2023-06-30}
}

@article{abdin2024phi3,
  title   = {Phi-3 Technical Report: A Highly Capable Language Model Locally on Your Phone},
  author  = {Abdin, Marah and others},
  journal = {arXiv preprint arXiv:2404.14219},
  year    = {2024}
}

@inproceedings{reimers2019sentencebert,
  title     = {Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks},
  author    = {Reimers, Nils and Gurevych, Iryna},
  booktitle = {Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing},
  year      = {2019}
}

@article{grattafiori2024llama3,
  title   = {The Llama 3 Herd of Models},
  author  = {Grattafiori, Aaron and others},
  journal = {arXiv preprint arXiv:2407.21783},
  year    = {2024}
}
```

### Citing this project

```bibtex
@misc{scads2026promptinjection,
  title        = {Sanitizing Inputs to Protect LLMs Against Prompt Injection Attacks},
  author       = {{SCADS}},
  year         = {2026},
  note         = {CPTS 421 Capstone, Washington State University},
  howpublished = {\url{https://github.com/koguma100/LLM_Prompt_Injection_Capstone}}
}
```

## License

MIT License

