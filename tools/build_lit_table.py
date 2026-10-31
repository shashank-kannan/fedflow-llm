#!/usr/bin/env python3
"""Builds references/lit_table.csv. Venue, publisher and year come from references/verification_log.csv;
Technique and Inference are paraphrased from references/abstracts/<key>.txt; Cons states only what the abstract shows
the work does not address relative to this project (forecast-driven rerouting in an emulated SDN, federated training).
Works whose abstract could not be read are not in the table. Run from the repository root."""
import csv
log = {r["key"]: r for r in csv.DictReader(open("references/verification_log.csv", encoding="utf-8"))}
rows = [  # key, technique (from abstract), inference (from abstract), cons (scope gap vs. this project, from abstract)
 ("yang2026hfrl", "GCN-LSTM-attention utilisation forecast feeding hierarchical federated RL routing agents (POMDP, actor-critic)",
  "Forecast-aware routing kept lower steady-state end-to-end latency than DDQN, shortest-path and ELB as load grew",
  "Satellite constellation simulation; no SDN controller or emulated network"),
 ("silva2026netlink", "Federated ML classifier of SDN link utilisation from end-to-end traffic matrices at an MEC layer",
  "Link load can be estimated without per-link sensors and used by a routing VNF",
  "Classifies current link state; no forecast of future load"),
 ("kim2022drlsdn", "Deep RL agent sets link weights; SDN controller installs paths; offline training on an M/M/1/K model",
  "Balanced delay and loss better than hop-count routing and a demand-based RL method in simulation",
  "Simulation only; no traffic forecasting or federated training"),
 ("yuliana2026hybrid", "Hybrid LSTM-Transformer with sinusoidal time embedding on operator KPI data from 23 cells",
  "Lower error than ARIMA, LSTM-only and ConvLSTM baselines on real KPI data",
  "Forecasting only; no routing action"),
 ("ma2025byzantine", "Asynchronous federated learning with local differential privacy and distributionally robust optimisation",
  "Traffic prediction stays robust to Byzantine clients while data remains local",
  "Forecasting only; no use of forecasts in a network control loop"),
 ("wang2026mobilellm", "Partially frozen GPT-2 fusing numerical traffic tokens with semantic context embeddings",
  "Lower MAE than strong baselines on Milan, Trentino and Shanghai traffic",
  "Forecasting only; no routing or controller in the loop"),
 ("sun2025fdallm", "Functional data analysis features with engineered prompts for LLM traffic prediction",
  "Prompting with FDA features improved LLM traffic forecasts on a real dataset",
  "No federated training; no routing action"),
 ("rong2025stgllm", "Spatio-temporal generative LLM trained on edge servers over road-network subgraphs",
  "Better accuracy and training efficiency than baselines on two road-traffic datasets",
  "Road traffic, not network traffic; no routing"),
 ("zhou2025llmtelecom", "Survey of LLMs for telecom: generation, classification, optimisation and prediction",
  "Lists time-series and multimodal traffic prediction as LLM telecom tasks",
  "Survey; no new measurements"),
 ("yang2026dmllm", "Survey of LLM decision-making for wireless: prompts, chain of thought, decision frameworks, multi-agent",
  "LLM use in wireless decisions is still fragmented and exploratory",
  "Survey; no emulated network results"),
]
with open("references/lit_table.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["S.No", "key", "Journal/Conference name and publisher, year", "Technique adopted", "Inference", "Cons"])
    for i, (k, tech, inf, cons) in enumerate(rows, 1):
        r = log[k]
        assert r["usable"] == "yes" and 2021 <= int(r["year"]) <= 2026, k  # table rule: 2021-2026, verified
        w.writerow([i, k, f"{r['venue']}, {r['publisher']}, {r['year']}", tech, inf, cons])
print(len(rows), "rows")
