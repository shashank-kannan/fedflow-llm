# FedFlow-LLM: speaker notes

Total speaking time: **27:15** (1635 s), inside the 25 to 28 minute target, which leaves the 10-minute Q&A free.
Each number names the file it was read from. The same notes are in `main.tex` as `\note{}` on each frame.

| # | Frame | Time | Running total |
|---:|---|---:|---:|
| 1 | Title | 0:30 | 0:30 |
| 2 | Problem statement | 1:00 | 1:30 |
| 3 | Objectives | 1:00 | 2:30 |
| 4 | Literature review 1/3 | 0:45 | 3:15 |
| 5 | Literature review 2/3 | 0:45 | 4:00 |
| 6 | Literature review 3/3 | 0:45 | 4:45 |
| 7 | Research gap and novelty | 1:00 | 5:45 |
| 8 | Methodology 1/5: system overview | 1:30 | 7:15 |
| 9 | Methodology 2/5: data and windows | 1:00 | 8:15 |
| 10 | Methodology 3/5: federated LoRA | 1:00 | 9:15 |
| 11 | Methodology 4/5: network and controller | 1:30 | 10:45 |
| 12 | Methodology 5/5: modes, metrics, claim rule | 1:00 | 11:45 |
| 13 | Implementation 1/5: stack | 0:45 | 12:30 |
| 14 | Implementation 2/5: training | 1:00 | 13:30 |
| 15 | Implementation 3/5: procedure | 1:00 | 14:30 |
| 16 | Implementation 4/5: forecast-to-reroute | 1:30 | 16:00 |
| 17 | Implementation 5/5: reproducibility | 0:45 | 16:45 |
| 18 | Results 1/5: forecast accuracy | 1:30 | 18:15 |
| 19 | Results 2/5: routing, all modes | 1:30 | 19:45 |
| 20 | Results 3/5: telecom delay, flips, headline | 2:00 | 21:45 |
| 21 | Results 4/5: literature comparison, v2 | 1:30 | 23:15 |
| 22 | Results 5/5: limits | 1:30 | 24:45 |
| 23 | Conclusion | 1:00 | 25:45 |
| 24 | Future work | 0:45 | 26:30 |
| 25 | References 1/2 | 0:15 | 26:45 |
| 26 | References 2/2 | 0:15 | 27:00 |
| 27 | Q&A / Thank you | 0:15 | 27:15 |

---

## 1 Title (0:30)
"We are presenting FedFlow-LLM, a course project in computer networks. One question: does forecast-driven rerouting give lower delay than reactive rerouting in an emulated software-defined network?"
Numbers: none.

## 2 Problem statement (1:00)
"A reactive controller only sees load after it has arrived. If the primary link is already full, packets queue and delay rises. A forecast could, in principle, move traffic before the jump. Traffic records are per cell and sensitive, so we train with federated learning instead of pooling the data."
Numbers: none.

## 3 Objectives (1:00)
"Five objectives. Train a small language model as a traffic forecaster with federated LoRA. Connect its forecast to a POX controller that picks a path. Compare five routing modes on delay, loss and route flips. Check forecast error against repeat-last and moving-average baselines. And list the limits."
Numbers: five modes, from `experiments/run_experiment.py` (`MODES`).

## 4 Literature review 1/3 (0:45)
"Three works from 2026 that put federated learning near routing or SDN control."
Records: [1] Crossref DOI 10.1109/JIOT.2026.3708793; abstract via Semantic Scholar for that DOI. [2] Crossref DOI 10.1109/ACCESS.2026.3675110; abstract via OpenAlex. [3] Crossref DOI 10.1007/s11227-026-08655-7; the abstract sits behind the publisher's login, so the technique comes from the Semantic Scholar summary. The Cons column states how each work's scope differs from our question, based on its abstract.

## 5 Literature review 2/3 (0:45)
"Forecasting work. Note row 5 uses the same Milan data source as we do."
Records: [4] Crossref DOI 10.1109/ACCESS.2026.3669215. Its R² 0.9357 and RMSE 0.9822 come from its abstract (OpenAlex). [5] Crossref DOI 10.1109/TMC.2026.3684577. Its 0.88% to 32.62% comes from its abstract (OpenAlex). [6] Crossref DOI 10.1109/TITS.2024.3456890 (issue Oct 2025; online 17 Sep 2024). These numbers are theirs, not ours.

## 6 Literature review 3/3 (0:45)
"Two surveys that place LLM forecasting and decision making in telecom."
Records: [7] Crossref DOI 10.1109/COMST.2024.3465447 (issue June 2025). [8] Crossref DOI 10.1109/COMST.2025.3614494 (vol 28, 2026). The quoted phrase "fragmented and exploratory" is from the abstract of [8].

## 7 Research gap and novelty (1:00)
"The forecasting papers we read report forecast error and stop. The routing papers use simulators. What we add is the combination: a federated, LoRA-tuned small LLM whose forecast drives an SDN reroute decision, tested in an emulated network with a real controller. We do not claim it is the first of its kind."
Numbers: none.

## 8 Methodology 1/5: system overview (1:30)
"Left to right: traffic windows train a federated LoRA model with six clients. At run time the model's forecast becomes one number, the peak of its six predicted values. That number goes into a file. The POX controller reads the file every second; above 100 it sends traffic on the alternate path. Mininet carries the traffic."
Sources: 12 in and 6 out come from the prompt in `training/data/telecom/traffic_train.json`. The 6 clients are `NUM_CLIENTS` in `training/client.py`. The 1 s poll and the threshold of 100 are `CHECK_INTERVAL` and `THRESHOLD` in `controller/reroute_trigger.py`. The peak of 6 is in the docstring of `experiments/run_experiment.py`.

## 9 Methodology 2/5: data and windows (1:00)
"Internet activity from the Milan grid, November 2013. Six cells, one per client; the network test used cells 7511 and 8336. Each example gives 12 past values and asks for the next 6. One scale factor maps the data so that 100 means the 10 Mbps primary link."
Sources: dates, cells, split (0–1439 / 1440–1727 / 1728–2015), 10-minute slots and the scaling rule come from `datasets/telecom_milan/README.md`. The 366 test windows are in `results/final_telecom/outputs/metrics.json` and the 91 in `results/final/SUMMARY.md`.

## 10 Methodology 3/5: federated LoRA (1:00)
"Flower runs FedAvg over six simulated clients. On the telecom data, client i only sees windows from cell i. Twenty-five rounds, 200 training examples in all. Only the LoRA adapter is trained and averaged."
Sources: `training/client.py` holds rank 8, alpha 16, `q_proj`/`v_proj`, dropout 0.05, lr 1e-4 and the model name. `training/server.py` holds `NUM_ROUNDS` = 25 and FedAvg. The 200 examples are the length of `training/data/telecom/traffic_train.json`. Client i gets cell i because `train_starts.json` cycles through cells 0–5 and the client takes every 6th example.

## 11 Methodology 4/5: network and controller (1:30)
"Two hosts, four switches. The primary path through s3 is 10 Mbps; the alternate through s4 is 50 Mbps. The topology has a loop, so the controller never floods; it uses fixed tables, and the hosts have static ARP. Every second it reads the forecast file: above 100 means alternate."
Sources: the topology and link rates are in `controller/topo.py` and `CLAUDE.md`. The rule "> 100 means alternate" is `decide_path` in `controller/reroute_trigger.py`.

## 12 Methodology 5/5: modes, metrics, claim rule (1:00)
"Five modes differ only in the number written to the file each step. Static never leaves the primary path, alt never leaves the alternate, oracle sees the true future, reactive sees the last true value, and model uses the forecast. We say 'lower' only if all three model runs sit below all three reactive runs on a cell."
Sources: the mode definitions are in `experiments/run_experiment.py`. The metrics are columns of `summary.csv`. The claim rule comes from the task brief (see SLIDES_DECISIONS.md).

## 13 Implementation 1/5: stack (0:45)
"Training uses Qwen2.5-1.5B-Instruct with PEFT and PyTorch, inside Flower. The network side is Mininet with a POX controller; iperf makes the UDP load and ping measures delay."
Sources: the imports in `training/client.py`; iperf 2.1.5 is named in the docstring of `experiments/run_experiment.py`.

## 14 Implementation 2/5: training (1:00)
"Training ran on Colab with one T4 GPU. Loss fell from 1.711 after round 1 to 0.608 after round 25. This is training loss on training examples, so it says nothing about forecast quality; forecast quality is on slide 18."
Sources: 1.711 and 0.608 are rounds 1 and 25 of `results/final_telecom/outputs/loss_history.csv` (1.7109, 0.6077). The T4 is from `CLAUDE.md`. `README.md` says the loss is measured on training examples.

## 15 Implementation 3/5: procedure (1:00)
"Each cell gets one 36-step trace, picked from the true traffic by a rule fixed before training. Each step sends 5 seconds of UDP at v over 10 megabits per second. Every mode is repeated three times on the same trace."
Sources: `TRACE_LEN` 36, `STEP_SECONDS` 5 and `REPS` 3 are in `experiments/run_experiment.py`. The slice starts 1837 and 1960, with 8 crossings each, are in `datasets/telecom_milan/README.md`. The synthetic start 1452 with 4 crossings is in `results/experiment/README.md`.

## 16 Implementation 4/5: forecast-to-reroute (1:30)
"At each step the model mode writes the peak of the latest forecast whose history ends before this step. The controller reads it within a second and flips if needed; a flip deletes the flows, which are reinstalled on the next packet. For scoring, an onset is a window where the last known value is at or below 100 but the true peak goes above 100. The model catches it if its own peak is above 100."
Sources: the docstring of `experiments/run_experiment.py`, `controller/reroute_trigger.py`, and the onset definition in `results/final_telecom/SUMMARY.md`.

## 17 Implementation 5/5: reproducibility (0:45)
"Every run keeps its raw ping, iperf, server, POX and step files. The summary table is rebuilt from those by a script. Cells, scaling and traces were fixed before any training. What we did not run: a moving-average forecast in the routing loop, and any statistical test."
Sources: `results/experiment/README.md`, `experiments/summarize.py`, `datasets/telecom_milan/README.md`. The moving-average mode exists on branch `baseline-check` but was not run.

## 18 Results 1/5: forecast accuracy (1:30)
"On the telecom test set the model's mean absolute error is 15.14, against 16.51 for repeat-last and 15.58 for a moving average. On RMSE the moving average is lower: 23.95 against 24.76. The model caught 6 of 14 onsets on cell 7511 and 4 of 14 on 8336."
Sources: telecom MAE and RMSE (15.138, 16.511, 15.583; 24.759, 26.161, 23.951) are in `results/final_telecom/outputs/metrics.json`. Synthetic MAE 10.34, 11.29 and 10.86 are in `results/final/SUMMARY.md`. Onsets 6/14 and 4/14 are in `results/final_telecom/SUMMARY.md`.

## 19 Results 2/5: routing, all modes (1:30)
"All five modes on three traces. On synthetic data, reactive was lower than the model: 9.75 against 24.84 ms. On both Milan cells, the model was lower than reactive. Always using the alternate path gave the lowest delay everywhere, because in this topology the alternate path is simply faster and has no cost."
Each value is the mean of the 3 `ping_mean_ms` rows.
- Synthetic, `results/experiment/summary.csv`: 43.127, 9.754, 24.837, 0.111, 0.111
- 7511, `results/experiment_telecom/7511/summary.csv`: 48.322, 16.056, 9.532, 0.184, 0.176
- 8336, `results/experiment_telecom/8336/summary.csv`: 58.896, 13.911, 7.490, 0.208, 0.183

UDP loss: `server_udp_loss_pct` is 0.0 in every row except 8336 static rep 1, which is "server report count mismatch" and not scored. Its client-side loss is 0.0.

## 20 Results 3/5: telecom delay, flips, headline (2:00)
"This is the headline. On both Milan cells, the model mode had lower mean ping delay than reactive: 9.5 against 16.1 ms on 7511, and 7.5 against 13.9 on 8336. On each cell, every model run was below every reactive run. But read the two lines under it. The model wrote a value above 100 on more steps, so it spent more time on the faster path; part of the gain may come from that, not from better forecasts. We did not test whether the forecast's content matters, and there is no statistical test. The model also flipped routes less: 5 and 3 times per run against 15."
Repetition check (`ping_mean_ms`): it passed on both cells.
- 7511: model 9.98, 8.90, 9.71; reactive 15.65, 16.09, 16.43
- 8336: model 7.85, 7.10, 7.52; reactive 13.33, 14.61, 13.80

The shares are `frac_written_above_100` (0.7222 and 0.6111 on 7511; 0.8889 and 0.7778 on 8336). The flips are `flip_lines`: 7511 reactive 15, model 5; 8336 reactive 15, model 3. Both are in the two telecom `summary.csv` files.

## 21 Results 4/5: literature comparison, v2 (1:30)
"We compare with three recent works in the same area. None is like-for-like: different data, scaling, horizon and metric. So these rows show where we sit, not who is ahead. Below: a second model, v2, trained to catch more jumps. On validation it caught 17 of 29 onsets against 11, but calm false alarms rose from 4 of 110 to 16 of 111 and MAE rose from 15.00 to 15.78. Under rules written before the run, it was not adopted."
Sources: the literature numbers come from the abstracts of DOIs 10.1109/TMC.2026.3684577, 10.1109/ACCESS.2026.3669215 and 10.1109/JIOT.2026.3708793. The v2 numbers come from `~/fedflow_data/compare_v1_v2_val.md`, outside the repo, written by `training/compare_variants.py` on branch `v2`. That file's decision line is "DO NOT ADOPT".

## 22 Results 5/5: limits (1:30)
Read S1, S2, S5 and S11 aloud; keep the rest for Q&A. Wording is verbatim from `tools/required_statements.json`. The slide shows the approved one-line versions.
- **S1** Each experiment cell replays one 36-step trace three times, so the repetitions show repeatability, not variety. (Source: `results/experiment_telecom/7511/summary.csv`, `results/experiment_telecom/8336/summary.csv`.)
- **S2** On both telecom cells the model wrote a value above 100 (alternate path) on more steps than reactive routing did (26 vs 22 steps on cell 7511, 32 vs 28 steps on cell 8336), so part of its delay gain may come from using the faster path more, not from better forecasts. (Source: counted from `raw_model_*_steps.csv` and `raw_reactive_*_steps.csv` (value_written > 100) in `results/experiment_telecom/7511/` and `8336/`; identical in all 3 reps.)
- **S3** UDP packet loss was 0% in every scored run because the 10 Mbps link slowed the sender instead of dropping packets; we did not verify that mechanism, so loss does not separate the modes. (Source: server_udp_loss_pct in the three `summary.csv` files; `results/experiment/README.md`.)
- **S4** The controller logs contain repeated Python AttributeError lines and large numbers of 'using alt path' log lines after route flips (for example 1060 lines for one switch in one step of a quick run). We did not establish the cause. POX kept running and every run completed, and the same controller was used in all experiments, so modes are compared only with each other and absolute numbers are not claimed. (Source: `results/experiment_telecom/7511/quick/raw_reactive_1_pox.txt`: 1060 `using alt path' lines for switch 2 in step 4 (forecast 106.72), starting at the FLIP on log line 331; 9 AttributeError lines.)
- **S5** We did not test whether the forecast's content matters: no experiment replaced the model with a simple forecast that has the same timing. (Source: modes in `experiments/run_experiment.py`; ma/persist modes exist on branch baseline-check, not run.)
- **S6** The telecom data is from Milan, November 2013, scaled to a unitless load where 100 stands for the 10 Mbps primary link. (Source: `datasets/telecom_milan/README.md`.)
- **S7** On the synthetic data the model's forecasts did not beat reactive routing on mean delay (24.84 ms vs 9.75 ms). (Source: `results/experiment/summary.csv`.)
- **S8** An attempt to improve the model (v2) caught more jumps (17 vs 11 pooled onset windows on validation) but raised calm false alarms (16 of 111 vs 4 of 110) and mean error (15.78 vs 15.00). It was not adopted under rules written before the run, and v1 remains the final model. The v2 attempt was designed after the v1 test results were known and was judged on a separate validation block. (Source: `~/fedflow_data/compare_v1_v2_val.md`.)
- **S9** Jump (onset) recall is modest and can be reported only for the telecom cells with at least 10 onset windows; the windows overlap, so they are not independent samples. (Source: `results/final_telecom/outputs/forecasts.csv`: 7511 6 of 14, 8336 4 of 14 onsets caught; other cells under 10 onset windows.)
- **S10** Training loss shows that training ran and converged. It is not a measure of forecast quality, because in v1 it was computed over every token of the training text, prompt and padding included. (Source: `training/client.py` lines 143 and 173: labels=input_ids, no masking, padding to 256 tokens.)
- **S11** The forecasts used in the experiments came from one training run on a Colab T4 GPU. Run-to-run variation in training was not measured. A local re-run of 20 test windows with the same adapter matched the Colab forecasts on 89 of 120 values (largest difference 4.3); beyond that the effect of different GPUs was not measured, so numbers from different GPUs are not mixed. (Source: `~/fedflow_data/local_val/training/outputs/forecasts.csv` vs `results/final_telecom/outputs/forecasts.csv`; adapters byte-identical.)
- **S12** The test block was scored once and the model was not tuned on it. (Source: task statement; not checkable from a single file.)
- **S13** All routing results come from an emulated network (Mininet with POX), not a real network. (Source: `controller/topo.py`, `controller/reroute_trigger.py`.)
- **S14** Dataset: Telecom Italia Big Data Challenge, Milan, November 2013, Harvard Dataverse DOI 10.7910/DVN/EGZHFV; attribution and licence terms are in datasets/telecom_milan/NOTICE.md. (Source: `datasets/telecom_milan/NOTICE.md`, `datasets/telecom_milan/README.md`.)

## 23 Conclusion (1:00)
"We built a federated LoRA forecaster, connected it to a POX controller, and measured five routing modes in Mininet on three traces. On the two Milan cells the model mode had lower mean delay than reactive, 9.5 against 16.1 and 7.5 against 13.9 ms. On the synthetic trace it did not, 24.84 against 9.75. Part of the Milan gain may come from simply using the faster path more."
Sources: the same as slides 19 and 20.

## 24 Future work (0:45)
"First, the key missing test: run a moving-average forecast through the same loop with the same timing. If it gives the same delay, the forecast's content is not what matters. The code for that mode exists on the baseline-check branch but has not been run. Then more cells and traces, a cost on the alternate path so that 'always alternate' is not free, more runs with a proper test, and a held-out loss."
Numbers: none.

## 25–26 References (0:15 each)
22 entries. Each was checked against its DOI record (Crossref or DataCite), its arXiv page, the PMLR page or the NeurIPS proceedings page on 31 Oct 2026. Do not read them aloud.

## 27 Q&A / Thank you (0:15)
"Thank you. We are happy to take questions."
Likely questions: why alt is lowest (slide 19), why the synthetic result differs (S7), and whether the gain comes from the forecasts (S2, S5).
