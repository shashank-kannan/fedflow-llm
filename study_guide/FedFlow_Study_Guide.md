# FedFlow-LLM Study Guide

A plain-language guide to the whole project, for explaining it to a professor and answering hard questions.

Every number is followed by the file it comes from, in square brackets. "not in the files" means no file in the project holds that fact.

[[TOC]]

# Part 0. How to use this guide

> **In one line:** Read Parts 1 to 2 first, then the glossary, then the rest in order; learn the cheat sheet last.

## Reading order

Part 1 explains the problem with no jargon. Part 2 shows the whole project on one page. Part 3 is the glossary: come back to it whenever a word is unclear.

Parts 4 to 6 explain the data, the model and the network test. Part 7 gives the results, and Part 8 covers a second attempt that was not used. Part 9 lists every limit.

Part 10 is a bank of hard questions with honest answers. Parts 11 and 12 are what you say out loud and what you memorise.

## What "done" looks like for each part

| Part | You are done when you can... |
|---|---|
| 1 The problem | explain reactive versus predictive rerouting without using any technical word |
| 2 The pipeline | draw the six boxes from traffic data to the network, from memory |
| 3 Glossary | define every bold term in one sentence |
| 4 Data | say where the data came from and why 100 means 10 Mbps |
| 5 Model | name the model, the LoRA settings and the federated setup |
| 6 Experiment | describe the two paths, the five modes and one 36-step run |
| 7 Results | quote the headline with its two caveats, and the forecast errors |
| 8 v2 | say why v2 was not adopted, with its numbers |
| 9 Limits | list all 14 limits without looking |
| 10 Questions | answer any question in that part in under 30 seconds |
| 11 and 12 | give the 60-second explanation and the cheat sheet from memory |

How to use this table: tick a part only when you can do the thing in its right-hand column out loud.

# Part 1. The problem in plain words

> **In one line:** Can a traffic forecast move data off a slow path before it jams, giving less delay than waiting for the jam to happen?

## An analogy first

Picture a town with two roads between two places: a narrow lane and a wide highway. Normally everyone uses the lane. When the lane jams, cars wait.

A **reactive** traffic officer sends cars to the highway after they see the jam. A **predictive** officer reads a forecast and sends cars to the highway before the jam arrives. That is the whole idea; now the real case.

## What a network is

A **network** is a set of computers connected by cables and boxes that pass data along. The computers at the ends are called **hosts**. The boxes in the middle are called **switches**.

Data travels in small pieces called **packets**. A **link** is one cable between two devices, and it has a maximum speed.

## What traffic is

**Traffic** is the amount of data moving through the network over time. It rises and falls: busy in the evening, quiet at night.

In this project, traffic is a list of numbers, one every 10 minutes [datasets/telecom_milan/README.md]. Each number says how busy one area was in that slot.

## What a route is

A **route** (or **path**) is the chain of links a packet follows from one host to another. In this project there are exactly two paths between the two hosts [controller/topo.py].

The **primary path** is slow: 10 Mbps. The **alternate path** is fast: 50 Mbps [controller/topo.py]. Traffic uses the primary path unless the controller moves it.

## What congestion means

**Congestion** happens when more data arrives at a link than the link can carry. Packets wait in a queue, so they take longer to arrive.

That waiting time is **delay**. More congestion means more delay. This project measures delay with ping (see Part 3).

## Why predicting traffic might help

A reactive system can only move traffic after it has already seen the load. By then, packets have already waited.

If a forecast says "the load will go above what the slow link can carry", the system could move traffic early. Whether this gives lower delay is the question this project tests.

## Reactive versus predictive rerouting in this project

**Reactive** routing here uses the true traffic value of the previous 5-second step [experiments/run_experiment.py]. **Predictive** routing uses the highest of the model's 6 forecast values [experiments/run_experiment.py].

Both feed the same rule in the controller: a value above 100 sends traffic to the fast path [controller/reroute_trigger.py]. So the only difference is where the number comes from.

## The research question

The project asks: does forecast-driven (predictive) rerouting give lower delay than reactive rerouting in an emulated software-defined network [CLAUDE.md]?

"Emulated" means the network is a realistic copy running inside one computer, not real hardware. Part 6 explains this.

# Part 2. The whole project on one page

> **In one line:** Traffic data trains a forecasting model; its forecasts go into a file; a controller reads the file and picks the slow or fast path.

## The pipeline in words

First, real traffic numbers from Milan are cut into short windows. A small language model learns, across 6 simulated sites, to predict the next 6 numbers from the past 12.

The trained model then forecasts traffic for a held-out test period. During the network test, one value per step is written to a file. The network controller reads that file every second and chooses the path.

## The pipeline as a numbered list

1. **Traffic data:** Milan internet activity, November 2013, 10-minute slots, scaled so that 100 means the 10 Mbps link [datasets/telecom_milan/README.md].
2. **Training:** Qwen2.5-1.5B-Instruct with LoRA, trained by Flower and FedAvg over 6 clients and 25 rounds, on Colab [training/client.py, training/server.py].
3. **Forecast:** for each test window, the model writes "PREDICTION: v1, ..., v6" [training/generate_data.py, training/infer.py].
4. **Forecast file:** at each 5-second step, the experiment writes one number to controller/forecast_value.txt [experiments/run_experiment.py].
5. **Controller:** POX reads the file every 1 second and compares the number with 100 [controller/reroute_trigger.py].
6. **Network:** Mininet sends the traffic on the 10 Mbps primary path or the 50 Mbps alternate path [controller/topo.py].

## Flowchart

```
 Milan traffic data (cells.csv)
          |
          v
 Training on Colab: 6 clients x 25 rounds (Flower, FedAvg, LoRA)
          |
          v
 Trained adapter  -->  forecasts.csv (6 values per window, made in advance)
                              |
                              v
 Experiment, every 5 s: write one value to forecast_value.txt
                              |
                              v
 POX controller, every 1 s: value > 100 ?
          |                                  |
         no                                 yes
          v                                  v
 Primary path s1-s3-s2 (10 Mbps)   Alternate path s1-s4-s2 (50 Mbps)
          |                                  |
          +---------------> h1 <-------------+
                 ping and UDP measured here
```

> **Watch out:** The forecasts were computed in advance and stored in forecasts.csv. The model did not run live during the network test [experiments/run_experiment.py].

# Part 3. Glossary

> **In one line:** Every technical word in the project, in one or two plain sentences.

## Networks

| Term | Meaning |
|---|---|
| **Host** | A computer at the end of the network that sends or receives data. Here: h1 and h2 [controller/topo.py]. |
| **Switch** | A box that passes packets between links. Here: s1, s2, s3 and s4 [controller/topo.py]. |
| **Link** | One connection between two devices, with a speed limit. |
| **Path** | The chain of links from one host to the other. Here there are two. |
| **Packet** | A small piece of data sent over the network. |
| **Mbps** | Megabits per second: how much data a link can carry each second. 10 Mbps is the slow path here. |
| **Congestion** | More data arriving than a link can carry, so packets queue and wait. |
| **Latency (delay)** | The time a packet takes to get there and back. Measured here in milliseconds (ms). |
| **Ping** | A tool that sends a tiny packet and times the reply. The project pings every 0.2 s [experiments/run_experiment.py]. |
| **p95** | The 95th percentile: 95 out of 100 ping times were at or below this value. It shows the bad cases. |
| **UDP** | A simple way to send data that does not wait for confirmations. The project's test load is UDP. |
| **Packet loss** | Packets that are sent but never arrive. |
| **iperf** | A tool that sends a chosen amount of traffic and reports how much arrived [experiments/run_experiment.py]. |
| **SDN** | Software-defined networking: switches follow rules set by a separate program instead of deciding alone. |
| **OpenFlow** | The language a controller uses to give rules to switches. |
| **Controller** | The program that decides the routes and tells the switches. Here: POX. |
| **POX** | A Python program that acts as an OpenFlow controller. It runs the project's rerouting rule [controller/reroute_trigger.py]. |
| **Mininet** | Software that builds a virtual network of hosts, switches and links inside one computer. |
| **Emulation** | Running a realistic copy of a network in software, with real network code but no real cables. |
| **Static ARP** | Each host is told the other host's hardware address in advance, so no broadcast messages are needed [experiments/run_experiment.py]. |

What this table means: these are the parts of the test network and the tools used to measure it.

## Routing in this project

| Term | Meaning |
|---|---|
| **Primary path** | s1-s3-s2 at 10 Mbps: the default, slow route [controller/topo.py]. |
| **Alternate path** | s1-s4-s2 at 50 Mbps: the fast route [controller/topo.py]. |
| **Threshold** | The cut-off value 100. Above it, the controller uses the alternate path [controller/reroute_trigger.py]. |
| **Route flip** | One switch of path, from primary to alternate or back. Counted from "FLIP" lines in the controller log [experiments/summarize.py]. |
| **Static** | Mode that writes 0 every step, so traffic always stays on the slow path [experiments/run_experiment.py]. |
| **Reactive** | Mode that writes the true value of the previous step [experiments/run_experiment.py]. |
| **Model mode** | Mode that writes the highest of the model's 6 forecasts from the latest usable window [experiments/run_experiment.py]. |
| **Oracle** | Mode that writes the highest of the 6 true future values: a perfect forecast, used as a reference [experiments/run_experiment.py]. |
| **Alt** | Mode that writes 1000 every step, so traffic always uses the fast path [experiments/run_experiment.py]. |
| **Trace** | The 36 traffic values replayed in one run, one per 5-second step [experiments/run_experiment.py]. |

What this table means: the five modes differ only in which number is written to the forecast file each step.

## Machine learning

| Term | Meaning |
|---|---|
| **Forecast** | A prediction of future values. Here: the next 6 traffic values. |
| **LLM** | Large language model: a program trained on huge amounts of text to continue text. |
| **Token** | A small piece of text (a word or part of a word) that an LLM reads or writes. |
| **Prompt** | The text given to the model; here it contains the 12 past values [training/generate_data.py]. |
| **Fine-tuning** | Training an existing model a little more on a specific task. |
| **LoRA** | Low-Rank Adaptation: fine-tuning that trains a small add-on instead of all the model's weights. |
| **Adapter** | The small set of trained LoRA weights. Saved as adapter.npz [training/server.py]. |
| **GPU** | A graphics chip that runs model training fast. Training here used a Colab T4 GPU [CLAUDE.md]. |
| **Federated learning** | Several sites each train on their own data and share only model updates, never the data. |
| **Client** | One simulated site in federated learning. There are 6 [training/client.py]. |
| **Flower** | The Python library that runs the federated training [training/server.py]. |
| **FedAvg** | Federated averaging: the server averages the clients' updates into one model [training/server.py]. |
| **Round** | One cycle: send the model out, train locally, collect and average. There are 25 [training/server.py]. |
| **Training loss** | A score of how wrong the model is on its own training text. Lower means it fits that text better. |
| **Overfitting** | Fitting the training data so closely that the model does worse on new data. |
| **Window** | 12 past values plus the 6 values that followed them [training/generate_data.py]. |

What this table means: these words describe how the forecaster was built and trained.

## Measuring forecasts and data splits

| Term | Meaning |
|---|---|
| **MAE** | Mean absolute error: the average size of the forecast's mistakes. Lower is better. |
| **RMSE** | Root mean squared error: like MAE, but large mistakes count more. Lower is better. |
| **Baseline** | A simple method used for comparison, to see if the model adds anything. |
| **Persistence (repeat-last)** | Baseline that repeats the last known value 6 times [training/infer.py]. |
| **Moving average** | Baseline that repeats the average of the last 3 values 6 times [training/infer.py]. |
| **Onset** | A window where the last known value is at most 100 and the true peak goes above 100: traffic is about to cross the threshold [results/final_telecom/SUMMARY.md]. |
| **Onset recall** | Of all onset windows, the share where the forecast also went above 100. |
| **Calm window** | Last value at most 100 and true peak at most 100 [results/final_telecom/SUMMARY.md]. |
| **False alarm** | A calm window where the forecast still went above 100. |
| **Training block** | Slots 0 to 1439 of the telecom data, used for training [training/generate_data.py]. |
| **Validation block** | Slots 1440 to 1727, used to choose between model versions [training/generate_data.py]. |
| **Test block** | Slots 1728 to 2015, used once for the final score [training/generate_data.py]. |

What this table means: these words describe how good the forecasts were, and which data was used for what.

# Part 4. The data

> **In one line:** Real internet activity from six areas of Milan in November 2013, rescaled so that 100 stands for the slow link's capacity; plus a made-up series used first.

## The Milan dataset

The data is "Telecommunications - SMS, Call, Internet - MI", published on Harvard Dataverse with DOI 10.7910/DVN/EGZHFV [datasets/telecom_milan/README.md]. The record lists the author as "Telecom Italia" [datasets/telecom_milan/README.md].

It covers 1 to 14 November 2013 [datasets/telecom_milan/README.md]. Only the internet column is used [datasets/telecom_milan/README.md].

> **Watch out:** Your notes call this the "Telecom Italia Big Data Challenge". That name is not in the project files, so use the Dataverse title above and say it is from Telecom Italia.

## What a cell is

Milan is divided into a grid of squares; each square is a **cell** with a number, such as 7511 [datasets/telecom_milan/README.md]. Six cells were chosen: 9721, 6997, 8336, 7511, 8062 and 7584 [datasets/telecom_milan/README.md].

They were picked by a fixed rule on their training-period averages, not by hand [datasets/telecom_milan/README.md]. Two of them, 7511 and 8336, are the "experiment cells" used in the network test [datasets/telecom_milan/README.md].

## Time slots

Each day has 144 slots of 10 minutes, so 14 days give 2016 slots [datasets/telecom_milan/README.md]. The split is by time, never shuffled.

| Block | Slots | Days |
|---|---|---|
| Training | 0 to 1439 | days 0 to 9 |
| Validation | 1440 to 1727 | days 10 to 11 |
| Test | 1728 to 2015 | days 12 to 13 |

What this table means: the model learns from the first ten days, is checked on the next two, and is scored once on the last two [datasets/telecom_milan/README.md].

## Why the values are scaled so that 100 means 10 Mbps

The raw values are unitless activity counts, not Mbps. They were multiplied by one factor, k = 2.3306204138 [datasets/telecom_milan/README.md].

The factor makes the median of the six cells' training averages equal to 90 [datasets/telecom_milan/README.md]. The project then treats 100 as the 10 Mbps capacity of the slow path [datasets/telecom_milan/README.md].

> **Watch out:** This is a modelling choice. The scaled values are not measured Mbps [datasets/telecom_milan/README.md].

## The synthetic data and why it exists

Before the Milan data, the project used a made-up series: 14 days at 10-minute intervals with daily cycles, weekend dips and random bursts [README.md]. It was a controlled first test of the whole pipeline.

Its test block is days 10 to 11, scored with 91 windows [results/final/outputs/metrics.json]. Its results are reported in Part 7, including where the model did worse.

## Attribution and licence

Attribution details are in datasets/telecom_milan/NOTICE.md. This guide does not state a licence conclusion.

# Part 5. The model and training

> **In one line:** A 1.5-billion-parameter language model, fine-tuned with LoRA by 6 federated clients over 25 rounds, learns to write the next 6 traffic values.

## The model

The model is Qwen2.5-1.5B-Instruct [training/client.py]. It is a general-purpose language model, not built for traffic.

It reads numbers as text and writes numbers as text. The project teaches it a fixed question-and-answer format.

## LoRA settings

| Setting | Value | Source |
|---|---|---|
| Rank r | 8 | training/client.py |
| Alpha | 16 | training/client.py |
| Target modules | q_proj, v_proj | training/client.py |
| Dropout | 0.05 | training/client.py |

What this table means: only small add-on matrices inside two kinds of attention layer are trained; the rest of the model stays frozen [training/client.py].

## Why LoRA rather than full fine-tuning

Full fine-tuning changes every weight of the model, which needs much more memory. LoRA trains a small adapter, so it fits on a single Colab T4 GPU [CLAUDE.md].

It also matters for federated learning: only the small adapter is sent between clients and server, never the whole model [README.md].

## The federated setup

Flower runs a simulation of 6 clients on one GPU [training/server.py]. Each round, every client trains on its own examples, then the server averages their adapters with FedAvg [training/server.py].

There are 200 training examples in total [training/generate_data.py]. Example j belongs to cell j mod 6, and client i takes every 6th example starting at i, so client i only ever sees cell i [datasets/telecom_milan/README.md, training/client.py].

> **If pushed:** "Why does client i only see cell i?" Because it imitates real sites that each hold their own area's data and never share it.

## What 25 rounds means

One round is: send the current adapter out, let each client train one pass over its own examples, collect and average [training/client.py, training/server.py]. This repeats 25 times [training/server.py].

Each client trains with batch size 2 and learning rate 0.0001 [training/client.py].

## The prompt and the answer

The prompt gives 12 past values measured at 10-minute intervals and asks for the next 6 [training/generate_data.py]. It ends by asking for the format "PREDICTION: v1, v2, v3, v4, v5, v6" [training/generate_data.py].

The training answer has three lines: a trend direction, a one-sentence justification based on a simple slope, and the PREDICTION line with the 6 true values [training/generate_data.py].

## The training loss

On the telecom run, the loss went from 1.7109 in round 1 to 0.6077 in round 25 [results/final_telecom/outputs/loss_history.csv]. On the synthetic run, from 1.7224 to 0.5976 [results/final/outputs/loss_history.csv].

> **Watch out:** A falling loss shows the model fits its training text better. It does not show that the forecasts are good on new data.

The v1 loss was computed over every token, including the prompt and the padding [training/client.py]. It was also measured on the first 10 training examples of each client, not on held-out data [training/client.py, README.md].

# Part 6. The network experiment

> **In one line:** A replayed 36-step traffic trace runs through a two-path virtual network five ways, three times each, and the delay is measured.

## The topology

Host h1 connects to switch s1, and host h2 to switch s2 [controller/topo.py]. Two paths join s1 and s2.

| Path | Switches | Speed |
|---|---|---|
| Primary | s1-s3-s2 | 10 Mbps |
| Alternate | s1-s4-s2 | 50 Mbps |

What this table means: traffic above 10 Mbps cannot fit on the primary path, but fits easily on the alternate path [controller/topo.py].

The controller uses fixed forwarding tables and never floods packets [controller/reroute_trigger.py]. The hosts use static ARP [experiments/run_experiment.py].

## The threshold and the controller

POX reads controller/forecast_value.txt every 1 second [controller/reroute_trigger.py]. If the value is above 100, it switches to the alternate path; otherwise it uses the primary path [controller/reroute_trigger.py].

When it switches, it deletes all flow rules, so the next packets get new rules for the new path [controller/reroute_trigger.py].

## The five modes

| Mode | Value written each step | Purpose |
|---|---|---|
| static | 0 | always the slow path |
| reactive | true value of the previous step | react after the fact |
| model | highest of the model's 6 forecasts | predict |
| oracle | highest of the 6 true future values | perfect forecast, reference |
| alt | 1000 | always the fast path, reference |

What this table means: all five modes use the same controller rule; only the written number differs [experiments/run_experiment.py].

The model and oracle use the most recent forecast window whose history ends at or before the previous step [experiments/run_experiment.py]. Windows start every 3 slots, so a window can include up to 2 steps that have already passed [experiments/run_experiment.py].

## One run, step by step

A run replays 36 steps of 5 seconds [experiments/run_experiment.py]. A step's traffic value v becomes UDP traffic of v/10 Mbps from h2 to h1 for 5 seconds [experiments/run_experiment.py].

At each step the experiment starts a fresh iperf server, writes the mode's value to the forecast file, then sends that step's traffic [experiments/run_experiment.py]. Ping runs every 0.2 seconds for the whole run [experiments/run_experiment.py].

## The 36-step trace

For each experiment cell, the trace is the 36-step test slice with the most upward crossings of 100 in the true traffic [datasets/telecom_milan/README.md]. For cell 7511 it starts at slot 1837, and for cell 8336 at slot 1960, each with 8 crossings [datasets/telecom_milan/README.md].

The slice was chosen from true traffic only, never from model outputs [datasets/telecom_milan/README.md].

## The 3 repetitions

Each mode runs 3 times per cell, in rep-major order: all modes for rep 1, then rep 2, then rep 3 [experiments/run_experiment.py]. This spreads slow drift in the computer evenly over the modes.

> **Watch out:** All 3 repetitions replay the same trace. They show that the result repeats, not that it holds for other traffic.

## What each measure means

| Measure | What it measures | Better is |
|---|---|---|
| Ping mean | average round-trip time, ms | lower |
| Ping p95 | the slow end of ping times, ms | lower |
| UDP loss | share of datagrams lost, from the iperf server's own report | lower |
| Delivered share | datagrams delivered, as a percentage of the alt mode's mean | higher |
| Route flips | number of path switches in the controller log | context only |
| Share written above 100 | share of steps sent to the alternate path | context only |

What this table means: ping mean is the main delay measure; the last two rows show how much each mode used the fast path [experiments/summarize.py].

## Why UDP loss was 0%

UDP loss was 0% in every scored run [results/experiment/README.md, results/experiment_telecom/7511/summary.csv, results/experiment_telecom/8336/summary.csv]. The project's explanation is that the 10 Mbps link slowed the sender instead of overflowing [results/experiment/README.md].

> **Watch out:** That mechanism is not verified [results/experiment/README.md]. One run, cell 8336 static rep 1, has no loss number at all: its server reports did not match [results/experiment_telecom/8336/summary.csv].

# Part 7. Results

> **In one line:** On both Milan cells, model-driven routing gave lower mean ping than reactive routing; but it also used the fast path more, and on synthetic data it did not.

## Telecom cell 7511

> **Watch out:** The model sent more steps to the fast path than reactive did, and the 3 repetitions replay one trace. Part of the delay gap may come from using the fast path more.

| Mode | Mean ping, ms (min to max of 3 reps) | Share of steps above 100 | Route flips |
|---|---|---|---|
| static | 48.32 (47.38 to 49.90), see the note below | 0.0000 | 0 |
| reactive | 16.06 (15.65 to 16.43) | 0.6111 | 15 |
| model | 9.53 (8.90 to 9.98) | 0.7222 | 5 |
| oracle | 0.18 (0.13 to 0.23) | 1.0000 | 0 |
| alt | 0.18 (0.16 to 0.19) | 1.0000 | 0 |

What this table means: every model repetition is below every reactive repetition, so on this cell model routing gave lower mean ping than reactive routing [results/experiment_telecom/7511/summary.csv].

The model wrote a value above 100 at 0.7222 of the steps, which is 26 of 36, and reactive at 0.6111, which is 22 of 36 [results/experiment_telecom/7511/summary.csv].

> **Watch out:** Your notes give static on 7511 as 48.4 ms. The file gives 48.32, which rounds to 48.3. The table uses the file value; the conflict is listed in STUDY_DECISIONS.md.

## Telecom cell 8336

> **Watch out:** Same caveat: the model used the fast path at more steps than reactive did, and the repetitions replay one trace.

| Mode | Mean ping, ms (min to max of 3 reps) | Share of steps above 100 | Route flips |
|---|---|---|---|
| static | 58.90 (57.16 to 59.77) | 0.0000 | 0 |
| reactive | 13.91 (13.33 to 14.61) | 0.7778 | 15 |
| model | 7.49 (7.10 to 7.85) | 0.8889 | 3 |
| oracle | 0.21 (0.13 to 0.25) | 1.0000 | 0 |
| alt | 0.18 (0.11 to 0.25) | 1.0000 | 0 |

What this table means: every model repetition is below every reactive repetition here too [results/experiment_telecom/8336/summary.csv].

The model wrote a value above 100 at 0.8889 of the steps (32 of 36), and reactive at 0.7778 (28 of 36) [results/experiment_telecom/8336/summary.csv].

## Synthetic data

> **Watch out:** On synthetic data the result goes the other way: the model's mean ping was higher than reactive's.

| Mode | Mean ping, ms (min to max of 3 reps) | Share of steps above 100 | Route flips |
|---|---|---|---|
| static | 43.13 (42.22 to 43.83) | 0.0000 | 0 |
| reactive | 9.75 (9.71 to 9.84) | 0.6111 | 7 |
| model | 24.84 (24.77 to 24.95) | 0.3333 | 3 |
| oracle | 0.11 (0.11 to 0.12) | 0.9167 | 1 |
| alt | 0.11 (0.11 to 0.12) | 1.0000 | 0 |

What this table means: on synthetic data the model used the fast path less than reactive did, and had higher delay [results/experiment/README.md].

## What the routing numbers say

On the two Milan cells tested, forecast-driven routing gave lower mean ping delay than reactive routing: 9.5 against 16.0 ms on cell 7511, and 7.5 against 13.9 ms on cell 8336 [results/experiment_telecom/7511/summary.csv, results/experiment_telecom/8336/summary.csv].

The word "lower" is used only because every model repetition is below every reactive repetition on that cell [results/experiment_telecom/7511/summary.csv, results/experiment_telecom/8336/summary.csv].

## What the routing numbers do not say

No statistical test was run; no file shows one. The 3 repetitions replay one trace per cell, so this is not evidence for other traffic.

The model used the fast path more often than reactive on both cells. A check of whether the forecast's content matters (same timing, simpler forecast) was planned but not run [PLAN_BASELINE_CHECK.md, branch baseline-check].

## Forecast accuracy on the telecom test block

> **Watch out:** The model's MAE is the lowest of the three, but its RMSE is higher than the moving average's, so its large mistakes are bigger.

All 366 test windows were scored, with 0 parse failures [results/final_telecom/outputs/metrics.json].

| Method | MAE | RMSE |
|---|---|---|
| Model | 15.14 | 24.76 |
| Repeat-last (persistence) | 16.51 | 26.16 |
| Moving average (last 3) | 15.58 | 23.95 |

What this table means: the model's average error is lower than both baselines, but its RMSE is higher than the moving average's, so its large mistakes are bigger [results/final_telecom/outputs/metrics.json].

## Forecast accuracy per cell (telecom test)

> **Watch out:** On three of the six cells, a simple baseline has an MAE as low as or lower than the model's.

| Cell (windows) | Model MAE | Repeat-last MAE | Moving average MAE |
|---|---|---|---|
| 9721 (46) | 9.08 | 9.49 | 8.57 |
| 6997 (46) | 11.66 | 12.08 | 12.84 |
| 8336 (91) | 11.56 | 15.00 | 13.31 |
| 7511 (91) | 15.37 | 17.07 | 15.99 |
| 8062 (46) | 17.21 | 17.60 | 17.20 |
| 7584 (46) | 29.22 | 28.75 | 27.42 |

What this table means: on the two experiment cells the model has the lowest MAE, but on cells 9721, 8062 and 7584 a simple baseline is as low or lower [results/final_telecom/outputs/metrics.json].

## Forecast accuracy on the synthetic test block

> **Watch out:** Lower forecast error on synthetic data did not turn into lower delay than reactive routing.

| Method | MAE | RMSE |
|---|---|---|
| Model | 10.34 | 15.57 |
| Repeat-last (persistence) | 11.29 | 16.96 |
| Moving average (last 3) | 10.86 | 16.97 |

What this table means: on 91 synthetic test windows the model had the lowest errors of the three [results/final/outputs/metrics.json]. Lower forecast error did not turn into lower delay than reactive on synthetic data [results/experiment/README.md].

## Onset recall

> **Watch out:** Onset recall is modest, the counts are small, and the windows overlap, so they are not independent samples [results/final_telecom/SUMMARY.md].

| Data and cell | Onset windows | Flagged by the model | Recall |
|---|---|---|---|
| Telecom 7511 | 14 | 6 | 42.9% |
| Telecom 8336 | 14 | 4 | 28.6% |
| Synthetic | 10 | 1 | 10.0% |

What this table means: the model foresaw roughly a third to a half of the threshold crossings on the telecom cells, and 1 in 10 on synthetic data [results/final_telecom/SUMMARY.md, results/final/SUMMARY.md].

Repeat-last can never flag an onset, because its peak is the last value, which is at most 100 in an onset window [results/final_telecom/SUMMARY.md].

# Part 8. The v2 attempt

> **In one line:** A second version with three changes was trained and judged by rules written before its run; it failed two of the four rules, so v1 stayed final.

## What was changed

v2 is v1 plus exactly three changes [PLAN_V2.md, branch v2]. First, the loss counts only the answer tokens. Second, the prompt states the Milan time and day type of the last value. Third, training examples are balanced between onset and other windows.

Everything else stayed the same: model, LoRA settings, 25 rounds, 6 clients, seeds and the data split [PLAN_V2.md, branch v2].

## The rules, written before the run

The plan was committed on 30 October 2026 at 01:19, before any v2 code [git log of branch v2, commit d589c09]. It said v2 would be adopted only if all four of these held on the validation block [PLAN_V2.md, branch v2]:

1. Overall model MAE lower than v1's.
2. Pooled onset recall over all six cells higher than v1's.
3. Calm false-alarm rate at most 5 percentage points above v1's.
4. Parse failures no more than v1's.

## The numbers

| Rule | v1 | v2 | Holds |
|---|---|---|---|
| 1. MAE lower | 15.00 | 15.78 | no |
| 2. Onset recall higher | 11 of 29 | 17 of 29 | yes |
| 3. False alarms within 5 points | 4 of 110 | 16 of 111 | no |
| 4. Parse failures no more | 1 | 0 | yes |

What this table means: v2 caught more onsets but raised many more false alarms and had higher error, so it failed rules 1 and 3 [~/fedflow_data/compare_v1_v2_val.md].

The calm-window counts differ, 110 against 111, because one v1 calm window did not parse and was left out [~/fedflow_data/compare_v1_v2_val.md].

## Why v1 stayed the final model

The comparison script printed "DECISION: DO NOT ADOPT" [~/fedflow_data/compare_v1_v2_val.md]. So v1 is the final model, and v2 is reported as a negative result.

> **Watch out:** v2 was designed after the v1 test results were known. It was judged on the separate validation block, not the test block, and it was not adopted.

# Part 9. Limits and threats

> **In one line:** Fourteen things this project does not show or cannot rule out. Mention them before anyone asks.

## The 14 limits

1. **One trace per cell.** Each cell replays one 36-step trace three times, so the repetitions show repeatability, not variety [experiments/run_experiment.py].

2. **More use of the fast path.** On both telecom cells the model sent more steps to the alternate path than reactive did: 0.7222 against 0.6111 on 7511, and 0.8889 against 0.7778 on 8336 [results/experiment_telecom/7511/summary.csv, results/experiment_telecom/8336/summary.csv]. Part of its delay gain may come from that, not from better forecasts.

3. **No packet loss.** UDP loss was 0% in every scored run, probably because the 10 Mbps link slowed the sender [results/experiment/README.md]. This is not verified, so loss does not separate the modes.

4. **Controller log errors.** The controller logs contain repeated Python AttributeError lines, and bursts of "using alt path" lines after flips. AttributeError lines appear in all 15 controller logs of each telecom cell [results/experiment_telecom/7511/raw_*_pox.txt, results/experiment_telecom/8336/raw_*_pox.txt]. The cause is not established.

5. **Forecast content not tested.** No run replaced the model with a simple forecast that has the same timing. Such a check is planned but not run [PLAN_BASELINE_CHECK.md, branch baseline-check].

6. **Old, rescaled data.** The telecom data is from Milan, November 2013, rescaled to a unitless load [datasets/telecom_milan/README.md].

7. **Synthetic result went the other way.** On synthetic data the model did not give lower mean delay than reactive routing: 24.84 against 9.75 ms [results/experiment/README.md].

8. **v2 came after v1 results.** The v2 attempt was designed after the v1 test results were known. It was judged on a separate validation block and not adopted [~/fedflow_data/compare_v1_v2_val.md].

9. **Modest onset recall, overlapping windows.** Onset recall is modest (6 of 14 and 4 of 14), and the windows overlap, so they are not independent [results/final_telecom/SUMMARY.md].

10. **Training loss is not forecast quality.** In v1 it was computed over every token, prompt and padding included [training/client.py].

11. **One training run.** The forecasts came from one training run on a Colab T4 GPU. Run-to-run variation was not measured. The GPU-mismatch count is not yet computed (not in the files).

12. **Test block used once.** The test block was scored once and not tuned on [PLAN_V2.md, branch v2].

13. **Emulation only.** All routing results come from an emulated network, not a real one [CLAUDE.md].

14. **Attribution and licence.** Dataset attribution and licence are in datasets/telecom_milan/NOTICE.md. This guide states no licence conclusion.

> **If pushed:** "Which limit matters most?" Limits 2 and 5 together: the model used the fast path more, and nobody has yet tested whether a simple forecast with the same timing would do as well.

# Part 10. Annoying questions

> **In one line:** Hard questions with honest answers. When the honest answer is a weakness, it comes first, marked "Watch out".

## Basics

### Q1. What is the project, in one sentence?

It tests whether a traffic forecast from a federated, fine-tuned language model can move traffic to a fast path early enough to give lower delay than reacting after the fact. The test runs in an emulated network.

Source: CLAUDE.md

### Q2. What does "reactive" mean here, exactly?

Reactive mode writes the true traffic value of the previous 5-second step. If that value is above 100, the controller uses the fast path for this step.

Source: experiments/run_experiment.py

### Q3. What does the model mode write?

It writes the highest of the model's 6 forecast values, from the most recent window whose history ends at or before the previous step. The same rule then compares it with 100.

Source: experiments/run_experiment.py

### Q4. What are oracle and alt for?

They are references, not competitors. Oracle uses the true future values, a perfect forecast; alt always uses the fast path. They show the best delay this network can give.

Source: experiments/run_experiment.py

### Q5. Did the model run live during the experiment, or were forecasts precomputed?

Precomputed. infer.py produced forecasts.csv after training, and the experiment reads that file and writes one value per step to the forecast file. The model itself was not running during the network test.

Source: experiments/run_experiment.py, training/infer.py

### Q6. What does the controller actually do?

POX reads the forecast file every second. If the number is above 100, it sends traffic on the alternate path; otherwise on the primary path. When the decision changes, it deletes all flow rules so new ones are installed.

Source: controller/reroute_trigger.py

## Why this design

### Q7. Why an LLM for numbers and not an LSTM?

> **Watch out:** The files do not record a comparison with an LSTM or any statistical forecasting model, so there is no evidence either way.

The project's stated goal was to fine-tune Qwen2.5-1.5B-Instruct for traffic forecasting with federated learning. The only comparisons run were against repeat-last and moving average.

Source: README.md, results/final_telecom/outputs/metrics.json

### Q8. Why 100?

100 is defined to stand for the 10 Mbps capacity of the primary path. The data is scaled so that the six cells' median training average is 90, just under that line.

Source: controller/reroute_trigger.py, datasets/telecom_milan/README.md

### Q9. Why federated, when one model could train on everything?

> **Watch out:** Federated training was not compared with central training on the same data. We do not know whether federation helped, hurt or made no difference.

Federated learning imitates sites that keep their own data private and share only model updates. That is the setting the project chose to demonstrate.

Source: README.md

### Q10. Is each client just a separate model?

No. Each round, the server averages the six clients' adapters into one shared adapter with FedAvg, and every client starts the next round from it. There is one final model.

Source: training/server.py, training/client.py

### Q11. Each client trains on one cell only. Is that really federated learning?

Yes in mechanics: separate data per client, local training, averaged updates. It is a simulation on one GPU, not separate machines.

Source: training/server.py, datasets/telecom_milan/README.md

### Q12. Why LoRA rather than training all the weights?

LoRA trains only a small adapter, which needs far less memory and fits on one Colab T4 GPU. In federated learning, only that small adapter is exchanged.

Source: training/client.py, CLAUDE.md, README.md

### Q13. Why a 1.5B model and not a bigger one?

> **Watch out:** The files do not record why this size was chosen, and no bigger model was tried.

The client code notes that the model matches the project's stated target. Training ran on a Colab T4 GPU.

Source: training/client.py, CLAUDE.md

### Q14. Why 12 values in and 6 out?

These are fixed design settings: 12 history values, 6 predicted values. The files do not record a search over other lengths.

Source: training/generate_data.py

### Q15. Why 6 clients?

There are six chosen cells and one client per cell, so client i trains only on cell i.

Source: training/client.py, datasets/telecom_milan/README.md

### Q16. Why emulation and not hardware?

> **Watch out:** All results come from emulation. The files do not record why hardware was not used.

Mininet runs a full two-path network with real network software inside one computer. It makes every run repeatable.

Source: CLAUDE.md, controller/topo.py

### Q17. Why POX and not Ryu?

> **Watch out:** The files do not record a reason for choosing POX over Ryu.

POX is the controller the project's code is written for, and it only loads modules from ~/pox/ext.

Source: CLAUDE.md, controller/reroute_trigger.py

### Q18. Why 2013 data?

> **Watch out:** The data is from November 2013 and covers only 14 days. How well it reflects networks today is not established.

It is a public, citable dataset of real urban mobile internet activity, with per-cell time series.

Source: datasets/telecom_milan/README.md

## Is the result real

### Q19. Is the delay difference real or noise?

> **Watch out:** No statistical test was run, and the 3 repetitions replay the same trace.

What we can say: on each telecom cell, every model repetition is below every reactive repetition. On 7511 the ranges are 8.90 to 9.98 ms against 15.65 to 16.43 ms.

Source: results/experiment_telecom/7511/summary.csv, results/experiment_telecom/8336/summary.csv

### Q20. Why only 3 repetitions?

3 repetitions per mode per cell was the design. They check that the same run gives similar numbers again; they do not add new traffic.

Source: experiments/run_experiment.py

### Q21. Why no confidence intervals or significance tests?

> **Watch out:** None were computed. No file shows a statistical test.

The project reports the mean and the minimum-to-maximum range of the 3 repetitions instead.

Source: results/experiment/README.md, experiments/summarize.py

### Q22. Is 9.5 ms against 16.0 ms a meaningful difference?

> **Watch out:** "Meaningful" was not defined or tested; no statistical test was run.

On cell 7511 the ranges do not overlap: model 8.90 to 9.98 ms, reactive 15.65 to 16.43 ms. More traces and an agreed test would be needed to say more.

Source: results/experiment_telecom/7511/summary.csv

### Q23. Did you tune the model on the test data?

No. The test block was scored once. The v2 decision used the separate validation block.

Source: PLAN_V2.md (branch v2), ~/fedflow_data/compare_v1_v2_val.md

### Q24. Was the experiment trace picked to favour the model?

No. The 36-step slice was chosen from true traffic only, by a fixed rule (most upward crossings of 100), never from model outputs.

Source: datasets/telecom_milan/README.md

### Q25. Would a different training run give the same forecasts?

> **Watch out:** We do not know. There was one training run, and run-to-run variation was not measured.

Source: (limit 11; not in the files)

## Is the model really better

### Q26. Is the model better than reactive routing?

> **Watch out:** Only on the two Milan cells, only in mean ping, only on one trace each, and with more use of the fast path. On synthetic data it was not.

On telecom it gave lower mean ping: 9.53 against 16.06 ms on 7511, and 7.49 against 13.91 ms on 8336.

Source: results/experiment_telecom/7511/summary.csv, results/experiment_telecom/8336/summary.csv, results/experiment/README.md

### Q27. Is the model better than a simple moving average?

> **Watch out:** Mixed. On the telecom test its MAE is lower (15.14 against 15.58) but its RMSE is higher (24.76 against 23.95).

Per cell, the moving average has a lower MAE than the model on cells 9721 and 7584, and about the same on 8062. A moving average was not tried as a routing mode.

Source: results/final_telecom/outputs/metrics.json

### Q28. If the model mostly uses the fast path, is it forecasting?

> **Watch out:** We cannot separate the two yet. The model wrote values above 100 at 0.7222 and 0.8889 of steps, more than reactive on both cells.

It foresaw 6 of 14 and 4 of 14 onsets on the experiment cells, so it does react to coming peaks some of the time. A test with a simple forecast of the same timing was planned but not run.

Source: results/experiment_telecom/7511/summary.csv, results/experiment_telecom/8336/summary.csv, results/final_telecom/SUMMARY.md, PLAN_BASELINE_CHECK.md (branch baseline-check)

### Q29. Does the forecast's content matter, or only its timing?

> **Watch out:** Not tested. No run replaced the model with a simple forecast of the same timing.

A plan for that check exists, with its rules written before any run.

Source: PLAN_BASELINE_CHECK.md (branch baseline-check)

### Q30. Why did the model do worse on synthetic data?

> **Watch out:** The cause is not established.

What the files show: on synthetic data the model wrote above 100 at only 0.3333 of steps, against 0.6111 for reactive, and caught 1 of 10 onsets. So it stayed on the slow path more.

Source: results/experiment/README.md, results/final/SUMMARY.md

### Q31. Does a falling training loss mean the model works?

No. The loss fell from 1.7109 to 0.6077 on telecom, but that only shows a better fit to training text. Forecast quality comes from the test MAE, RMSE and onset recall.

Source: results/final_telecom/outputs/loss_history.csv, training/client.py

### Q32. Is this new?

> **Watch out:** The project files contain no literature review, so novelty is not established.

Source: not in the files

## What it does not show

### Q33. Does this show the approach works on real networks?

No. Every routing result comes from an emulated network.

Source: CLAUDE.md

### Q34. Does it show the approach works for other areas or times?

No. Two cells were tested, each with one 36-step trace from November 2013.

Source: datasets/telecom_milan/README.md, experiments/run_experiment.py

### Q35. Does it show anything about packet loss?

No. UDP loss was 0% in every scored run, so loss does not separate the modes.

Source: results/experiment_telecom/7511/summary.csv, results/experiment_telecom/8336/summary.csv, results/experiment/README.md

### Q36. Could it run in real time?

> **Watch out:** Not tested. The forecasts were precomputed, and inference time per forecast is not in the files.

The controller itself checks the file once per second.

Source: experiments/run_experiment.py, controller/reroute_trigger.py

### Q37. What would break it?

> **Watch out:** None of these were tested; this is reasoning, not a result.

A forecast that is late or wrong at the moment traffic crosses 100 would leave traffic on the slow path. Traffic patterns unlike the training cells could also hurt.

Source: not in the files

## Numbers and metrics

### Q38. What is ping, and why is it the main measure?

Ping times a tiny packet's round trip, every 0.2 seconds here. When the slow path is congested, ping packets wait in the same queue, so ping shows the delay users would feel.

Source: experiments/run_experiment.py, experiments/summarize.py

### Q39. Why do oracle and alt get about 0.2 ms?

Both keep traffic on the 50 Mbps fast path at every step, where the load never fills the link. On 7511, oracle averaged 0.18 ms and alt 0.18 ms.

Source: results/experiment_telecom/7511/summary.csv

### Q40. Why is UDP loss 0%? Isn't that suspicious?

> **Watch out:** The explanation, that the 10 Mbps link slowed the sender, is not verified.

It was 0% in every scored run. One run, 8336 static rep 1, has no loss value because its server reports did not match.

Source: results/experiment/README.md, results/experiment_telecom/8336/summary.csv

### Q41. What is MAE and what does 15.14 mean?

MAE is the average size of the forecast error, in the same scaled units as the traffic. 15.14 means the model was off by about 15 units per value on average, where 100 stands for 10 Mbps.

Source: results/final_telecom/outputs/metrics.json

### Q42. What is onset recall and why is it low?

> **Watch out:** It is modest: 6 of 14 on 7511 and 4 of 14 on 8336, and the windows overlap.

It is the share of real threshold crossings that the forecast also predicted. The model tends to under-predict peaks: on 7511 its onset peaks were on average 44.04 below the true peaks.

Source: results/final_telecom/SUMMARY.md

### Q43. What does a route flip tell you?

How often the path changed. Reactive flipped 15 times per run on each telecom cell; the model flipped 5 times on 7511 and 3 times on 8336.

Source: results/experiment_telecom/7511/summary.csv, results/experiment_telecom/8336/summary.csv

## The network and the controller

### Q44. What are the errors in the controller logs? Do they invalidate the results?

> **Watch out:** The cause is not established. AttributeError lines appear in all 15 controller logs of each telecom cell.

Each traceback ends inside POX's own ICMP parsing code (pox/lib/packet/icmp.py). Whether this changed any delay number is not known.

Source: results/experiment_telecom/7511/raw_*_pox.txt, results/experiment_telecom/8336/raw_*_pox.txt

### Q45. Why are there bursts of "using alt path" lines?

> **Watch out:** The cause is not established.

The controller logs one such line for each packet that reaches it while on the alternate path. Bursts follow flips, when all rules are deleted and packets go to the controller until new rules are installed.

Source: controller/reroute_trigger.py

### Q46. Why does a flip delete all flow rules?

So the next packets go to the controller and get rules from the newly chosen path. This is the same in every mode.

Source: controller/reroute_trigger.py

### Q47. Is this a real network?

No. It is Mininet: real network software on virtual hosts, switches and links inside one computer.

Source: CLAUDE.md, controller/topo.py

### Q48. Why no flooding and static ARP?

The topology has a loop, s1-s3-s2-s4-s1, and flooding would cause a broadcast storm. Static ARP removes the need for broadcast address requests.

Source: CLAUDE.md, experiments/run_experiment.py

## Data and fairness

### Q49. Why were these six cells chosen?

By a fixed rule on training-period averages, picking cells nearest to set percentiles, decided before any model was trained.

Source: datasets/telecom_milan/README.md

### Q50. Do the training windows overlap the test windows?

No. Training uses slots 0 to 1439, validation 1440 to 1727, test 1728 to 2015, and a check script confirms that no window crosses a block.

Source: training/generate_data.py, training/check_split.py

### Q51. Why were v2's rules written before its run? Isn't that cheating?

It is the opposite: fixing the rules first stops anyone from choosing the rule after seeing the result. v2 failed two rules and was not adopted.

Source: PLAN_V2.md (branch v2), ~/fedflow_data/compare_v1_v2_val.md

### Q52. Why was v2 not used?

It failed two of four rules on validation: MAE 15.78 against 15.00, and calm false alarms 16 of 111 against 4 of 110. It did catch more onsets: 17 of 29 against 11 of 29.

Source: ~/fedflow_data/compare_v1_v2_val.md

## Next steps

### Q53. What is the biggest weakness?

That the model used the fast path more often than reactive, and no test yet separates forecast quality from simply using the fast path more.

Source: results/experiment_telecom/7511/summary.csv, results/experiment_telecom/8336/summary.csv

### Q54. What would you do next?

First, run the planned check that replaces the model with simple forecasts of the same timing. Then use more traces, more training runs, and a statistical test agreed in advance.

Source: PLAN_BASELINE_CHECK.md (branch baseline-check)

### Q55. Would a real network operator do this?

> **Watch out:** Not established. It would need real-time forecasts, real hardware and much more testing.

Source: not in the files

# Part 11. 60-second and 3-minute explanations

> **In one line:** Say the headline, and always say its two caveats in the same breath.

## The 60-second version

"Networks get slow when a link gets more traffic than it can carry. A reactive controller moves traffic only after it sees the load. I tested whether a traffic forecast could move it earlier.

I fine-tuned a small language model, Qwen2.5-1.5B, with LoRA, using federated learning over six Milan cells. It predicts the next six traffic values from the past twelve.

In an emulated network with a slow and a fast path, model-driven routing gave lower mean ping than reactive routing on both cells tested: 9.5 against 16.0 ms, and 7.5 against 13.9 ms.

Two caveats: the model used the fast path more often than reactive, and each cell replays one trace. On synthetic data, the model did worse than reactive."

## The 3-minute version

"The problem: when a link is overloaded, packets queue and delay rises. A reactive system reroutes only after seeing the overload. I asked whether forecast-driven rerouting gives lower delay.

The data is real internet activity from six cells of Milan, November 2013, in 10-minute slots. I scaled it so that 100 means the 10 Mbps capacity of the slow path.

The model is Qwen2.5-1.5B-Instruct with LoRA rank 8. Six simulated clients, one per cell, trained it with Flower and FedAvg for 25 rounds. It reads 12 values and writes the next 6.

On the test block the model's MAE was 15.14, against 16.51 for repeat-last and 15.58 for a moving average. Its RMSE was higher than the moving average's.

The network is Mininet with a 10 Mbps and a 50 Mbps path, run by a POX controller that switches when the written value is above 100. I compared five modes over a 36-step trace, three times each.

On both cells, every model repetition had lower mean ping than every reactive repetition: 9.5 against 16.0 ms, and 7.5 against 13.9 ms.

But the model sent more steps to the fast path, so part of the gain may be from that. Each cell replays one trace, so this is repeatability, not variety. On synthetic data the model was worse than reactive.

I also tried a v2 with three changes. It failed two of four pre-written rules on validation, so v1 stayed final. The next step is to test whether a simple forecast with the same timing does as well."

# Part 12. Cheat sheet

> **In one line:** Everything to remember, on one page.

## The question

Does forecast-driven rerouting give lower delay than reactive rerouting in an emulated software-defined network? [CLAUDE.md]

## The pipeline in one line

Milan traffic, then a federated LoRA-tuned Qwen2.5-1.5B, then precomputed forecasts, then a forecast file, then the POX controller (above 100 means the fast path), then the Mininet network.

## The 5 most important numbers

| Number | Meaning | Source |
|---|---|---|
| 9.53 vs 16.06 ms | model vs reactive mean ping, cell 7511 | results/experiment_telecom/7511/summary.csv |
| 7.49 vs 13.91 ms | model vs reactive mean ping, cell 8336 | results/experiment_telecom/8336/summary.csv |
| 0.7222 vs 0.6111 | share of steps above 100, model vs reactive, cell 7511 | results/experiment_telecom/7511/summary.csv |
| 24.84 vs 9.75 ms | model vs reactive mean ping, synthetic | results/experiment/README.md |
| 15.14 / 16.51 / 15.58 | MAE of model / repeat-last / moving average, telecom test | results/final_telecom/outputs/metrics.json |

What this table means: lower delay on telecom, with more fast-path use, and the opposite result on synthetic data.

## The 3 limits you must mention

1. The model used the fast path more often than reactive, so part of the gain may come from that.
2. Each cell replays one 36-step trace three times: repeatability, not variety.
3. On synthetic data the model did not give lower delay than reactive.

## Is predictive routing better than reactive routing?

The honest answer: "On the two Milan cells tested, forecast-driven routing gave lower mean ping delay than reactive routing, but it also used the fast path more, and on synthetic data it did not. Whether the forecast's content matters is not yet tested."
