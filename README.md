# Sanitizing Inputs to Protect LLMs Against Prompt Injection Attacks

## Project summary

Researching and testing sanitization techniques for mitigated prompt injections through poisoned data assuming trusted user prompts.

In positions where users – researchers, professors, and recruiters – take in large amounts of data for LLM analysis, prompt injections can stay hidden among a breadth of benign data. Our solution gives the user trust that the data they provide an LLM for processing will be sanitized of any prompt injections that could compromise internal systems.

## Installation

### Prerequisites

### This project requires Python and several packages listed in code/requirements.txt:

    requests
    scikit-learn
    matplotlib
    scipy
    numpy
    flask
    ollama

### Add-ons (Python packages)

    Requests: making http requests to local LLMs
    Scikit-learn: statistical outputs for testing detection performance
    Matplotlib: plotting the confusion matrix
    Scipy: delivers functions for computing the confusion matrix.
    Numpy: general math operations
    Flask: python web framework
    Ollama: locally run open-source LLMs

### Installation Steps

For running the Data_Sanitization_Engine.py, run:

    pip install -r requirements.txt (in code directory)

For running the Flask app install:

Flask, Ollama, Ollama model of choice (modify code)

Then run:

    python run.py

Future development will provide a Dockerfile to bypass manually entering the above steps.

## Functionality

In the locally hosted web page, enter a prompt for the LLM and the accompanying data. Note that these fields are separated, and only the “data” field will be processed. Once you have submitted, the Python backend will detect the data according to several regular expressions representative of prompt injections and with the response of an LLM classifier. Then, parts of the data determined to be prompt injections are removed and replaced with “[REDACTED]”. 

## Known Problems

We are unaware of any current problems with the code, as our scope for this sprint was limited and focused on creating a functioning prototype.

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
| [jayavibhav/prompt-injection](https://huggingface.co/datasets/jayavibhav/prompt-injection) | Labeled test samples (`code/hugging-face/query.sql`) | Not stated |
| [opensporks/resumes](https://huggingface.co/datasets/opensporks/resumes) (mirror of Kaggle [snehaanbhawal/resume-dataset](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset)) | Resume test data (`code/hugging-face/query-resumes.sql`) | CC0 1.0 |
| [Blog Authorship Corpus](https://u.cs.biu.ac.il/~koppel/BlogCorpus.htm) | Injection detector dataset (`code/dataset-generation`) | Non-commercial research use |
| [HuggingFaceH4/instruction-dataset](https://huggingface.co/datasets/HuggingFaceH4/instruction-dataset) | Injection detector dataset (`code/dataset-generation`) | Apache 2.0 |
| [databricks/databricks-dolly-15k](https://huggingface.co/datasets/databricks/databricks-dolly-15k) | Injection detector dataset (`code/dataset-generation`) | CC BY-SA 3.0 |
| [Meta Llama 3 8B](https://ollama.com/library/llama3) via [Ollama](https://ollama.com) | LLM classifier in the Flask app | Meta Llama 3 Community License |

Third-party data is not redistributed in this repo; see [code/dataset-generation/README.md](code/dataset-generation/README.md) for download steps and licensing notes.

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

