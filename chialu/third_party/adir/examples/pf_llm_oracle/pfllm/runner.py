"""Running ChampSim with a hint table, and reading what comes back.

One binary serves every configuration: the ensemble, the applied hint
fields, the buffer size and the reserved policy are read from the
environment by the lmhint module, and a sub-prefetcher run is simply a
table that names that member for every load PC. So the sweep, the
oracle and every candidate differ only in the table -- no rebuild.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# ChampSim runs are the whole cost of this task, so a run whose output is
# already on disk is never repeated. The directory name is a hash of the
# configuration, so a file being there means that exact run finished.
DEFAULT_WORKERS = int(os.environ.get("PFLLM_WORKERS", "8"))

# One simulation holds one slot for as long as its process runs. The bound has to
# be here rather than in the pool `run_many` opens, because a mapped node calls
# this from every member at once: seven members each opening a pool of
# PFLLM_WORKERS would put seven times that many ChampSim processes on a machine
# other people are using. Reused results take no slot -- they are a file read.
_SLOTS = threading.BoundedSemaphore(DEFAULT_WORKERS)

# A simulation's cost is set by how much the hint table asks for, not by the
# trace: the seed prefetches for every load PC and issues 24M prefetches over
# 60M instructions, which is three to four times the work of the same trace
# with prefetching off. The hour this defaulted to was measured with it off.
TIMEOUT_S = int(os.environ.get("PFLLM_SIM_TIMEOUT", "21600"))


class SimError(RuntimeError):
    pass


def run_one(champsim_bin: str, trace: str, table: str | None, out_dir: Path, tag: str,
            ensemble: str = "full", fields: str = "SDF", phb_entries: int = 256,
            default_policy: str = "none", warmup: int = 1000000, sim: int = 3000000,
            timeout: int = 0) -> dict:
    """One simulation. Returns the ROI metrics plus the module's sidecar."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cs_json = out_dir / f"{tag}.champsim.json"
    st_json = out_dir / f"{tag}.lmhint.json"
    if cs_json.is_file() and st_json.is_file():
        try:
            return _read(cs_json, st_json)
        except (ValueError, KeyError, OSError):
            pass                       # a truncated result from an interrupted run
    env = dict(os.environ)
    env.update({"LMHINT_ENSEMBLE": ensemble, "LMHINT_FIELDS": fields,
                "LMHINT_PHB_ENTRIES": str(int(phb_entries)),
                "LMHINT_DEFAULT": default_policy,
                "LMHINT_STATS": str(st_json),
                "LMHINT_TABLE": str(table) if table else ""})
    cmd = [champsim_bin, "--warmup-instructions", str(int(warmup)),
           "--simulation-instructions", str(int(sim)), "--hide-heartbeat",
           "--json", str(cs_json), trace]
    with _SLOTS:
        p = subprocess.run(cmd, capture_output=True, text=True, env=env,
                           timeout=timeout or TIMEOUT_S)
    if p.returncode != 0 or not cs_json.is_file():
        raise SimError(f"champsim rc={p.returncode}: {(p.stderr or p.stdout)[-400:]}")
    return _read(cs_json, st_json)


def _read(cs_json: Path, st_json: Path) -> dict:
    doc = json.loads(cs_json.read_text())
    roi = (doc[0] if isinstance(doc, list) else doc)["roi"]
    core = roi["cores"][0]
    l1d = roi["cpu0_L1D"]
    load = l1d["LOAD"]
    dram = roi.get("DRAM") or []
    reads = sum(int(d.get("RQ ROW_BUFFER_HIT", 0)) + int(d.get("RQ ROW_BUFFER_MISS", 0)) for d in dram)
    side = json.loads(st_json.read_text()) if st_json.is_file() else {}
    cycles = max(1, int(core["cycles"]))
    return {"ipc": int(core["instructions"]) / cycles,
            "instructions": int(core["instructions"]), "cycles": cycles,
            "l1d_load_hit": int(sum(load["hit"])), "l1d_load_miss": int(sum(load["miss"])),
            "pf_issued": int(l1d.get("prefetch issued", 0)),
            "pf_useful": int(l1d.get("useful prefetch", 0)),
            "pf_useless": int(l1d.get("useless prefetch", 0)),
            "dram_reads": reads,
            "per_pc": {int(k): v for k, v in (side.get("per_pc") or {}).items()},
            "per_member": side.get("per_member") or {},
            "phb_hit": side.get("phb_hit", 0), "phb_miss": side.get("phb_miss", 0),
            "pht_entries": side.get("pht_entries", 0)}


def run_many(jobs: list, workers: int = 0) -> list:
    """`jobs` are kwargs dicts for run_one; ChampSim is a subprocess, so
    threads are enough to use several cores."""
    with ThreadPoolExecutor(max_workers=max(1, workers or DEFAULT_WORKERS)) as ex:
        futs = [ex.submit(run_one, **j) for j in jobs]
        return [f.result() for f in futs]


def geomean(xs) -> float:
    vals = [float(v) for v in xs if v and float(v) > 0]
    if not vals:
        return 0.0
    return math.exp(sum(math.log(v) for v in vals) / len(vals))


def trace_path(trace_dir: str, benchmark: str) -> str:
    for ext in (".champsim", ".champsim.xz", ".champsim.gz"):
        p = Path(trace_dir) / f"{benchmark}{ext}"
        if p.is_file():
            return str(p)
    raise SimError(f"no trace for {benchmark} under {trace_dir}")


def binary_path(bench_dir: str, benchmark: str) -> str:
    p = Path(bench_dir) / benchmark
    if not p.is_file():
        raise SimError(f"no binary for {benchmark} under {bench_dir}")
    return str(p)
