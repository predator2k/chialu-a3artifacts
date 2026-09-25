#!/usr/bin/env python3
"""Archive every opencode session a run used, next to the run.

    python3 harness/archive_sessions.py <run dir> [<run dir> ...] [--jobs 8]

A run records the id of each LLM call's opencode session (`llm_calls.jsonl`, the
plain loop's `results_db.jsonl` and `call_<k>/call.json`, skydiscover's rows) but
keeps only a text transcript; the whole session -- every message, tool call and
tool result, the reasoning, the per-step usage -- lives in opencode's own store
(`~/.local/share/opencode/opencode.db`), which is shared by every run and can be
pruned. This copies each session out with `opencode export <id>` into
`<run>/sessions/<id>.json.gz` (gzip; one file per session) and writes
`<run>/sessions/index.json` (id -> file, bytes, where it was found, or the reason
it is missing). The ids are found by scanning the run's JSON/JSONL files, so a
new recorder needs no change here. A session opencode on this host does not know
is looked up on the EDA host (`--remote`), whose store holds the calls run there.
Already archived sessions are skipped, so the command can be rerun at any time.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SID = re.compile(r"\bses_[A-Za-z0-9]{16,40}\b")
REMOTE = "<host>"
REMOTE_ENV = "source $REMOTE_HOME/chialu-home/chialu-env.sh >/dev/null 2>&1"


def session_ids(run: Path) -> set:
    ids: set = set()
    for p in list(run.rglob("*.jsonl")) + list(run.rglob("*.json")):
        if "sessions" in p.parts or p.stat().st_size > 2_000_000_000:
            continue
        try:
            with open(p, errors="replace") as f:
                for line in f:
                    ids.update(SID.findall(line))
        except OSError:
            continue
    return ids


def _complete(text: str) -> str | None:
    """The JSON document in `text`, or None when it is cut short or absent."""
    i = text.find("{")
    if i < 0:
        return None
    try:
        json.loads(text[i:])
    except ValueError:
        return None
    return text[i:]


def export(sid: str, remote: str | None, tmp: Path) -> tuple:
    """(json text or None, where, error). stdout goes to a file: opencode exits before a pipe drains and
    cuts the export at 64 KiB (the same reason chia's opencode backend captures to a file)."""
    f = tmp / f"{sid}.json.part"
    try:
        with open(f, "w") as fh:
            r = subprocess.run(["opencode", "export", sid], stdout=fh, stderr=subprocess.PIPE, text=True, timeout=300)
        text = _complete(f.read_text(errors="replace"))
        if r.returncode == 0 and text:
            return text, "local", ""
        err = (r.stderr or "")[-300:] or "export incomplete"
    except subprocess.TimeoutExpired:
        err = "timeout"
    finally:
        f.unlink(missing_ok=True)
    if remote:
        try:
            part = f"$REMOTE_HOME/chialu-home/tmp/{sid}.json.part"
            r = subprocess.run(["ssh", "-o", "BatchMode=yes", remote,
                                f"{REMOTE_ENV}; opencode export {sid} > {part}; rc=$?; cat {part}; rm -f {part}; exit $rc"],
                               capture_output=True, text=True, timeout=300)
            text = _complete(r.stdout)
            if r.returncode == 0 and text:
                return text, remote, ""
            err += " | remote: " + (r.stderr or "")[-200:]
        except subprocess.TimeoutExpired as e:
            err += f" | remote: {type(e).__name__}"
    return None, "", err.strip()


def archive(run: Path, jobs: int, remote: str | None) -> dict:
    out = run / "sessions"
    out.mkdir(exist_ok=True)
    idx_path = out / "index.json"
    index = json.loads(idx_path.read_text()) if idx_path.is_file() else {}
    todo = sorted(s for s in session_ids(run) if not (out / f"{s}.json.gz").is_file())

    tmp = Path(os.environ.get("TMPDIR") or out)

    def one(sid):
        text, where, err = export(sid, remote, tmp)
        if text is None:
            return sid, {"missing": err}
        (out / f"{sid}.json.gz").write_bytes(gzip.compress(text.encode(), 6))
        return sid, {"file": f"{sid}.json.gz", "bytes": len(text), "from": where}

    with ThreadPoolExecutor(jobs) as ex:
        for sid, rec in ex.map(one, todo):
            index[sid] = rec
    idx_path.write_text(json.dumps(index, indent=1, sort_keys=True))
    n_ok = sum(1 for v in index.values() if "file" in v)
    print(f"{run}: {len(index)} sessions, {n_ok} archived, {len(index) - n_ok} missing ({len(todo)} new this pass)",
          flush=True)
    return index


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("runs", nargs="+", type=Path)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--remote", default=REMOTE, help="EDA host to ask for sessions this host lacks ('' for none)")
    a = ap.parse_args()
    for run in a.runs:
        if run.is_dir():
            archive(run, a.jobs, a.remote or None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
