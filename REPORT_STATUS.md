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
- [x] Phase 3 addendum: Cons rule applied (`tools/build_lit_table.py`); every table row has a readable abstract
- [x] Phase 4: fixed statements S1–S16 in `tools/required_statements.json` (fills and deviations: REPORT_DECISIONS.md items 16–21)
- [x] Phase 5: report written: `report/report_src.tex` rendered by `tools/render_report.py` into `report/main_paste.tex` (one self-contained file; preamble copied verbatim from the template plus tikz, pgfplots, booktabs, tabularx, array; only image is Amrita.jpg; 8 inline figures (6 pgfplots, 2 TikZ), 9 tables, 24 references inline in IEEE style, all cited)
- [x] Phase 6: humanizer skill found at `~/.claude/skills/synced/.../humanizer` (not loaded in the session skill list). Its rules were applied while writing the prose, in one pass. **The per-paragraph multiset gate, second pass and kept/discarded counts were skipped at the user's request** ("don't run any verification gate"), so no counts exist.
- [ ] Phase 7: checks **skipped at the user's request** (no check_report.py, no overlap_check.py). Only the renderer's own stops ran: no unresolved placeholder, every \cite key has a verified record, 24 entries, none uncited.
- [x] Phase 8: delivered `report/main_paste.tex` and `report/PASTE_STEPS.txt`; no zip.

## Compile status

**Not compiled.** No TeX engine is installed here (`pdflatex`, `latexmk`, `tectonic` all missing), so whether it compiles and the page count (target 15–25) are unknown until it is built in Overleaf.

## Commands run (Phases 5–8)

- `python3 -I -B tools/render_report.py` (renders main_paste.tex; stops on unresolved placeholders or unverified cite keys)

## Left to fill in the report

- `[October 2026]` on the title page (MONTH_YEAR was given in brackets, so it stays a visible placeholder).
- "Submitted for the university examination held on ..." and Place/Date/signatures: template blanks, left as in the template.

## Copy to Windows

`cp report/main_paste.tex /mnt/c/Users/shash/Downloads/main_paste.tex`

## Files created (all phases)

tools/build_numbers.py, tools/make_figures.py, tools/verify_refs.py, tools/build_lit_table.py, tools/render_report.py, tools/required_statements.json (rewritten);
figures/*.pdf, *.png, *.data.csv, captions.json, tikz/fig_pipeline.tex, tikz/fig_topology.tex;
references/refs.bib, verification_log.csv, lit_table.csv, abstracts/*.txt;
report/generated/numbers.json, numbers.tex, numbers.md, sanity.txt; report/report_src.tex, report/main_paste.tex, report/PASTE_STEPS.txt;
results/v2_attempt/ (copies + CHECKSUMS.txt); templates/report_template/ (unzipped copy); REPORT_STATUS.md, REPORT_DECISIONS.md.

## Notes

- The template zip was not in `templates/`. It was found at `/mnt/c/Users/shash/Downloads/23AID206_report_template.zip` and copied; the original is not edited.
