"""chiacache's CHIA nodes: the static ISA check, the build, the
conformance run against the reference, and the cache simulation of
every shape under valgrind's cachegrind with the configured L1 and L2."""
from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from adir import node

FORBIDDEN = (r"\basm\b", r"__asm__", r"#\s*include\s*<[xe]?mmintrin\.h>", r"#\s*include\s*<immintrin\.h>",
             r"#\s*pragma\s+omp", r"__builtin_ia32", r"_mm\d*_", r"#\s*include\s*<omp\.h>")


@node(outputs=["ok", "detail"])
def isa_check(source, ext: str) -> dict:
    """The kernels use only what the extension admits: under plain_c, no
    inline assembly, no vector intrinsics, no OpenMP."""
    texts = source.values() if isinstance(source, dict) else [str(source)]
    hits = []
    for t in texts:
        for pat in FORBIDDEN:
            m = re.search(pat, t)
            if m:
                hits.append(m.group(0))
    if ext != "plain_c":
        return {"ok": False, "detail": f"unknown extension {ext}"}
    return {"ok": not hits, "detail": "" if not hits else "not admitted under plain_c: " + ", ".join(sorted(set(hits)))}


@node(outputs=["ok", "binary", "detail", "seconds"], resources={"build": 1}, transient=["binary"])
def build(source: str, reference: str, timeout_s: int = 120) -> dict:
    """gcc -O2 of the candidate (the kernels and the harness) with the
    reference; the binary comes back base64-encoded."""
    t0 = time.time()
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "all.c"
        src.write_text(source + "\n" + reference + "\n")
        out = Path(td) / "gemm"
        try:
            r = subprocess.run(["gcc", "-O2", "-std=c11", "-fno-tree-vectorize", "-o", str(out), str(src), "-lm"],
                               capture_output=True, text=True, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            return {"ok": False, "detail": "gcc timeout", "seconds": round(time.time() - t0, 1)}
        if r.returncode != 0:
            return {"ok": False, "detail": r.stderr[-3000:], "seconds": round(time.time() - t0, 1)}
        data = out.read_bytes()
    return {"ok": True, "binary": base64.b64encode(data).decode(), "detail": "",
            "seconds": round(time.time() - t0, 1)}


def _binary(binary: str, td: str) -> Path:
    p = Path(td) / "gemm"
    p.write_bytes(base64.b64decode(binary))
    p.chmod(0o755)
    return p


def _shapes(shapes) -> list:
    data = json.loads(shapes) if isinstance(shapes, str) else shapes
    return list(data)


@node(outputs=["pass", "detail", "mismatches", "seconds"])
def conformance(binary: str, shapes, trials: int = 3, timeout_s: int = 300) -> dict:
    """Every shape, `trials` random operand sets each, against the
    reference inside the harness."""
    t0 = time.time()
    mism, lines = [], []
    with tempfile.TemporaryDirectory() as td:
        exe = _binary(binary, td)
        for s in _shapes(shapes):
            for t in range(int(trials)):
                cmd = [str(exe), s["member"], str(s["M"]), str(s["N"]), str(s["K"]), "check", str(t + 1)]
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
                except subprocess.TimeoutExpired:
                    mism.append(f"{s['member']} {s['M']}x{s['N']}x{s['K']}: timeout")
                    continue
                if r.returncode != 0:
                    mism.append(f"{s['member']} {s['M']}x{s['N']}x{s['K']} trial {t + 1}: "
                                f"{(r.stdout + r.stderr).strip()[-200:]}")
                elif t == 0:
                    lines.append(f"{s['member']} {s['M']}x{s['N']}x{s['K']}: {r.stdout.strip()}")
    return {"pass": not mism, "mismatches": mism,
            "detail": "\n".join(mism) if mism else "every shape matches the reference\n" + "\n".join(lines),
            "seconds": round(time.time() - t0, 1)}


def _parse_summary(text: str) -> dict:
    """cachegrind's `events:` and `summary:` lines as a dict."""
    ev = re.search(r"^events:\s*(.*)$", text, re.M)
    sm = re.search(r"^summary:\s*(.*)$", text, re.M)
    if not ev or not sm:
        return {}
    names = ev.group(1).split()
    vals = [int(x) for x in sm.group(1).split()]
    return dict(zip(names, vals))


L1_HIT, L1_MISS, LL_MISS = 1, 5, 60


@node(outputs=["ok", "cycles", "stats", "detail", "seconds"], resources={"sim": 1})
def cachesim(binary: str, shapes, l2_size_kb: int, l2_ways: int, line_bytes: int = 64,
             l1_size_kb: int = 32, timeout_s: int = 900) -> dict:
    """Every shape under cachegrind with the configured L1 (8-way) and
    L2 as the last level. cycles per shape follow a stated model: one
    per instruction, 5 per first-level data miss, 60 per last-level
    miss. `stats` is the per-shape breakdown."""
    t0 = time.time()
    if shutil.which("valgrind") is None:
        return {"ok": False, "detail": "valgrind is not installed", "seconds": 0.0}
    cycles, rows = {}, []
    with tempfile.TemporaryDirectory() as td:
        exe = _binary(binary, td)
        for s in _shapes(shapes):
            key = f"{s['member']}:{s['M']}x{s['N']}x{s['K']}"
            outf = Path(td) / "cg.out"
            cmd = ["valgrind", "--tool=cachegrind", "--cache-sim=yes",
                   f"--I1={l1_size_kb * 1024},8,{line_bytes}", f"--D1={l1_size_kb * 1024},8,{line_bytes}",
                   f"--LL={int(l2_size_kb) * 1024},{int(l2_ways)},{line_bytes}",
                   f"--cachegrind-out-file={outf}", str(exe), s["member"], str(s["M"]), str(s["N"]),
                   str(s["K"]), "run", "1"]
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, cwd=td)
            except subprocess.TimeoutExpired:
                return {"ok": False, "detail": f"{key}: cachegrind timeout", "seconds": round(time.time() - t0, 1)}
            if r.returncode != 0 or not outf.is_file():
                return {"ok": False, "detail": f"{key}: {r.stderr[-800:]}", "seconds": round(time.time() - t0, 1)}
            c = _parse_summary(outf.read_text())
            if not c:
                return {"ok": False, "detail": f"{key}: no cachegrind summary", "seconds": round(time.time() - t0, 1)}
            d1 = c.get("D1mr", 0) + c.get("D1mw", 0)
            ll = c.get("DLmr", 0) + c.get("DLmw", 0)
            cyc = L1_HIT * c.get("Ir", 0) + L1_MISS * d1 + LL_MISS * ll
            cycles[key] = int(cyc)
            rows.append(f"{key}: Ir {c.get('Ir', 0):,}, D1 misses {d1:,}, LL misses {ll:,}, cycles {int(cyc):,}")
    return {"ok": True, "cycles": cycles, "stats": "\n".join(rows), "detail": "",
            "seconds": round(time.time() - t0, 1)}
