# CHECK_SLIDES: frame-by-frame check against the professor's rules and the brief

Not compiled (no `pdflatex`/`latexmk` on this machine), so layout and overflow are **not visually verified**.
Source checks done: braces balanced; 26 `frame` environments, and the references frame uses `allowframebreaks` with one manual `\framebreak`, so the deck should come out at 27 slides. If the reference text overflows, it can break into a third page (28 slides); check after the first compile.

| # | Frame | Professor's rule | Content check | Figure/table/diagram | Notes with sources |
|---:|---|---|---|---|---|
| 1 | Title | 1 Title slide | placeholders [TEAM MEMBER NAMES], [ROLL NUMBERS] left in | – | yes |
| 2 | Problem statement | 2 | 5 bullets | – | yes |
| 3 | Objectives | 3 | 5 items | – | yes |
| 4–6 | Literature review 1/3–3/3 | 4: table, ≤3 slides, recent works | exact columns; 3/3/2 rows; 2025–2026 works only; `\footnotesize` = 9 pt | table | DOI record per row |
| 7 | Research gap and novelty | 5 | novelty = combination; no "first" claim | – | yes |
| 8–12 | Methodology 1/5–5/5 | 6: ≤5 slides | flowchart (TikZ), topology (TikZ), modes table, claim rule | TikZ ×2, tables | yes |
| 13–17 | Implementation 1/5–5/5 | 7: ≤5 slides | stack, training, procedure, reroute logic, reproducibility | 2 figure slots, tables | yes |
| 18–22 | Results 1/5–5/5 | 8: ≤5 slides, ≥1–2 literature comparisons | lit comparison on 21 with 3 works labelled "not like-for-like" | 4 figure slots, tables | yes |
| 23 | Conclusion | 9 | 5 bullets | – | yes |
| 24 | Future work | 10 | item 1 = moving-average forecast, same timing | – | yes |
| 25–26 | References | 11: 20–25 | 22 entries, all checked | – | yes |
| 27 | Q&A / Thank you | 12 | – | – | yes |

## Brief-specific checks

- Headline on frame 20, together with S2 and S5: **yes**. Repetition check passed on both cells (7511: model max 9.98 < reactive min 15.65; 8336: model max 7.85 < reactive min 13.33), so "lower" is used for both.
- S7 and S1 on frame 19: **yes**. S8 and the v2 table on frame 21: **yes**. All 14 S-lines on frame 22, with full wording in the notes: **yes**.
- Each figure keeps its caveat on the same slide: frame 14 (loss ≠ forecast quality), 16 (polling lag), 18 (scaled units, overlapping windows), 20 (S2, S5 and the share of steps written above 100).
- Banned words ("proves", "significant", "wins", "beats", "outperforms"): searched with `grep -i -E 'prove|significan|\bwins?\b|\bbeat|outperform'` over `main.tex` and `speaker_notes.md`. Remaining hits: "improved" inside the published title of reference [3], and "did not beat" in S7, a negation that is allowed.
- Mode colours: static grey, reactive orange, model blue, oracle green, alt purple. They are set once as macros and used in every table and text mention. The colours inside the figure files depend on the figure step.
- Slide numbers: the Madrid footline shows them.
- Timing: 27:15 in total (`speaker_notes.md`).
