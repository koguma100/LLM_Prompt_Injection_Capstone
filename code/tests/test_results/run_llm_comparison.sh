#!/usr/bin/env bash
# Runs run_eval twice per sample set (early exit on / off) and records wall time. From code/ run:
#     bash tests/test_results/run_llm_comparison.sh
set -u
OUT=tests/test_results/llm_runs
mkdir -p "$OUT"
PY=${PY:-python}
run() {  # name mode args...
  local name=$1 mode=$2; shift 2
  local extra=""; [ "$mode" = full ] && extra="--no-early-exit"
  local start=$(date +%s)
  $PY -m evaluation.run_eval "$@" --quiet $extra --out "$OUT/${name}_$mode" > "$OUT/${name}_$mode.log" 2>&1
  echo "$name,$mode,$(( $(date +%s) - start ))" >> "$OUT/timings.csv"
}
echo "set,mode,seconds" > "$OUT/timings.csv"
for mode in early full; do
  run resumes_half_pi $mode --samples resumes_half_pi
  run embedded_pi_tests $mode --samples embedded_pi_tests
  run imperative_tests $mode --samples imperative_tests
  run datasetv2_holdout100 $mode --samples training/injection_detector_datasetv2.csv --holdout --limit 100 --seed 0
done
echo done
