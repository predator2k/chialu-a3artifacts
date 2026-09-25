"""PDF corpus inventory and the per-paper extraction prompt.

The legacy/knowledge/pdf corpus feeds the per-family docs (knowledge/arch)
through a map-reduce: one extraction NOTE per document (map, an LLM
reads one pdf against the family vocabulary), then one family md per
family (reduce, synthesized from every note that tags it). This
module owns the map side's inputs:

* inventory   classify every pdf as paper / book / thesis / standard /
              report / slides and record pages + handle + citation:
              legacy/knowledge/pdf/inventory.tsv, papers.txt, books.txt
* vocab       the controlled vocabulary the extractor classifies
              against: every family in chialu/spaces with its one-line
              doc, design choices and component slots
* prompt      render knowledge/extract/paper_prompt.md for one handle
              (vocabulary + rules first so the prefix caches across the
              corpus; handle/citation/domain hint and the document last)

Books are NOT handled by the paper prompt: a book gets a table-of-
contents pass (chapter -> families) and then the paper prompt per
relevant chapter, filed under <handle>#chN.

CLI:  python3 -m chialu.extract inventory
      python3 -m chialu.extract vocab
      python3 -m chialu.extract prompt <handle> [--text FILE] [--domains a,b]
      python3 -m chialu.extract run [--parallel 16] [--limit N] [--only h1,h2]
                (codex exec -m gpt-5.6-sol per paper -> knowledge/notes/<handle>.md)
"""

from __future__ import annotations

import csv
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from chialu.archdocs import ARCH_DIR, KNOWLEDGE, PDF_DIR

LEGACY = Path(__file__).resolve().parents[1] / "legacy" / "knowledge"   # the corpus tooling's files, outside the agent's knowledge path
EXTRACT_DIR = LEGACY / "extract"
NOTES_DIR = LEGACY / "notes"
INVENTORY = PDF_DIR / "inventory.tsv"
PROMPT_TEMPLATE = EXTRACT_DIR / "paper_prompt.md"

KINDS = ("paper", "book", "thesis", "standard", "report", "slides")

# Hand-classified documents (kind, note). Everything else is a paper
# unless a citation keyword or the page count says otherwise.
_OVERRIDES = {
    "muller_2018": ("book", "full book, 640 pp"),
    "richards_1955": ("book", "full book, 416 pp"),
    "muller_2016": ("book", "full book, 273 pp"),
    "mead_conway1980": ("book", "full book, 258 pp"),
    "lala_2001": ("book", "full book, 240 pp"),
    "thornton_1970": ("book", "full book, 101 pp"),
    "ercegovac_2004": ("book", "chapter excerpt, 59 pp"),
    "von_neumann_1956": ("book", "book chapter, 56 pp"),
    "dedinechin_2024": ("book", "excerpt, 22 pp"),
    "kulisch_1981": ("book", "excerpt, 5 pp"),
    "cody_1980": ("book", "1-page stub only"),
    "bewick1994": ("thesis", "PhD dissertation, 170 pp"),
    "goldschmidt_1964": ("thesis", "MS thesis, 44 pp"),
    "ieee754_2008": ("standard", ""),
    "ieee754_2019": ("standard", "1-page stub only"),
    "ocp_mx_2023": ("standard", ""),
    "burks1946": ("report", "IAS report"),
    "burks_1946": ("report", "IAS report"),
    "weinberger_smith1958": ("report", "NBS circular"),
}
_FILE_OVERRIDES = {
    "adder_arch.pdf": ("thesis", "unidentified dissertation (diss.dvi), 110 pp"),
    "webb2007.pdf": ("slides", "Hot Chips 19 z6 slides; no handle"),
    "rupley2012.pdf": ("slides", "slide deck; no handle"),
    "zierler1976.pdf": ("report", "1-page book review of Rao 1974; no handle"),
}
_BOOK_RE = re.compile(
    r"Van Nostrand|Addison|Morgan Kaufmann|Birkh|Academic Press|"
    r"Prentice|University Press|Handbook|Scott, Foresman|McGraw|Wiley|"
    r"Kluwer|Oxford|Cambridge|\bed\.,", re.I)
_THESIS_RE = re.compile(r"\bthesis\b|dissertation", re.I)
_STD_RE = re.compile(r"IEEE Std|Specification|Standard for", re.I)


def _pdf_files():
    return sorted(p for p in PDF_DIR.iterdir()
                  if p.suffix.lower() == ".pdf")


def _pages(path: Path):
    try:
        out = subprocess.run(["pdfinfo", str(path)], capture_output=True,
                             text=True, timeout=60).stdout
        m = re.search(r"^Pages:\s+(\d+)", out, re.M)
        t = re.search(r"^Title:\s+(.*)$", out, re.M)
        if m:
            return int(m.group(1)), (t.group(1).strip() if t else "")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    try:
        from pypdf import PdfReader
        r = PdfReader(str(path))
        meta = r.metadata or {}
        return len(r.pages), str(meta.get("/Title", "") or "")
    except Exception:
        return 0, ""


def handle_sources() -> dict:
    """handle -> bibliography stem (adders, multipliers, ...) — the domain
    hint, from which domain's bibliography introduced the handle."""
    src = {}
    for path in sorted(glob.glob(str(LEGACY / "bib" / "*.md"))):
        stem = Path(path).stem
        in_bib = False
        with open(path) as f:
            for line in f:
                if line.startswith("## bibliography"):
                    in_bib = True
                    continue
                if in_bib and line.startswith("## "):
                    in_bib = False
                if not in_bib:
                    continue
                m = re.match(r"(?:\*\s*)?([a-z0-9_]+)\s*->", line.strip())
                if m:
                    src.setdefault(m.group(1), stem)
    return src


def classify(handles, pages, fname, citation):
    for h in handles:
        if h in _OVERRIDES:
            return _OVERRIDES[h]
    if fname in _FILE_OVERRIDES:
        return _FILE_OVERRIDES[fname]
    if _THESIS_RE.search(citation):
        return "thesis", ""
    if _STD_RE.search(citation):
        return "standard", ""
    if _BOOK_RE.search(citation) and not re.search(r"LNCS|Proc|pp\.",
                                                    citation):
        return "book", ""
    if pages > 150:
        return "book", "by page count"
    note = "1-page file: stub?" if pages == 1 else ""
    return "paper", note


def build_inventory():
    from chialu.papers import PAPER_DB
    hmap = json.loads((PDF_DIR / "handles.json").read_text())
    rev = {}
    for h, f in hmap.items():
        rev.setdefault(f, []).append(h)
    man = {}
    mpath = PDF_DIR / "manifest.jsonl"
    if mpath.exists():
        for ln in mpath.read_text().splitlines():
            if ln.strip():
                d = json.loads(ln)
                man[d["handle"]] = d.get("citation", "")
    src = handle_sources()
    rows = []
    for p in _pdf_files():
        hs = sorted(rev.get(p.name, []))
        pages, title = _pages(p)
        cit = ""
        for h in hs:
            ref = PAPER_DB.papers.get(h)
            cit = ref.ref if ref else man.get(h, "")
            if cit:
                break
        kind, note = classify(hs, pages, p.name, cit)
        rows.append({"file": p.name, "handles": ",".join(hs) or "-",
                     "pages": pages, "kind": kind,
                     "domain": ",".join(sorted({src[h] for h in hs
                                                if h in src})) or "-",
                     "note": note, "pdf_title": title, "citation": cit})
    return rows


def write_inventory(rows):
    cols = ["file", "handles", "pages", "kind", "domain", "note",
            "pdf_title", "citation"]
    with open(INVENTORY, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t",
                           lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    papers = [r for r in rows if r["kind"] in ("paper", "report")]
    books = [r for r in rows if r["kind"] in ("book", "thesis",
                                              "standard", "slides")]

    def dump(path, rs):
        with open(path, "w") as f:
            for r in rs:
                f.write(f"{r['handles']}\t{r['pages']}\t{r['kind']}\t"
                        f"{r['file']}\t{r['citation'] or r['pdf_title']}\n")
    dump(PDF_DIR / "papers.txt", papers)
    dump(PDF_DIR / "books.txt", books)
    return papers, books


def read_inventory():
    with open(INVENTORY) as f:
        return list(csv.DictReader(f, delimiter="\t"))


# ---------------------------------------------------------------- vocab

def _named_spaces():
    from chialu.spaces import (adder_spaces, approx_spaces,
                                  checker_spaces, decimal_spaces, div_spaces,
                                  dsp_posit_spaces, fma_dot_spaces,
                                  fp_spaces, mul_spaces, redundant_spaces,
                                  sfu_spaces, shift_simd_spaces)
    return [
        ("adder", "carry-propagate adders", adder_spaces.cpa_space()),
        ("adder", "incrementers", adder_spaces.incrementer_space()),
        ("adder", "comparators", adder_spaces.comparator_space()),
        ("mul", "integer multipliers", mul_spaces.mul_space(16)),
        ("div", "dividers / square root", div_spaces.div_space()),
        ("div", "reciprocal seed tables", div_spaces.seed_table_space()),
        ("div", "multiplicative final rounding",
         div_spaces.mult_final_round_space()),
        ("fp", "floating-point adders", fp_spaces.fp_add_space()),
        ("fp", "floating-point multipliers", fp_spaces.fp_mul_space(11)),
        ("fp", "floating-point dividers", fp_spaces.fp_div_space()),
        ("fp", "floating-point comparators", fp_spaces.fp_cmp_space()),
        ("fp", "format converters", fp_spaces.fp_cvt_space()),
        ("dot", "dot-product / FMA / MAC", fma_dot_spaces.dot_acc_space(8)),
        ("shift", "shifters", shift_simd_spaces.shifter_space()),
        ("shift", "bit counting", shift_simd_spaces.bitcount_space()),
        ("shift", "sub-word SIMD", shift_simd_spaces.subword_space()),
        ("checker", "concurrent error detection",
         checker_spaces.checker_space()),
        ("checker", "two-rail / self-checking", checker_spaces.two_rail_space()),
        ("sfu", "elementary-function units", sfu_spaces.sfu_approx_space()),
        ("sfu", "polynomial datapaths", sfu_spaces.poly_datapath_space()),
        ("sfu", "segmentation", sfu_spaces.segment_space()),
        ("sfu", "range reduction", sfu_spaces.range_reduction_space()),
        ("decimal", "decimal adders", decimal_spaces.decimal_adder_space()),
        ("decimal", "decimal multipliers", decimal_spaces.decimal_mul_space()),
        ("decimal", "decimal dividers", decimal_spaces.decimal_div_space()),
        ("redundant", "signed-digit arithmetic",
         redundant_spaces.signed_digit_space()),
        ("redundant", "residue number systems", redundant_spaces.rns_space()),
        ("approx", "approximate adders", approx_spaces.approx_adder_space()),
        ("approx", "approximate multipliers",
         approx_spaces.approx_mul_space(16)),
        ("approx", "approximate dividers", approx_spaces.approx_div_space()),
        ("dsp", "posit units", dsp_posit_spaces.posit_unit_space()),
    ]


# survey report stem -> vocabulary domains it mostly concerns
DOMAIN_OF_SURVEY = {
    "adders": ("adder", "approx", "checker"),
    "multipliers": ("mul", "adder", "approx"),
    "dividers": ("div", "adder", "fp"),
    "fp_add": ("fp", "adder", "shift"),
    "fma_dot": ("dot", "fp", "mul", "adder"),
    "sfu_elementary": ("sfu", "fp", "mul"),
    "checkers": ("checker", "adder", "mul"),
    "decimal_arith": ("decimal", "adder", "mul"),
    "redundant_online": ("redundant", "adder", "mul", "div"),
    "approximate_arith": ("approx", "adder", "mul", "div"),
    "shift_simd": ("shift", "adder"),
    "fpga_arith": ("dsp", "adder", "mul", "sfu"),
    "commercial_units": ("fp", "dot", "div", "mul", "adder"),
}


def render_vocab(domains=None) -> str:
    """The controlled vocabulary block: family, one-line doc, choices,
    slots; grouped by space. `domains` restricts to those keys."""
    lines = []
    seen = set()
    for dom, title, space in _named_spaces():
        if domains and dom not in domains:
            continue
        lines.append(f"### {dom}: {title}")
        for a in space.candidates:
            key = (dom, a.family)
            if key in seen:
                continue
            seen.add(key)
            head = f"* {a.family}"
            if a.execution_style != "feed_forward":
                head += f" ({a.execution_style})"
            head += f" — {a.doc}"
            lines.append(head)
            for name, ch in a.design_choices.items():
                lines.append(f"    {name}: {ch.describe()}")
            for slot, sub in a.components.items():
                fams = ", ".join(x.family for x in sub.candidates)
                lines.append(f"    slot {slot}: {{{fams}}}")
        lines.append("")
    return "\n".join(lines).rstrip()


# --------------------------------------------------------------- prompt

def render_prompt(handle: str, text: str | None = None,
                  domains=None) -> str:
    from chialu.papers import PAPER_DB
    from chialu.archdocs import pdf_path
    tmpl = PROMPT_TEMPLATE.read_text()
    ref = PAPER_DB.papers.get(handle)
    citation = ref.ref if ref else "UNKNOWN (handle not in bibliography)"
    src = handle_sources().get(handle)
    hint = (f"{src} (survey report that cites it; likely domains: "
            f"{', '.join(DOMAIN_OF_SURVEY.get(src, ()))})"
            if src else "none")
    p = pdf_path(handle)
    doc = text if text is not None else (
        f"<<ATTACH {p.name if p else 'THE PDF'} OR PASTE ITS TEXT HERE>>")
    return (tmpl.replace("{{VOCABULARY}}", render_vocab(domains))
                .replace("{{HANDLE}}", handle)
                .replace("{{CITATION}}", citation)
                .replace("{{DOMAIN_HINT}}", hint)
                .replace("{{DOCUMENT}}", doc))


# ------------------------------------------------------------------ run

RUN_DIR = Path(__file__).resolve().parents[1] / "run" / "extract"
CODEX_MODEL = "gpt-5.6-sol"
_PREAMBLE = ("Operating instructions for this run: the complete document "
             "text is included at the end of this prompt. Do not run shell "
             "commands, do not read or write files, do not explore the "
             "working directory. Reply with the note only, starting at the "
             "`---` front-matter line, with no code fence around it.\n\n")


MAX_TEXT = 900_000      # codex caps a turn at 1,048,576 chars; prompt ~85k


def pdf_text(path: Path) -> str:
    """-layout text; falls back to raw mode and then truncates when the
    text layer is oversized (vectorized fonts, OCR garbage)."""
    r = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                       capture_output=True, text=True, timeout=300)
    text = r.stdout
    if len(text) > MAX_TEXT:
        r = subprocess.run(["pdftotext", str(path), "-"],
                           capture_output=True, text=True, timeout=300)
        text = r.stdout
    if len(text) > MAX_TEXT:
        text = text[:MAX_TEXT] + "\n\n[TEXT TRUNCATED AT 900k CHARS]\n"
    return text


def paper_jobs():
    """(handle, pdf path) for every paper/report row with a handle; a
    file shared by several handles is extracted once, under the first."""
    jobs, seen = [], set()
    for r in read_inventory():
        if r["kind"] not in ("paper", "report") or r["handles"] == "-":
            continue
        if r["file"] in seen:
            continue
        seen.add(r["file"])
        jobs.append((r["handles"].split(",")[0], PDF_DIR / r["file"]))
    return jobs


def _clean_note(raw: str) -> str:
    s = raw.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else ""
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    i = s.find("---")
    return s[i:].strip() + "\n" if i >= 0 else s + "\n"


def extract_one(handle: str, pdf: Path, model: str = CODEX_MODEL,
                timeout: int = 1800) -> str:
    """Run one paper through codex; returns a status word. Writes
    knowledge/notes/<handle>.md on success, run/extract/<handle>.* always."""
    NOTES_DIR.mkdir(exist_ok=True)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    note = NOTES_DIR / f"{handle}.md"
    if note.exists():
        return "exists"
    log = RUN_DIR / f"{handle}.log"
    try:
        text = pdf_text(pdf)
    except Exception as e:                       # noqa: BLE001
        log.write_text(f"pdftotext failed: {e}\n")
        return "pdftotext_error"
    if len(text.strip()) < 500:
        log.write_text(f"no text layer ({len(text)} chars)\n")
        return "unreadable"
    prompt = _PREAMBLE + render_prompt(handle, text)
    (RUN_DIR / f"{handle}.prompt.md").write_text(prompt)
    out = RUN_DIR / f"{handle}.out.md"
    work = RUN_DIR / "work"
    work.mkdir(exist_ok=True)
    cmd = ["codex", "exec", "-m", model, "-s", "read-only", "--ephemeral",
           "--skip-git-repo-check", "--color", "never", "-C", str(work),
           "-o", str(out), "-"]
    with open(log, "w") as lf:
        try:
            r = subprocess.run(cmd, input=prompt, stdout=lf, stderr=lf,
                               text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return "timeout"
    if r.returncode != 0 or not out.exists():
        return f"codex_rc{r.returncode}"
    body = _clean_note(out.read_text())
    if not body.startswith("---") or f"handle: {handle}" not in body:
        return "bad_note"
    note.write_text(body)
    return "ok"


def run_batch(parallel: int = 16, limit: int | None = None,
              model: str = CODEX_MODEL, only=None):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    jobs = paper_jobs()
    if only:
        jobs = [j for j in jobs if j[0] in only]
    if limit:
        jobs = jobs[:limit]
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    status = RUN_DIR / "status.tsv"
    done = 0
    print(f"[extract] {len(jobs)} papers, {parallel} parallel, model {model}",
          flush=True)
    with ThreadPoolExecutor(parallel) as ex, open(status, "a") as sf:
        futs = {ex.submit(extract_one, h, p, model): h for h, p in jobs}
        for fut in as_completed(futs):
            h = futs[fut]
            try:
                st = fut.result()
            except Exception as e:               # noqa: BLE001
                st = f"error: {e}"
            done += 1
            sf.write(f"{h}\t{st}\n")
            sf.flush()
            print(f"[{done}/{len(jobs)}] {h}: {st}", flush=True)


# ---------------------------------------------------------------- books
#
# Non-paper documents (book / thesis / standard / slides) are too long
# for one extraction call and are not organized around one claim, so
# they go through three passes, each persisted under
# knowledge/extract/segments/<key>.json so the plan is reviewable:
#
#   segment   chapter boundaries as pdf page indices — from the pdf
#             outline when it has a usable chapter level, else from a
#             table-of-contents pass over the front pages plus the
#             first two lines of every page; documents <= 60 pages are
#             one segment
#   triage    which segments to extract and which families they touch
#             (one call per document: vocabulary + a 500-word excerpt
#             of every segment)
#   run-books the chapter prompt per planned segment (standard prompt
#             for standards) -> knowledge/notes/<key>__<seg>.md with
#             front-matter handle <key>#<seg>
#
# <key> is the bibliography handle; a handle-less file gets the
# provisional key file_<stem> until a handle is assigned.

SEG_DIR = EXTRACT_DIR / "segments"
SCHEMA_DIR = EXTRACT_DIR / "schemas"
BOOK_KINDS = ("book", "thesis", "standard", "slides")
SINGLE_SEGMENT_MAX_PAGES = 60
TOC_FRONT_PAGES = 40
_NUMBERED = re.compile(
    r"^(\d+|[IVXLC]+|Appendix\s+\w+|Annex\s+\w+|[A-Z])[\s.:]")


def book_rows():
    return [r for r in read_inventory()
            if r["kind"] in BOOK_KINDS and int(r["pages"]) > 1]


def doc_key(row) -> str:
    if row["handles"] != "-":
        return row["handles"].split(",")[0]
    stem = re.sub(r"[^a-z0-9]+", "_", Path(row["file"]).stem.lower())
    return "file_" + stem.strip("_")


def find_row(key: str):
    for r in book_rows():
        if doc_key(r) == key:
            return r
    raise SystemExit(f"no book-class document with key {key!r}")


def pages_text(pdf: Path) -> list:
    r = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                       capture_output=True, text=True, timeout=600)
    pages = r.stdout.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


def page_heads(pages, n_lines: int = 2) -> str:
    out = []
    for i, pg in enumerate(pages):
        lines = [ln.strip() for ln in pg.strip().splitlines() if ln.strip()]
        out.append(f"p{i}: " + " | ".join(lines[:n_lines]))
    return "\n".join(out)


def outline_segments(pdf: Path, n_pages: int):
    """Chapter segments from the pdf outline: the level whose numbered
    entries number 8..60 (most entries wins, shallower on ties)."""
    try:
        from pypdf import PdfReader
        rd = PdfReader(str(pdf))
        flat = []

        def walk(items, lvl):
            for it in items:
                if isinstance(it, list):
                    walk(it, lvl + 1)
                else:
                    try:
                        pg = rd.get_destination_page_number(it)
                    except Exception:      # noqa: BLE001
                        pg = None
                    flat.append((lvl, (it.title or "").strip(), pg))
        walk(rd.outline, 0)
    except Exception:                      # noqa: BLE001
        return None
    best = None
    for lvl in range(4):                  # shallowest chapter-like level
        n = sum(1 for l, t, p in flat
                if l == lvl and p is not None and _NUMBERED.match(t))
        if 8 <= n <= 60:
            best = lvl
            break
    if best is None:
        return None
    ents = sorted((p, t) for l, t, p in flat if l == best and p is not None)
    segs, k = [], 0
    for i, (p, t) in enumerate(ents):
        if not _NUMBERED.match(t):
            continue
        end = (ents[i + 1][0] - 1) if i + 1 < len(ents) else n_pages - 1
        if end < p:
            end = p
        k += 1
        segs.append({"id": f"s{k:02d}", "title": t, "start": p, "end": end,
                     "kind": "chapter"})
    return segs


def _codex(prompt: str, out: Path, log: Path, model: str,
           schema: Path | None = None, timeout: int = 1800) -> int:
    work = RUN_DIR / "work"
    work.mkdir(parents=True, exist_ok=True)
    cmd = ["codex", "exec", "-m", model, "-s", "read-only", "--ephemeral",
           "--skip-git-repo-check", "--color", "never", "-C", str(work),
           "-o", str(out)]
    if schema:
        cmd += ["--output-schema", str(schema)]
    cmd.append("-")
    with open(log, "w") as lf:
        try:
            r = subprocess.run(cmd, input=prompt, stdout=lf, stderr=lf,
                               text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return -1
    return r.returncode


def _load_json_out(out: Path):
    s = out.read_text().strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1]
        s = s.rsplit("```", 1)[0]
    return json.loads(s)


def seg_path(key: str) -> Path:
    return SEG_DIR / f"{key}.json"


def segment(key: str, model: str = CODEX_MODEL, force: bool = False):
    """Write knowledge/extract/segments/<key>.json (segments only)."""
    SEG_DIR.mkdir(parents=True, exist_ok=True)
    sp = seg_path(key)
    if sp.exists() and not force:
        return "exists"
    row = find_row(key)
    pdf = PDF_DIR / row["file"]
    pages = pages_text(pdf)
    n = len(pages)
    doc = {"key": key, "file": row["file"], "kind": row["kind"],
           "citation": row["citation"], "pages": n, "title": "",
           "authors": "", "source": "", "segments": []}
    if sum(len(p) for p in pages) < max(2000, 100 * n):
        # scanned pdf: no text layer — a TOC pass would only be
        # invented from the model's memory of the book
        doc["source"] = "unreadable"
        sp.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
        return "unreadable"
    if n <= SINGLE_SEGMENT_MAX_PAGES:
        doc["source"] = "single"
        doc["segments"] = [{"id": "s01", "title": "whole document",
                            "start": 0, "end": n - 1, "kind": "whole"}]
    else:
        segs = outline_segments(pdf, n)
        if segs:
            doc["source"] = "outline"
            doc["segments"] = segs
        else:
            doc["source"] = "toc_llm"
            RUN_DIR.mkdir(parents=True, exist_ok=True)
            front = "\n".join(f"<<PAGE {i}>>\n{pages[i]}"
                              for i in range(min(TOC_FRONT_PAGES, n)))
            front = front[:200_000]
            prompt = ((EXTRACT_DIR / "toc_prompt.md").read_text()
                      .replace("{{KEY}}", key)
                      .replace("{{CITATION}}", row["citation"]
                               or row["pdf_title"] or row["file"])
                      .replace("{{N_PAGES_MINUS_1}}", str(n - 1))
                      .replace("{{N_PAGES}}", str(n))
                      .replace("{{FRONT}}", front)
                      .replace("{{HEADS}}", page_heads(pages)))
            out, log = RUN_DIR / f"{key}.toc.json", RUN_DIR / f"{key}.toc.log"
            (RUN_DIR / f"{key}.toc.prompt.md").write_text(prompt)
            rc = _codex(prompt, out, log, model,
                        schema=SCHEMA_DIR / "toc.schema.json")
            if rc != 0 or not out.exists():
                return f"toc_codex_rc{rc}"
            j = _load_json_out(out)
            doc["title"], doc["authors"] = j.get("title", ""), \
                j.get("authors", "")
            segs = []
            for i, s in enumerate(j["segments"], 1):
                a, b = int(s["start"]), int(s["end"])
                a, b = max(0, min(a, n - 1)), max(0, min(b, n - 1))
                segs.append({"id": f"s{i:02d}", "title": s["title"],
                             "start": a, "end": max(a, b),
                             "kind": s.get("kind", "chapter")})
            doc["segments"] = segs
    for s in doc["segments"]:
        s.setdefault("extract", None)
        s.setdefault("families", [])
        s.setdefault("why", "")
    sp.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    return f"{doc['source']}:{len(doc['segments'])}"


def _excerpt(pages, seg, words: int = 500) -> str:
    text = " ".join(pages[i] for i in range(seg["start"], seg["end"] + 1))
    return " ".join(text.split()[:words])


def triage(key: str, model: str = CODEX_MODEL, force: bool = False):
    """Fill extract/families/why on every segment of <key>.json."""
    sp = seg_path(key)
    if not sp.exists():
        return "no_segments"
    doc = json.loads(sp.read_text())
    segs = doc["segments"]
    if all(s.get("extract") is not None for s in segs) and not force:
        return "exists"
    if doc["kind"] == "standard" or doc["source"] == "single":
        for s in segs:
            s["extract"] = s["kind"] not in ("front", "back")
            s["why"] = "whole document / standard: extracted as is"
        sp.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
        return "rule"
    pages = pages_text(PDF_DIR / doc["file"])
    listing = "\n\n".join(
        f"### {s['id']}  {s['title']}  (pdf pages {s['start']}-{s['end']}, "
        f"{s['kind']})\n{_excerpt(pages, s)}" for s in segs)
    prompt = ((EXTRACT_DIR / "triage_prompt.md").read_text()
              .replace("{{VOCABULARY}}", render_vocab())
              .replace("{{KEY}}", key)
              .replace("{{CITATION}}", doc["citation"] or doc["title"])
              .replace("{{KIND}}", doc["kind"])
              .replace("{{SEGMENTS}}", listing))
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    out, log = RUN_DIR / f"{key}.triage.json", RUN_DIR / f"{key}.triage.log"
    (RUN_DIR / f"{key}.triage.prompt.md").write_text(prompt)
    rc = _codex(prompt, out, log, model,
                schema=SCHEMA_DIR / "triage.schema.json")
    if rc != 0 or not out.exists():
        return f"triage_codex_rc{rc}"
    verdict = {v["id"]: v for v in _load_json_out(out)["segments"]}
    for s in segs:
        v = verdict.get(s["id"])
        if v:
            s["extract"] = bool(v["extract"])
            s["families"] = list(v.get("families", []))
            s["why"] = v.get("why", "")
        else:
            s["extract"], s["why"] = False, "no triage verdict"
    sp.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    return f"triage:{sum(1 for s in segs if s['extract'])}/{len(segs)}"


def render_chapter_prompt(doc, seg, text: str) -> str:
    kind = doc["kind"]
    tmpl = "standard_prompt.md" if kind == "standard" else "chapter_prompt.md"
    note_kind = {"book": "book_chapter", "thesis": "thesis_chapter",
                 "standard": "standard", "slides": "slides"}[kind]
    chapters = "\n".join(
        f"* {s['id']}: {s['title']} (pdf pages {s['start']}-{s['end']})"
        for s in doc["segments"])
    return ((EXTRACT_DIR / tmpl).read_text()
            .replace("{{VOCABULARY}}", render_vocab())
            .replace("{{HANDLE}}", f"{doc['key']}#{seg['id']}")
            .replace("{{PARENT}}", doc["key"])
            .replace("{{CITATION}}", doc["citation"] or doc["title"])
            .replace("{{KIND}}", note_kind)
            .replace("{{CHAPTER_TITLE}}", seg["title"])
            .replace("{{PDF_PAGES}}", f"{seg['start']}-{seg['end']}")
            .replace("{{CHAPTER_LIST}}", chapters)
            .replace("{{FAMILY_HINT}}", ", ".join(seg.get("families", []))
                     or "none")
            .replace("{{DOCUMENT}}", text))


def extract_segment(doc, seg, model: str = CODEX_MODEL,
                    timeout: int = 2400) -> str:
    NOTES_DIR.mkdir(exist_ok=True)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    key, sid = doc["key"], seg["id"]
    note = NOTES_DIR / f"{key}__{sid}.md"
    if note.exists():
        return "exists"
    pages = pages_text(PDF_DIR / doc["file"])
    raw = sum(len(pages[i].strip())
              for i in range(seg["start"], seg["end"] + 1))
    if raw < 500:                    # labels excluded: scanned chapter
        return "unreadable"
    text = "\n".join(f"<<PAGE {i}>>\n{pages[i]}"
                     for i in range(seg["start"], seg["end"] + 1))
    if len(text) > MAX_TEXT:
        text = text[:MAX_TEXT] + "\n\n[TEXT TRUNCATED AT 900k CHARS]\n"
    prompt = _PREAMBLE + render_chapter_prompt(doc, seg, text)
    stem = f"{key}__{sid}"
    (RUN_DIR / f"{stem}.prompt.md").write_text(prompt)
    out, log = RUN_DIR / f"{stem}.out.md", RUN_DIR / f"{stem}.log"
    rc = _codex(prompt, out, log, model, timeout=timeout)
    if rc == -1:
        return "timeout"
    if rc != 0 or not out.exists():
        return f"codex_rc{rc}"
    body = _clean_note(out.read_text())
    if not body.startswith("---") or f"handle: {key}#{sid}" not in body:
        return "bad_note"
    note.write_text(body)
    return "ok"


def run_books(parallel: int = 16, only=None, model: str = CODEX_MODEL):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    jobs = []
    for sp in sorted(SEG_DIR.glob("*.json")):
        doc = json.loads(sp.read_text())
        if only and doc["key"] not in only:
            continue
        for s in doc["segments"]:
            if s.get("extract"):
                jobs.append((doc, s))
    status = RUN_DIR / "status_books.tsv"
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[extract] {len(jobs)} segments, {parallel} parallel, "
          f"model {model}", flush=True)
    done = 0
    with ThreadPoolExecutor(parallel) as ex, open(status, "a") as sf:
        futs = {ex.submit(extract_segment, d, s, model):
                f"{d['key']}#{s['id']}" for d, s in jobs}
        for fut in as_completed(futs):
            h = futs[fut]
            try:
                st = fut.result()
            except Exception as e:               # noqa: BLE001
                st = f"error: {e}"
            done += 1
            sf.write(f"{h}\t{st}\n")
            sf.flush()
            print(f"[{done}/{len(jobs)}] {h}: {st}", flush=True)


def books_report():
    for r in book_rows():
        key = doc_key(r)
        sp = seg_path(key)
        if sp.exists():
            d = json.loads(sp.read_text())
            segs = d["segments"]
            planned = sum(1 for s in segs if s.get("extract"))
            triaged = all(s.get("extract") is not None for s in segs)
            notes = sum(1 for s in segs
                        if (NOTES_DIR / f"{key}__{s['id']}.md").exists())
            st = (f"{d['source']} {len(segs)} segs, "
                  f"{'planned ' + str(planned) if triaged else 'untriaged'}, "
                  f"notes {notes}")
        else:
            st = "unsegmented"
        print(f"{key:24s} {r['kind']:8s} {r['pages']:>4s}p  {st}")


# --------------------------------------------------------------- reduce
#
# The reduce side gathers, per family, every note block that names it
# (plus the chapter taxonomies that map onto it and the space-gap
# bullets that mention it) into one bundle under run/extract/reduce/,
# ordered by authority, capped in size. A writer (subagent) turns each
# bundle into knowledge/arch/<domain>/<family>.md following
# knowledge/extract/reduce_prompt.md; the bundle carries the family's
# structural definition and the handle -> citation lines to copy.

REDUCE_DIR = RUN_DIR / "reduce"
AUTHORITY_RANK = {"textbook": 0, "thesis": 1, "landmark": 2, "survey": 3,
                  "standard": 4, "incremental": 5, "slides": 6}
BUNDLE_CAP = 140_000          # chars


def _note_meta(text: str) -> dict:
    m = {}
    fm = ""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        fm = text[3:end] if end > 0 else ""
    for ln in fm.splitlines():
        if ":" in ln:
            k, v = ln.split(":", 1)
            m[k.strip()] = v.strip()
    return m


def _sections(text: str) -> dict:
    """'## name' -> body text (top-level sections after front matter)."""
    out, cur, buf = {}, None, []
    for ln in text.splitlines():
        if ln.startswith("## "):
            if cur:
                out[cur] = "\n".join(buf).strip()
            cur, buf = ln[3:].strip(), []
        elif cur:
            buf.append(ln)
    if cur:
        out[cur] = "\n".join(buf).strip()
    return out


_BLOCK_RE = re.compile(r"^### ([a-z0-9_]+)\s*\((role:[^)]*)\)\s*$", re.M)


def _family_blocks(fam_section: str):
    """[(family, role, block_text)] from a '## families' section."""
    hits = list(_BLOCK_RE.finditer(fam_section))
    out = []
    for i, h in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(fam_section)
        out.append((h.group(1), h.group(2), fam_section[h.end():end].strip()))
    return out


def family_domains() -> dict:
    """family -> (domain, Architecture) — first space that defines it,
    top-level candidates first, then the families reachable only
    through component slots (they inherit the domain of the space that
    opens the slot)."""
    fd = {}
    spaces = _named_spaces()
    for dom, _title, space in spaces:
        for a in space.candidates:
            fd.setdefault(a.family, (dom, a))

    def walk(dom, space):
        for a in space.candidates:
            fd.setdefault(a.family, (dom, a))
            for sub in a.components.values():
                walk(dom, sub)
    for dom, _title, space in spaces:
        walk(dom, space)
    return fd


def _structure(arch) -> str:
    lines = [f"family: {arch.family}",
             f"execution_style: {arch.execution_style}",
             f"one-line doc (spaces): {arch.doc}"]
    for name, ch in arch.design_choices.items():
        lines.append(f"choice {name}: {ch.describe()}")
    for slot, sub in arch.components.items():
        lines.append(f"slot {slot}: {{{', '.join(x.family for x in sub.candidates)}}}")
    if arch.mutations:
        lines.append("mutations: " + ", ".join(arch.mutations))
    return "\n".join(lines)


def _shrink_tables(block: str, keep_rows: int = 6) -> str:
    out, rows = [], 0
    for ln in block.splitlines():
        if ln.startswith("|"):
            rows += 1
            if rows > keep_rows + 2:          # header + separator + rows
                continue
        else:
            rows = 0
        out.append(ln)
    return "\n".join(out)


def build_reduce_index():
    from chialu.papers import PAPER_DB
    REDUCE_DIR.mkdir(parents=True, exist_ok=True)
    fd = family_domains()
    per = {f: [] for f in fd}
    gaps = {f: [] for f in fd}
    unknown, new_fams = {}, []
    for p in sorted(NOTES_DIR.glob("*.md")):
        text = p.read_text()
        meta = _note_meta(text)
        sec = _sections(text)
        handle = meta.get("handle", p.stem)
        auth = meta.get("authority", "incremental")
        rank = AUTHORITY_RANK.get(auth, 5)
        tax = sec.get("taxonomy", "")
        for fam, role, body in _family_blocks(sec.get("families", "")):
            if fam not in per:
                unknown.setdefault(fam, []).append(handle)
                continue
            extra = ""
            if tax and tax.strip() != "none" and f"-> {fam}" in tax:
                extra = "\n\ntaxonomy (from this chapter):\n" + tax[:2500]
            per[fam].append((rank, auth, handle, role,
                             meta.get("status", ""), body + extra))
        sg = sec.get("space_gaps", "")
        if sg and sg.strip() != "none":
            for ln in sg.splitlines():
                for fam in per:
                    if re.search(rf"\b{re.escape(fam)}\b", ln):
                        gaps[fam].append(f"{ln.strip()}  [{handle}]")
        nf = sec.get("new_families", "")
        if nf and nf.strip() != "none":
            for m in re.finditer(r"^### ([a-z0-9_]+)\s*\(([^)]*)\)", nf, re.M):
                new_fams.append((m.group(1), m.group(2), handle))
    index_rows = []
    for fam, (dom, arch) in sorted(fd.items()):
        blocks = sorted(per[fam], key=lambda b: (b[0], b[2]))
        cites = {}
        for _r, _a, h, _ro, _s, _b in blocks:
            ref = PAPER_DB.papers.get(h.split("#")[0])
            if ref:
                cites[h.split("#")[0]] = ref.ref
        parts = [f"# reduce bundle: {fam}  (domain {dom})", "",
                 "## structure (authoritative, from chialu/spaces)", "",
                 _structure(arch), "",
                 f"## evidence: {len(blocks)} note blocks, "
                 f"ordered textbook > thesis > landmark > survey > incremental", ""]
        size = sum(len(p) for p in parts)
        omitted = []
        for i, (r, a, h, role, st, body) in enumerate(blocks):
            hdr = f"### [{a}] {h}  ({role}; note status {st})"
            if size > BUNDLE_CAP * 0.7:
                body = _shrink_tables(body)
            if size + len(body) > BUNDLE_CAP and a in ("incremental", "slides"):
                omitted.append(h)
                continue
            parts += [hdr, "", body, ""]
            size += len(hdr) + len(body) + 4
        if omitted:
            parts += ["### omitted for size (incremental): "
                      + ", ".join(omitted), ""]
        # named-variant candidates: enum choice values the notes pin
        from adir import Enum as EnumChoice
        enum_choices = {k: ch for k, ch in arch.design_choices.items()
                        if isinstance(ch, EnumChoice)}
        usage = {}
        for _r, _a, h, _ro, _s, body in blocks:
            for m in re.finditer(r"^\s{2}([a-z0-9_]+):\s*([^#\n]+?)\s*(?:#.*)?$",
                                 body, re.M):
                k, val = m.group(1), m.group(2).strip()
                if k in enum_choices and val in map(str, enum_choices[k].members()):
                    usage.setdefault((k, val), []).append(h)
        parts += ["## variant candidates (enum values the notes pin; "
                  "count, handles)", ""]
        if usage:
            for (k, val), hs in sorted(usage.items(),
                                       key=lambda kv: (-len(kv[1]), kv[0])):
                parts.append(f"* {k} = {val}: {len(hs)} — "
                             + ", ".join(sorted(set(hs))[:10]))
        else:
            parts.append("none")
        parts.append("")
        parts += ["## space_gaps mentioning this family (raw, from notes)", ""]
        parts += [f"* {g}" for g in gaps[fam][:60]] or ["none"]
        parts += ["", "## citations (copy verbatim into ## references)", ""]
        parts += [f"{h} -> {c}" for h, c in sorted(cites.items())] or ["none"]
        (REDUCE_DIR / f"{fam}.md").write_text("\n".join(parts) + "\n")
        index_rows.append((fam, dom, len(blocks), size,
                           str(ARCH_DIR / dom / f"{fam}.md")))
    with open(REDUCE_DIR / "INDEX.tsv", "w") as f:
        f.write("family\tdomain\tblocks\tbundle_chars\ttarget\n")
        for r in index_rows:
            f.write("\t".join(map(str, r)) + "\n")
    with open(REDUCE_DIR / "new_families.tsv", "w") as f:
        f.write("proposed\tdetail\thandle\n")
        for n, d, h in sorted(new_fams):
            f.write(f"{n}\t{d}\t{h}\n")
    with open(REDUCE_DIR / "unknown_families.tsv", "w") as f:
        for fam, hs in sorted(unknown.items()):
            f.write(f"{fam}\t{len(hs)}\t{','.join(hs[:8])}\n")
    return index_rows, new_fams, unknown


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmds = ("inventory", "vocab", "prompt", "run", "segment", "triage",
            "run-books", "books", "reduce-index")
    if argv and argv[0] == "reduce-index":
        rows, nf, unk = build_reduce_index()
        zero = [r[0] for r in rows if r[2] == 0]
        print(f"[reduce] {len(rows)} families -> {REDUCE_DIR}; "
              f"{len(zero)} with no note blocks: {', '.join(zero)}")
        print(f"  new-family proposals {len(nf)}, unknown family names in "
              f"notes {len(unk)} (see unknown_families.tsv)")
        big = sorted(rows, key=lambda r: -r[3])[:5]
        print("  largest bundles: " + ", ".join(f"{r[0]}={r[3]//1000}k"
                                                for r in big))
        return 0
    if not argv or argv[0] not in cmds:
        print(__doc__)
        return 2
    cmd = argv[0]
    model = argv[argv.index("--model") + 1] \
        if "--model" in argv else CODEX_MODEL
    force = "--force" in argv
    if cmd == "books":
        books_report()
        return 0
    if cmd in ("segment", "triage"):
        keys = [argv[1]] if len(argv) > 1 and not argv[1].startswith("--") \
            else None
        if keys is None or keys == ["all"]:
            keys = [doc_key(r) for r in book_rows()]
        fn = segment if cmd == "segment" else triage
        for k in keys:
            print(f"{cmd} {k}: {fn(k, model, force)}", flush=True)
        return 0
    if cmd == "run-books":
        par = int(argv[argv.index("--parallel") + 1]) \
            if "--parallel" in argv else 16
        only = set(argv[argv.index("--only") + 1].split(",")) \
            if "--only" in argv else None
        run_books(par, only, model)
        return 0
    if cmd == "run":
        par = int(argv[argv.index("--parallel") + 1]) \
            if "--parallel" in argv else 16
        lim = int(argv[argv.index("--limit") + 1]) \
            if "--limit" in argv else None
        model = argv[argv.index("--model") + 1] \
            if "--model" in argv else CODEX_MODEL
        only = set(argv[argv.index("--only") + 1].split(",")) \
            if "--only" in argv else None
        run_batch(par, lim, model, only)
        return 0
    if cmd == "inventory":
        rows = build_inventory()
        papers, books = write_inventory(rows)
        from collections import Counter
        c = Counter(r["kind"] for r in rows)
        print(f"[extract] {len(rows)} pdfs -> {INVENTORY.name}: "
              + ", ".join(f"{k}={c[k]}" for k in KINDS if c[k]))
        print(f"  papers.txt {len(papers)}  books.txt {len(books)}  "
              f"no-handle {sum(1 for r in rows if r['handles'] == '-')}")
        return 0
    if cmd == "vocab":
        print(render_vocab())
        return 0
    handle = argv[1] if len(argv) > 1 else None
    if not handle:
        print("usage: prompt <handle> [--text FILE] [--domains a,b]")
        return 2
    text, domains = None, None
    if "--text" in argv:
        text = Path(argv[argv.index("--text") + 1]).read_text()
    if "--domains" in argv:
        domains = set(argv[argv.index("--domains") + 1].split(","))
    print(render_prompt(handle, text, domains))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
