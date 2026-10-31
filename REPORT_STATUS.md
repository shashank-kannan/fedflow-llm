# REPORT_STATUS: FedFlow-LLM project report

Started 31 Oct 2026 on branch `main`. This file was written before any work and is updated after each phase.
A new session continues from the first unticked phase.

Rules kept: no sudo, no push, no training, GPU, Mininet, POX or model run.
Read-only: `results/`, `datasets/`, `controller/`, `experiments/`, `training/`, `notebooks/`, `~/fedflow_data`.
Write only: `report/`, `figures/`, `references/`, `tools/`, `results/v2_attempt/` (copies plus checksums), this file and `REPORT_DECISIONS.md`.
CLAUDE.md rule 3 (wait for plan OK) is overridden by the task ("do not stop for plan approval").

## Phases

- [x] Phase 0: template located, unzipped to `templates/report_template/`, `main.tex` read in full; `.git/info/exclude` updated
- [x] Phase 1: numbers (`tools/build_numbers.py`, `--selftest`, sanity facts, constants, LoRA/loss-token check, `results/v2_attempt/` copies)
  - Built: `--selftest` passes; outputs in `report/generated/` (numbers.json/.tex/.md, sanity.txt); `results/v2_attempt/` copies verified by CHECKSUMS.txt.
  - 2 of 43 sanity facts differed (7511 static 48.3 vs 48.4; reactive 16.1 vs 16.0); the user confirmed the computed values, and all 43 now pass.
- [x] Phase 2: figures (`tools/make_figures.py`, 6 matplotlib figures + 2 TikZ, `figures/captions.json`)
  - Done: 6 figures as PDF + PNG + `.data.csv`, 2 TikZ files in `figures/tikz/`, captions in `figures/captions.json`. Every number is read from `report/generated/numbers.json`, including link rates, threshold and window sizes. Run with `python3 -B` (matplotlib is in user site-packages, which `-I` hides).
- [x] Phase 3: references (`references/refs.bib`, `verification_log.csv`, `abstracts/`, `lit_table.csv`)
  - Done as far as the instructions go: 24 of 24 usable (`tools/verify_refs.py`), 19 abstracts saved, literature table 10 rows (2021–2026). The citation check (each reference cited at least once) waits for the report text. See REPORT_DECISIONS.md items 10–15.
- [ ] Phase 4 and later: **instructions not received** (the task text stops mid-sentence in Phase 3, at "Technique and inference come from the abstract you"). Report writing, humanizing and Overleaf packaging wait for the rest of the instructions.

## Notes

- The template zip was not in `templates/`. It was found at `/mnt/c/Users/shash/Downloads/23AID206_report_template.zip` and copied; the original is not edited.
