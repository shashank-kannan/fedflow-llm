# REPORT_DECISIONS: open points that change what the report claims

Each item is waiting for the user unless marked resolved.

1. **RESOLVED (31 Oct 2026): the user confirmed the computed values 48.3 and 16.1 ms.** Original note: two sanity facts differ from the computed values (Phase 1, `report/generated/sanity.txt`).
   - Cell 7511 static mean ping: computed **48.3219** ms → 48.3; the task expects ~48.4. Runs: 47.38, 49.90, 47.69 (`results/experiment_telecom/7511/summary.csv`).
   - Cell 7511 reactive mean ping: computed **16.0562** ms → 16.1; the task expects ~16.0. Runs: 15.65, 16.09, 16.43 (same file).
   - The other 41 facts pass, including UDP loss 0 in every scored run.
   - The slide deck already uses 16.1 (decision 19 in `SLIDES_DECISIONS.md`). The report will use the computed values (48.3, 16.1) once confirmed.
2. **PARTLY RESOLVED (part 1 received 31 Oct 2026; part 2 pending).** Task text is cut off. It ends in Phase 3 at "Technique and inference come from the abstract you". The rest of Phase 3 and every later phase (writing the report, humanizing, Overleaf packaging) were not received.
3. **"humanizer" skill not found.** It is not in this session's skill list and there is no skill folder under `~/.claude/skills` or in the repo. Prose can't be run through it until it is installed or its rules are pasted.
4. **RESOLVED: STUDENT_2 roll number is `CB.AI.U4AID25120`** (the user corrected "ADI" to "AID").
5. **Roll number for STUDENT_1 changed.** It is now `CB.AI.U4AID25150`; the slide deck has `CB.AI.U4AID125150` from the earlier message. The report will use the new one; the deck is unchanged until asked.
6. **Slope baseline on the test blocks: not computed.** The test `forecasts.csv` and `metrics.json` (synthetic and telecom) have no slope column; only the validation files do. No value is derived.
7. **Synthetic per-cell results: not applicable.** The synthetic data is one series, so "per cell" exists only for the telecom and validation blocks.
8. **Template location.** The zip was not in `templates/`; it was copied from `/mnt/c/Users/shash/Downloads/23AID206_report_template.zip` (sha256 `2bd37b1b…`, identical to the original).
9. **The template has no Results chapter.** Its "Organization of the Report" lists "Chapter 4: Results and Discussion", but its skeleton goes Introduction, Background, Proposed Work, Conclusion. Waiting on the report-writing instructions; the likely choice is to add the Results chapter the template's own outline names.

## Facts confirmed in Phase 1 (from code)

- Base model `Qwen/Qwen2.5-1.5B-Instruct`, loaded in **float16, not 4-bit**, so the method is **LoRA, not QLoRA**.
- LoRA r = 8, alpha = 16, targets `q_proj`, `v_proj`, dropout 0.05.
- Loss tokens: `labels=input_ids` in both fit and evaluate, no label set to -100 (no masking), padding to `max_length` = 256. The loss covers prompt, answer and padding.
- 36 steps of 5 s, 5 modes, 3 reps (`experiments/run_experiment.py`). 25 rounds (`training/server.py`), 6 clients (`training/client.py`), 200 training examples (each `traffic_train.json`), 12 history and 6 future values (`training/generate_data.py`), threshold 100 and 1 s polling (`controller/reroute_trigger.py`).
- No `run_config.json` exists for the v1 run (only v2 runs write one), so the v1 constants come from code.

## Phase 3 (references), 31 Oct 2026

10. **24 usable references, 0 unusable.** Each record was opened (Crossref for DOIs, DataCite for the dataset, the arXiv page, the PMLR page) and its title matched. Every seed IEEE document number and the ScienceDirect PII match the DOI record's landing URL (`references/verification_log.csv`). The four works added for the "further 2021–2026" requirement are: Kim et al. 2022 (IEEE Access, DRL routing on SDN), Ma et al. 2025 (IEEE TNSE, federated cellular traffic prediction), Sun et al. 2025 (IEEE IoT-J, LLM network traffic prediction) and Lv et al. 2025 (Computer Networks, LLM base-station traffic prediction).
11. **Years follow the DOI record's issue year.** Zhou et al. is 2025, Rong et al. 2025 and Yang et al. (decision-making survey) 2026, although each appeared online a year earlier. Trinh et al. is 2018 per the record (the seed list doubted the year). The 2018 and 2020 works stay in the reference list but not in the literature table.
12. **Short record titles used as-is.** Crossref titles the OpenFlow paper "OpenFlow" and the Mininet paper "A network in a laptop". `refs.bib` uses those record titles, as the rule requires, not the longer titles usually cited.
13. **Four usable works are not in the literature table** because no abstract could be read (publisher login; none on Crossref, OpenAlex or Semantic Scholar): SDMART (Sadeghi), Kalam et al., Gao et al. and Lv et al. (Betastack). They stay in `refs.bib` and can be cited for their title-level topic only. The table has 10 rows, all 2021–2026.
14. **RESOLVED by part 1:** Cons = what the abstract shows the work does not address relative to our problem; no flaw the abstract does not show. Four "Centralised" claims the abstracts do not state were removed (`tools/build_lit_table.py`). Original note: literature-table "Cons" column = scope difference from this project's question, read from each abstract (for example "no routing action"). The instruction text was cut off at "Technique and inference come from the abstract you", so the rule for Cons was not received. Other papers' numbers are left out of the table so that no number is typed by hand.
15. **"Each reference cited at least once"** can only be checked once the report text exists (a later phase).

## Phase 4 (fixed statements), 31 Oct 2026

16. **`tools/required_statements.json` now holds S1–S16 for the report** (it replaces the slide-era S1–S14; that version is in git history at `7582ab8`). The text is verbatim from part 1. Meta notes such as "(Fill by counting…)" and "(proposed addition…)" are not part of the statements.
17. **Deviation, S2 fill:** counted from every `raw_*_steps.csv` (value_written > 100, identical in all 3 runs): 26 vs 22 on cell 7511, 32 vs 28 on cell 8336. These match the expected values.
18. **Deviation, S4 fill:** the rule's first wording is used. Evidence: the quick pipeline-test run is `results/experiment/quick` (synthetic, oracle mode). The runner's own `write_forecast()` in `experiments/run_experiment.py` rewrites the forecast file at the start of every step. `raw_oracle_1_steps.csv` shows 152.46 written at four separate times (01:15:42.241, :48.853, :55.438, 01:16:02.047). The value really repeats: those steps take the oracle peak of windows 1443 and 1446, and both true peaks are 152.46 in `results/final/outputs/forecasts.csv`. Switch 4 has exactly 32 "using alt path" lines (switch 1 has 25, switch 2 has 21), and the log has 2 AttributeError lines. `controller/write_forecast.py` is the manual tool used in the live demo, not in these runs. This is not a top-of-file issue, because the file was updated.
19. **RESOLVED (31 Oct 2026): the user chose to keep S11 as written (the 89-of-120 wording).** Deviation, S11: part 1's S11 says the 20-row GPU check "was not carried out". The files show one exists: `~/fedflow_data/local_val/training/outputs/forecasts.csv` re-ran 20 test windows (120 values) with an adapter byte-identical to the Colab one, and 89 of 120 values match (largest difference 4.3). As part 1 instructs, this is reported to the user. Meanwhile S11 holds the wording the user chose for this finding earlier ("wording A", 31 Oct 2026).
20. **Deviation, headline:** the fixed headline reads "9.5 vs 16.0 ms on cell 7511". The user confirmed the computed 16.1 (item 1), so the report will write 16.1. The claim rule passes on both cells (model max 9.98 < reactive min 15.65; model max 7.85 < reactive min 13.33). The headline is not a key in the S1–S16 file.
21. **S15 and S16 included as proposed** (delete on request). S15's -44.04 and -33.36 match `numbers.json` (computed from forecasts.csv). S16 matches `training/client.py` line 168 (`self.examples[:10]`).
