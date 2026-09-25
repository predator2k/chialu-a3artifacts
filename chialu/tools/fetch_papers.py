#!/usr/bin/env python3
"""Fetch open-access PDFs for the kb bibliography entries.

Sources, in order:
  1. Crossref  (query.bibliographic)         -> DOI
  2. OpenAlex  (by DOI, else by title)       -> best_oa_location / oa_url PDF links
  3. arXiv API (by title)                    -> preprint PDF, used when OpenAlex yields nothing usable

Legal open-access sources only. A paper with no OA copy goes on the failed list.

Resumable: a handle with an existing valid PDF, or already recorded in
papers/manifest.jsonl (unless --retry lists its status), is skipped.

Usage:
  python3 tools/fetch_papers.py [--limit N] [--only h1,h2] [--retry status1,status2]
"""
import difflib
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIR = os.path.join(ROOT, "legacy", "knowledge", "bib")
PAPERS = os.path.join(ROOT, "chialu", "knowledge", "pdf")
MANIFEST = os.path.join(PAPERS, "manifest.jsonl")
FAILED = os.path.join(PAPERS, "failed_downloads.txt")

UA = "chialu-kb-fetch (mailto:<email>)"
MAILTO = "<email>"
TIMEOUT = 30
SLEEP = 0.2
MIN_SIZE = 10 * 1024
MAX_SIZE = 100 * 1024 * 1024

ENTRY_RE = re.compile(r"^\*?\s*([A-Za-z0-9_.\-]+)\s*->\s*(.+?)\s*$")
TITLE_RE = re.compile(r'"([^"]+)"')

_unverified_ctx = ssl._create_unverified_context()


def parse_entries():
    """Return ordered list of (handle, citation), deduped by handle (first wins)."""
    entries = []
    seen = set()
    for name in sorted(os.listdir(KB_DIR)):
        if not name.endswith(".md"):
            continue
        inbib = False
        with open(os.path.join(KB_DIR, name), encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if re.match(r"^## [Bb]ibliography", line):
                    inbib = True
                    continue
                if line.startswith("## "):
                    inbib = False
                    continue
                if not inbib or not line.strip():
                    continue
                m = ENTRY_RE.match(line)
                if not m or " " in m.group(1):
                    continue
                handle, citation = m.group(1), m.group(2)
                citation = re.sub(r"^\[unverified\]\s*", "", citation)
                if handle not in seen:
                    seen.add(handle)
                    entries.append((handle, citation))
    return entries


def http_get(url, timeout=TIMEOUT):
    """GET url, return (bytes, content_type). Retries once without cert verification."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(MAX_SIZE), r.headers.get("Content-Type", "")
    except urllib.error.URLError as e:
        if isinstance(getattr(e, "reason", None), ssl.SSLError) or isinstance(e, ssl.SSLError):
            with urllib.request.urlopen(req, timeout=timeout, context=_unverified_ctx) as r:
                return r.read(MAX_SIZE), r.headers.get("Content-Type", "")
        raise


def api_json(url):
    time.sleep(SLEEP)
    data, _ = http_get(url)
    return json.loads(data.decode("utf-8"))


def norm(s):
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())


def similar(a, b):
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    if na in nb or nb in na:
        return 1.0
    return difflib.SequenceMatcher(None, na, nb).ratio()


def extract_title(citation):
    m = TITLE_RE.search(citation)
    return m.group(1) if m else None


def crossref_doi(citation, title):
    q = urllib.parse.quote_plus(citation[:500])
    url = f"https://api.crossref.org/works?query.bibliographic={q}&rows=3&mailto={MAILTO}"
    data = api_json(url)
    for item in data.get("message", {}).get("items", []):
        cand = (item.get("title") or [""])[0]
        if title and cand and similar(title, cand) >= 0.75:
            return item.get("DOI")
    return None


def openalex_by_doi(doi):
    url = f"https://api.openalex.org/works/https://doi.org/{urllib.parse.quote(doi)}?mailto={MAILTO}"
    try:
        return api_json(url)
    except Exception:
        return None


def openalex_by_title(title):
    safe = norm(title)
    if not safe:
        return None
    url = ("https://api.openalex.org/works?filter=title.search:"
           + urllib.parse.quote(safe) + f"&per-page=3&mailto={MAILTO}")
    try:
        data = api_json(url)
    except Exception:
        return None
    for work in data.get("results", []):
        if similar(title, work.get("title") or "") >= 0.8:
            return work
    return None


def oa_urls(work):
    """Ordered candidate PDF URLs from an OpenAlex work."""
    urls = []

    def add(u):
        if not u:
            return
        u = re.sub(r"arxiv\.org/abs/", "arxiv.org/pdf/", u)
        if u not in urls:
            urls.append(u)

    boa = work.get("best_oa_location") or {}
    add(boa.get("pdf_url"))
    add((work.get("open_access") or {}).get("oa_url"))
    for loc in work.get("locations") or []:
        if loc.get("is_oa"):
            add(loc.get("pdf_url"))
    add(boa.get("landing_page_url") if str(boa.get("landing_page_url", "")).endswith(".pdf") else None)
    return urls


def arxiv_pdf(title):
    safe = norm(title)
    if not safe:
        return None
    q = urllib.parse.urlencode({"search_query": f'ti:"{safe}"', "max_results": 5})
    time.sleep(SLEEP)
    try:
        data, _ = http_get(f"http://export.arxiv.org/api/query?{q}")
        root = ET.fromstring(data)
    except Exception:
        return None
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("a:entry", ns):
        etitle = "".join((entry.findtext("a:title", "", ns) or "").split("\n"))
        if similar(title, etitle) < 0.8:
            continue
        for link in entry.findall("a:link", ns):
            if link.get("title") == "pdf" or "/pdf/" in (link.get("href") or ""):
                return link.get("href")
        eid = entry.findtext("a:id", "", ns)
        if "/abs/" in eid:
            return eid.replace("/abs/", "/pdf/")
    return None


def valid_pdf_file(path):
    try:
        if os.path.getsize(path) <= MIN_SIZE:
            return False
        with open(path, "rb") as f:
            return f.read(5).startswith(b"%PDF")
    except OSError:
        return False


def try_download(url, dest):
    """Return (status, nbytes). status: 'ok' | 'not_pdf' | 'fetch_failed'."""
    time.sleep(SLEEP)
    try:
        data, _ctype = http_get(url)
    except Exception:
        return "fetch_failed", 0
    if data.startswith(b"%PDF") and len(data) > MIN_SIZE:
        with open(dest, "wb") as f:
            f.write(data)
        return "ok", len(data)
    return "not_pdf", len(data)


def process(handle, citation):
    """Return manifest record dict."""
    dest = os.path.join(PAPERS, handle + ".pdf")
    title = extract_title(citation)
    doi = None
    work = None

    try:
        doi = crossref_doi(citation, title)
    except Exception:
        pass

    if doi:
        work = openalex_by_doi(doi)
    if work is None and title:
        work = openalex_by_title(title)
        if work and not doi:
            wdoi = work.get("doi") or ""
            doi = wdoi.replace("https://doi.org/", "") or None

    candidates = oa_urls(work) if work else []

    saw_not_pdf = False
    attempted = False
    for url in candidates[:6]:
        attempted = True
        status, nbytes = try_download(url, dest)
        if status == "ok":
            return {"handle": handle, "citation": citation, "doi": doi,
                    "source_url": url, "status": "ok", "bytes": nbytes}
        if status == "not_pdf":
            saw_not_pdf = True

    if title:
        ax = arxiv_pdf(title)
        if ax:
            attempted = True
            status, nbytes = try_download(ax, dest)
            if status == "ok":
                return {"handle": handle, "citation": citation, "doi": doi,
                        "source_url": ax, "status": "ok", "bytes": nbytes}
            if status == "not_pdf":
                saw_not_pdf = True

    if os.path.exists(dest) and not valid_pdf_file(dest):
        os.remove(dest)

    if attempted:
        status = "not_pdf" if saw_not_pdf else "fetch_failed"
    elif doi:
        status = "no_oa"
    else:
        status = "no_doi"
    return {"handle": handle, "citation": citation, "doi": doi,
            "source_url": None, "status": status, "bytes": 0}


def load_manifest():
    records = {}
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rec = json.loads(line)
                        records[rec["handle"]] = rec
                    except (ValueError, KeyError):
                        pass
    return records


def write_outputs(entries, records):
    with open(MANIFEST, "w", encoding="utf-8") as f:
        for handle, _ in entries:
            if handle in records:
                f.write(json.dumps(records[handle]) + "\n")
    failed = sorted((r for r in records.values() if r["status"] != "ok"),
                    key=lambda r: r["handle"])
    n_ok = sum(1 for r in records.values() if r["status"] == "ok")
    with open(FAILED, "w", encoding="utf-8") as f:
        f.write(f"# attempted: {len(records)}  downloaded: {n_ok}  failed: {len(failed)}\n")
        f.write("# reasons: no_doi = no DOI/metadata match found; no_oa = DOI resolved but no "
                "legal open-access copy found; fetch_failed = OA URL(s) unreachable; "
                "not_pdf = OA URL(s) returned non-PDF content\n")
        f.write("# format: handle | reason | citation\n")
        for r in failed:
            f.write(f"{r['handle']} | {r['status']} | {r['citation']}\n")


def main():
    args = sys.argv[1:]
    limit = None
    only = None
    retry = set()
    while args:
        a = args.pop(0)
        if a == "--limit":
            limit = int(args.pop(0))
        elif a == "--only":
            only = set(args.pop(0).split(","))
        elif a == "--retry":
            retry = set(args.pop(0).split(","))
        else:
            sys.exit(f"unknown arg: {a}")

    os.makedirs(PAPERS, exist_ok=True)
    entries = parse_entries()
    if only:
        entries = [e for e in entries if e[0] in only]
    if limit:
        entries = entries[:limit]

    records = load_manifest()
    counts = {}
    t0 = time.time()
    done = 0
    mf = open(MANIFEST, "a", encoding="utf-8")
    try:
        for handle, citation in entries:
            done += 1
            dest = os.path.join(PAPERS, handle + ".pdf")
            prev = records.get(handle)
            skip = False
            if prev and prev["status"] == "ok" and valid_pdf_file(dest):
                skip = True
            elif not prev and valid_pdf_file(dest):
                prev = {"handle": handle, "citation": citation, "doi": None,
                        "source_url": None, "status": "ok",
                        "bytes": os.path.getsize(dest)}
                records[handle] = prev
                mf.write(json.dumps(prev) + "\n")
                mf.flush()
                skip = True
            elif prev and prev["status"] != "ok" and prev["status"] not in retry:
                skip = True

            if skip:
                rec = records[handle]
            else:
                try:
                    rec = process(handle, citation)
                except Exception as e:
                    rec = {"handle": handle, "citation": citation, "doi": None,
                           "source_url": None, "status": "fetch_failed", "bytes": 0}
                    print(f"  !! {handle}: unexpected {type(e).__name__}: {e}", flush=True)
                records[handle] = rec
                mf.write(json.dumps(rec) + "\n")
                mf.flush()
                print(f"  {rec['status']:<12} {handle}"
                      + (f" <- {rec['source_url']}" if rec["status"] == "ok" else ""),
                      flush=True)

            counts[rec["status"]] = counts.get(rec["status"], 0) + 1
            if done % 25 == 0:
                el = time.time() - t0
                print(f"[{done}/{len(entries)}] {counts}  elapsed {el/60:.1f} min", flush=True)
    finally:
        mf.close()

    write_outputs(parse_entries(), records)
    print(f"\nfinal: {counts}", flush=True)
    print(f"manifest: {MANIFEST}", flush=True)
    print(f"failed list: {FAILED}", flush=True)


if __name__ == "__main__":
    main()
