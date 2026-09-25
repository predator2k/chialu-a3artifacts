"""The evaluation graph's nodes.

The search rewrites one thing: a program that reads a binary's
disassembly and decides, per load PC, which member of the L1D ensemble
may prefetch for it, how aggressively, and which member must not see its
demand request. Everything else here measures that decision.

PF-LLM released no artifact, so its hint tables cannot be run on these
binaries and it cannot be a baseline. Two references are measured here
instead, and a candidate is read against them directly:

    baseline      no prefetching at all -- the floor, and the reference
                  the DRAM traffic of everything else is read against
    best_single   the strongest one-size-fits-all choice per workload,
                  taken from the sweep. Beating it is the whole reason
                  to decide per load PC rather than once per program.

An earlier version also assembled the sweep's per-PC argmin into a table
and called it an upper bound. It is not one: those choices are measured
in runs where a single member served every load, and composing them
changes the interference in the L1D and what every member trains on. The
first search candidate scored above it. What is reported now is what was
measured -- IPC, cycles, DRAM traffic -- against the two references.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from adir import node

from . import encoding as enc
from .runner import SimError, binary_path, geomean, run_many, run_one, trace_path

PKG_PARENT = str(Path(__file__).resolve().parents[1])


def _key(*parts) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(json.dumps(p, sort_keys=True, default=str).encode())
    return h.hexdigest()[:16]


def _work(work_dir: str, *parts) -> Path:
    d = Path(work_dir) / _key(*parts)
    d.mkdir(parents=True, exist_ok=True)
    return d


# ------------------------------------------------------------------ lint

_FORBIDDEN = [
    (r"\bimport\s+socket\b|\bimport\s+urllib\b|\bimport\s+requests\b|\bhttp[s]?://", "network access"),
    (r"\bos\.system\b|\bsubprocess\b|\beval\s*\(|\bexec\s*\(", "shelling out or evaluating code"),
    (r"\.champsim\b|trace_dir|/traces/", "reading the traces: the generator sees the binary only"),
    (r"\bipc\b|cumulative IPC|lmhint\.json|champsim\.json", "reading the measurement it is scored by"),
]
# a generator must derive its decision from the code, not carry a table of answers
_MAX_PC_LITERALS = 64
_PC_LITERAL = re.compile(r"0x4[0-9a-fA-F]{5,}")


@node(outputs=["ok", "detail", "n_pc_literals"])
def lint(source, ensemble, fields):
    """Outputs: ok, detail, n_pc_literals."""
    text = str(source)
    problems = []
    for pat, why in _FORBIDDEN:
        if re.search(pat, text):
            problems.append(why)
    n_lit = len(set(_PC_LITERAL.findall(text)))
    if n_lit > _MAX_PC_LITERALS:
        problems.append(f"{n_lit} literal PC constants: a lookup table, not an analysis")
    if "def emit_hints" not in text:
        problems.append("no emit_hints(disasm, loads, ensemble, fields)")
    return {"ok": not problems, "detail": "; ".join(problems) or "clean", "n_pc_literals": n_lit}


# --------------------------------------------------------------- hintgen

@node(outputs=["ok", "detail", "hints", "coverage", "distribution", "seconds", "deterministic"])
def hintgen(source, benchmarks, bench_dir, ensemble, fields, work_dir, timeout_s=300):
    """Outputs: ok, detail, hints, coverage, distribution, seconds, deterministic."""
    members = enc.members(ensemble)
    d = _work(work_dir, "hintgen", source, sorted(benchmarks), ensemble, fields)
    gen = d / "hintgen.py"
    gen.write_text(str(source))
    out, dist, covered, total = {}, {}, 0, 0
    t0 = time.time()
    deterministic = True
    for b in benchmarks:
        res = []
        for rep in range(2):                     # twice: the generator must be a function of the binary
            o = d / f"{b}.{rep}.json"
            p = subprocess.run([sys.executable, "-m", "pfllm.harness", str(gen),
                                binary_path(bench_dir, b), ",".join(members), fields, str(o)],
                               capture_output=True, text=True, timeout=timeout_s,
                               cwd=PKG_PARENT)
            if p.returncode != 0:
                return {"ok": False, "detail": f"{b}: {(p.stderr or p.stdout)[-400:]}",
                        "hints": "", "coverage": 0.0, "distribution": {}, "seconds": time.time() - t0,
                        "deterministic": False}
            res.append(json.loads(o.read_text()))
        if res[0]["hints"] != res[1]["hints"]:
            deterministic = False
        h = res[0]
        out[b] = h["hints"]
        total += h["n_loads"]
        covered += sum(1 for v in h["hints"].values() if v)
        for v in h["hints"].values():
            dist[v["select"]] = dist.get(v["select"], 0) + 1
    path = d / "hints.json"
    path.write_text(json.dumps(out))
    return {"ok": True, "detail": f"{covered}/{total} load PCs", "hints": str(path),
            "coverage": (covered / total) if total else 0.0, "distribution": dist,
            "seconds": time.time() - t0, "deterministic": deterministic}


# -------------------------------------------------------------- pack_pht

@node(outputs=["ok", "detail", "tables", "pht_kb_per_mb", "entries"])
def pack_pht(hints, fields, bits, bench_dir, work_dir):
    """Outputs: ok, detail, tables, pht_kb_per_mb, entries."""
    doc = json.loads(Path(str(hints)).read_text())
    d = _work(work_dir, "pack", hints, fields, bits)
    tables, total, text_mb = {}, 0, 0.0
    for b, hs in doc.items():
        # the filter field is two bits: the three most-filtered members become the side table
        counts = {}
        for v in hs.values():
            if v.get("filter"):
                counts[v["filter"]] = counts.get(v["filter"], 0) + 1
        cand = [m for m, _ in sorted(counts.items(), key=lambda kv: -kv[1])][:3]
        slot = {m: i + 1 for i, m in enumerate(cand)}
        packed = {}
        for pc, v in hs.items():
            packed[int(pc)] = enc.encode(v["select"], v.get("degree", 2),
                                         slot.get(v.get("filter") or "", 0), fields)
        blob = enc.pack(packed, cand)
        p = d / f"{b}.lmht"
        p.write_bytes(blob)
        tables[b] = str(p)
        total += sum(1 for x in packed.values() if x)
        text_mb += max(Path(binary_path(bench_dir, b)).stat().st_size, 1) / (1 << 20)
    kb = total * int(bits) / 8 / 1024
    return {"ok": True, "detail": f"{total} entries", "tables": tables,
            "pht_kb_per_mb": (kb / text_mb) if text_mb else 0.0, "entries": total}


# -------------------------------------------------------------- simulate

@node(outputs=["ok", "detail", "ipc", "cycles", "instructions", "dram_reads", "l1d_mpki",
               "pf_useless_pct", "deterministic", "dram_traffic_increase_pct", "per_pc"],
      resources={"champsim": 1},
      # per_pc is one entry per load PC: it travels to whatever reads it and stays
      # out of the archive, which would otherwise carry every entry per candidate.
      transient=["per_pc"])
def simulate(benchmark, tables, trace_dir, champsim_bin, work_dir, ensemble="full", fields="SDF",
             phb_entries=256, default_policy="none", warmup_instructions=1000000,
             simulation_instructions=3000000, repeat=1, baseline_dram=None):
    """One workload, one simulation, scalars out.

    The run file maps this over the workloads rather than passing a list,
    so each is a member with its own hash, cache entry and duration. That
    is what lets `giveup` stop waiting on the slow one: under this seed pr
    runs three times as long as bfs, and a node that took the list would
    have been one call the length of its slowest workload.

    Outputs: ok, detail, ipc, cycles, instructions, dram_reads, l1d_mpki, pf_useless_pct, deterministic, dram_traffic_increase_pct, per_pc."""
    b = str(benchmark)
    d = _work(work_dir, "sim1", b, tables, ensemble, fields, phb_entries, default_policy,
              warmup_instructions, simulation_instructions, repeat)
    jobs = [dict(champsim_bin=champsim_bin, trace=trace_path(trace_dir, b),
                 table=(tables or {}).get(b), out_dir=d, tag=f"{b}.{r}",
                 ensemble=ensemble, fields=fields, phb_entries=phb_entries,
                 default_policy=default_policy, warmup=warmup_instructions,
                 sim=simulation_instructions)
            for r in range(max(1, int(repeat)))]
    try:
        res = run_many(jobs)
    except (SimError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "detail": f"{b}: {str(e)[-300:]}", "ipc": 0.0, "cycles": 0,
                "instructions": 0, "dram_reads": 0, "l1d_mpki": 0.0, "pf_useless_pct": 0.0,
                "deterministic": False, "dram_traffic_increase_pct": 0.0, "per_pc": {}}
    vals = [r["ipc"] for r in res]
    deterministic = len(vals) < 2 or (max(vals) - min(vals) <= 1e-9)
    first = res[0]
    # against this workload's own reference; a total over a set of workloads that
    # is not the set the reference was measured on compares different programs
    ref = None
    if isinstance(baseline_dram, dict):
        ref = baseline_dram.get(b)
    elif baseline_dram:
        ref = baseline_dram
    inc = 100.0 * (first["dram_reads"] - float(ref)) / float(ref) if ref else 0.0
    return {"ok": True,
            "detail": f"{b}: ipc {first['ipc']:.4f}, {first['cycles']} cycles, "
                      f"{first['dram_reads']} dram reads",
            "ipc": first["ipc"], "cycles": first["cycles"],
            "instructions": first["instructions"], "dram_reads": first["dram_reads"],
            "l1d_mpki": 1000.0 * first["l1d_load_miss"] / max(first["instructions"], 1),
            "pf_useless_pct": 100.0 * first["pf_useless"] / max(first["pf_issued"], 1),
            "deterministic": deterministic, "dram_traffic_increase_pct": inc,
            "per_pc": first["per_pc"]}


# ----------------------------------------------------------------- sweep

@node(outputs=["ok", "detail", "misses", "ipc", "dram", "configs"],
      resources={"champsim": 1},
      transient=["misses"])   # one entry per load PC
def sweep(member, benchmark, bench_dir, trace_dir, champsim_bin, work_dir, ensemble="full",
          phb_entries=256, warmup_instructions=1000000, simulation_instructions=3000000):
    """The ground truth for one (ensemble member, workload) cell.

    The run file maps this over the product of the two rather than over
    the members alone: a cell is then one workload's three degree levels
    instead of every workload's, which both fills the executor at the
    tail and gives each cell its own cache entry. For each of the
    member's degree levels a uniform table names it for every load PC of
    that binary, and the run records each PC's L1D demand misses. The
    per-PC argmin over every cell of a workload is what a perfect static
    hint table would ask for; `best_single` is what one member alone can
    do.

    Outputs: ok, detail, misses, ipc, dram, configs."""
    from .harness import build_inputs
    b = str(benchmark)
    levels = [1] if member == "none" else [1, 2, 3]
    d = _work(work_dir, "sweep1", member, b, ensemble, phb_entries,
              warmup_instructions, simulation_instructions)
    _, loads = build_inputs(binary_path(bench_dir, b), context_lines=0)
    tables = {}
    for lv in levels:
        packed = {r["pc"]: enc.encode(member, lv, 0, "SD") for r in loads}
        pth = d / f"{b}.{member}.{lv}.lmht"
        pth.write_bytes(enc.pack(packed, []))
        tables[lv] = str(pth)
    jobs = [dict(champsim_bin=champsim_bin, trace=trace_path(trace_dir, b), table=tables[lv],
                 out_dir=d, tag=f"{b}.{member}.{lv}", ensemble=ensemble, fields="SD",
                 phb_entries=phb_entries, default_policy="none", warmup=warmup_instructions,
                 sim=simulation_instructions)
            for lv in levels]
    try:
        res = run_many(jobs)
    except (SimError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "detail": f"{member}/{b}: {str(e)[-300:]}", "misses": {},
                "ipc": {}, "dram": {}, "configs": []}
    misses, ipc, dram = {}, {}, {}
    for lv, r in zip(levels, res):
        cfg = f"{member}:{lv}"
        ipc[cfg] = r["ipc"]
        dram[cfg] = r["dram_reads"]
        for pc, (_acc, ms) in r["per_pc"].items():
            misses.setdefault(str(pc), {})[cfg] = ms
    return {"ok": True, "detail": f"{member}/{b}: {len(jobs)} runs", "misses": {b: misses},
            "ipc": {b: ipc}, "dram": {b: dram}, "configs": [f"{member}:{lv}" for lv in levels]}


def _merge(mapped: dict) -> dict:
    """A mapped node's output arrives keyed by its member -- here
    `<member>.<workload>` -- and each cell already carries the workload
    it measured, so folding them together rebuilds the whole table."""
    out = {}
    for _cell, per_bench in (mapped or {}).items():
        for b, rows in (per_bench or {}).items():
            dst = out.setdefault(b, {})
            for k, v in rows.items():
                if isinstance(v, dict):
                    dst.setdefault(k, {}).update(v)
                else:
                    dst[k] = v
    return out


# ---------------------------------------------------------- best_single

@node(outputs=["ok", "detail", "ipc", "ipc_geomean", "dram", "choice"])
def best_single(ipc, dram):
    """The strongest one-size-fits-all choice: per workload, the best
    (member, degree) run of the sweep, and the DRAM traffic that choice
    cost. Beating this is the whole reason to decide per load PC rather
    than once per program, and its traffic is the budget a candidate is
    read against -- against the no-prefetch baseline every prefetcher
    looks profligate, because fetching early is what a prefetcher does.

    The traffic is per workload, not a total: the sweep covers every
    workload and a candidate is scored on a subset, so summed totals
    would compare different sets of programs.

    Outputs: ok, detail, ipc, ipc_geomean, dram, choice."""
    per_ipc, per_dram = _merge(ipc), _merge(dram)
    best, choice, reads = {}, {}, {}
    for b, cfgs in per_ipc.items():
        if not cfgs:
            continue
        c = max(cfgs, key=lambda k: cfgs[k])
        best[b] = cfgs[c]
        choice[b] = c
        reads[b] = int((per_dram.get(b) or {}).get(c, 0))
    return {"ok": True, "detail": json.dumps(choice), "ipc": best,
            "ipc_geomean": geomean(best.values()), "dram": reads, "choice": choice}


# ----------------------------------------------------------- state_bytes

@node(outputs=["ok", "detail", "bytes"])
def state_bytes(phb_entries, hint_bits, ensemble):
    """The on-chip cost the candidate's declaration implies: the hint
    buffer, its tags, and the filter-candidate side table. The ensemble
    members themselves are the paper's and are not counted."""
    tag_bits = 48                      # a 48-bit virtual PC, as in the paper
    per_entry = (tag_bits + int(hint_bits) + 1 + 7) // 8
    total = int(phb_entries) * per_entry + 3 + 16
    return {"ok": True, "bytes": total,
            "detail": f"{phb_entries} x {per_entry}B + 19B (filter table, reserved entry)"}
