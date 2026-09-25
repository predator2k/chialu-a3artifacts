"""cacheflex's CHIA nodes over the artifact checkout (`root`): the
cross-build of the QEMU mock binary and the gem5 SPM binary (the
artifact's three-step build through spm_compiler.py), the QEMU check
of the loop nest against a naive reference, and one gem5 cell with the
artifact's canonical flag block."""
from __future__ import annotations

import base64
import re
import subprocess
import tempfile
import time
from pathlib import Path

from adir import node
from cacheflex.domain import WORKLOADS

GEM5_BASE = [
    "--cpu-type=DerivO3CPU", "--sys-clock=1.5GHz", "--cpu-clock=2.5GHz",
    "--caches", "--l2cache", "--l3cache",
    "--l1d_size=64kB", "--l1i_size=64kB", "--l1d_assoc=4", "--l1i_assoc=4",
    "--l2_size=512kB", "--l2_assoc=8", "--l3_size=4MB", "--l3_assoc=16",
    "--cacheline_size=64", "--mem-size=16GB", "--mem-channels=2", "--mem-type=DDR4_2400_8x8",
    "--l1i-hwp-type=StridePrefetcher", "--l1d-hwp-type=StridePrefetcher",
    "--l2-hwp-type=AMPMPrefetcher", "--l3-hwp-type=BOPPrefetcher",
    "-P", "system.cpu[0].icache.prefetcher.degree=4", "-P", "system.cpu[0].dcache.prefetcher.degree=4",
    "-P", "system.cpu[0].icache.tag_latency=2", "-P", "system.cpu[0].icache.data_latency=2",
    "-P", "system.cpu[0].fetchWidth=5", "-P", "system.cpu[0].decodeWidth=5",
    "-P", "system.cpu[0].commitWidth=5", "-P", "system.cpu[0].renameWidth=5",
    "-P", "system.cpu[0].dispatchWidth=8", "-P", "system.cpu[0].issueWidth=8", "-P", "system.cpu[0].wbWidth=8",
    "-P", "system.cpu[0].numROBEntries=128", "-P", "system.cpu[0].numIQEntries=80",
    "-P", "system.cpu[0].LQEntries=32", "-P", "system.cpu[0].SQEntries=48",
    "-P", "system.cpu[0].numPhysIntRegs=128", "-P", "system.cpu[0].numPhysFloatRegs=192",
    "-P", "system.cpu[0].numPhysVecRegs=192", "-P", "system.cpu[0].numPhysVecPredRegs=64",
    "-P", "system.cpu[0].cacheLoadPorts=2", "-P", "system.cpu[0].cacheStorePorts=1",
    "-P", "system.cpu[0].fuPool.FUList[0].count=2", "-P", "system.cpu[0].fuPool.FUList[2].count=2",
    "-P", "system.cpu[0].fuPool.FUList[5].count=2", "-P", "system.cpu[0].fuPool.FUList[7].count=2",
    "-P", "system.cpu[0].fuPool.FUList[9].count=2",
    "-P", "system.tol2bus.frontend_latency=1", "-P", "system.tol2bus.header_latency=0",
    "-P", "system.tol2bus.forward_latency=1", "-P", "system.tol2bus.response_latency=1",
    "-P", "system.tol2bus.width=64",
    "-P", "system.l2.tag_latency=8", "-P", "system.l2.data_latency=8", "-P", "system.l2.response_latency=8",
    "-P", "system.tol3bus.width=32", "-P", "system.tol3bus.frontend_latency=10",
    "-P", "system.tol3bus.forward_latency=10", "-P", "system.tol3bus.response_latency=10",
    "-P", "system.l3.tag_latency=35", "-P", "system.l3.data_latency=35", "-P", "system.l3.response_latency=35",
]
SPM_PORTS = {4: (2, 1), 8: (2, 1), 16: (1, 1)}
CPU_HZ = 2.5e9
STATS_BEGIN = "---------- Begin Simulation Statistics"
STATS_END = "---------- End Simulation Statistics"


class Env:
    def __init__(self, root: str):
        self.root = Path(root).expanduser()
        tc = self.root / "tools" / "arm-gnu-toolchain-15.2.rel1-x86_64-aarch64-none-linux-gnu" / "bin"
        self.cxx = tc / "aarch64-none-linux-gnu-g++"
        self.qemu = self.root / "tools" / "usr" / "bin" / "qemu-aarch64-static"
        self.gem5 = self.root / "gem5" / "build" / "ARM" / "gem5.opt"
        self.se = self.root / "gem5" / "configs" / "deprecated" / "example" / "se.py"
        self.spm_compiler = self.root / "spm_tools" / "spm_compiler.py"
        self.m5op = self.root / "gem5" / "util" / "m5" / "build" / "arm64" / "out" / "m5op.o"
        self.includes = [f"-I{self.root / 'kernels' / 'llama_bench_spm'}", f"-I{self.root / 'kernels' / 'llama_bench'}",
                         f"-I{self.root / 'kernels' / 'gemm' / 'cacheflex' / 'src'}", f"-I{self.root / 'gem5' / 'include'}"]

    def missing(self, gem5: bool) -> list:
        need = [self.cxx, self.spm_compiler] + ([self.gem5, self.se, self.m5op] if gem5 else [self.qemu])
        return [str(p) for p in need if not p.exists()]


def _run(cmd, cwd, timeout_s):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, cwd=cwd)


@node(outputs=["ok", "binary_gem5", "binary_mock", "detail", "seconds"], resources={"cf_build": 1},
      transient=["binary_gem5", "binary_mock"])
def build(source: str, root: str, vl: int, timeout_s: int = 900) -> dict:
    """Two binaries from the candidate (the loop nest and the harness):
    the QEMU mock (`-DMOCK_SPM -DVERIFY`, the cache microkernel in place
    of the SPM one) and the gem5 SPM binary through the artifact's three
    steps (C++ to assembly, the SPM encoder, the link with m5op)."""
    t0 = time.time()
    env = Env(root)
    miss = env.missing(gem5=True) + env.missing(gem5=False)
    if miss:
        return {"ok": False, "detail": "artifact parts missing: " + ", ".join(sorted(set(miss))), "seconds": 0.0}
    flags = ["-O3", "-std=c++17", "-march=armv8.2-a+sve+fp16", f"-DVL_{int(vl)}"] + env.includes
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "cand.cpp"
        src.write_text(source)
        try:
            r = _run([str(env.cxx), *flags, "-static", "-DMOCK_SPM", "-DVERIFY", str(src), "-lm", "-o", "mock"],
                     td, timeout_s)
            if r.returncode != 0:
                return {"ok": False, "detail": "mock build: " + r.stderr[-3000:], "seconds": round(time.time() - t0, 1)}
            r = _run([str(env.cxx), *flags, "-mbranch-protection=none", "-DGEM5", "-DGEM5_SE", "-S", "-o", "cand.s", str(src)],
                     td, timeout_s)
            if r.returncode != 0:
                return {"ok": False, "detail": "spm build (asm): " + r.stderr[-3000:], "seconds": round(time.time() - t0, 1)}
            r = _run(["python3", str(env.spm_compiler), "cand.s", "cand_enc.s"], td, timeout_s)
            if r.returncode != 0:
                return {"ok": False, "detail": "spm encoder: " + (r.stderr or r.stdout)[-3000:], "seconds": round(time.time() - t0, 1)}
            r = _run([str(env.cxx), "-static", "-o", "spm", "cand_enc.s", str(env.m5op), "-lm"], td, timeout_s)
            if r.returncode != 0:
                return {"ok": False, "detail": "spm link: " + r.stderr[-3000:], "seconds": round(time.time() - t0, 1)}
        except subprocess.TimeoutExpired:
            return {"ok": False, "detail": "build timeout", "seconds": round(time.time() - t0, 1)}
        mock = (Path(td) / "mock").read_bytes()
        spm = (Path(td) / "spm").read_bytes()
    return {"ok": True, "binary_gem5": base64.b64encode(spm).decode(), "binary_mock": base64.b64encode(mock).decode(),
            "detail": "", "seconds": round(time.time() - t0, 1)}


def _exe(binary: str, td: str, name: str) -> Path:
    p = Path(td) / name
    p.write_bytes(base64.b64decode(binary))
    p.chmod(0o755)
    return p


def _checksum(text: str):
    m = re.search(r"CHECKSUM_LOGICAL:\s*([-+0-9.eE]+)", text)
    return float(m.group(1)) if m else None


def _verdict(text: str):
    """(ok, maxerr) of the harness's VERIFY compare, or (None, None)
    where it did not run (the binary refused the shape before it)."""
    m = re.search(r"VERIFY (OK|MISMATCH) maxerr=([-+0-9.eE]+)", text)
    return (m.group(1) == "OK", float(m.group(2))) if m else (None, None)


@node(outputs=["pass", "detail", "checksum", "maxerr", "seconds"], resources={"cf_sim": 1})
def verify(binary_mock: str, root: str, vl: int, workload: str, kc: int, mc: int,
           timeout_s: int = 1800) -> dict:
    """The mock binary under QEMU at the SVE length of `vl`, twice: a
    reduced shape (M/4, K, N/4, rounded to the tiles) whose tiles are
    clamped to it, then the workload's shape at the declared KC and MC
    for the checksum the gem5 cell must reproduce. The mock carries
    `-DVERIFY`, so each run compares against a naive reference and both
    verdicts decide the node: the reduced shape is the cheap screen, the
    workload shape is the one that exercises the declared tiles."""
    t0 = time.time()
    env = Env(root)
    miss = env.missing(gem5=False)
    if miss:
        return {"pass": None, "detail": "artifact parts missing: " + ", ".join(miss), "seconds": 0.0}
    m, k, n = WORKLOADS[str(workload)]
    nt = 3 * int(vl) * 8
    small = (max(8, (int(m) // 4) // 8 * 8), int(k), max(nt, (int(n) // 4) // nt * nt))
    kc_small = min(int(kc), small[1])
    mc_small = min(int(mc), small[0])
    with tempfile.TemporaryDirectory() as td:
        exe = _exe(binary_mock, td, "mock")
        cpu = f"max,sve-default-vector-length={int(vl) * 16}"
        try:
            r = _run([str(env.qemu), "-cpu", cpu, str(exe), str(small[0]), str(small[1]), str(small[2]), "1",
                      str(kc_small), str(mc_small)], td, timeout_s)
        except subprocess.TimeoutExpired:
            return {"pass": None, "detail": "QEMU timeout on the reduced shape", "seconds": round(time.time() - t0, 1)}
        out = r.stdout + r.stderr
        ok, maxerr = _verdict(out)
        if not ok:
            return {"pass": False, "detail": f"reduced shape {small} KC={kc_small} MC={mc_small}: " + out[-1500:],
                    "maxerr": maxerr, "seconds": round(time.time() - t0, 1)}
        try:
            r = _run([str(env.qemu), "-cpu", cpu, str(exe), str(m), str(k), str(n), "1", str(kc), str(mc)], td, timeout_s)
        except subprocess.TimeoutExpired:
            return {"pass": None, "detail": "QEMU timeout on the workload shape", "seconds": round(time.time() - t0, 1)}
        out2 = r.stdout + r.stderr
    # the workload shape at the declared tiles: its own VERIFY verdict, not the reduced
    # one, is what says the nest is right where the gem5 cell will measure it. A binary
    # that refused the shape (KC over the SPM cap) exits before the compare and leaves
    # no verdict, which is a failure here too.
    ok2, maxerr2 = _verdict(out2)
    cs = _checksum(out2)
    if not ok2 or cs is None:
        why = "the reference compare did not run" if ok2 is None else \
              (f"mismatch against the reference (maxerr {maxerr2:g})" if not ok2 else "no checksum")
        return {"pass": False, "detail": f"workload shape {(m, k, n)} KC={kc} MC={mc}: {why}: " + out2[-1500:],
                "maxerr": maxerr2 if maxerr2 is not None else maxerr,
                "seconds": round(time.time() - t0, 1)}
    return {"pass": True, "detail": f"reduced shape {small} and workload shape {(m, k, n)} at KC={kc} MC={mc} "
                                    f"both match the reference (maxerr {maxerr:g}, {maxerr2:g}); "
                                    f"workload checksum {cs:.10g}", "checksum": cs, "maxerr": maxerr2,
            "seconds": round(time.time() - t0, 1)}


def _roi(stats: str) -> dict:
    parts = stats.split(STATS_BEGIN)
    if len(parts) < 2:
        return {}
    roi = parts[1].split(STATS_END, 1)[0]
    out = {}
    for name in ("simTicks", "simFreq", "system.l2.spmReads", "system.l2.spmWrites",
                 "system.cpu.numCycles", "system.cpu.dcache.overallMisses::total",
                 "system.l2.overallMisses::total", "system.cpu.ipc"):
        m = re.search(rf"^{re.escape(name)}\s+(\S+)", roi, re.M)
        if m:
            try:
                out[name] = float(m.group(1))
            except ValueError:
                pass
    return out


@node(outputs=["ok", "cycles", "spm_reads", "checksum", "checksum_match", "stats", "detail", "seconds"],
      resources={"cf_sim": 1})
def gem5_cell(binary_gem5: str, root: str, vl: int, workload: str, kc: int, mc: int,
              mock_checksum=None, timeout_s: int = 7200) -> dict:
    """One cell on the artifact's gem5 fork with its canonical flag block
    and the VL's SPM ports: cycles at 2.5 GHz over the ROI, the SPM
    reads, the checksum against the mock's."""
    t0 = time.time()
    env = Env(root)
    miss = env.missing(gem5=True)
    if miss:
        return {"ok": False, "detail": "artifact parts missing: " + ", ".join(miss), "seconds": 0.0}
    lp, sp = SPM_PORTS[int(vl)]
    m, k, n = WORKLOADS[str(workload)]
    # `map_over` hands a node the member it maps and every other input whole, so a
    # `verify` mapped over the same workloads arrives here as the whole mapping;
    # this cell is one member of it and takes the checksum of its own workload.
    if isinstance(mock_checksum, dict):
        mock_checksum = mock_checksum.get(str(workload))
    with tempfile.TemporaryDirectory() as td:
        exe = _exe(binary_gem5, td, "spm")
        out = Path(td) / "m5out"
        cmd = [str(env.gem5), f"--outdir={out}", str(env.se), *GEM5_BASE,
               "-P", f"system.cpu[0].isa[0].sve_vl_se={int(vl)}",
               "-P", f"system.cpu[0].spmLoadPorts={lp}", "-P", f"system.cpu[0].spmStorePorts={sp}",
               "-c", str(exe), "-o", f"{m} {k} {n} 1 {kc} {mc}"]
        try:
            r = _run(cmd, td, timeout_s)
        except subprocess.TimeoutExpired:
            return {"ok": False, "detail": f"gem5 timeout after {timeout_s}s", "seconds": round(time.time() - t0, 1)}
        stats_file = out / "stats.txt"
        stats = stats_file.read_text() if stats_file.is_file() else ""
        text = r.stdout + r.stderr
    roi = _roi(stats)
    if r.returncode != 0 or "simTicks" not in roi:
        return {"ok": False, "detail": text[-3000:] or "no ROI statistics", "seconds": round(time.time() - t0, 1)}
    cycles = roi["simTicks"] * CPU_HZ / roi["simFreq"]
    cs = _checksum(text)
    match = None
    if cs is not None and isinstance(mock_checksum, (int, float)):
        match = abs(cs - float(mock_checksum)) <= 1e-6 * max(1.0, abs(float(mock_checksum)))
    lines = [f"{k}: {v:.6g}" for k, v in roi.items()]
    return {"ok": True, "cycles": cycles, "spm_reads": roi.get("system.l2.spmReads"), "checksum": cs,
            "checksum_match": match, "stats": "\n".join(lines), "detail": "",
            "seconds": round(time.time() - t0, 1)}
