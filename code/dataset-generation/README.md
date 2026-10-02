# Dataset Generation

Builds `injection_detector_dataset.csv`, a labeled dataset for training a prompt-injection detector, from the [Blog Authorship Corpus](https://u.cs.biu.ac.il/~koppel/BlogCorpus.htm) (Koppel et al.) plus instruction prompts from Hugging Face.

Neither the blog corpus (~800 MB unzipped) nor the generated CSV is committed to this repo; see [Licensing](#licensing). Download the corpus and build the CSV locally with the steps below.

## 1. Download the blog corpus

From this folder (`code/dataset-generation/`):

```bash
curl -L -o blogs.zip https://u.cs.biu.ac.il/~koppel/blogs/blogs.zip   # ~313 MB
unzip -q blogs.zip && rm blogs.zip
```

This creates `blogs/`, which holds 19,320 `.xml` files (for example `1000331.female.37.indUnk.Leo.xml`). `blogs/` is listed in `.gitignore`.

You don't need to download the instruction datasets (`HuggingFaceH4/instruction-dataset`, `databricks/databricks-dolly-15k`). The build script fetches them through the `datasets` library.

## 2. Install dependencies

```bash
pip install datasets nltk pandas numpy
```

The NLTK tokenizer and tagger data download automatically on first run.

## 3. Build and validate

```bash
python3 build_injection_dataset.py --blogs-dir ./blogs --out injection_detector_dataset.csv
python3 validate_injection_dataset.py injection_detector_dataset.csv
```

For a quick test run, add `--max-blog-files 500` to the build command. Defaults are 3000 injection, 3000 benign-imperative and 6000 normal examples, with `--seed 42`. See the docstring in `build_injection_dataset.py` for the column schema.

## 4. Train the detector

The BoW training script reads the dataset from `code/training/`. Copy it there under the version name it expects, then train from `code/`:

```bash
cp injection_detector_dataset.csv ../training/injection_detector_datasetv2.csv
cd .. && python training/train_bow.py
```

## Citations

### Source datasets

| Dataset | Used for | License |
| --- | --- | --- |
| [Blog Authorship Corpus](https://u.cs.biu.ac.il/~koppel/BlogCorpus.htm) | Normal text, benign imperatives, and host text for injections | Non-commercial research use |
| [HuggingFaceH4/instruction-dataset](https://huggingface.co/datasets/HuggingFaceH4/instruction-dataset) | Injected instructions (327 prompts) | Apache 2.0 |
| [databricks/databricks-dolly-15k](https://huggingface.co/datasets/databricks/databricks-dolly-15k) | Injected instructions (~15k prompts) | CC BY-SA 3.0 |

```bibtex
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
```

### Licensing

The scripts in this folder are covered by the repository's MIT license. They contain no third-party data; they download it at run time.

The generated `injection_detector_dataset.csv` is **not** distributed with this repo and is not covered by the MIT license. It mixes Blog Authorship Corpus text (non-commercial research use only) with Dolly instructions (CC BY-SA 3.0), so anyone who builds it is responsible for following the terms of both source datasets.

### Citing this dataset

```bibtex
@misc{scads2026injectiondataset,
  title        = {Prompt Injection Detector Dataset},
  author       = {{SCADS}},
  year         = {2026},
  note         = {CPTS 421 Capstone, Washington State University. Built from the Blog Authorship Corpus, HuggingFaceH4/instruction-dataset, and databricks-dolly-15k},
  howpublished = {\url{https://github.com/koguma100/LLM_Prompt_Injection_Capstone/tree/main/code/dataset-generation}}
}
```
