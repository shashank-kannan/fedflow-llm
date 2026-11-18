# FedFlow-LLM

**Does predicting traffic help a network reroute before congestion, compared with reacting after it?**

FedFlow-LLM fine-tunes a small instruction-tuned LLM (Qwen2.5-1.5B-Instruct) with federated learning to forecast network traffic, and uses the forecast to reroute traffic in an emulated software-defined network (Mininet + POX). It compares forecast-driven (proactive) routing with reactive routing on delay and packet loss.

Computer Networks course project.

## Headline result

On the two Milan cells tested, forecast-driven routing gave lower mean ping delay than reactive routing (9.5 vs 16.1 ms on cell 7511, 7.5 vs 13.9 ms on cell 8336). On each cell, every model repetition was below every reactive one. On the synthetic trace it was the other way round (24.8 vs 9.8 ms).

Read this together with the caveats below: part of the Milan gain may come from the model using the faster path more, and no experiment tested a simple forecast with the same timing.

## How it works

1. **Traffic windows.** Each example is 12 past traffic values; the target is the next 6.
2. **Federated LoRA training.** Flower simulates 6 clients on one GPU. Client *i* learns only from traffic cell *i*. Each client trains a LoRA adapter (rank 8, alpha 16, dropout 0.05, on `q_proj` and `v_proj`) and the server merges the adapters with FedAvg over 25 rounds. Only the adapter weights are trained and exchanged; the base model stays frozen.
3. **Forecast.** The trained model reads the latest window and predicts the next 6 values.
4. **Forecast file.** The predicted value is written to a small file that the controller reads.
5. **POX controller.** If the value is above 100 (equal to 10 Mbps), it switches traffic to the alternate path. It uses fixed forwarding tables and never floods.
6. **Mininet network.** h1 on s1 talks to h2 on s2 over a primary path s1-s3-s2 at 10 Mbps or an alternate path s1-s4-s2 at 50 Mbps. Each experiment is 36 steps of 5 s.

Routing modes: **static** (always primary), **reactive** (writes the true value of the previous step), **model** (writes the peak of the model's 6-step forecast), and two references, **oracle** (writes the true peak of the coming window) and **alt** (always alternate).

## Results

Mean ping delay in ms, over 3 repetitions per mode (min to max in brackets). Emulated network, not a real one.

| Mode | Synthetic | Telecom 7511 | Telecom 8336 |
|---|---:|---:|---:|
| Static | 43.1 (42.22 to 43.83) | 48.3 (47.38 to 49.90) | 58.9 (57.16 to 59.77) |
| Reactive | 9.8 (9.71 to 9.84) | 16.1 (15.65 to 16.43) | 13.9 (13.33 to 14.61) |
| Model | 24.8 (24.77 to 24.95) | 9.5 (8.90 to 9.98) | 7.5 (7.10 to 7.85) |
| Oracle (reference) | 0.1 | 0.2 | 0.2 |
| Alt (reference) | 0.1 | 0.2 | 0.2 |

Route flips per run on the telecom cells: model 5 and 3, reactive 15 and 15 (cells 7511 and 8336).

Forecast error (MAE) on held-out windows. This measures forecasting, not routing.

| Test set | Model | Repeat-last | Moving average |
|---|---:|---:|---:|
| Telecom (366 windows) | 15.14 | 16.51 | 15.58 |
| Synthetic (91 windows) | 10.34 | 11.29 | 10.86 |

Onset recall (traffic about to cross 100): cell 7511 6 of 14, cell 8336 4 of 14. Modest, and the windows overlap.

Sources: `results/experiment/summary.csv`, `results/experiment_telecom/7511/summary.csv`, `results/experiment_telecom/8336/summary.csv`, `results/final/outputs/metrics.json`, `results/final_telecom/outputs/metrics.json`, `results/final_telecom/SUMMARY.md`.

## Caveats

- Each experiment cell replays one 36-step trace three times, so the repetitions show repeatability, not variety.
- On both telecom cells the model wrote a value above 100 (alternate path) on more steps than reactive routing did (26 vs 22 steps on cell 7511, 32 vs 28 steps on cell 8336), so part of its delay gain may come from using the faster path more, not from better forecasts.
- We did not test whether the forecast's content matters: no experiment replaced the model with a simple forecast that has the same timing.
- UDP packet loss was 0% in every scored run, so loss does not separate the modes.
- All routing results come from an emulated network (Mininet with POX), not a real network.

## Repository layout

| Folder | Contents |
|---|---|
| `training/` | Data generation (`generate_data.py`), Flower client and server (`client.py`, `server.py`) |
| `controller/` | Mininet topology (`topo.py`) and POX controllers (`reroute_trigger.py`, `reactive_switch.py`, `write_forecast.py`) |
| `experiments/` | Routing experiment runner (`run_experiment.py`) and summariser (`summarize.py`) |
| `datasets/telecom_milan/` | Scaled Milan traffic for six cells, with attribution in `NOTICE.md` |
| `notebooks/` | Colab notebooks for synthetic and telecom training |
| `results/` | Training outputs, forecasts, metrics and routing experiment summaries |
| `slides/`, `study_guide/` | Presentation deck, speaker notes and study guide |

## Setup (Google Colab, GPU runtime)

Training runs on Colab (T4 GPU). Run these in order:

```bash
pip install -q torch transformers peft accelerate bitsandbytes "flwr[simulation]"
pip uninstall -y torch
pip install -q torch --index-url https://download.pytorch.org/whl/cu121
pip uninstall -y torchvision torchaudio
pip install -q transformers==4.46.3 peft==0.13.2
```

## How to run

Training, from inside `training/` (or use the notebooks in `notebooks/`):

```bash
python generate_data.py   # writes data/synthetic_traffic.csv and data/traffic_train.json
python server.py          # runs the 6-client, 25-round federated simulation
```

Routing experiments, on a Linux machine with Mininet and POX (POX loads controllers from `~/pox/ext`):

```bash
python3 experiments/run_experiment.py --selftest                 # builds the trace only; no Mininet, no sudo
sudo python3 experiments/run_experiment.py                       # synthetic: 5 modes x 3 repetitions
sudo python3 experiments/run_experiment.py --dataset telecom --cell 7511
```

## Data

Synthetic traffic: 14 days at 10-minute intervals, with daily cycles, weekend dips and random bursts.

Telecom data: Telecom Italia Big Data Challenge, Milan, November 2013, Harvard Dataverse, DOI [10.7910/DVN/EGZHFV](https://doi.org/10.7910/DVN/EGZHFV), released under ODbL 1.0. This repository holds only a derived, scaled aggregate of six grid squares, where 100 stands for the 10 Mbps primary link. Attribution and licence terms are in [`datasets/telecom_milan/NOTICE.md`](datasets/telecom_milan/NOTICE.md).
