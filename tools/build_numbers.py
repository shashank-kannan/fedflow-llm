#!/usr/bin/env python3
"""
Builds every number used in the FedFlow-LLM report from the saved run files.

Reads only (never writes) results/, datasets/, training/, experiments/, controller/ and the
validation copies in results/v2_attempt/. Writes:
  report/generated/numbers.json   every computed value, unrounded, with its source file
  report/generated/numbers.tex    \\newcommand macros with report rounding (ms 1 dp, MAE/RMSE 2 dp, % 1 dp)
  report/generated/numbers.md     human-readable tables of the same values
  report/generated/sanity.txt     the sanity-fact check; exit code 2 if any fact fails

Usage:  python3 tools/build_numbers.py              build everything
        python3 tools/build_numbers.py --selftest   check the helpers on made-up data
Only the Python standard library is used.
"""
import csv
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "report", "generated")
THRESHOLD = 100.0  # 100 traffic units = the 10 Mbps primary link (checked against the code below)

EXPERIMENTS = {  # dataset label -> folder holding summary.csv and raw_<mode>_<rep>_* files
    "synthetic": "results/experiment",
    "t7511": "results/experiment_telecom/7511",
    "t8336": "results/experiment_telecom/8336",
}
SUMMARY_COLUMNS = ["ping_mean_ms", "ping_p95_ms", "server_udp_loss_pct", "delivered_vs_alt_pct",
                   "flip_lines", "frac_written_above_100"]
FORECAST_BLOCKS = {  # block label -> (forecasts file, metrics file)
    "synthetic_test": ("results/final/outputs/forecasts.csv", "results/final/outputs/metrics.json"),
    "telecom_test": ("results/final_telecom/outputs/forecasts.csv", "results/final_telecom/outputs/metrics.json"),
    "val_v1": ("results/v2_attempt/val_v1/val_forecasts.csv", "results/v2_attempt/val_v1/val_metrics.json"),
    "val_v2": ("results/v2_attempt/val_v2/val_forecasts.csv", "results/v2_attempt/val_v2/val_metrics.json"),
}
METHODS = ["model", "persistence", "moving_avg", "slope"]  # persistence = repeat-last


# ---------------------------------------------------------------- helpers (covered by --selftest)

def num(text):
    """Float for a numeric cell; None for text such as 'not computed' or a mismatch note."""
    try:
        v = float(text)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def stats(values):
    """mean/min/max over the numeric values; n = how many were usable (text values are left out)."""
    vals = [v for v in (num(x) for x in values) if v is not None]
    if not vals:
        return {"mean": None, "min": None, "max": None, "n": 0, "n_total": len(values)}
    return {"mean": sum(vals) / len(vals), "min": min(vals), "max": max(vals), "n": len(vals), "n_total": len(values)}


def mae_rmse(pairs):
    """(MAE, RMSE, count) over (prediction, truth) pairs."""
    if not pairs:
        return None, None, 0
    err = [p - t for p, t in pairs]
    return sum(abs(e) for e in err) / len(err), math.sqrt(sum(e * e for e in err) / len(err)), len(err)


def group_windows(rows):
    """Group forecast rows (one per step) into windows keyed by (cell, start); steps 1..6 in order."""
    win = {}
    for r in rows:
        key = (r.get("cell", "0"), r["start"])  # the synthetic file has no cell column: one series
        win.setdefault(key, []).append(r)
    for key, steps in win.items():
        steps.sort(key=lambda r: int(r["step"]))
        if [int(r["step"]) for r in steps] != list(range(1, 7)):
            raise ValueError(f"window {key} does not have steps 1-6")
    return win


def classify(steps, method="model"):
    """Onset / calm / high window type plus whether `method` flags a value above the threshold.
    Last history value = the persistence column (repeat-last forecasts the last history value)."""
    last = num(steps[0]["persistence"])
    true_peak = max(num(r["true"]) for r in steps)
    pred = [num(r[method]) for r in steps]
    pred_peak = None if any(p is None for p in pred) else max(pred)
    kind = "high" if last > THRESHOLD else ("onset" if true_peak > THRESHOLD else "calm")
    return kind, true_peak, pred_peak


def parsed(steps):
    """True when the model's six predictions for this window were parsed."""
    return all(str(r.get("parsed", "True")) == "True" for r in steps)


def rnd(v, dp):
    """Report rounding (half away from zero, as written by hand); None stays 'not computed'."""
    if v is None:
        return "not computed"
    q = 10 ** dp
    return f"{math.floor(abs(v) * q + 0.5) / q * (1 if v >= 0 else -1):.{dp}f}"


# ---------------------------------------------------------------- readers

def read_csv(rel):
    with open(os.path.join(ROOT, rel), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def grab(rel, pattern):
    """First regex group from a source file; stops the build if the constant is missing."""
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        m = re.search(pattern, f.read(), re.M)
    if not m:
        sys.exit(f"STOP: constant {pattern!r} not found in {rel}")
    return m.group(1)


# ---------------------------------------------------------------- builders

def constants():
    c = {
        "trace_len": int(grab("experiments/run_experiment.py", r"^TRACE_LEN\s*=\s*(\d+)")),
        "step_seconds": int(grab("experiments/run_experiment.py", r"^STEP_SECONDS\s*=\s*(\d+)")),
        "reps": int(grab("experiments/run_experiment.py", r"^REPS\s*=\s*(\d+)")),
        "modes": re.findall(r'"(\w+)"', grab("experiments/run_experiment.py", r"^MODES\s*=\s*\[(.*)\]")),
        "rounds": int(grab("training/server.py", r'FEDFLOW_ROUNDS",\s*"(\d+)"')),
        "clients": int(grab("training/client.py", r"^NUM_CLIENTS\s*=\s*(\d+)")),
        "history_len": int(grab("training/generate_data.py", r"^HISTORY_LEN\s*=\s*(\d+)")),
        "horizon": int(grab("training/generate_data.py", r"^HORIZON\s*=\s*(\d+)")),
        "threshold": float(grab("controller/reroute_trigger.py", r"^THRESHOLD\s*=\s*([\d.]+)")),
        "poll_seconds": float(grab("controller/reroute_trigger.py", r"^CHECK_INTERVAL\s*=\s*([\d.]+)")),
        "model_name": grab("training/client.py", r'^MODEL_NAME\s*=\s*"([^"]+)"'),
        "lora_r": int(grab("training/client.py", r"^\s*r=(\d+),")),
        "lora_alpha": int(grab("training/client.py", r"^\s*lora_alpha=(\d+),")),
        "lora_targets": re.findall(r'"(\w+)"', grab("training/client.py", r"target_modules=\[([^\]]*)\]")),
        "lora_dropout": float(grab("training/client.py", r"^\s*lora_dropout=([\d.]+),")),
        "max_length": int(grab("training/client.py", r"^MAX_LENGTH\s*=\s*(\d+)")),
        "learning_rate": float(grab("training/client.py", r"lr=([\deE.-]+)\)")),
        "local_epochs": int(grab("training/client.py", r"^LOCAL_EPOCHS\s*=\s*(\d+)")),
        "local_batch": int(grab("training/client.py", r"^LOCAL_BATCH_SIZE\s*=\s*(\d+)")),
        "primary_mbps": int(grab("controller/topo.py", r"addLink\(s1, s3, bw=(\d+)\)")),
        "alternate_mbps": int(grab("controller/topo.py", r"addLink\(s1, s4, bw=(\d+)\)")),
        "moving_avg_window": int(grab("training/infer.py", r"sum\(history\[-(\d+):\]\)")),
        "train_examples_telecom": len(read_json("training/data/telecom/traffic_train.json")),
        "train_examples_synthetic": len(read_json("training/data/traffic_train.json")),
    }
    src = open(os.path.join(ROOT, "training/client.py"), encoding="utf-8").read()
    c["base_dtype"] = "float16" if "torch_dtype=torch.float16" in src else "not found"
    c["four_bit"] = bool(re.search(r"load_in_4bit\s*=\s*True|BitsAndBytesConfig", src))  # QLoRA only if True
    c["labels_equal_input_ids"] = src.count("labels=input_ids") >= 2  # fit and evaluate
    c["label_masking"] = "-100" in src  # no masking unless some label is set to -100
    c["padding_max_length"] = 'padding="max_length"' in src
    meta = read_json("datasets/telecom_milan/cells_meta.json")
    c["cells"] = meta["squares"]
    c["scale_k"] = meta["k"]
    c["split"] = meta["split"]
    c["experiment_cells"] = [{"square": e["square"], "slice_start": e["best_slice_start"],
                              "crossings": e["best_slice_crossings"]} for e in meta["experiment_cells"]]
    return c


def routing(c):
    out = {}
    for label, folder in EXPERIMENTS.items():
        rows = read_csv(f"{folder}/summary.csv")
        out[label] = {}
        for mode in c["modes"]:
            mrows = [r for r in rows if r["mode"] == mode]
            entry = {col: stats([r[col] for r in mrows]) for col in SUMMARY_COLUMNS}
            above = []  # steps written above 100, counted from each run's own raw step file
            for r in mrows:
                steps = read_csv(f"{folder}/raw_{mode}_{r['rep']}_steps.csv")
                above.append(sum(1 for s in steps if num(s["value_written"]) > THRESHOLD))
            entry["steps_above_100"] = stats(above)
            entry["steps_total"] = len(steps)
            entry["source"] = f"{folder}/summary.csv; {folder}/raw_{mode}_*_steps.csv"
            out[label][mode] = entry
        # Flip lines counted again from the raw POX logs, to confirm summary.csv.
        for mode in c["modes"]:
            raw = []
            for r in [x for x in rows if x["mode"] == mode]:
                with open(os.path.join(ROOT, folder, f"raw_{mode}_{r['rep']}_pox.txt"), encoding="utf-8") as f:
                    raw.append(sum(1 for line in f if " FLIP " in line))
            out[label][mode]["flip_lines_raw_pox"] = raw
        if "reactive" in out[label] and "model" in out[label]:
            rv, mv = out[label]["reactive"]["ping_mean_ms"], out[label]["model"]["ping_mean_ms"]
            out[label]["relative_reduction_model_vs_reactive_pct"] = 100 * (rv["mean"] - mv["mean"]) / rv["mean"]
            out[label]["every_model_rep_below_every_reactive_rep"] = mv["max"] < rv["min"]
    return out


def forecasts():
    out = {}
    for label, (fc_rel, met_rel) in FORECAST_BLOCKS.items():
        win = group_windows(read_csv(fc_rel))
        metrics = read_json(met_rel)
        block = {"source": f"{fc_rel}; {met_rel}", "windows": len(win),
                 "windows_parsed": sum(1 for s in win.values() if parsed(s))}
        cells = sorted({k[0] for k in win}, key=int)
        for scope in ["overall"] + cells:
            keys = [k for k in win if scope == "overall" or k[0] == scope]
            res = {}
            for m in METHODS:
                if m not in win[keys[0]][0]:
                    res[m] = {"mae": None, "rmse": None, "n_values": 0}  # this file has no such column
                    continue
                pairs = [(num(r[m]), num(r["true"])) for k in keys if parsed(win[k]) for r in win[k]]
                mae, rmse, n = mae_rmse(pairs)
                res[m] = {"mae": mae, "rmse": rmse, "n_values": n}
            # Onset recall and calm false alarms (model), from the forecast file alone.
            on = flag = calm = calm_fa = 0
            err = []
            for k in keys:
                if not parsed(win[k]):
                    continue
                kind, tp, pp = classify(win[k])
                if kind == "onset":
                    on += 1; flag += pp > THRESHOLD; err.append(pp - tp)
                elif kind == "calm":
                    calm += 1; calm_fa += pp > THRESHOLD
            res["onset"] = {"windows": on, "flagged": flag, "mean_peak_error": (sum(err) / len(err)) if err else None,
                            "calm_windows": calm, "calm_false_alarms": calm_fa}
            if scope != "overall" and "per_cell" in metrics:
                res["square_id"] = metrics["per_cell"][scope]["square_id"]
            res["windows"] = len(keys)
            block[scope] = res
        # Cross-check against the run's own metrics.json (same windows, so values must agree).
        block["metrics_json_model_mae"] = metrics["model"]["mae"]
        block["metrics_json_model_rmse"] = metrics["model"]["rmse"]
        block["metrics_json_windows_scored"] = metrics["windows_scored"]
        out[label] = block
    return out


def route_timeline():
    """Cell 7511, rep 1: true load and the value reactive and model wrote at each step."""
    out = {"source": "results/experiment_telecom/7511/raw_{reactive,model}_1_steps.csv"}
    for mode in ("reactive", "model"):
        rows = read_csv(f"results/experiment_telecom/7511/raw_{mode}_1_steps.csv")
        out["step"] = [int(r["step"]) for r in rows]
        out["true"] = [num(r["true_value"]) for r in rows]  # same trace in both files
        out[mode] = [num(r["value_written"]) for r in rows]
    return out


def training_loss():
    out = {}
    for label, rel in [("synthetic", "results/final/outputs/loss_history.csv"),
                       ("telecom", "results/final_telecom/outputs/loss_history.csv")]:
        rows = read_csv(rel)
        out[label] = {"source": rel, "rounds": [int(r["round"]) for r in rows], "loss": [num(r["loss"]) for r in rows]}
    return out


# ---------------------------------------------------------------- sanity facts from the task

def sanity(R, F):
    """(label, computed, expected, decimals). A fact passes when the computed value, rounded to the
    expected value's decimals, equals it."""
    p = lambda d, m, col="ping_mean_ms": R[d][m][col]["mean"]
    facts = [
        # 48.3 and 16.1 replace the task's ~48.4 and ~16.0: the user confirmed the computed values on 31 Oct 2026
        ("7511 static ping ms", p("t7511", "static"), "48.3"), ("7511 reactive ping ms", p("t7511", "reactive"), "16.1"),
        ("7511 model ping ms", p("t7511", "model"), "9.5"), ("7511 oracle ping ms", p("t7511", "oracle"), "0.2"),
        ("7511 alt ping ms", p("t7511", "alt"), "0.2"),
        ("8336 static ping ms", p("t8336", "static"), "58.9"), ("8336 reactive ping ms", p("t8336", "reactive"), "13.9"),
        ("8336 model ping ms", p("t8336", "model"), "7.5"),
        ("synthetic static ping ms", p("synthetic", "static"), "43.13"),
        ("synthetic reactive ping ms", p("synthetic", "reactive"), "9.75"),
        ("synthetic model ping ms", p("synthetic", "model"), "24.84"),
        ("synthetic oracle ping ms", p("synthetic", "oracle"), "0.11"), ("synthetic alt ping ms", p("synthetic", "alt"), "0.11"),
        ("7511 reactive flips", p("t7511", "reactive", "flip_lines"), "15"), ("7511 model flips", p("t7511", "model", "flip_lines"), "5"),
        ("8336 reactive flips", p("t8336", "reactive", "flip_lines"), "15"), ("8336 model flips", p("t8336", "model", "flip_lines"), "3"),
        ("telecom test MAE model", F["telecom_test"]["overall"]["model"]["mae"], "15.14"),
        ("telecom test MAE repeat-last", F["telecom_test"]["overall"]["persistence"]["mae"], "16.51"),
        ("telecom test MAE moving avg", F["telecom_test"]["overall"]["moving_avg"]["mae"], "15.58"),
        ("telecom test RMSE model", F["telecom_test"]["overall"]["model"]["rmse"], "24.76"),
        ("telecom test RMSE repeat-last", F["telecom_test"]["overall"]["persistence"]["rmse"], "26.16"),
        ("telecom test RMSE moving avg", F["telecom_test"]["overall"]["moving_avg"]["rmse"], "23.95"),
        ("telecom test windows", F["telecom_test"]["windows"], "366"),
        ("synthetic test MAE model", F["synthetic_test"]["overall"]["model"]["mae"], "10.34"),
        ("synthetic test MAE repeat-last", F["synthetic_test"]["overall"]["persistence"]["mae"], "11.29"),
        ("synthetic test MAE moving avg", F["synthetic_test"]["overall"]["moving_avg"]["mae"], "10.86"),
        ("synthetic test windows", F["synthetic_test"]["windows"], "91"),
        ("7511 onset windows", F["telecom_test"]["3"]["onset"]["windows"], "14"),
        ("7511 onsets flagged", F["telecom_test"]["3"]["onset"]["flagged"], "6"),
        ("8336 onset windows", F["telecom_test"]["2"]["onset"]["windows"], "14"),
        ("8336 onsets flagged", F["telecom_test"]["2"]["onset"]["flagged"], "4"),
        ("7511 mean peak error", F["telecom_test"]["3"]["onset"]["mean_peak_error"], "-44.04"),
        ("8336 mean peak error", F["telecom_test"]["2"]["onset"]["mean_peak_error"], "-33.36"),
        ("val v1 MAE", F["val_v1"]["overall"]["model"]["mae"], "15.00"),
        ("val v2 MAE", F["val_v2"]["overall"]["model"]["mae"], "15.78"),
        ("val v1 pooled onsets flagged", F["val_v1"]["overall"]["onset"]["flagged"], "11"),
        ("val v2 pooled onsets flagged", F["val_v2"]["overall"]["onset"]["flagged"], "17"),
        ("val v1 pooled onset windows", F["val_v1"]["overall"]["onset"]["windows"], "29"),
        ("val v2 pooled onset windows", F["val_v2"]["overall"]["onset"]["windows"], "29"),
        ("val v1 calm false alarms", F["val_v1"]["overall"]["onset"]["calm_false_alarms"], "4"),
        ("val v1 calm windows", F["val_v1"]["overall"]["onset"]["calm_windows"], "110"),
        ("val v2 calm false alarms", F["val_v2"]["overall"]["onset"]["calm_false_alarms"], "16"),
        ("val v2 calm windows", F["val_v2"]["overall"]["onset"]["calm_windows"], "111"),
    ]
    lines, failed = [], 0
    for label, value, expected in facts:
        dp = len(expected.split(".")[1]) if "." in expected else 0
        got = rnd(value, dp)
        ok = got == expected
        failed += not ok
        lines.append(f"{'OK  ' if ok else 'FAIL'} {label}: computed {value!r} -> {got}, expected {expected}")
    # UDP loss 0 in every scored run (text values = not scored, listed separately).
    for d in EXPERIMENTS:
        for m, e in R[d].items():
            if not isinstance(e, dict) or "server_udp_loss_pct" not in e:
                continue
            s = e["server_udp_loss_pct"]
            ok = s["n"] == 0 or s["max"] == 0.0
            failed += not ok
            lines.append(f"{'OK  ' if ok else 'FAIL'} UDP loss {d} {m}: max {s['max']} over {s['n']} of {s['n_total']} scored runs")
    return lines, failed


# ---------------------------------------------------------------- writers

def write_outputs(c, R, F, L, T, lines, failed):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "numbers.json"), "w", encoding="utf-8") as f:
        json.dump({"constants": c, "routing": R, "forecasts": F, "training_loss": L, "route_timeline": T}, f, indent=1, default=str)
    with open(os.path.join(OUT, "sanity.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + f"\n\nFAILED: {failed}\n")
    # LaTeX macros: letters only in names, so digits are spelled out.
    word = {"synthetic": "Syn", "t7511": "CellA", "t8336": "CellB"}
    mw = {"static": "Static", "reactive": "Reactive", "model": "Model", "oracle": "Oracle", "alt": "Alt"}
    tex = ["% Generated by tools/build_numbers.py -- do not edit by hand.", "% CellA = square 7511, CellB = square 8336."]
    for d, dw in word.items():
        for m, w in mw.items():
            e = R[d][m]
            tex.append(f"\\newcommand{{\\Ping{dw}{w}}}{{{rnd(e['ping_mean_ms']['mean'], 1 if d != 'synthetic' else 2)}}}")
            tex.append(f"\\newcommand{{\\Flips{dw}{w}}}{{{rnd(e['flip_lines']['mean'], 0)}}}")
            tex.append(f"\\newcommand{{\\Above{dw}{w}}}{{{rnd(e['steps_above_100']['mean'], 0)}}}")
            tex.append(f"\\newcommand{{\\AbovePct{dw}{w}}}{{{rnd(100 * e['frac_written_above_100']['mean'], 1)}}}")
        if d != "synthetic":
            tex.append(f"\\newcommand{{\\Reduction{dw}}}{{{rnd(R[d]['relative_reduction_model_vs_reactive_pct'], 1)}}}")
    bw = {"synthetic_test": "SynTest", "telecom_test": "TelTest", "val_v1": "ValOne", "val_v2": "ValTwo"}
    mm = {"model": "Model", "persistence": "Last", "moving_avg": "MA", "slope": "Slope"}
    for b, w in bw.items():
        for m, mw2 in mm.items():
            o = F[b]["overall"][m]
            tex.append(f"\\newcommand{{\\MAE{w}{mw2}}}{{{rnd(o['mae'], 2)}}}")
            tex.append(f"\\newcommand{{\\RMSE{w}{mw2}}}{{{rnd(o['rmse'], 2)}}}")
        o = F[b]["overall"]["onset"]
        tex += [f"\\newcommand{{\\Windows{w}}}{{{F[b]['windows']}}}",
                f"\\newcommand{{\\Onsets{w}}}{{{o['windows']}}}", f"\\newcommand{{\\OnsetsHit{w}}}{{{o['flagged']}}}",
                f"\\newcommand{{\\Calm{w}}}{{{o['calm_windows']}}}", f"\\newcommand{{\\CalmFA{w}}}{{{o['calm_false_alarms']}}}"]
    for cell, w in [("3", "CellA"), ("2", "CellB")]:
        o = F["telecom_test"][cell]["onset"]
        tex += [f"\\newcommand{{\\Onsets{w}}}{{{o['windows']}}}", f"\\newcommand{{\\OnsetsHit{w}}}{{{o['flagged']}}}",
                f"\\newcommand{{\\PeakErr{w}}}{{{rnd(o['mean_peak_error'], 2)}}}"]
    tl = L["telecom"]["loss"]
    tex += [f"\\newcommand{{\\LossFirst}}{{{rnd(tl[0], 3)}}}", f"\\newcommand{{\\LossLast}}{{{rnd(tl[-1], 3)}}}"]
    with open(os.path.join(OUT, "numbers.tex"), "w", encoding="utf-8") as f:
        f.write("\n".join(tex) + "\n")
    # Markdown tables for reading.
    md = ["# FedFlow-LLM numbers (generated by tools/build_numbers.py)", ""]
    for d in EXPERIMENTS:
        md += [f"## Routing: {d} ({EXPERIMENTS[d]})", "",
               "| mode | ping mean ms (min-max, n) | ping p95 ms | UDP loss % (n) | delivered vs alt % | flips | steps >100 | share >100 % |",
               "|---|---|---|---|---|---|---|---|"]
        for m in c["modes"]:
            e = R[d][m]
            s = lambda col, dp: f"{rnd(e[col]['mean'], dp)} ({rnd(e[col]['min'], dp)}-{rnd(e[col]['max'], dp)}, n={e[col]['n']})"
            md.append(f"| {m} | {s('ping_mean_ms', 2)} | {s('ping_p95_ms', 1)} | {s('server_udp_loss_pct', 1)} | "
                      f"{s('delivered_vs_alt_pct', 1)} | {s('flip_lines', 0)} | {s('steps_above_100', 0)} of {e['steps_total']} | "
                      f"{rnd(100 * e['frac_written_above_100']['mean'], 1)} |")
        if d != "synthetic":
            md.append(f"\nRelative reduction (reactive - model)/reactive: {rnd(R[d]['relative_reduction_model_vs_reactive_pct'], 1)}%; "
                      f"every model rep below every reactive rep: {R[d]['every_model_rep_below_every_reactive_rep']}")
        md.append("")
    for b in FORECAST_BLOCKS:
        blk = F[b]
        md += [f"## Forecasts: {b} ({blk['source']})", f"Windows {blk['windows']}, parsed {blk['windows_parsed']}.", "",
               "| scope | model MAE/RMSE | repeat-last | moving avg | slope | onsets hit/windows | mean peak err | calm FA/calm |",
               "|---|---|---|---|---|---|---|---|"]
        for scope in [k for k in blk if k == "overall" or k.isdigit()]:
            r = blk[scope]
            f2 = lambda m: f"{rnd(r[m]['mae'], 2)} / {rnd(r[m]['rmse'], 2)}"
            name = scope if scope == "overall" else f"cell {scope} ({r.get('square_id', '-')})"
            o = r["onset"]
            md.append(f"| {name} | {f2('model')} | {f2('persistence')} | {f2('moving_avg')} | {f2('slope')} | "
                      f"{o['flagged']}/{o['windows']} | {rnd(o['mean_peak_error'], 2)} | {o['calm_false_alarms']}/{o['calm_windows']} |")
        md.append("")
    with open(os.path.join(OUT, "numbers.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")


# ---------------------------------------------------------------- selftest

def selftest():
    assert num("1.5") == 1.5 and num("not computed") is None and num("server report count mismatch") is None
    s = stats(["1", "3", "not computed"])
    assert s == {"mean": 2.0, "min": 1.0, "max": 3.0, "n": 2, "n_total": 3}, s
    assert stats(["x"])["n"] == 0
    mae, rmse, n = mae_rmse([(1, 0), (0, 3)])
    assert (mae, n) == (2.0, 2) and abs(rmse - math.sqrt(5)) < 1e-12
    assert rnd(16.056, 1) == "16.1" and rnd(48.322, 1) == "48.3" and rnd(-44.035, 2) == "-44.04" and rnd(0.25, 1) == "0.3"
    assert rnd(None, 2) == "not computed"
    mk = lambda last, trues, preds: [{"cell": "0", "start": "0", "step": str(i + 1), "persistence": str(last),
                                      "true": str(t), "model": str(p)} for i, (t, p) in enumerate(zip(trues, preds))]
    w = group_windows(mk(90, [95, 101, 99, 98, 97, 96], [99, 100, 99, 99, 99, 99]))
    kind, tp, pp = classify(w[("0", "0")])
    assert (kind, tp, pp) == ("onset", 101.0, 100.0)  # exactly 100 is not "above"
    assert classify(mk(100, [90] * 6, [101] * 6))[0] == "calm"  # last value 100 counts as not high
    assert classify(mk(100.5, [90] * 6, [90] * 6))[0] == "high"
    try:
        group_windows(mk(90, [1] * 5, [1] * 5))
        raise AssertionError("a 5-step window must be refused")
    except ValueError:
        pass
    print("SELFTEST OK")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return
    c = constants()
    if c["threshold"] != THRESHOLD:
        sys.exit(f"STOP: controller threshold {c['threshold']} differs from {THRESHOLD}")
    R, F, L, T = routing(c), forecasts(), training_loss(), route_timeline()
    lines, failed = sanity(R, F)
    write_outputs(c, R, F, L, T, lines, failed)
    print("\n".join(l for l in lines if l.startswith("FAIL")) or "all sanity facts OK")
    print(f"wrote {OUT}/numbers.json, numbers.tex, numbers.md, sanity.txt; failed facts: {failed}")
    sys.exit(2 if failed else 0)


if __name__ == "__main__":
    main()
