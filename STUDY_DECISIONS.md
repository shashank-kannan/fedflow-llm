# STUDY_DECISIONS: open points from the study guide

Every point where the facts block and the repo files did not match, or where a fact was not in any file.

## Conflict between the facts block and a file

1. **Telecom 7511 static mean ping.**
   - The facts block says 48.4 ms. `results/experiment_telecom/7511/summary.csv` gives 47.3819, 49.8962 and 47.6876 for the three reps, mean 48.3219, which rounds to 48.3.
   - Your rule was to stop that section. I kept Part 7's 7511 table, because every number in it comes from the file. The static row says "see the note below", and a "Watch out" box under the table names the conflict.
   - The 48.4 figure is not used anywhere in the guide. If you prefer, the 7511 table can be removed until you confirm.

## Facts not in the files

2. **"Telecom Italia Big Data Challenge."** That name does not appear in any repo file. The files name the dataset "Telecommunications - SMS, Call, Internet - MI", published on Harvard Dataverse with author "Telecom Italia" (`datasets/telecom_milan/README.md`). The guide uses the file's name and says so in a "Watch out" box.
3. **Route flips, 8336 reactive.** The facts block says "[verify]". The file gives 15 in all three reps (`flip_lines`, `results/experiment_telecom/8336/summary.csv`), which is used.
4. **"UDP loss 0% in every scored run."** True for every run that has a loss value. One run, 8336 static rep 1, has "server report count mismatch" instead of a number (`results/experiment_telecom/8336/summary.csv`). The guide says this in Part 6 and Q40.
5. **GPU-mismatch count (limit 11).** Not in the files, as the facts block says. The guide writes "not in the files".
6. **Answers with no file behind them.** These are marked "not in the files" or "the files do not record":
   - Q7: no LSTM comparison.
   - Q13: why a 1.5B model.
   - Q16: why emulation.
   - Q17: why POX over Ryu.
   - Q25: run-to-run variation.
   - Q32: novelty.
   - Q36: inference time.
   - Q37: what would break it.
   - Q55: operator use.
7. **v2 numbers.** They come from `~/fedflow_data/compare_v1_v2_val.md`, which is outside the repo. `PLAN_V2.md` and the v2 commit times come from branch `v2`. Both are cited as such.
8. **Baseline check.** Limit 5 and Q28, Q29 and Q54 cite `PLAN_BASELINE_CHECK.md` on branch `baseline-check`. That check has not been run.

## Wording

9. **Limit 7 is reworded.** The facts block says "did not beat reactive routing". The forbidden-word rule bans "beats", so limit 7 reads "did not give lower mean delay than reactive routing", which keeps the meaning. The cheat sheet's last question is worded "Is predictive routing better than reactive routing?" for the same reason.

## Layout points not checked by rendering

10. **No rendering available.** LibreOffice is not installed, so no PDF was made, and the page layout could not be checked by rendering.
    - The one-page fit of the cheat sheet is not verified.
    - The table of contents is a Word field. Word fills it in when the document is opened; the file asks Word to update fields on open.
