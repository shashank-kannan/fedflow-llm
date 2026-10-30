# STUDY_STATUS: FedFlow-LLM study guide

Started 31 Oct 2026 on branch `main` (clean tree at `ea073d9`). Written before any work, then updated as parts are finished.

Rules followed: write only in `study_guide/`, `STUDY_STATUS.md` and `STUDY_DECISIONS.md`. No sudo, no push, no training, no model run.
Every number is checked against a repo file and cited. Anything that isn't in a file is written "not in the files" and listed in `STUDY_DECISIONS.md`.

## Tools found

- python-docx: not installed in system Python. Installed with `pip install --target` into a scratch folder outside the repo (a venv could not be made: ensurepip is missing).
- LibreOffice (`soffice`): not installed, so no PDF copy can be made.
- pandoc: not installed.

## Parts

- [x] Facts verified against the repo
- [x] Part 0 How to use this guide
- [x] Part 1 The problem in plain words
- [x] Part 2 The whole project on one page
- [x] Part 3 Glossary
- [x] Part 4 The data
- [x] Part 5 The model and training
- [x] Part 6 The network experiment
- [x] Part 7 Results
- [x] Part 8 The v2 attempt
- [x] Part 9 Limits and threats
- [x] Part 10 Annoying questions
- [x] Part 11 60-second and 3-minute explanations
- [x] Part 12 Cheat sheet
- [x] DOCX built
- [ ] PDF built: **not done**, LibreOffice is not installed
- [x] Committed (study_guide/ and the status files only); not pushed

## Notes per part

- Facts: every item in the facts block was checked against the repo. Results:
  - One conflict: 7511 static is 48.32 in the file, against 48.4 in the block.
  - Two facts are not in the files: the "Big Data Challenge" name and the GPU-mismatch count.
  - All are in `STUDY_DECISIONS.md`.
- Headline check: on both telecom cells every model rep is below every reactive rep (7511: model max 9.9826 < reactive min 15.6496;
  8336: model max 7.8507 < reactive min 13.3251, from the two summary.csv files). So "lower" is used.
- Forecasts in the experiment are precomputed: `experiments/run_experiment.py` reads `forecasts.csv`. Answered in Q5.
- Part 3 has 58 glossary entries. Part 10 has 55 questions in the 9 required groups.
- Banned words ("proves", "significant", "wins", "beats" and their forms) were searched for: none remain.
- Paragraph length was checked: no prose paragraph is longer than 360 characters (about 4 lines at 12 pt on A4 with 2.5 cm margins).

## DOCX layout (checked by reading the file back with python-docx)

- A4, 2.5 cm margins, Calibri 12 pt, line spacing 1.5, 8 pt after paragraphs.
- 13 Parts, each starting on a new page. "Page X of Y" in the footer. A Word table-of-contents field, with "update fields on open" set.
- Callout boxes are shaded one-cell tables, labelled "In one line", "Watch out" and "If pushed". Tables use 10.5 pt, and 9.5 pt on the cheat sheet.
- **Not verified:** the rendered page count and the one-page fit of the cheat sheet. No renderer is installed. Open the DOCX in Word and check Part 12.

## Files created

- `study_guide/FedFlow_Study_Guide.md` (source)
- `study_guide/FedFlow_Study_Guide.docx`
- `study_guide/build_docx.py` (the builder, so the DOCX can be rebuilt; it needs python-docx)
- `STUDY_STATUS.md`
- `STUDY_DECISIONS.md`

No other file was changed.
