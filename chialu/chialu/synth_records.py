"""Lossless synthesis receipts and replay, independent of any results database.

Large inputs and logs live in a content-addressed gzip store; small receipts travel
with every measurement. Copy the store with an archive (or set --artifacts on replay)
so paths remain resolvable after moving it. Hashes cover uncompressed bytes.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import statistics
import tempfile
import time
from functools import lru_cache
from pathlib import Path

VERSION = "median-per-metric-v1"
FIELDS = ("repeats", "seeds", "runs", "statistics", "median_rule", "successful_runs",
          "cells_run_index", "report_run")


def seeds_for(repeats=5, seeds=None):
    """The first mapping is unchanged; subsequent fixed seeds perturb after strash."""
    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats < 1:
        raise ValueError("repeats must be a positive integer")
    values = list(seeds) if seeds is not None else [11, 23, 37, 53][:repeats - 1]
    if seeds is None and repeats > 5:
        values += [53 + 16 * i for i in range(1, repeats - 4)]
    if len(values) != repeats - 1 or any(type(s) is not int or s < 0 for s in values):
        raise ValueError("seeds must contain repeats - 1 nonnegative integers")
    if len(set(values)) != len(values):
        raise ValueError("permutation seeds must be distinct")
    return [None, *values]


def root():
    return Path(os.environ.get("CHIALU_SYNTH_RECORDS") or
                Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / "chialu/synth_records")


def put(data):
    data = data.encode() if isinstance(data, str) else data
    digest = hashlib.sha256(data).hexdigest()
    base = root().resolve()
    base.mkdir(parents=True, exist_ok=True)
    path = base / (digest + ".gz")
    if not path.exists():
        # Atomic replacement permits independent workers to archive an identical input.
        with tempfile.NamedTemporaryFile(dir=base, delete=False) as f:
            f.write(gzip.compress(data, mtime=0))
            tmp = f.name
        os.replace(tmp, path)
    return {"sha256": digest, "path": str(path), "encoding": "gzip"}


def get(ref, artifacts=None):
    path = Path(artifacts) / (ref["sha256"] + ".gz") if artifacts else Path(ref["path"])
    data = gzip.decompress(path.read_bytes())
    if hashlib.sha256(data).hexdigest() != ref["sha256"]:
        raise ValueError(f"artifact hash mismatch: {path}")
    return data


@lru_cache(maxsize=16)
def executable_hash(name, path, size, mtime):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tools_identity():
    from chialu.synthdb import tool_versions
    files = {}
    for name in ("yosys", "yosys-abc"):
        path = shutil.which(name)
        if path:
            st = Path(path).stat()
            files[name] = executable_hash(name, path, st.st_size, st.st_mtime_ns)
    return {"versions": tool_versions(), "executables": files}


def trace(result):
    """Keep the complete receipt when a consumer renames area or delay fields."""
    return {k: result[k] for k in FIELDS if k in result}


def aggregate(runs, seconds):
    """Require every run to succeed: a failed five-run call has no fitness median.

    Partial statistics are diagnostic only, preventing a timeout from selecting a
    lucky subset. Cells come from the successful run nearest median area (ties by
    index), since separate metric medians need not describe one physical netlist.
    """
    good = [r for r in runs if r.get("ok") and r.get("area_um2") is not None
            and r.get("abc_delay_ps") is not None]
    complete = len(good) == len(runs)
    stats = {}
    for metric in ("area_um2", "abc_delay_ps", "cells"):
        values = [r[metric] for r in good if r.get(metric) is not None]
        stats[metric] = {"median": statistics.median(values), "min": min(values), "max": max(values),
                         "std": statistics.pstdev(values)} if values else {}
    representative = min(good, key=lambda r: (abs(r["area_um2"] - stats["area_um2"]["median"]),
                                              r["repeat_index"])) if good else None
    return {"ok": complete, "area_um2": stats["area_um2"].get("median") if complete else None,
            "abc_delay_ps": stats["abc_delay_ps"].get("median") if complete else None,
            "cells": representative.get("cells") if complete else None,
            "cells_run_index": representative["repeat_index"] if complete else None,
            "seconds": round(seconds, 3), "repeats": len(runs), "seeds": [r["abc_seed"] for r in runs],
            "runs": runs, "successful_runs": len(good), "statistics": stats,
            "median_rule": "all_requested_runs_must_succeed; partial_statistics_are_diagnostic_only",
            "pdk": runs[0].get("pdk"), "clock_ps": runs[0].get("clock_ps"),
            "detail": "" if complete else "; ".join(f"run {r['repeat_index']}: {r.get('detail', r['status'])}"
                                                        for r in runs if r not in good)}


def replay(record, artifacts=None):
    """Replay the recorded mapping input and script; reject tool/library drift first."""
    from chialu import eda
    identity = tools_identity()
    if identity != record["tools"]:
        raise ValueError("tool identity differs from the recorded run")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        rtl = td / "cand.sv"
        rtl.write_bytes(get(record["rtl"], artifacts))
        libs = []
        for i, ref in enumerate(record["liberties"]):
            p = td / f"lib{i}.lib"
            p.write_bytes(get(ref, artifacts))
            libs.append(str(p))
        netlist = None
        if record["mapping_input"] == "rtlil":
            netlist = td / "pre.il"
            netlist.write_bytes(get(record["netlist"], artifacts))
        pdk = dict(record["pdk_descriptor"], liberty=libs)
        result = eda._synth_mapped(rtl, record["top"], pdk, record["clock_ps"], record["timeout_s"],
                                   record["effort"], record["share"], time.time(),
                                   hierarchy=record.get("hierarchy", False),
                                   abc_script_override=record["abc_script"], pre_netlist=netlist,
                                   keep_scopeinfo=record.get("keep_scopeinfo", False),
                                   repeat_index=record["repeat_index"], abc_seed=record["abc_seed"])
    fields = ("status", "area_um2", "abc_delay_ps", "cells")
    return {"matches": all(result.get(k) == record.get(k) for k in fields),
            "expected": {k: record.get(k) for k in fields},
            "actual": {k: result.get(k) for k in fields},
            "replay_record": put(json.dumps(result, sort_keys=True)), "run": result}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Replay one synthesis run and compare exact parsed numbers")
    ap.add_argument("record", type=Path, help="a run receipt or a synth_ppa result JSON")
    ap.add_argument("--run", type=int, default=0)
    ap.add_argument("--measurement", default="repeats5", help="measurement in a baseline wrapper (default repeats5)")
    ap.add_argument("--artifacts", type=Path, help="relocated content-addressed artifact directory")
    a = ap.parse_args(argv)
    record = json.loads(a.record.read_text())
    if a.measurement in record:
        record = record[a.measurement]
    result = replay(record["runs"][a.run] if "runs" in record else record, a.artifacts)
    print(json.dumps({k: v for k, v in result.items() if k != "run"}, indent=2))
    return 0 if result["matches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
