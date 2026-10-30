# FedFlow-LLM: Study Guide

Every number is followed by the file it comes from, in square brackets.

# 1. The project in one page

> **In one line:** Can a traffic forecast move data to a fast path before the slow path jams, giving less delay than reacting after the jam?

## The question

Does forecast-driven (predictive) rerouting give lower delay than reactive rerouting in an emulated software-defined network [CLAUDE.md]?

**Reactive** routing uses the true traffic of the previous 5-second step. **Predictive** routing uses the highest of the model's 6 forecast values. Both go through the same controller rule: above 100 means the fast path [experiments/run_experiment.py, controller/reroute_trigger.py].

## The pipeline

```
Milan traffic (6 cells, 10-min slots, scaled so 100 = 10 Mbps)
   -> Qwen2.5-1.5B + LoRA, trained by 6 federated clients (Flower, FedAvg, 25 rounds)
   -> forecasts.csv: next 6 values for each test window (made in advance)
   -> each 5 s step: one value written to forecast_value.txt
   -> POX controller, every 1 s: value > 100 ?
   -> no: primary path s1-s3-s2 (10 Mbps)   yes: alternate path s1-s4-s2 (50 Mbps)
```

> **Watch out:** The model did not run live. Its forecasts were computed in advance and replayed from forecasts.csv [experiments/run_experiment.py].

## The headline

On the two Milan cells tested, forecast-driven routing gave lower mean ping than reactive routing: 9.5 against 16.0 ms on cell 7511, and 7.5 against 13.9 ms on cell 8336. On each cell, every model repetition was below every reactive repetition [results/experiment_telecom/7511/summary.csv, results/experiment_telecom/8336/summary.csv].

> **Watch out:** The model also sent more steps to the fast path than reactive did, each cell replays one trace, and on synthetic data the model had higher delay than reactive.

# 2. How it was built

## Data

Real internet activity from Milan, 1 to 14 November 2013, Telecom Italia, Harvard Dataverse DOI 10.7910/DVN/EGZHFV [datasets/telecom_milan/README.md]. Each **cell** is one square of the city grid; six were chosen by a fixed rule, and 7511 and 8336 are the experiment cells [datasets/telecom_milan/README.md].

Values are multiplied by one factor, k = 2.3306204138, so that 100 stands for the 10 Mbps slow link [datasets/telecom_milan/README.md]. This is a modelling choice, not measured Mbps.

| Block | Slots | Used for |
|---|---|---|
| Training | 0 to 1439 | learning |
| Validation | 1440 to 1727 | choosing between v1 and v2 |
| Test | 1728 to 2015 | final score, used once |

A made-up synthetic series was used first, as a controlled test of the pipeline [README.md].

## Model and training

| Item | Value | Source |
|---|---|---|
| Model | Qwen2.5-1.5B-Instruct | training/client.py |
| LoRA | rank 8, alpha 16, q_proj and v_proj, dropout 0.05 | training/client.py |
| Federated setup | Flower, FedAvg, 6 clients, 25 rounds | training/server.py |
| Data | 200 examples; client i sees only cell i | training/generate_data.py, training/client.py |
| Input and output | 12 past values in, "PREDICTION: v1, ..., v6" out | training/generate_data.py |

**LoRA** trains a small add-on (the adapter) instead of the whole model, so it fits on one Colab T4 GPU. In **federated learning**, each client trains on its own data and only the adapter is averaged by the server (**FedAvg**).

## The network test

Mininet emulates host h1 on switch s1 and host h2 on switch s2, joined by a 10 Mbps primary path and a 50 Mbps alternate path [controller/topo.py]. The POX controller reads the forecast file every second and switches paths at 100 [controller/reroute_trigger.py].

| Mode | Value written each step |
|---|---|
| static | 0: always the slow path |
| reactive | true value of the previous step |
| model | highest of the model's 6 forecasts |
| oracle | highest of the 6 true future values (perfect forecast) |
| alt | 1000: always the fast path |

Each run replays a 36-step trace of 5-second steps; step value v becomes v/10 Mbps of UDP traffic, and ping runs every 0.2 s [experiments/run_experiment.py]. Each mode runs 3 times per cell [experiments/run_experiment.py]. The main measure is mean **ping**, the round-trip time of a small packet.

# 3. Results

## Routing delay, telecom

> **Watch out:** The model used the fast path at more steps than reactive, so part of its gain may come from that rather than from better forecasts.

| Mode | 7511: mean ping, ms | 8336: mean ping, ms | Steps above 100 (7511 / 8336) |
|---|---|---|---|
| static | 48.32 | 58.90 | 0 / 0 |
| reactive | 16.06 (15.65 to 16.43) | 13.91 (13.33 to 14.61) | 22 / 28 of 36 |
| model | 9.53 (8.90 to 9.98) | 7.49 (7.10 to 7.85) | 26 / 32 of 36 |
| oracle | 0.18 | 0.21 | 36 / 36 |
| alt | 0.18 | 0.18 | 36 / 36 |

Ranges are the min to max of the 3 repetitions [results/experiment_telecom/7511/summary.csv, results/experiment_telecom/8336/summary.csv]. Your notes give 7511 static as 48.4; the file says 48.32 (see STUDY_DECISIONS.md).

## Routing delay, synthetic

> **Watch out:** Here the result goes the other way.

| Mode | Mean ping, ms | Steps above 100 |
|---|---|---|
| reactive | 9.75 | 0.6111 of steps |
| model | 24.84 | 0.3333 of steps |

On synthetic data the model stayed on the slow path more, and its delay was higher than reactive's [results/experiment/README.md].

## Forecast accuracy, telecom test (366 windows)

| Method | MAE | RMSE |
|---|---|---|
| Model | 15.14 | 24.76 |
| Repeat last value | 16.51 | 26.16 |
| Moving average of last 3 | 15.58 | 23.95 |

**MAE** is the average error; **RMSE** weights big errors more. The model's MAE is lowest, but its RMSE is higher than the moving average's [results/final_telecom/outputs/metrics.json]. On the synthetic test (91 windows) the model's MAE was 10.34, against 11.29 and 10.86 [results/final/outputs/metrics.json].

## Catching threshold crossings

An **onset** is a window where traffic is at or below 100 now and goes above 100 within the next 6 steps. The model foresaw 6 of 14 onsets on cell 7511 and 4 of 14 on cell 8336; the windows overlap, so these are not independent [results/final_telecom/SUMMARY.md].

## The v2 attempt

v2 changed three things: loss on answer tokens only, the time of day in the prompt, and more onset examples in training [PLAN_V2.md, branch v2]. Its four pass rules were written before it ran, and it was judged on the validation block.

| Rule | v1 | v2 | Passed |
|---|---|---|---|
| MAE lower | 15.00 | 15.78 | no |
| Onset recall higher | 11 of 29 | 17 of 29 | yes |
| False alarms within 5 points | 4 of 110 | 16 of 111 | no |
| Parse failures no more | 1 | 0 | yes |

v2 failed two rules, so v1 stayed final [~/fedflow_data/compare_v1_v2_val.md].

# 4. Limits (say these before you are asked)

1. Each cell replays one 36-step trace three times: repeatability, not variety.
2. The model used the fast path more than reactive (26 against 22 of 36 steps on 7511, 32 against 28 on 8336), so part of the gain may come from that [results/experiment_telecom/*/summary.csv].
3. UDP loss was 0% in every scored run, probably because the slow link slowed the sender; not verified, so loss does not separate the modes [results/experiment/README.md].
4. The controller logs contain repeated Python AttributeError lines and bursts of "using alt path" lines after flips; the cause is not established [results/experiment_telecom/*/raw_*_pox.txt].
5. Not tested: whether the forecast's content matters. No run replaced the model with a simple forecast of the same timing.
6. The data is from Milan, November 2013, rescaled to a unitless load.
7. On synthetic data the model did not give lower mean delay than reactive.
8. v2 was designed after the v1 test results were known; it was judged on validation and not adopted.
9. Onset recall is modest (6 of 14, 4 of 14) and the windows overlap.
10. Training loss is not forecast quality; in v1 it covered every token, prompt and padding included [training/client.py].
11. One training run on a Colab T4; run-to-run variation not measured; GPU-mismatch count not yet computed.
12. The test block was scored once and not tuned on.
13. All routing results come from an emulated network, not a real one.
14. Dataset attribution and licence: datasets/telecom_milan/NOTICE.md. No licence conclusion is stated here.

No statistical test was run; no file shows one.

# 5. Hard questions, short answers

**Why an LLM and not an LSTM?** Not compared; the files hold no LSTM or statistical-model test. Only repeat-last and moving average were compared.

**Is the model better than a moving average?** Mixed: lower MAE (15.14 against 15.58) but higher RMSE (24.76 against 23.95) [results/final_telecom/outputs/metrics.json].

**Did the model run live?** No. Forecasts were precomputed and replayed [experiments/run_experiment.py].

**If the model mostly uses the fast path, is it forecasting?** Not separated yet. It caught some onsets (6 of 14, 4 of 14), but no same-timing simple forecast was tested.

**Why 100?** It is defined as the 10 Mbps capacity of the slow path; the data is scaled to match [datasets/telecom_milan/README.md].

**Why federated?** To imitate sites that keep their data private. Federated was not compared with central training.

**Is each client a separate model?** No. FedAvg averages the six adapters each round into one shared model [training/server.py].

**Why 3 repetitions? Why no significance test?** 3 was the design; they replay the same trace. No statistical test was run.

**Does a falling training loss mean it works?** No. Loss fell from 1.71 to 0.61, but that is fit to training text, not forecast quality [results/final_telecom/outputs/loss_history.csv].

**Why was v2 not used?** It failed two of four pre-written rules: higher MAE and many more false alarms.

**Did you tune on the test data?** No. The test block was scored once; v2 was judged on validation.

**Why does it do worse on synthetic data?** Not established. There the model went above 100 at fewer steps than reactive (0.3333 against 0.6111) [results/experiment/README.md].

**What next?** First, test simple forecasts with the same timing; then more traces, more training runs and an agreed statistical test.

# 6. Cheat sheet

**Question:** Does predictive rerouting give lower delay than reactive rerouting, in an emulated network?

**Pipeline:** Milan traffic, then federated LoRA Qwen2.5-1.5B, then precomputed forecasts, then the POX controller (above 100 means the fast path), then Mininet.

| Number | Meaning |
|---|---|
| 9.53 vs 16.06 ms | model vs reactive, cell 7511 |
| 7.49 vs 13.91 ms | model vs reactive, cell 8336 |
| 26 vs 22 of 36 steps | fast-path use, model vs reactive, cell 7511 |
| 24.84 vs 9.75 ms | model vs reactive, synthetic |
| 15.14 / 16.51 / 15.58 | MAE: model / repeat-last / moving average |

**Three limits to always mention:** the model used the fast path more; one trace per cell; synthetic went the other way.

**The honest answer:** "On the two Milan cells tested, forecast-driven routing gave lower mean ping than reactive routing, but it also used the fast path more, and on synthetic data it did not. Whether the forecast's content matters is not yet tested."
