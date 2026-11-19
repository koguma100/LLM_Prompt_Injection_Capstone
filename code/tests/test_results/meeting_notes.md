# Weighted early-exit: meeting notes (2026-11-08)

## Talking points

1. **What the weighting does.** Each cheap detector that fires adds its weight to a vote: instruction regex 1.0,
   authority regex 1.0, BoW model 1.0 and semantic outliers 0.5. If the vote reaches 2.0, the sample is called an
   injection right away and the 4 LLM calls (2 answers + 2 validations) are skipped.

2. **It is a speed feature, not an accuracy feature.** A skip only happens when detectors fired, and any detection
   already makes the prediction "injection". So accuracy, precision and recall are the same with or without
   early exit. The weighting only decides *when we can stop early*.

3. **It cuts LLM work by about 5–10% on realistic data.** The share of samples that skip the LLM:
   - BoW holdout set: 5.6% (135 of 2400)
   - Hugging Face prompts: 10.5% (105 of 1000)
   - Resumes with injections: 10% (5 of 50)
   - Benign resumes: 0%

   Each skip saves 4 LLM calls, about 15 s per sample on this machine.

4. **When it skips, it is mostly right.** Skipped samples that really are injections: 83% on the holdout set and
   92% on Hugging Face. It was 100% on every hand-made injection set.

5. **All benign skips on real data come from one pair: the authority regex plus BoW.** The authority regex matches
   everyday phrases like "tell me" and "print", and BoW is noisy (see 6). The instruction regex plus BoW pair never
   skipped a benign sample on real data.

6. **BoW is the noisiest detector in the system, independent of the weighting.** It flags 29% of benign holdout
   samples, 55% of benign Hugging Face prompts and 86% of benign resumes. That is why a threshold of 1.0 (any one
   detector) would be unusable: it would skip about half of all benign samples.

7. **Easy improvement: weight the authority regex at 0.5.** In the offline simulation, benign skips drop to zero on
   all real data. The cost is fewer skips: 2.8% on the holdout set (was 5.6%) and 7.7% on Hugging Face (was 10.5%).

8. **The 0.5 weight on semantic outliers does nothing right now.** That detector is commented out in
   `pipeline.py`, so the highest possible vote is 3.0, and thresholds of 1.5 and 2.0 behave identically. In
   practice, "2.0" means "2 of the 3 active detectors agree".

9. **Trade-offs to mention:**
   - Skipped samples get no LLM answer. In the webapp, the user sees "Skipped" instead of a response.
   - Skipped samples are left out of the sanitization fail-rate table. They are the most obvious injections, so
     that table looks slightly worse with early exit on. Use `--no-early-exit` when measuring sanitization.

10. **Questions for the group:**
    - Is the goal of early exit speed, or should a skip become a hard "block"?
    - Should we adopt authority = 0.5, or retune the authority regex itself?
    - Should we re-enable semantic outliers so their weight counts?
    - Should `imperative_tests` keep the label "benign"? It contains "Ignore all previous instructions", and all 8 of
      its "benign skips" are those lines.

## Evidence

### Setup
- 126 of 126 unit tests pass (`pytest tests`). These include new tests for `cheap_vote`, skipping and `skip_threshold=None`.
- The BoW models were retrained with `training/train_bow.py` on dataset v2, restored from git history (commit `7584964^`).
  This used the same split as before (test size 0.2, seed 10), so "holdout" means rows BoW never saw.
- The offline analysis runs only the cheap detectors, with no LLM: `python tests/test_results/weighting_analysis.py`
  (about 6 s for all sets).
- The Hugging Face set loads as 1000 samples (500 injection, 500 benign).

### Where the behavior comes from in the code
- `sanitizer/pipeline.py`, `Result.prediction`: `1 if self.detections or self.sanitized_valid is False`. Any detection means 1.
- `sanitizer/pipeline.py`, `process_single`: `llm_skipped = score >= skip_threshold`. The score only goes up when a detector fired.
- `sanitizer/pipeline.py`, `process_single`: `outlier_clauses = []`, because the detector call is commented out.

### Skip results at threshold 2.0 (`cheap_vote_summary.csv`)
| Set | Samples | Injection / benign | Skipped | Skip rate | Skipped benign | Share of skips that are injections |
|---|---|---|---|---|---|---|
| datasetv2 BoW holdout | 2400 | 631 / 1769 | 135 | 5.6% | 23 | 83.0% |
| hugging_face_prompts | 1000 | 500 / 500 | 105 | 10.5% | 8 | 92.4% |
| resumes_half_pi | 50 | 26 / 24 | 5 | 10.0% | 0 | 100% |
| resumes_all_benign | 50 | 0 / 50 | 0 | 0% | 0 | — |
| embedded_pi_tests | 15 | 15 / 0 | 7 | 46.7% | 0 | 100% |
| simple_prompts | 4 | 4 / 0 | 3 | 75% | 0 | 100% |
| imperative_tests | 25 | 0 / 25 | 8 | 32% | 8 | 0% (label issue, see point 10) |

### How often each detector fires (`detector_hits.csv`)
| Set | Instruction regex (inj / benign) | Authority regex (inj / benign) | BoW (inj / benign) |
|---|---|---|---|
| datasetv2 holdout | 67/631 · **0**/1769 | 58/631 · 50/1769 | 554/631 · **508/1769** |
| hugging_face_prompts | 77/500 · **0**/500 | 29/500 · 19/500 | 315/500 · **275/500** |
| resumes_all_benign | — · 0/50 | — · 0/50 | — · **43/50** |

The instruction regex is very precise but catches only about 11% of injections. BoW catches about 88% of injections,
but it also flags many benign samples.

### Which detector pairs caused the skips (`per_sample_scores.csv`)
| Set | Instruction + BoW | Authority + BoW | All three |
|---|---|---|---|
| datasetv2 holdout | 64 injection / 0 benign | 45 injection / **23 benign** | 3 injection |
| hugging_face_prompts | 71 / 0 | 20 / **8** | 6 |

Benign examples skipped because of authority + BoW: the authority regex matched "tell me" in
"Tell me about the Tao of modern society." and "print" in a blog post about a festival ("horse raising, Mongolian wrestling...").

### Threshold sweep (`threshold_sweep.csv`)
| Threshold | Holdout skip rate | Share of holdout skips that are injections | HF skip rate | Share of HF skips that are injections |
|---|---|---|---|---|
| 1.0 | 45.8% | 51.3% | 60.4% | 52.6% |
| 1.5 / 2.0 (same result) | 5.6% | 83.0% | 10.5% | 92.4% |
| 2.5 / 3.0 | 0.1% | 100% | 0.6% | 100% |

### Alternative: authority weight 0.5 (`alt_weights_authority_0.5.csv`)
| Set | Skip rate (now → alt) | Benign skips (now → alt) |
|---|---|---|
| datasetv2 holdout | 5.6% → 2.8% | 23 → 0 |
| hugging_face_prompts | 10.5% → 7.7% | 8 → 0 |
| resumes_half_pi | 10% → 10% | 0 → 0 |

### LLM runs with early exit on vs. off (`llm_runs/`)
*In progress when these notes were written. Sets: resumes_half_pi, embedded_pi_tests, imperative_tests, and 100
holdout rows. Each set runs once with early exit and once with `--no-early-exit`, and `llm_runs/timings.csv`
records the wall time.* The first observation is about 15 s per sample when the LLM stage runs.
