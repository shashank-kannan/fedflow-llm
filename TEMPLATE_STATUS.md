# TEMPLATE_STATUS: template conformance of the report (form only)

Started 31 Oct 2026 on `main`. Input: the user pasted the report text; it is the delivered `report/main_paste.tex`, copied to `report/main_overleaf.tex`. Work copy: `report/main_fixed.tex`.

## Phases

- [x] Phase 1: preamble diff: identical to the template plus only the allowed additions (tikz, pgfplots+compat, booktabs, tabularx, array); no fix needed
- [x] Phase 2: front matter: date line set to OCTOBER - 2026 (no brackets; user to confirm). Certificate: step (a) local \sloppy + \emergencystretch, step (b) removed the two blank \\ lines after the paragraph (it spilled onto page 3 in compiled.pdf). Declaration: steps (a) and (b), removed the four blank \\ lines (the countersignature spilled onto page 5). No wording changed.
- [x] Phase 3: body structure already matches (Ch.1 sections in template order, Ch.2 starts with Introduction, organization list matches 5 chapters, References in the TOC via \addcontentsline); Amrita.jpg copied to report/
- [ ] Phase 4: checker NOT written: the user stopped all tests and gates
- [x] Phase 5: delivered report/main_fixed.tex and report/PASTE_STEPS.txt. Not compiled here (no TeX), so the one-page fit of the certificate and declaration is unverified.

Why the logo was missing in compiled.pdf: Amrita.jpg was not in the Overleaf project (pages 1-2 contain no image).

Files created: TEMPLATE_STATUS.md, report/main_overleaf.tex, report/main_fixed.tex, report/compiled.pdf, report/Amrita.jpg, report/PASTE_STEPS.txt (rewritten).

## Tools found

- `pdflatex`: not installed, so main_fixed.tex cannot be compiled here.
- poppler (`pdftotext`, `pdfimages`, `pdffonts`): not installed. The checker uses `pypdf` (pip --user) instead.
- `report/compiled.pdf`: copied from `/mnt/c/Users/shash/Downloads/CNreport.pdf` (the user's Overleaf compile of the pre-fix version).
