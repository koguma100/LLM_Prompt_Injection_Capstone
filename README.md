# Sanitizing Inputs to Protect LLMs Against Prompt Injection Attacks

## Project summary

Researching and testing sanitization techniques for mitigated prompt injections through poisoned data assuming trusted user prompts.

In positions where users – researchers, professors, and recruiters – take in large amounts of data for LLM analysis, prompt injections can stay hidden among a breadth of benign data. Our solution gives the user trust that the data they provide an LLM for processing will be sanitized of any prompt injections that could compromise internal systems.

## Installation

### Prerequisites

- Python 3.10 or newer
- [Ollama](https://ollama.com), running locally, with the `phi3:mini` model

The Python packages are listed in `code/requirements.txt`:

    requests, numpy, scipy      HTTP calls to Ollama, math, entropy
    nltk                        sentence splitting for redaction
    sentence-transformers       clause embeddings for semantic outlier detection
    scikit-learn                Bag-of-Words classifier and evaluation metrics
    confusables                 homoglyph mapping for text normalization
    matplotlib                  confusion matrix and result plots
    Flask                       web app
    pandas, datasets            BoW training and dataset generation
    pytest                      unit tests

### Installation Steps

From the `code/` directory, install the dependencies and this project's packages:

    pip install -r requirements.txt

Pull the model the pipeline calls (to use a different one, change `LLM_MODEL` in `code/sanitizer/config.py`):

    ollama pull phi3:mini

The trained BoW models (`.pkl`) and the training datasets are not committed. Before running the engine, regenerate them:

1. Build the injection detector dataset by following [code/dataset-generation/README.md](code/dataset-generation/README.md), then save it as `code/training/injection_detector_datasetv2.csv`.
2. From `code/`, run `python training/train_bow.py`. It trains both BoW models and saves them to `code/models/` (see `--help` for the dataset version and model options).

### Running

From the `code/` directory:

    python -m evaluation.run_eval   # batch evaluation; stats and plots go to code/results/
    python -m webapp                # web app at http://127.0.0.1:5000
    pytest                          # unit tests

`run_eval` evaluates the `resumes_half_pi` sample set with a hiring question by default. Choose another set or prompt with `--samples` and `--prompt`; `--help` lists the sample sets. Each set is a CSV with `text,label` columns (1 = prompt injection, 0 = benign) in `code/evaluation/data/`, so a new set can be added by saving a CSV there.

The web app runs with debug mode off. Set `FLASK_DEBUG=1` to turn on the debugger and auto-reload while developing.

### Code layout

    code/
    ├── sanitizer/           # detection, sanitization and LLM pipeline (importable package); settings in config.py
    │   └── detection/       # regex, semantic outlier, BoW and Base64 detectors
    ├── webapp/              # Flask web app
    ├── evaluation/          # batch evaluation (run_eval.py), sample sets (data/), Hugging Face queries
    ├── training/            # BoW model training (train_bow.py)
    ├── dataset-generation/  # builds the injection detector dataset
    ├── tests/               # pytest unit tests
    ├── models/              # trained models (not committed)
    ├── results/             # evaluation outputs (not committed)
    └── legacy/              # unused older code, kept for reference

Future development will provide a Dockerfile to bypass manually entering the above steps.

## Functionality

In the locally hosted web page, enter a prompt for the LLM and the accompanying data. The prompt is trusted; only the data is scanned. `sanitizer.pipeline.process_single` then:

1. **Detects** possible injections in the data with:
   - regular expressions for instruction overrides ("ignore previous instructions") and authority claims ("I am your system administrator")
   - semantic outliers: clauses whose sentence embedding (`all-MiniLM-L6-v2`) is far from the rest of the text
   - a Bag-of-Words Naive Bayes classifier that flags malicious sentences
2. **Redacts** each detection with "[REDACTED]". A detection that starts a sentence, or spans more than one, is redacted through the end of its sentence; a detection in the middle of a sentence is cut out as a clause.
3. **Compares** the LLM's answer to the prompt with the original data and with the sanitized data, and asks the LLM whether each answer is still relevant to the prompt (output validation).

The data is reported as a prompt injection if anything was detected or the answer to the sanitized data failed output validation. The web page shows the original and sanitized data side by side, with the LLM's answer to each. `python -m evaluation.run_eval` runs the same pipeline over a labeled sample set and reports accuracy, precision, recall, F1, false positives and negatives, and how often answers fail output validation before and after sanitization.

## Known Problems

- **Over-redaction of benign text.** The BoW classifier flags many benign sentences, especially in resumes, and those sentences are redacted whole. Semantic outlier detection also flags benign clauses in long, list-like text.
- **Missed injections.** Injections phrased indirectly or quoted inside a request (for example "...the prompt template is irrelevant and should be disregarded") are not detected.
- **Detectors not yet in the pipeline.** Text normalization (`sanitizer/normalize.py`, for homoglyphs, leetspeak and hidden characters) and Base64 detection (`sanitizer/detection/encoding.py`) are implemented and tested but not called by the pipeline, so obfuscated injections are only caught if another detector flags them.
- **Resume framing.** The pipeline sends the data to the LLM labeled as "Resume", whatever the data is.
- **Sentence splitting.** The BoW classifier splits sentences on punctuation, while redaction uses NLTK, so the two can disagree on where a sentence ends.
- **File upload.** The web page shows a file upload field, but uploaded files are not processed yet.

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

