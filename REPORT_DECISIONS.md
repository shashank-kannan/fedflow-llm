# REPORT_DECISIONS: open points that change what the report claims

Each item is waiting for the user unless marked resolved.

1. **RESOLVED (31 Oct 2026): the user confirmed the computed values 48.3 and 16.1 ms.** Original note: two sanity facts differ from the computed values (Phase 1, `report/generated/sanity.txt`).
   - Cell 7511 static mean ping: computed **48.3219** ms → 48.3; the task expects ~48.4. Runs: 47.38, 49.90, 47.69 (`results/experiment_telecom/7511/summary.csv`).
   - Cell 7511 reactive mean ping: computed **16.0562** ms → 16.1; the task expects ~16.0. Runs: 15.65, 16.09, 16.43 (same file).
   - The other 41 facts pass, including UDP loss 0 in every scored run.
   - The slide deck already uses 16.1 (decision 19 in `SLIDES_DECISIONS.md`). The report will use the computed values (48.3, 16.1) once confirmed.
2. **Task text is cut off.** It ends in Phase 3 at "Technique and inference come from the abstract you". The rest of Phase 3 and every later phase (writing the report, humanizing, Overleaf packaging) were not received.
3. **"humanizer" skill not found.** It is not in this session's skill list and there is no skill folder under `~/.claude/skills` or in the repo. Prose can't be run through it until it is installed or its rules are pasted.
4. **Roll number for STUDENT_2.** Given as `CB.AI.U4ADI25120` ("ADI"); the other three use "AID". It will be used exactly as given unless corrected.
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
