#!/usr/bin/env python3
"""
Renders report/main_paste.tex: one self-contained LaTeX file for Overleaf's main.tex.

Inputs: the template's main.tex (preamble copied verbatim), report/report_src.tex (body with placeholders),
report/generated/numbers.json, tools/required_statements.json, figures/*.data.csv, figures/captions.json,
figures/tikz/*.tex, references/refs.bib and references/lit_table.csv.
Placeholders: <<path|fmt>> where path starts with R. (routing), F. (forecasts), C. (constants) or L. (training_loss)
and fmt is 0-3 (decimals), s (string) or pct0/pct1 (x100). The script stops on any unresolved placeholder or marker.
Usage: python3 tools/render_report.py
"""
import csv
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "templates", "report_template", "Report template", "main.tex")
N = json.load(open(os.path.join(ROOT, "report", "generated", "numbers.json"), encoding="utf-8"))
S = json.load(open(os.path.join(ROOT, "tools", "required_statements.json"), encoding="utf-8"))
CAP = json.load(open(os.path.join(ROOT, "figures", "captions.json"), encoding="utf-8"))
C, R, F = N["constants"], N["routing"], N["forecasts"]
MODES = C["modes"]
REFERENCE = {"oracle", "alt"}
COLOUR = {"static": "7F7F7F", "reactive": "D55E00", "model": "0072B2", "oracle": "009E73", "alt": "CC79A7",
          "persistence": "E69F00", "moving_avg": "56B4E9", "true": "555555"}
CNAME = {"static": "cStatic", "reactive": "cReactive", "model": "cModel", "oracle": "cOracle", "alt": "cAlt",
         "persistence": "cLast", "moving_avg": "cMA", "true": "cTrue"}


def rnd(v, dp):
    """Half away from zero, the same rounding as tools/build_numbers.py."""
    if v is None:
        return "not computed"
    q = 10 ** dp
    r = math.floor(abs(v) * q + 0.5) / q * (1 if v >= 0 else -1)
    return f"{r:.{dp}f}"


def esc(s):
    """Escape LaTeX specials in plain text (statements, captions, table text)."""
    s = str(s).replace("\\", r"\textbackslash{}")
    for a, b in [("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#"), ("$", r"\$")]:
        s = s.replace(a, b)
    return s


def lookup(path):
    alias = {"R": "routing", "F": "forecasts", "C": "constants", "L": "training_loss"}
    head, *rest = path.split(".")
    node = N[alias[head]]
    for k in rest:
        node = node[int(k)] if isinstance(node, list) else node[k]
    return node


def fill(m):
    path, fmt = m.group(1), m.group(2)
    v = lookup(path)
    if fmt == "s":
        return esc(v)
    if fmt.startswith("pct"):
        return rnd(100 * v, int(fmt[3:]))
    return rnd(float(v), int(fmt))


# ------------------------------------------------------------------ tables

def read_csv(rel):
    with open(os.path.join(ROOT, rel), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def lit_table():
    rows = read_csv("references/lit_table.csv")
    body = []
    for r in rows:
        venue = esc(r["Journal/Conference name and publisher, year"].replace("&amp;", "&")
                    .replace("Institute of Electrical and Electronics Engineers (IEEE)", "IEEE"))
        body.append(f"{r['S.No']} & {venue} \\cite{{{r['key']}}} & {esc(r['Technique adopted'])} & "
                    f"{esc(r['Inference'])} & {esc(r['Cons'])} \\\\")
    return (r"""\begin{table}[htbp]
\centering
\footnotesize
\caption[Literature survey of recent related work]{Literature survey: verified works from 2021 to 2026. Technique and inference are paraphrased from each work's abstract; Cons lists what the abstract shows the work does not address relative to our problem.}
\label{tab:lit}
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{0.6cm}>{\raggedright\arraybackslash}p{2.9cm}>{\raggedright\arraybackslash}X>{\raggedright\arraybackslash}X>{\raggedright\arraybackslash}X@{}}
\toprule
S.No & Journal/Conference name and publisher, year & Technique adopted & Inference & Cons \\ \midrule
""" + "\n".join(body) + "\n\\bottomrule\n\\end{tabularx}\n\\end{table}")


def acc_table():
    names = {"model": "FedFlow-LLM model", "persistence": "Repeat-last", "moving_avg": f"Moving average (last {C['moving_avg_window']})"}
    rows = []
    for m, label in names.items():
        s, t = F["synthetic_test"]["overall"][m], F["telecom_test"]["overall"][m]
        rows.append(f"{label} & {rnd(s['mae'], 2)} & {rnd(s['rmse'], 2)} & {rnd(t['mae'], 2)} & {rnd(t['rmse'], 2)} \\\\")
    return (r"""\begin{table}[htbp]
\centering
\caption[Forecast error on the test blocks]{Forecast error on the held-out test blocks (load units, %s = %s Mbps).}
\label{tab:acc}
\begin{tabular}{@{}lrrrr@{}}
\toprule
 & \multicolumn{2}{c}{Synthetic test (%s windows)} & \multicolumn{2}{c}{Telecom test (%s windows)} \\
Method & MAE & RMSE & MAE & RMSE \\ \midrule
""" % (rnd(C["threshold"], 0), C["primary_mbps"], F["synthetic_test"]["windows"], F["telecom_test"]["windows"])
            + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}")


def onset_table():
    rows = []
    for key in ("3", "2"):
        b = F["telecom_test"][key]
        o = b["onset"]
        rows.append(f"{b['square_id']} & {b['windows']} & {o['windows']} & {o['flagged']} & {rnd(o['mean_peak_error'], 2)} & "
                    f"{o['calm_false_alarms']} of {o['calm_windows']} \\\\")
    return (r"""\begin{table}[htbp]
\centering
\caption[Onset windows on the experiment cells]{Onset windows on the two experiment cells, telecom test block. Cells with fewer than 10 onset windows are not reported.}
\label{tab:onset}
\begin{tabular}{@{}rrrrrr@{}}
\toprule
Cell & Windows & Onsets & Caught & Mean peak error & Calm false alarms \\ \midrule
""" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}")


def routing_rows(d, with_cell):
    out = []
    for m in MODES:
        e = R[d][m]
        p = e["ping_mean_ms"]
        dp = 2 if d == "synthetic" else 1
        loss = e["server_udp_loss_pct"]
        cell = (d[1:] + " & ") if with_cell else ""
        name = m + (" (ref.)" if m in REFERENCE else "")
        out.append(f"{cell}{name} & {rnd(p['mean'], dp)} ({rnd(p['min'], dp)}--{rnd(p['max'], dp)}) & {p['n']} & "
                   f"{rnd(e['ping_p95_ms']['mean'], 1)} & {rnd(e['flip_lines']['mean'], 0)} & "
                   f"{rnd(e['steps_above_100']['mean'], 0)} of {e['steps_total']} & {rnd(loss['max'], 1)} ({loss['n']} runs) \\\\")
    return out


def routing_table(which):
    if which == "synthetic":
        head = "Mode & Mean ping ms (min--max) & $n$ & p95 ms & Flips & Steps $>$100 & UDP loss \\% \\\\"
        rows = routing_rows("synthetic", False)
        cap = ("Routing on the synthetic trace", "Routing results on the synthetic trace, every mode (mean over the runs, min--max in brackets; $n$ = runs used; UDP loss is the maximum over scored runs).", "tab:synth", "@{}lrrrrrr@{}")
    else:
        head = "Cell & Mode & Mean ping ms (min--max) & $n$ & p95 ms & Flips & Steps $>$100 & UDP loss \\% \\\\"
        rows = routing_rows("t7511", True) + ["\\midrule"] + routing_rows("t8336", True)
        cap = ("Routing on the two Milan cells", "Routing results on the two Milan cells, every mode (mean over the runs, min--max in brackets; $n$ = runs used; UDP loss is the maximum over scored runs).", "tab:telecom", "@{}rlrrrrrr@{}")
    return (f"\\begin{{table}}[htbp]\n\\centering\n\\footnotesize\n\\caption[{cap[0]}]{{{cap[1]}}}\n\\label{{{cap[2]}}}\n"
            f"\\begin{{tabular}}{{{cap[3]}}}\n\\toprule\n{head} \\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}")


def v2_table():
    a, b = F["val_v1"], F["val_v2"]
    rows = [("MAE", rnd(a["overall"]["model"]["mae"], 2), rnd(b["overall"]["model"]["mae"], 2)),
            ("RMSE", rnd(a["overall"]["model"]["rmse"], 2), rnd(b["overall"]["model"]["rmse"], 2)),
            ("Pooled onsets caught", f"{a['overall']['onset']['flagged']} of {a['overall']['onset']['windows']}",
             f"{b['overall']['onset']['flagged']} of {b['overall']['onset']['windows']}"),
            ("Calm false alarms", f"{a['overall']['onset']['calm_false_alarms']} of {a['overall']['onset']['calm_windows']}",
             f"{b['overall']['onset']['calm_false_alarms']} of {b['overall']['onset']['calm_windows']}"),
            ("Windows parsed", f"{a['windows_parsed']} of {a['windows']}", f"{b['windows_parsed']} of {b['windows']}")]
    return (r"""\begin{table}[htbp]
\centering
\caption[v1 and v2 on the validation block]{v1 (final model) and v2 on the validation block.}
\label{tab:v2}
\begin{tabular}{@{}lrr@{}}
\toprule
Measure & v1 & v2 \\ \midrule
""" + "\n".join(f"{x} & {y} & {z} \\\\" for x, y, z in rows) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}")


# ------------------------------------------------------------------ statements

def statement(k):
    return esc(S[k])


def headline_paragraph():
    cells = []
    for d, sq in (("t7511", "7511"), ("t8336", "8336")):
        if R[d]["every_model_rep_below_every_reactive_rep"]:
            cells.append((sq, rnd(R[d]["model"]["ping_mean_ms"]["mean"], 1), rnd(R[d]["reactive"]["ping_mean_ms"]["mean"], 1)))
    if len(cells) == 2:
        head = (f"On the two Milan cells tested, forecast-driven routing gave lower mean ping delay than reactive routing "
                f"({cells[0][1]} vs {cells[0][2]} ms on cell {cells[0][0]}, {cells[1][1]} vs {cells[1][2]} ms on cell {cells[1][0]}).")
    else:
        head = "On the two Milan cells tested, no ordering claimed between forecast-driven and reactive routing."
    return head + " " + statement("S2") + " " + statement("S5")


def statements_list():
    items = "\n".join(f"\\item[S{i}] {statement(f'S{i}')}" for i in range(1, 17))
    return "\\begin{description}\n" + items + "\n\\end{description}"


# ------------------------------------------------------------------ plots

AXIS = ("tick label style={font=\\scriptsize}, label style={font=\\small}, title style={font=\\small}, "
        "axis x line*=bottom, axis y line*=left, ymin=0")


def fig(body, name, short, label):
    return (f"\\begin{{figure}}[htbp]\n\\centering\n{body}\n\\caption[{short}]{{{esc(CAP[name])}}}\n"
            f"\\label{{{label}}}\n\\end{{figure}}")


def bar_style(m, shift=None):
    s = f"fill={CNAME[m]}, draw=black"
    if m in REFERENCE:
        s = f"fill={CNAME[m]}!35, draw=black, postaction={{pattern=north east lines, pattern color={CNAME[m]}}}"
    return s + (f", bar shift={shift}" if shift is not None else ", bar shift=0pt")


def plot_delay():
    rows = read_csv("figures/fig_telecom_delay.data.csv")
    top = max(float(r["max_ms"]) for r in rows) * 1.18
    parts = []
    for j, cell in enumerate(("Cell 7511", "Cell 8336")):
        cr = {r["mode"]: r for r in rows if r["cell"] == cell}
        labels = ",".join(f"{{{m}{'*' if m in REFERENCE else ''}\\\\n={cr[m]['n_runs']}\\\\{rnd(float(cr[m]['share_steps_written_above_100_pct']), 0)}\\%}}"
                          for m in MODES)
        pos = "name=a0" if j == 0 else "name=a1, at={(a0.south east)}, anchor=south west, xshift=1.3cm"
        ylab = "ylabel={Mean ping delay (ms)}, " if j == 0 else ""
        s = [f"\\begin{{axis}}[{pos}, ybar, bar width=10pt, width=0.46\\textwidth, height=6.2cm, xmin=0.4, xmax=5.6, "
             f"ymax={top:.1f}, xtick={{1,2,3,4,5}}, xticklabels={{{labels}}}, xticklabel style={{align=center, font=\\tiny}}, "
             f"{ylab}title={{{cell}}}, {AXIS}]"]
        for i, m in enumerate(MODES, 1):
            r = cr[m]
            mean, lo, hi = float(r["mean_ms"]), float(r["min_ms"]), float(r["max_ms"])
            s.append(f"\\addplot[{bar_style(m)}, error bars/.cd, y dir=both, y explicit] coordinates "
                     f"{{({i},{mean:.4f}) += (0,{hi - mean:.4f}) -= (0,{mean - lo:.4f})}};")
            s.append(f"\\node[font=\\tiny, above] at (axis cs:{i},{hi:.4f}) {{{rnd(mean, 1)}}};")
        s.append("\\end{axis}")
        parts.append("\n".join(s))
    body = "\\begin{tikzpicture}\n" + "\n".join(parts) + "\n\\end{tikzpicture}"
    return fig(body, "fig_telecom_delay", "Mean ping delay per mode on the Milan cells", "fig:delay")


def plot_flips():
    rows = read_csv("figures/fig_telecom_flips.data.csv")
    top = max(float(r["mean_flips"]) for r in rows) * 1.2 + 1
    s = [f"\\begin{{axis}}[ybar, bar width=10pt, width=0.85\\textwidth, height=6cm, xmin=0.4, xmax=5.6, ymax={top:.1f}, "
         f"xtick={{1,2,3,4,5}}, xticklabels={{{','.join(MODES)}}}, ylabel={{Route flips per run}}, {AXIS}]"]
    for i, m in enumerate(MODES, 1):
        for cell, shift, extra in (("Cell 7511", "-6pt", ""), ("Cell 8336", "6pt", ", postaction={pattern=dots}")):
            r = next(x for x in rows if x["cell"] == cell and x["mode"] == m)
            v = float(r["mean_flips"])
            style = bar_style(m, shift) + (extra if m not in REFERENCE else "")
            s.append(f"\\addplot[{style}] coordinates {{({i},{v:.4f})}};")
            s.append(f"\\node[font=\\tiny, above, xshift={shift}] at (axis cs:{i},{v:.4f}) {{{rnd(v, 0)}}};")
    s.append("\\end{axis}")
    body = "\\begin{tikzpicture}\n" + "\n".join(s) + "\n\\end{tikzpicture}\\\\[2pt]\n{\\footnotesize Left bar of each pair: cell 7511; right bar (dotted): cell 8336.}"
    return fig(body, "fig_telecom_flips", "Route flips per run on the Milan cells", "fig:flips")


def plot_timeline():
    rows = read_csv("figures/fig_route_timeline.data.csv")
    top = max(max(float(r["true_load"]), float(r["reactive_written"]), float(r["model_written"])) for r in rows) * 1.08
    last = int(rows[-1]["step"])
    thr = C["threshold"]
    coords = lambda col: " ".join(f"({r['step']},{float(r[col]):.2f})" for r in rows)
    body = f"""\\begin{{tikzpicture}}
\\begin{{axis}}[width=0.95\\textwidth, height=6.2cm, xmin=0, xmax={last}, ymax={top:.1f},
  xlabel={{Step ({C['step_seconds']} s each), cell 7511, run 1}}, ylabel={{Load ({rnd(thr, 0)} = {C['primary_mbps']} Mbps)}},
  legend style={{font=\\scriptsize, at={{(0.99,0.99)}}, anchor=north east}}, legend columns=2, {AXIS}]
\\fill[yellow!20] (axis cs:0,{thr:.0f}) rectangle (axis cs:{last},{top:.1f});
\\addplot[const plot, color=cTrue, thick] coordinates {{{coords('true_load')}}};
\\addlegendentry{{true load}}
\\addplot[const plot, color=cReactive, thick] coordinates {{{coords('reactive_written')}}};
\\addlegendentry{{reactive (written)}}
\\addplot[const plot, color=cModel, very thick] coordinates {{{coords('model_written')}}};
\\addlegendentry{{model (written)}}
\\addplot[black, dashed] coordinates {{(0,{thr:.0f}) ({last},{thr:.0f})}};
\\addlegendentry{{threshold {rnd(thr, 0)}}}
\\end{{axis}}
\\end{{tikzpicture}}"""
    return fig(body, "fig_route_timeline", "Values written each step, cell 7511", "fig:timeline")


def grouped_bars(rows, xkey, series, label_of, ylabel, name, short, label, legend_at="north west"):
    xs = list(dict.fromkeys(r[xkey] for r in rows))
    top = max(float(r["mae"]) for r in rows) * 1.2
    s = [f"\\begin{{axis}}[ybar, bar width=11pt, width=0.85\\textwidth, height=6cm, symbolic x coords={{{','.join(xs)}}}, "
         f"xtick=data, enlarge x limits={0.4 if len(xs) < 3 else 0.1}, ymax={top:.1f}, ylabel={{{ylabel}}}, "
         f"nodes near coords, nodes near coords style={{font=\\tiny, /pgf/number format/.cd, fixed, precision=2}}, "
         f"legend style={{font=\\scriptsize, at={{(0.02,0.98)}}, anchor={legend_at}}}, {AXIS}]"]
    for m in series:
        pts = " ".join(f"({r[xkey]},{float(r['mae']):.4f})" for r in rows if r["method"] == m)
        s.append(f"\\addplot[fill={CNAME[m]}, draw=black] coordinates {{{pts}}};")
        s.append(f"\\addlegendentry{{{label_of[m]}}}")
    s.append("\\end{axis}")
    return fig("\\begin{tikzpicture}\n" + "\n".join(s) + "\n\\end{tikzpicture}", name, short, label)


def plot_acc_overall():
    rows = read_csv("figures/fig_accuracy_overall.data.csv")
    lab = {"model": "FedFlow-LLM model", "persistence": "repeat-last", "moving_avg": f"moving average (last {C['moving_avg_window']})"}
    return grouped_bars(rows, "block", ["model", "persistence", "moving_avg"], lab, "MAE (load units)",
                        "fig_accuracy_overall", "Forecast MAE on the test blocks", "fig:accoverall")


def plot_acc_cell():
    rows = read_csv("figures/fig_accuracy_by_cell.data.csv")
    lab = {"model": "FedFlow-LLM model", "persistence": "repeat-last"}
    return grouped_bars(rows, "square_id", ["model", "persistence"], lab, "MAE (load units)",
                        "fig_accuracy_by_cell", "Forecast MAE per cell, telecom test", "fig:acccell")


def plot_loss():
    rows = read_csv("figures/fig_training_loss.data.csv")
    top = max(float(r["loss"]) for r in rows) * 1.1
    s = [f"\\begin{{axis}}[width=0.8\\textwidth, height=5.6cm, xlabel={{Federated round}}, ylabel={{Training loss}}, "
         f"ymax={top:.2f}, legend style={{font=\\scriptsize}}, {AXIS}]"]
    for data, colour in (("synthetic", "cLast"), ("telecom", "cModel")):
        pts = " ".join(f"({r['round']},{float(r['loss']):.4f})" for r in rows if r["data"] == data)
        s.append(f"\\addplot[color={colour}, mark=*, mark size=1pt, thick] coordinates {{{pts}}};")
        s.append(f"\\addlegendentry{{{data} data}}")
    s.append("\\end{axis}")
    return fig("\\begin{tikzpicture}\n" + "\n".join(s) + "\n\\end{tikzpicture}", "fig_training_loss",
               "Federated training loss per round", "fig:loss")


def tikz(name):
    body = open(os.path.join(ROOT, "figures", "tikz", f"{name}.tex"), encoding="utf-8").read()
    if name == "fig_pipeline":
        body = "\\resizebox{\\textwidth}{!}{%\n" + body.strip() + "\n}"
    short = {"fig_pipeline": "FedFlow-LLM pipeline", "fig_topology": "Emulated network topology"}[name]
    label = {"fig_pipeline": "fig:pipeline", "fig_topology": "fig:topology"}[name]
    return fig(body, name, short, label)


PLOTS = {"fig_telecom_delay": plot_delay, "fig_telecom_flips": plot_flips, "fig_route_timeline": plot_timeline,
         "fig_accuracy_overall": plot_acc_overall, "fig_accuracy_by_cell": plot_acc_cell, "fig_training_loss": plot_loss}


# ------------------------------------------------------------------ bibliography

def parse_bib():
    text = open(os.path.join(ROOT, "references", "refs.bib"), encoding="utf-8").read()
    entries = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),\n(.*?)\n\}", text, re.S):
        fields = dict(re.findall(r"^\s+(\w+) = \{(.*)\},?$", m.group(3), re.M))
        entries[m.group(2)] = (m.group(1), fields)
    return entries


def ieee_name(n):
    n = n.strip()
    if n.startswith("{") and n.endswith("}"):
        return n[1:-1]  # corporate author
    if ", " not in n:
        return n  # record gives the name in natural order; kept as written
    fam, giv = n.split(", ", 1)
    initials = " ".join(p[0] + "." if not p.endswith(".") else p for p in giv.replace("-", " -").split() if p)
    return f"{initials.replace(' -', '-')} {fam}".strip()


def ieee_entry(key, kind, f):
    names = [ieee_name(a) for a in f.get("author", "").split(" and ") if a]
    if len(names) > 6:
        auth = names[0] + " \\emph{et al.}"
    elif len(names) > 1:
        auth = ", ".join(names[:-1]) + ", and " + names[-1]
    else:
        auth = names[0] if names else ""
    title = f.get("title", "").strip("{}")
    parts = [f"{auth}, ``{title},''"]
    if kind == "article":
        parts.append(f"\\emph{{{f['journal']}}}," if f.get("journal") else "")
    elif kind == "inproceedings":
        parts.append(f"in \\emph{{{f['booktitle']}}}," if f.get("booktitle") else "")
    elif f.get("eprint"):
        parts.append(f"arXiv:{f['eprint']},")
    elif f.get("publisher"):
        parts.append(f"{f['publisher']},")
    if f.get("volume"):
        parts.append(f"vol. {f['volume']},")
    if f.get("number"):
        parts.append(f"no. {f['number']},")
    if f.get("pages"):
        parts.append(f"pp. {f['pages']},")
    elif f.get("eid"):
        parts.append(f"Art. no. {f['eid']},")
    parts.append(f"{f.get('year', '')}" + ("," if f.get("doi") or (f.get("url") and not f.get("eprint")) else "."))
    if f.get("doi"):
        parts.append(f"doi: {f['doi'].replace('_', chr(92) + '_')}.")
    elif f.get("url") and not f.get("eprint"):
        parts.append(f"\\texttt{{{f['url']}}}.")
    return f"\\bibitem{{{key}}} " + " ".join(p for p in parts if p)


def bibliography(body):
    entries = parse_bib()
    order = []
    for group in re.findall(r"\\cite\{([^}]*)\}", body):
        for k in group.split(","):
            k = k.strip()
            if k not in order:
                order.append(k)
    missing = [k for k in order if k not in entries]
    if missing:
        sys.exit(f"STOP: cited keys without a verified record: {missing}")
    uncited = [k for k in entries if k not in order]
    items = "\n".join(ieee_entry(k, *entries[k]) for k in order)
    return ("\\begin{thebibliography}{99}\n\\addcontentsline{toc}{chapter}{References}\n" + items + "\n\\end{thebibliography}"), uncited


# ------------------------------------------------------------------ main

def preamble():
    t = open(TEMPLATE, encoding="utf-8").read()
    pre = t[:t.index("\\begin{document}")]
    added = ("% ---- packages added for the inline charts and tables (allowed additions) ----\n"
             "\\usepackage{tikz}\n\\usetikzlibrary{positioning,arrows.meta,patterns}\n"
             "\\usepackage{pgfplots}\n\\pgfplotsset{compat=1.18}\n"
             "\\usepackage{booktabs}\n\\usepackage{tabularx}\n\\usepackage{array}\n")
    return pre + added


def colours():
    return "\n".join(f"\\definecolor{{{CNAME[k]}}}{{HTML}}{{{v}}}" for k, v in COLOUR.items())


def main():
    src = open(os.path.join(ROOT, "report", "report_src.tex"), encoding="utf-8").read()
    src = "\n".join(l for l in src.splitlines() if not l.startswith("% Report body source") and not l.startswith("% (R. = routing"))
    body = re.sub(r"<<([A-Za-z0-9_.]+)\|(\w+)>>", fill, src)
    marks = {"%%COLOURS%%": colours, "%%LITTABLE%%": lit_table, "%%ACC_TABLE%%": acc_table,
             "%%ONSET_TABLE%%": onset_table, "%%V2_TABLE%%": v2_table, "%%STATEMENTS%%": statements_list,
             "%%HEADLINE_PARAGRAPH%%": headline_paragraph,
             "%%ROUTING_TABLE:synthetic%%": lambda: routing_table("synthetic"),
             "%%ROUTING_TABLE:telecom%%": lambda: routing_table("telecom")}
    for k, f in marks.items():
        body = body.replace(k, f())
    body = re.sub(r"%%S:(S\d+)%%", lambda m: statement(m.group(1)), body)
    body = re.sub(r"%%PLOT:(\w+)%%", lambda m: PLOTS[m.group(1)](), body)
    body = re.sub(r"%%TIKZ:(\w+)%%", lambda m: tikz(m.group(1)), body)
    bib, uncited = bibliography(body)
    body = body.replace("%%BIBLIOGRAPHY%%", bib)
    left = re.findall(r"<<[^>]*>>|%%[A-Z_:a-z0-9]+%%", body)
    if left:
        sys.exit(f"STOP: unresolved placeholders: {sorted(set(left))}")
    out = os.path.join(ROOT, "report", "main_paste.tex")
    with open(out, "w", encoding="utf-8") as f:
        f.write(preamble() + body + "\n")
    n_bib = bib.count(chr(92) + "bibitem")  # backslash not allowed inside an f-string expression
    print(f"wrote {out}; bibliography entries: {n_bib}; uncited: {uncited or 'none'}")


if __name__ == "__main__":
    main()
