#!/usr/bin/env python3
"""
Draws the report figures from report/generated/numbers.json (written by tools/build_numbers.py).
No number is typed here: every plotted value is read from that file.

Writes into figures/: <name>.pdf, <name>.png, <name>.data.csv for each figure, and captions.json.
Usage:  python3 tools/build_numbers.py && python3 tools/make_figures.py
"""
import csv
import json
import os

import matplotlib

matplotlib.use("Agg")  # no display needed
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "figures")
N = json.load(open(os.path.join(ROOT, "report", "generated", "numbers.json"), encoding="utf-8"))

plt.rcParams.update({
    "pdf.fonttype": 42, "ps.fonttype": 42,  # embed TrueType so text stays text in the PDF
    "font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9, "legend.fontsize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.spines.top": False, "axes.spines.right": False,
})
C = N["constants"]  # short name, used inside f-strings
MODES = C["modes"]
# Okabe-Ito colour-blind-safe palette; one colour per routing mode, the same in every figure.
MODE_COLOUR = {"static": "#7F7F7F", "reactive": "#D55E00", "model": "#0072B2", "oracle": "#009E73", "alt": "#CC79A7"}
METHOD_COLOUR = {"model": "#0072B2", "persistence": "#E69F00", "moving_avg": "#56B4E9"}
METHOD_LABEL = {"model": "FedFlow-LLM model", "persistence": "repeat-last",
                "moving_avg": f"moving average (last {C['moving_avg_window']})"}
REFERENCE = {"oracle", "alt"}  # not deployable: oracle sees the future, alt ignores load
CELL_NAME = {"t7511": "Cell 7511", "t8336": "Cell 8336"}
captions = {}


def save(fig, name, rows, header, caption):
    """PDF + PNG + the plotted data as CSV, and the caption."""
    fig.savefig(os.path.join(FIG, f"{name}.pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(FIG, f"{name}.png"), bbox_inches="tight", dpi=200)
    plt.close(fig)
    with open(os.path.join(FIG, f"{name}.data.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    captions[name] = caption


def fig_telecom_delay():
    R = N["routing"]
    top = max(R[d][m]["ping_mean_ms"]["max"] for d in ("t7511", "t8336") for m in MODES) * 1.22  # room for labels
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 3.0), sharey=True)
    rows = []
    ns = set()
    for ax, d in zip(axes, ("t7511", "t8336")):
        for i, m in enumerate(MODES):
            s = R[d][m]["ping_mean_ms"]
            share = 100 * R[d][m]["frac_written_above_100"]["mean"]
            ns.add(s["n"])
            ax.bar(i, s["mean"], color=MODE_COLOUR[m], edgecolor="black", linewidth=0.5,
                   hatch="///" if m in REFERENCE else None, alpha=0.55 if m in REFERENCE else 1.0)
            ax.errorbar(i, s["mean"], yerr=[[s["mean"] - s["min"]], [s["max"] - s["mean"]]],
                        color="black", capsize=3, linewidth=0.8)
            ax.text(i, s["max"] + top * 0.015, f"{s['mean']:.1f}\n{share:.0f}%", ha="center", va="bottom", fontsize=6.5)
            rows.append([CELL_NAME[d], m, s["mean"], s["min"], s["max"], s["n"], share])
        ax.set_xticks(range(len(MODES)), [f"{m}*" if m in REFERENCE else m for m in MODES], fontsize=7.5)
        ax.set_title(CELL_NAME[d])
        ax.set_ylim(0, top)
    axes[0].set_ylabel("Mean ping delay (ms)")
    n_note = f"n = {ns.pop()} runs per bar" if len(ns) == 1 else "n differs per bar (see data file)"
    fig.suptitle("Mean ping delay per routing mode on the two Milan cells", y=1.03)
    fig.text(0.5, -0.04, f"Labels: mean ms, then share of steps written above {C['threshold']:.0f}.  * reference mode (hatched).  "
             f"Whiskers: min to max; {n_note}.", ha="center", fontsize=7)
    save(fig, "fig_telecom_delay", rows, ["cell", "mode", "mean_ms", "min_ms", "max_ms", "n_runs", "share_steps_written_above_100_pct"],
         "Mean ping delay per routing mode on cells 7511 and 8336 (bars: mean of the runs; whiskers: min to max; n: runs used). "
         "Oracle and alt are hatched reference modes. Each label also gives the share of steps on which that mode wrote a value above 100.")


def fig_telecom_flips():
    R = N["routing"]
    fig, ax = plt.subplots(figsize=(6.0, 2.8))
    width = 0.38
    rows = []
    for j, d in enumerate(("t7511", "t8336")):
        for i, m in enumerate(MODES):
            s = R[d][m]["flip_lines"]
            x = i + (j - 0.5) * width
            ax.bar(x, s["mean"], width, color=MODE_COLOUR[m], edgecolor="black", linewidth=0.5,
                   hatch=("..." if j else None))
            ax.text(x, s["mean"] + 0.3, f"{s['mean']:.0f}", ha="center", fontsize=7.5)
            rows.append([CELL_NAME[d], m, s["mean"], s["min"], s["max"], s["n"]])
    ax.set_xticks(range(len(MODES)), MODES)
    ax.set_ylabel("Route flips per run")
    ax.set_ylim(bottom=0)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor="white", edgecolor="black", label="Cell 7511"),
                       Patch(facecolor="white", edgecolor="black", hatch="...", label="Cell 8336")], frameon=False)
    ax.set_title("Route flips per run, by routing mode and cell (same count in every run)")
    save(fig, "fig_telecom_flips", rows, ["cell", "mode", "mean_flips", "min", "max", "n_runs"],
         "Route flips (path changes logged by the POX controller) per run, for each routing mode on cells 7511 and 8336.")


def fig_route_timeline():
    T = N["route_timeline"]
    thr = N["constants"]["threshold"]
    fig, ax = plt.subplots(figsize=(6.4, 2.9))
    x = T["step"]
    ax.axhspan(thr, max(T["true"] + T["reactive"] + T["model"]) * 1.05, color="#F0E442", alpha=0.18, lw=0)
    ax.step(x, T["true"], where="post", color="#555555", lw=1.2, label="true load")
    ax.step(x, T["reactive"], where="post", color=MODE_COLOUR["reactive"], lw=1.2, label="reactive (value written)")
    ax.step(x, T["model"], where="post", color=MODE_COLOUR["model"], lw=1.8, label="model (value written)")
    ax.axhline(thr, color="black", ls="--", lw=0.9, label=f"threshold {thr:.0f} (= {C['primary_mbps']} Mbps)")
    ax.set_xlabel(f"Step ({C['step_seconds']} s each), cell 7511, run 1")
    ax.set_ylabel(f"Load ({thr:.0f} = {C['primary_mbps']} Mbps)")
    ax.set_ylim(0, max(T["true"] + T["reactive"] + T["model"]) * 1.05)
    ax.set_xlim(x[0], x[-1])
    ax.legend(ncol=2, frameon=False, loc="upper right")
    ax.set_title(f"Values written to the forecast file each step (shaded: above {thr:.0f}, alternate path)")
    save(fig, "fig_route_timeline", list(zip(x, T["true"], T["reactive"], T["model"])),
         ["step", "true_load", "reactive_written", "model_written"],
         f"Cell 7511, run 1: true load and the value the reactive and model modes wrote at each {C['step_seconds']} s step. "
         f"The controller sends traffic on the alternate path while the written value is above {C['threshold']:.0f} (shaded).")


def fig_accuracy_overall():
    F = N["forecasts"]
    blocks = [("synthetic_test", "Synthetic test"), ("telecom_test", "Telecom test")]
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    width = 0.26
    rows = []
    for j, m in enumerate(METHOD_COLOUR):
        for i, (b, label) in enumerate(blocks):
            v = F[b]["overall"][m]["mae"]
            x = i + (j - 1) * width
            ax.bar(x, v, width, color=METHOD_COLOUR[m], edgecolor="black", linewidth=0.5,
                   label=METHOD_LABEL[m] if i == 0 else None)
            ax.text(x, v + 0.2, f"{v:.2f}", ha="center", fontsize=7.5)
            rows.append([label, F[b]["windows"], m, v, F[b]["overall"][m]["rmse"]])
    ax.set_xticks(range(len(blocks)), [f"{l}\n({F[b]['windows']} windows)" for b, l in blocks])
    ax.set_ylabel("MAE (load units, 100 = 10 Mbps)")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("Forecast error (MAE) on the held-out test blocks")
    save(fig, "fig_accuracy_overall", rows, ["block", "windows", "method", "mae", "rmse"],
         f"Mean absolute error of the {C['horizon']}-step forecasts on the synthetic and telecom test blocks, "
         f"for the federated model, repeat-last and a {C['moving_avg_window']}-value moving average.")


def fig_accuracy_by_cell():
    F = N["forecasts"]["telecom_test"]
    cells = sorted([k for k in F if k.isdigit()], key=int)
    fig, ax = plt.subplots(figsize=(6.2, 2.9))
    width = 0.38
    rows = []
    for j, m in enumerate(("model", "persistence")):
        for i, c in enumerate(cells):
            v = F[c][m]["mae"]
            x = i + (j - 0.5) * width
            ax.bar(x, v, width, color=METHOD_COLOUR[m], edgecolor="black", linewidth=0.5,
                   label=METHOD_LABEL[m] if i == 0 else None)
            ax.text(x, v + 0.3, f"{v:.1f}", ha="center", fontsize=7)
            rows.append([F[c]["square_id"], F[c]["windows"], m, v])
    ax.set_xticks(range(len(cells)), [f"{F[c]['square_id']}\n({F[c]['windows']} win.)" for c in cells])
    ax.set_xlabel("Milan grid cell (square ID)")
    ax.set_ylabel("MAE (load units)")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("Forecast error (MAE) per cell on the telecom test block")
    save(fig, "fig_accuracy_by_cell", rows, ["square_id", "windows", "method", "mae"],
         "Mean absolute error per Milan cell on the telecom test block, federated model next to repeat-last.")


def fig_training_loss():
    L = N["training_loss"]
    fig, ax = plt.subplots(figsize=(5.4, 2.7))
    rows = []
    for label, colour in (("synthetic", "#E69F00"), ("telecom", "#0072B2")):
        ax.plot(L[label]["rounds"], L[label]["loss"], marker="o", ms=2.5, color=colour, label=f"{label} data")
        rows += [[label, r, v] for r, v in zip(L[label]["rounds"], L[label]["loss"])]
    ax.set_xlabel("Federated round")
    ax.set_ylabel("Training loss")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False)
    ax.set_title("Federated training loss per round")
    save(fig, "fig_training_loss", rows, ["data", "round", "loss"],
         "Training loss after each federated round (aggregated over clients by the Flower server, measured on training examples). "
         "It shows that training ran and converged; it is not a measure of forecast quality.")


def tikz_figures():
    """Pipeline and topology diagrams as TikZ, with every number taken from the constants."""
    os.makedirs(os.path.join(FIG, "tikz"), exist_ok=True)
    pipeline = r"""%% Generated by tools/make_figures.py. Needs \usetikzlibrary{positioning,arrows.meta}.
\begin{tikzpicture}[
    box/.style={draw, rounded corners, fill=blue!6, align=center, minimum width=3.2cm, minimum height=1.15cm, font=\small},
    arr/.style={-{Stealth[length=2.5mm]}, thick},
    lab/.style={font=\footnotesize, align=center, above=2pt},
    node distance=1.2cm and 1.4cm]
  \node[box] (tw) {Traffic windows\\%(H)s past $\rightarrow$ %(F)s future};
  \node[box, right=of tw] (fl) {Federated LoRA training\\Flower FedAvg, %(K)s clients};
  \node[box, right=of fl] (fc) {Forecast\\peak of %(F)s values};
  \node[box, below=of fc] (file) {Forecast file};
  \node[box, left=of file] (pox) {POX controller\\$>%(T)s \Rightarrow$ alternate path};
  \node[box, left=of pox] (mn) {Mininet network\\h1, h2, s1--s4};
  \draw[arr] (tw) -- (fl);
  \draw[arr] (fl) -- (fc);
  \draw[arr] (fc) -- (file);
  \draw[arr] (file) -- node[lab]{polled\\every %(P)s s} (pox);
  \draw[arr] (pox) -- node[lab]{flow\\rules} (mn);
\end{tikzpicture}
""" % {"H": C["history_len"], "F": C["horizon"], "K": C["clients"], "T": f"{C['threshold']:.0f}",
       "P": f"{C['poll_seconds']:.0f}"}
    topology = r"""%% Generated by tools/make_figures.py. Needs \usetikzlibrary{positioning}.
\begin{tikzpicture}[
    sw/.style={draw, circle, fill=blue!8, minimum size=0.95cm, font=\small},
    host/.style={draw, rectangle, fill=gray!15, minimum size=0.85cm, font=\small}]
  \node[host] (h1) at (0,0) {h1};
  \node[sw] (s1) at (1.8,0) {s1};
  \node[sw] (s3) at (4.2,1.4) {s3};
  \node[sw] (s4) at (4.2,-1.4) {s4};
  \node[sw] (s2) at (6.6,0) {s2};
  \node[host] (h2) at (8.4,0) {h2};
  \draw (h1) -- (s1);
  \draw (s2) -- (h2);
  \draw[very thick] (s1) -- (s3) -- (s2);
  \draw[very thick, dashed] (s1) -- (s4) -- (s2);
  \node[font=\footnotesize, above] at (4.2,1.9) {primary path, %(A)s Mbps};
  \node[font=\footnotesize, below] at (4.2,-1.9) {alternate path, %(B)s Mbps};
\end{tikzpicture}
""" % {"A": C["primary_mbps"], "B": C["alternate_mbps"]}
    for name, body in (("fig_pipeline", pipeline), ("fig_topology", topology)):
        with open(os.path.join(FIG, "tikz", f"{name}.tex"), "w", encoding="utf-8") as f:
            f.write(body)


def main():
    os.makedirs(FIG, exist_ok=True)
    for f in (fig_telecom_delay, fig_telecom_flips, fig_route_timeline, fig_accuracy_overall,
              fig_accuracy_by_cell, fig_training_loss, tikz_figures):
        f()
    c = N["constants"]
    tikz = {"fig_pipeline": f"FedFlow-LLM pipeline: traffic windows train a federated LoRA model on {c['clients']} clients; its "
                            "forecast is written to a file that the POX controller polls to choose a path in the Mininet network.",
            "fig_topology": f"Emulated topology: h1 on s1, h2 on s2; primary path s1-s3-s2 at {c['primary_mbps']} Mbps and "
                            f"alternate path s1-s4-s2 at {c['alternate_mbps']} Mbps."}
    captions.update(tikz)
    with open(os.path.join(FIG, "captions.json"), "w", encoding="utf-8") as f:
        json.dump(captions, f, indent=1)
    print("figures written:", ", ".join(sorted(captions)))


if __name__ == "__main__":
    main()
