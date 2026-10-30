# SLIDES_STATUS: FedFlow-LLM final presentation

> **Not compiled: `pdflatex` and `latexmk` are not installed** (no TeX engine at all on this machine). Nothing was installed.
> **All 6 figures are missing.** There is no `figures/` directory; each slot shows a visible placeholder.
> References: **22 verified**, so no `[TO FILL]` gaps.
> **S1–S14 on slide 22 are still drafts:** `tools/required_statements.json` was not found; see SLIDES_DECISIONS.md item 17.

Started 31 Oct 2026 on `main` at `ea073d9`. Rules kept: wrote only in `slides/`, `SLIDES_STATUS.md` and `SLIDES_DECISIONS.md`; no sudo; no push.
CLAUDE.md rule 3 (wait for plan OK) was overridden by the task instruction "do not stop for plan approval".

## Compile result

Not run. To build:

```
cd slides && latexmk -pdf main.tex
```

Source checks: braces balanced, 26 `frame` environments. The references frame breaks into 2 pages, giving **27 slides**. If the reference text overflows, it may break into a third page. Overflow on frames 4–6, 20, 21 and 22 is not visually checked.

## Missing figures (placeholder shown on the slide)

| Figure | Frame |
|---|---|
| fig_training_loss | 14 |
| fig_route_timeline | 16 |
| fig_accuracy_overall | 18 |
| fig_accuracy_by_cell | 18 |
| fig_telecom_delay | 20 |
| fig_telecom_flips | 20 |

## Fact verification (brief vs repo)

All facts match the repo except the items below; details are in `SLIDES_DECISIONS.md`.
- 7511 static delay is **48.3** ms, not 48.4.
- 8336 reactive flips = **15**.
- 8336 static rep 1 has no usable server report.
- v2 numbers are confirmed, but their source (`~/fedflow_data/compare_v1_v2_val.md`) is outside the repo.
- S1, S3–S6 and S9–S14 were undefined, so I drafted them.
- Headline repetition check **passed on both cells**: every model rep is below every reactive rep.

## References (all 22 checked on 31 Oct 2026)

| # | Record checked | Year used |
|---|---|---|
| 1 Yang et al., hierarchical FRL LEO | Crossref 10.1109/JIOT.2026.3708793 | 2026 |
| 2 Da Silva et al., NetLinkClassifier | Crossref 10.1109/ACCESS.2026.3675110 | 2026 |
| 3 SDMART | Crossref 10.1007/s11227-026-08655-7 | 2026 |
| 4 Kalam et al., 5G FL dual-attention | Crossref 10.1007/s40009-026-02191-x | 2026 |
| 5 Yuliana et al., LSTM-Transformer | Crossref 10.1109/ACCESS.2026.3669215 | 2026 |
| 6 MobileLLM | Crossref 10.1109/TMC.2026.3684577 | 2026 |
| 7 Gao et al., prompt-guided LLM car-following | Crossref 10.1016/j.simpat.2026.103262 | 2026 |
| 8 Lim et al., FL mobile edge survey | Crossref 10.1109/COMST.2020.2986024 | 2020 |
| 9 Trinh et al., LSTM mobile traffic | Crossref 10.1109/PIMRC.2018.8581000 | 2018 |
| 10 Zhou et al., LLM for telecom survey | Crossref 10.1109/COMST.2024.3465447 | 2025 |
| 11 Rong et al., STGLLM-E | Crossref 10.1109/TITS.2024.3456890 | 2025 |
| 12 Yang et al., decision-making LLM survey | Crossref 10.1109/COMST.2025.3614494 | 2026 |
| 13 Barlacchi et al., Milan dataset paper | Crossref 10.1038/sdata.2015.55 | 2015 |
| 14 Telecom Italia dataset | DataCite 10.7910/DVN/EGZHFV | 2015 |
| 15 McMahan et al., FedAvg | PMLR v54 page (pp. 1273–) | 2017 |
| 16 Hu et al., LoRA | arXiv 2106.09685 page | 2021 |
| 17 Beutel et al., Flower | arXiv 2007.14390 page | 2020 |
| 18 Qwen2.5 technical report | arXiv 2412.15115 page | 2024 |
| 19 Paszke et al., PyTorch | NeurIPS 2019 proceedings page | 2019 |
| 20 McKeown et al., OpenFlow | Crossref 10.1145/1355734.1355746 | 2008 |
| 21 Lantz et al., Mininet | Crossref 10.1145/1868447.1868466 | 2010 |
| 22 Kreutz et al., SDN survey | Crossref 10.1109/JPROC.2014.2371999 | 2015 |

Unverified references: **none used**. The abstracts of items 3 (partly), 4 and 7 could not be read; items 4 and 7 are therefore kept out of the literature table.

## Slide-by-slide checklist against the professor's rules

See `slides/CHECK_SLIDES.md`. In summary:

| Rule | Status |
|---|---|
| Title | done, with placeholders |
| Problem statement | done |
| Objectives | done |
| Literature review | 3 slides, 8 rows, exact columns, 2025–2026 |
| Research gap and novelty | done |
| Methodology | 5 slides, 2 TikZ diagrams |
| Implementation | 5 slides |
| Results | 5 slides, with literature comparison |
| Conclusion | done |
| Future work | done |
| References | 22 |
| Q&A | done |
| Duration | 27:15 of speaking time |

Banned-word scan: clean (see CHECK_SLIDES.md).

## Plan

- [x] Verify every fact in the brief against repo files
- [x] Repetition check for the headline
- [x] Verify references
- [x] slides/main.tex
- [x] slides/speaker_notes.md
- [x] slides/CHECK_SLIDES.md
- [x] Banned-word scan
- [ ] Compile (blocked: no TeX)
- [x] Commit slides/ and status files only (no push)

## Files created

- `slides/main.tex`
- `slides/speaker_notes.md`
- `slides/CHECK_SLIDES.md`
- `SLIDES_STATUS.md`
- `SLIDES_DECISIONS.md`
