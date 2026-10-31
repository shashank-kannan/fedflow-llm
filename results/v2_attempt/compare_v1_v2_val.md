# v1 vs v2 on the validation block

Written by `training/compare_variants.py` from these files only:

- v1: `/home/shashank/fedflow_data/val_v1/val_metrics.json`, `/home/shashank/fedflow_data/val_v1/val_forecasts.csv`
- v2: `/home/shashank/fedflow_data/val_v2/outputs/val_metrics.json`, `/home/shashank/fedflow_data/val_v2/outputs/val_forecasts.csv`

Adoption rules from PLAN_V2.md; all four must hold.

| Rule | v1 | v2 | Holds |
|---|---|---|---|
| 1. Overall model MAE lower than v1's | 15.0002 | 15.7826 | NO |
| 2. Pooled onset recall (all cells) higher than v1's | 11/29 (37.9%) | 17/29 (58.6%) | yes |
| 3. Calm false-alarm rate at most 5 points above v1's (v2 - v1 = +10.78 points) | 4/110 (3.6%) | 16/111 (14.4%) | NO |
| 4. Parse failures no more than v1's | 1 | 0 | yes |

## Runs

| | v1 | v2 |
|---|---:|---:|
| Variant (from metrics) | v1 (no variant field) | v2 |
| Windows used | 276 | 276 |
| Windows scored | 275 | 276 |
| Parse failures (metrics) | 1 | 0 |
| Unparsed windows (forecasts CSV) | 1 | 0 |
| Onset / calm / already-high windows | 29 / 111 / 136 | 29 / 111 / 136 |

## Error over all scored windows (from val_metrics.json)

| Method | v1 MAE | v2 MAE | v1 RMSE | v2 RMSE |
|---|---:|---:|---:|---:|
| Model | 15.00 | 15.78 | 25.13 | 25.74 |
| Persistence | 15.80 | 15.78 | 27.75 | 27.71 |
| Moving average (last 3) | 15.67 | 15.67 | 25.59 | 25.56 |
| Slope baseline | 19.29 | 19.25 | 32.01 | 31.96 |

Baselines depend only on the windows, so they match between the runs when both scored the same windows (they can differ only through which windows parsed).

## Peaks, pooled over all cells (from val_forecasts.csv)

| Measure | v1 model | v2 model | v1 slope | v2 slope |
|---|---:|---:|---:|---:|
| Onset recall | 11/29 (37.9%) | 17/29 (58.6%) | 8/29 (27.6%) | 8/29 (27.6%) |
| Calm false-alarm rate | 4/110 (3.6%) | 16/111 (14.4%) | 2/110 (1.8%) | 2/111 (1.8%) |
| Mean (predicted peak - true peak) on onsets | -51.05 | -47.65 | -52.08 | -52.08 |

Validation windows start every 6 slots and are 18 slots long, so neighbouring windows overlap; counts are not independent samples.

## Per cell

| Cell | Square | v1 MAE | v2 MAE | v1 RMSE | v2 RMSE | v1 onset recall | v2 onset recall | v1 calm false alarms | v2 calm false alarms | v1 mean onset error | v2 mean onset error | slope MAE (v1 run) | slope onset recall (v1 run) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 9721 | 7.05 | 8.17 | 10.44 | 11.90 | 0/1 (0.0%) | 0/1 (0.0%) | 1/45 (2.2%) | 5/45 (11.1%) | -51.27 | -51.97 | 7.17 | 0/1 (0.0%) |
| 1 | 6997 | 11.09 | 11.36 | 15.60 | 15.70 | 2/4 (50.0%) | 3/4 (75.0%) | 1/23 (4.3%) | 4/24 (16.7%) | -30.51 | -31.29 | 12.26 | 2/4 (50.0%) |
| 2 | 8336 | 12.05 | 11.74 | 17.80 | 17.36 | 4/8 (50.0%) | 4/8 (50.0%) | 1/15 (6.7%) | 1/15 (6.7%) | -46.46 | -47.82 | 14.90 | 1/8 (12.5%) |
| 3 | 7511 | 14.20 | 16.17 | 20.03 | 22.34 | 2/4 (50.0%) | 2/4 (50.0%) | 0/12 (0.0%) | 2/12 (16.7%) | -40.12 | -38.19 | 17.44 | 2/4 (50.0%) |
| 4 | 8062 | 19.26 | 19.74 | 32.95 | 34.21 | 2/7 (28.6%) | 5/7 (71.4%) | 1/8 (12.5%) | 3/8 (37.5%) | -71.31 | -66.10 | 26.66 | 2/7 (28.6%) |
| 5 | 7584 | 26.26 | 27.52 | 40.32 | 40.19 | 1/5 (20.0%) | 3/5 (60.0%) | 0/7 (0.0%) | 1/7 (14.3%) | -55.17 | -41.35 | 37.15 | 1/5 (20.0%) |

Per-cell onset counts are small; the pooled figures above are the ones the rules use.

**DECISION: DO NOT ADOPT**
