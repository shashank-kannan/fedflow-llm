#!/usr/bin/env python3
"""
Opens the record of every reference (Crossref / DataCite for DOIs, the arXiv abstract page, the PMLR page)
and writes, from those records only:
  references/refs.bib               BibTeX; a field the record lacks is left out
  references/verification_log.csv   key, title, venue, publisher, year, DOI/URL, record opened, date, title match, notes
  references/abstracts/<key>.txt    abstracts read (for checking only; never pasted into the report)

Abstract sources, in order: the Crossref record, OpenAlex, Semantic Scholar (both by DOI), the arXiv page.
Network access is used only for reference verification. Usage: python3 tools/verify_refs.py
"""
import csv
import datetime
import html
import json
import os
import re
import time
import unicodedata
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "references")
TODAY = datetime.date.today().isoformat()
UA = {"User-Agent": "FedFlow-LLM report reference check (mailto:none)"}

# key -> (kind, identifier, title as given in the task or as searched, seed landing page or None)
REFS = {
    "yang2026hfrl": ("doi", "10.1109/JIOT.2026.3708793", "Hierarchical Federated Reinforcement Learning for Distributed Routing with Traffic Forecasting in Large-Scale LEO Satellite Networks", "ieeexplore.ieee.org/abstract/document/11589232"),
    "silva2026netlink": ("doi", "10.1109/ACCESS.2026.3675110", "Federated Learning Approach for Edge Application of Network Link Classification Based on Traffic Matrices", "ieeexplore.ieee.org/document/11441365"),
    "sadeghi2026sdmart": ("doi", "10.1007/s11227-026-08655-7", "SDMART: an improved deep federated learning-based cache replacement method", "link.springer.com/article/10.1007/s11227-026-08655-7"),
    "kalam2026privacy": ("doi", "10.1007/s40009-026-02191-x", "Privacy-Preserving 5G Traffic Prediction Using Federated Learning with Dual-Attention", "link.springer.com/article/10.1007/s40009-026-02191-x"),
    "yuliana2026hybrid": ("doi", "10.1109/ACCESS.2026.3669215", "A Hybrid LSTM-Transformer Approach for Accurate Time Series Traffic Prediction in Cellular Networks", "ieeexplore.ieee.org/document/11417793"),
    "wang2026mobilellm": ("doi", "10.1109/TMC.2026.3684577", "MobileLLM: Semantic-Enhanced Large Language Model for Multimodal Cellular Traffic", "ieeexplore.ieee.org/document/11482510"),
    "gao2026prompt": ("doi", "10.1016/j.simpat.2026.103262", "Prompt-guided Large Language Models with chain-of-thought reasoning for mixed traffic car-following simulation", "sciencedirect.com/science/article/pii/S1569190X26000110"),
    "lim2020flsurvey": ("doi", "10.1109/COMST.2020.2986024", "Federated Learning in Mobile Edge Networks: A Comprehensive Survey", "ieeexplore.ieee.org/document/9060868"),
    "trinh2018lstm": ("doi", "10.1109/PIMRC.2018.8581000", "Mobile Traffic Prediction from Raw Data Using LSTM Networks", "ieeexplore.ieee.org/document/8581000"),
    "zhou2025llmtelecom": ("doi", "10.1109/COMST.2024.3465447", "Large Language Model (LLM) for Telecommunications: A Comprehensive Survey", "ieeexplore.ieee.org/document/10685369"),
    "rong2025stgllm": ("doi", "10.1109/TITS.2024.3456890", "Edge Computing Enabled Large-Scale Traffic Flow Prediction With GPT in Intelligent Autonomous Transport System for 6G Network", "ieeexplore.ieee.org/document/10682107"),
    "yang2026dmllm": ("doi", "10.1109/COMST.2025.3614494", "Decision-Making Large Language Model for Wireless Communication: A Comprehensive Survey on Key Techniques", "ieeexplore.ieee.org/document/11180008"),
    "barlacchi2015milan": ("doi", "10.1038/sdata.2015.55", "A multi-source dataset of urban life in the city of Milan and the Province of Trentino", "nature.com/articles/sdata201555"),
    "telecomitalia2015data": ("datacite", "10.7910/DVN/EGZHFV", "Telecommunications - SMS, Call, Internet - MI", None),
    "mckeown2008openflow": ("doi", "10.1145/1355734.1355746", "OpenFlow: enabling innovation in campus networks", None),
    "lantz2010mininet": ("doi", "10.1145/1868447.1868466", "A network in a laptop: rapid prototyping for software-defined networks", None),
    "mcmahan2017fedavg": ("pmlr", "https://proceedings.mlr.press/v54/mcmahan17a.html", "Communication-Efficient Learning of Deep Networks from Decentralized Data", None),
    "hu2021lora": ("arxiv", "2106.09685", "LoRA: Low-Rank Adaptation of Large Language Models", None),
    "beutel2020flower": ("arxiv", "2007.14390", "Flower: A Friendly Federated Learning Research Framework", None),
    "qwen2024qwen25": ("arxiv", "2412.15115", "Qwen2.5 Technical Report", None),
    "kim2022drlsdn": ("doi", "10.1109/ACCESS.2022.3151081", "Deep Reinforcement Learning-Based Routing on Software-Defined Networks", None),
    "ma2025byzantine": ("doi", "10.1109/TNSE.2025.3545912", "Cellular Traffic Prediction via Byzantine-Robust Asynchronous Federated Learning", None),
    "sun2025fdallm": ("doi", "10.1109/JIOT.2025.3604332", "FDALLM+: A Functional Data Analysis-Driven Large-Language Model Framework for Network Traffic Prediction", None),
    "lv2025betastack": ("doi", "10.1016/j.comnet.2025.111557", "Betastack: Enhancing base station traffic prediction with network-specific Large Language Models", None),
}


def get(url, as_json=True, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                body = r.read().decode("utf-8", "replace")
            return json.loads(body) if as_json else body
        except Exception as e:  # rate limits and timeouts: wait and retry
            last = e
            time.sleep(3 * (i + 1))
    raise last


def norm(s):
    """Lower-case letters and digits only, for title comparison."""
    s = unicodedata.normalize("NFKD", html.unescape(s or "")).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def title_match(given, record):
    g, r = norm(given), norm(record)
    if g == r:
        return "exact"
    if r.startswith(g) or g.startswith(r):
        return "prefix (given title is a shortened form)" if r.startswith(g) else "prefix (record title is shorter)"
    return "NO"


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(s or ""))).strip()


def openalex_abstract(doi):
    try:
        m = get("https://api.openalex.org/works/doi:" + doi)
    except Exception:
        return None
    ii = m.get("abstract_inverted_index")
    if not ii:
        return None
    pos = {p: w for w, ps in ii.items() for p in ps}  # rebuild the text from word positions
    return " ".join(pos[i] for i in sorted(pos))


def s2_abstract(doi):
    try:
        m = get(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=abstract")
        return m.get("abstract")
    except Exception:
        return None


def crossref(key, doi):
    m = get("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"]
    rec = {"title": strip_tags((m.get("title") or [""])[0]),
           "authors": [(a.get("given", ""), a.get("family", a.get("name", ""))) for a in m.get("author", [])],
           "venue": strip_tags((m.get("container-title") or [""])[0]), "publisher": m.get("publisher", ""),
           "year": (m.get("issued", {}).get("date-parts") or [[None]])[0][0],
           "online_year": (m.get("published-online", {}).get("date-parts") or [[None]])[0][0],
           "volume": m.get("volume"), "number": m.get("issue"), "pages": m.get("page"),
           "article_number": m.get("article-number"), "doi": m["DOI"], "type": m.get("type"),
           "url_record": "https://api.crossref.org/works/" + m["DOI"],
           "resource": (m.get("resource", {}).get("primary", {}) or {}).get("URL", "")}
    abstract, src = strip_tags(m.get("abstract")), "Crossref"
    if not abstract:
        abstract, src = openalex_abstract(doi), "OpenAlex"
    if not abstract:
        time.sleep(2)
        abstract, src = s2_abstract(doi), "Semantic Scholar"
    rec["abstract"], rec["abstract_source"] = (abstract, src) if abstract else (None, "none readable")
    return rec


def datacite(doi):
    a = get("https://api.datacite.org/dois/" + doi)["data"]["attributes"]
    return {"title": a["titles"][0]["title"], "authors": [("", "{" + c["name"] + "}") for c in a["creators"]],  # braces: corporate author, not a person
            "venue": "", "publisher": a["publisher"] if isinstance(a["publisher"], str) else a["publisher"].get("name", ""),
            "year": a["publicationYear"], "online_year": None, "volume": None, "number": None, "pages": None,
            "article_number": None, "doi": a["doi"].upper(), "type": "dataset", "url_record": "https://api.datacite.org/dois/" + doi,
            "resource": a.get("url", ""), "abstract": None, "abstract_source": "dataset record (no abstract)"}


def arxiv(aid):
    page = get(f"https://export.arxiv.org/abs/{aid}", as_json=False)
    meta = lambda n: [html.unescape(x) for x in re.findall(rf'<meta name="citation_{n}" content="([^"]*)"', page)]
    authors = []
    for a in meta("author"):
        fam, _, giv = a.partition(", ")
        if fam.strip(":") and fam != ":":
            authors.append((giv, fam))
    abstract = meta("abstract")
    date = (meta("date") or meta("online_date") or [""])[0]
    return {"title": meta("title")[0], "authors": authors, "venue": "", "publisher": "", "year": int(date[:4]) if date else None,
            "online_year": None, "volume": None, "number": None, "pages": None, "article_number": None, "doi": "",
            "eprint": aid, "type": "preprint", "url_record": f"https://arxiv.org/abs/{aid}", "resource": f"https://arxiv.org/abs/{aid}",
            "abstract": abstract[0] if abstract else None, "abstract_source": "arXiv page" if abstract else "none readable"}


def pmlr(url):
    page = get(url, as_json=False)
    meta = lambda n: [html.unescape(x) for x in re.findall(rf'<meta name="citation_{n}" content="([^"]*)"', page)]
    authors = []
    for a in meta("author"):
        fam, _, giv = a.partition(", ")
        authors.append((giv, fam))
    abstract = re.search(r'<div id="abstract" class="abstract">\s*(.*?)\s*</div>', page, re.S)
    first, last = (meta("firstpage") or [None])[0], (meta("lastpage") or [None])[0]
    return {"title": meta("title")[0], "authors": authors, "venue": (meta("conference_title") or meta("journal_title") or [""])[0],
            "publisher": (meta("publisher") or [""])[0], "year": int(meta("publication_date")[0][:4]),
            "online_year": None, "volume": (meta("volume") or [None])[0], "number": None,
            "pages": f"{first}--{last}" if first and last else None, "article_number": None, "doi": "",
            "type": "inproceedings", "url_record": url, "resource": url,
            "abstract": strip_tags(abstract.group(1)) if abstract else None,
            "abstract_source": "PMLR page" if abstract else "none readable"}


def bib_escape(s):
    return str(s).replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")


def to_bib(key, r):
    kind = {"journal-article": "article", "proceedings-article": "inproceedings", "inproceedings": "inproceedings",
            "dataset": "misc", "preprint": "misc"}.get(r["type"], "misc")
    names = " and ".join(f"{fam}, {giv}".strip(", ") for giv, fam in r["authors"])
    fields = [("author", names), ("title", "{" + bib_escape(r["title"]) + "}"),
              ("journal" if kind == "article" else "booktitle", r["venue"]),
              ("publisher", r["publisher"]), ("year", r["year"]), ("volume", r["volume"]), ("number", r["number"]),
              ("pages", (r["pages"] or "").replace("-", "--") if r["pages"] and "--" not in r["pages"] else r["pages"]),
              ("eid", r["article_number"]), ("doi", r["doi"])]
    if r.get("eprint"):
        fields += [("eprint", r["eprint"]), ("archiveprefix", "arXiv"), ("howpublished", f"arXiv:{r['eprint']}")]
    if kind == "misc" and r["type"] == "dataset":
        fields.append(("howpublished", r["publisher"] + " dataset"))
    if not r["doi"]:
        fields.append(("url", r["url_record"]))
    body = ",\n".join(f"  {k} = {{{bib_escape(v) if k not in ('title',) else v}}}" for k, v in fields if v not in (None, ""))
    return f"@{kind}{{{key},\n{body}\n}}\n"


def main():
    os.makedirs(os.path.join(OUT, "abstracts"), exist_ok=True)
    log, bib = [], []
    for key, (kind, ident, given, seed) in REFS.items():
        try:
            r = {"doi": crossref, "datacite": lambda k, i: datacite(i), "arxiv": lambda k, i: arxiv(i),
                 "pmlr": lambda k, i: pmlr(i)}[kind](key, ident) if kind == "doi" else \
                {"datacite": datacite, "arxiv": arxiv, "pmlr": pmlr}[kind](ident)
        except Exception as e:
            log.append({"key": key, "title": given, "record_opened": f"FAILED: {e}", "title_match": "NO", "usable": "NO"})
            print("FAIL", key, e)
            continue
        match = title_match(given, r["title"])
        notes = []
        if r.get("online_year") and r["online_year"] != r["year"]:
            notes.append(f"published online {r['online_year']}; issue year {r['year']} used (DOI record)")
        if seed and "ieeexplore" in seed:
            doc = re.search(r"(\d+)$", seed).group(1)
            notes.append(f"seed IEEE document {doc} {'matches' if doc in r['resource'] else 'NOT in'} the DOI record's landing URL ({r['resource']})")
        if seed and "pii/" in seed:
            pii = seed.split("pii/")[1]
            notes.append(f"seed PII {pii} {'matches' if pii in r['resource'] else 'differs from'} the DOI record's landing URL ({r['resource']})")
        usable = "yes" if match != "NO" else "NO"
        log.append({"key": key, "title": r["title"], "venue": r["venue"], "publisher": r["publisher"], "year": r["year"],
                    "doi_or_url": r["doi"] or r["url_record"], "record_opened": r["url_record"], "date": TODAY,
                    "title_match": match, "abstract_source": r["abstract_source"], "usable": usable, "notes": "; ".join(notes)})
        if r["abstract"]:
            with open(os.path.join(OUT, "abstracts", f"{key}.txt"), "w", encoding="utf-8") as f:
                f.write(f"{r['title']}\nSource: {r['abstract_source']} ({r['doi'] or r['url_record']}), read {TODAY}\n\n{r['abstract']}\n")
        if usable == "yes":
            bib.append(to_bib(key, r))
        print(f"{usable:>3} {match[:6]:6} {r['year']} {key}: {r['title'][:70]} | {r['abstract_source']}")
        time.sleep(1.2)
    with open(os.path.join(OUT, "refs.bib"), "w", encoding="utf-8") as f:
        f.write(f"% Generated by tools/verify_refs.py on {TODAY}; every field comes from the opened record.\n\n" + "\n".join(bib))
    cols = ["key", "title", "venue", "publisher", "year", "doi_or_url", "record_opened", "date", "title_match",
            "abstract_source", "usable", "notes"]
    with open(os.path.join(OUT, "verification_log.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in log:
            w.writerow({c: row.get(c, "") for c in cols})
    print(f"usable: {sum(1 for r in log if r.get('usable') == 'yes')} of {len(log)}")


if __name__ == "__main__":
    main()
