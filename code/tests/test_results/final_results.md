# Final results

Weights: rf_malicious 1, instruction_overrides 1, authority_overrides 0.5, llm_validation 0.5, outlier_clauses 0, bow_malicious 0; injection at a vote of 1; LLM stage skipped at 2.

`datasetv2_holdout` is the 20% of dataset v2 the Random Forest never trained on. The LLM rows use a random subset of 200 samples (resumes, holdout, Hugging Face). `imperative_tests` is labeled all benign but contains lines like "Ignore all previous instructions".


## All realistic sets (holdout + Hugging Face + resumes)

| Method | Samples | Accuracy | Precision | Recall | False-positive rate | F1 |
|---|---|---|---|---|---|---|
| Random Forest | 2540 | 85.3% | 100.0% | 44.9% | 0.0% | 62.0% |
| Instruction regex | 2540 | 76.3% | 100.0% | 11.3% | 0.0% | 20.4% |
| Authority regex | 2540 | 73.6% | 53.6% | 8.8% | 2.8% | 15.2% |
| LLM output check | 200 | 69.0% | 55.6% | 30.3% | 11.9% | 39.2% |
| Old rule: any detector fires | 2540 | 85.0% | 87.0% | 51.4% | 2.8% | 64.6% |
| Old rule + LLM check | 200 | 74.5% | 64.2% | 51.5% | 14.2% | 57.1% |
| Weighted pipeline, detectors only | 2540 | 85.7% | 100.0% | 46.4% | 0.0% | 63.4% |
| Weighted pipeline, full (with LLM check) | 200 | 76.0% | 100.0% | 27.3% | 0.0% | 42.9% |

## datasetv2_holdout

| Method | Samples | Accuracy | Precision | Recall | False-positive rate | F1 |
|---|---|---|---|---|---|---|
| Random Forest | 2400 | 86.4% | 100.0% | 48.3% | 0.0% | 65.2% |
| Instruction regex | 2400 | 76.5% | 100.0% | 10.6% | 0.0% | 19.2% |
| Authority regex | 2400 | 74.0% | 53.7% | 9.2% | 2.8% | 15.7% |
| LLM output check | 60 | 60.0% | 28.6% | 22.2% | 23.8% | 25.0% |
| Old rule: any detector fires | 2400 | 85.7% | 87.1% | 53.6% | 2.8% | 66.3% |
| Old rule + LLM check | 60 | 68.3% | 47.6% | 55.6% | 26.2% | 51.3% |
| Weighted pipeline, detectors only | 2400 | 86.4% | 100.0% | 48.3% | 0.0% | 65.2% |
| Weighted pipeline, full (with LLM check) | 60 | 83.3% | 100.0% | 44.4% | 0.0% | 61.5% |

## hugging_face_prompts

| Method | Samples | Accuracy | Precision | Recall | False-positive rate | F1 |
|---|---|---|---|---|---|---|
| Random Forest | 40 | 45.0% | — | 0.0% | 0.0% | 0.0% |
| Instruction regex | 40 | 57.5% | 100.0% | 22.7% | 0.0% | 37.0% |
| Authority regex | 40 | 45.0% | 50.0% | 9.1% | 11.1% | 15.4% |
| LLM output check | 40 | 65.0% | 72.2% | 59.1% | 27.8% | 65.0% |
| Old rule: any detector fires | 40 | 55.0% | 75.0% | 27.3% | 11.1% | 40.0% |
| Old rule + LLM check | 40 | 70.0% | 70.8% | 77.3% | 38.9% | 73.9% |
| Weighted pipeline, detectors only | 40 | 57.5% | 100.0% | 22.7% | 0.0% | 37.0% |
| Weighted pipeline, full (with LLM check) | 40 | 57.5% | 100.0% | 22.7% | 0.0% | 37.0% |

## resumes_half_pi

| Method | Samples | Accuracy | Precision | Recall | False-positive rate | F1 |
|---|---|---|---|---|---|---|
| Random Forest | 50 | 48.0% | — | 0.0% | 0.0% | 0.0% |
| Instruction regex | 50 | 58.0% | 100.0% | 19.2% | 0.0% | 32.3% |
| Authority regex | 50 | 48.0% | — | 0.0% | 0.0% | 0.0% |
| LLM output check | 50 | 54.0% | 100.0% | 11.5% | 0.0% | 20.7% |
| Old rule: any detector fires | 50 | 58.0% | 100.0% | 19.2% | 0.0% | 32.3% |
| Old rule + LLM check | 50 | 62.0% | 100.0% | 26.9% | 0.0% | 42.4% |
| Weighted pipeline, detectors only | 50 | 58.0% | 100.0% | 19.2% | 0.0% | 32.3% |
| Weighted pipeline, full (with LLM check) | 50 | 58.0% | 100.0% | 19.2% | 0.0% | 32.3% |

## resumes_all_benign

| Method | Samples | Accuracy | Precision | Recall | False-positive rate | F1 |
|---|---|---|---|---|---|---|
| Random Forest | 50 | 100.0% | — | — | 0.0% | — |
| Instruction regex | 50 | 100.0% | — | — | 0.0% | — |
| Authority regex | 50 | 100.0% | — | — | 0.0% | — |
| LLM output check | 50 | 98.0% | 0.0% | — | 2.0% | 0.0% |
| Old rule: any detector fires | 50 | 100.0% | — | — | 0.0% | — |
| Old rule + LLM check | 50 | 98.0% | 0.0% | — | 2.0% | 0.0% |
| Weighted pipeline, detectors only | 50 | 100.0% | — | — | 0.0% | — |
| Weighted pipeline, full (with LLM check) | 50 | 100.0% | — | — | 0.0% | — |

## embedded_pi_tests

| Method | Samples | Accuracy | Precision | Recall | False-positive rate | F1 |
|---|---|---|---|---|---|---|

## simple_prompts

| Method | Samples | Accuracy | Precision | Recall | False-positive rate | F1 |
|---|---|---|---|---|---|---|

## imperative_tests

| Method | Samples | Accuracy | Precision | Recall | False-positive rate | F1 |
|---|---|---|---|---|---|---|
