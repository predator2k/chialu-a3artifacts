"""One simulation runner for the verification flow, on Verilator.

    result = simulate(sources, tb, cwd, ...)

`sources` are the design files (the design and the extra SystemVerilog
of a checker), `tb` the testbench file, all inside `cwd`; the runner
writes its build under `cwd` and returns a Result with the phase times.

Verilator translates the design to C++ and compiles it (3.5 s for an
18 KB design, 10.7 s for 584 KB on the 20-core host), then runs two
orders of magnitude faster per vector than an event simulator. The
testbenches drive a combinational design with `#1` delays in an initial
block, which Verilator runs under `--timing`; that needs a C++ compiler
with coroutines (GCC 10 or later: on RHEL 8 `source
/opt/rh/gcc-toolset-11/enable` before the flow) and `libatomic`.

A build is compiled once per candidate and serves every campaign
(`build`, `run`, tb_gen.emit_tb_universal), so the compile is paid once
per design.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

# `auto` is a legal name and resolves to Verilator, so a run file that names it still loads; any
# other name is rejected rather than silently redirected.
SIMULATORS = ("verilator", "auto")
DEFAULT = os.environ.get("CHIALU_SIM", "verilator")
VERILATOR_JOBS = int(os.environ.get("CHIALU_VERILATOR_JOBS", "4"))
# the selftests' limit scale (tests/test_selftests.py) also stretches the internal EDA limits on a slower
# host; nothing in the evaluation sets it, so there it is 1
TIMEOUT_SCALE = float(os.environ.get("CHIALU_TEST_TIMEOUT_SCALE", "1"))


def scaled(seconds):
    return int(seconds * TIMEOUT_SCALE)


# the bench is compiled first so its `timescale carries into the design (which has none); TIMESCALEMOD
# stays off for a design that mixes modules with and without one
# --output-split keeps every generated C++ file small enough for the parallel build (one huge file serializes it)
VERILATOR_FLAGS = ("--binary", "--timing", "-Wno-fatal", "-Wno-lint", "-Wno-style", "-Wno-TIMESCALEMOD",
                   "--x-assign", "fast", "--x-initial", "fast", "-O2", "--output-split", "20000")


# ccache 3.7 adds a precompiled header to an object's hash only when the header's mtime and ctime are older
# than the second ccache started in (src/ccache.c, remember_include_file: the include_file_mtime and
# include_file_ctime checks leave before the pch hash). verilated.mk compiles every generated .cpp with
# -include Vtb__pch.h.{fast,slow}, made or copied milliseconds earlier, so without these two entries a
# design-independent source (Vtb.cpp, Vtb___024root__Slow.cpp, Vtb__Syms__Slow.cpp, Vtb__main.cpp) is served
# another design's object, which addresses the root object at that design's offsets: SIGSEGV in the first
# $value$plusargs, or eventsPending() false and an exit at 0 s without output. verilated.mk sets
# `CCACHE_SLOPPINESS ?= pch_defines,time_macros`, so the environment wins.
CCACHE_SLOPPINESS = ("pch_defines", "time_macros", "include_file_mtime", "include_file_ctime")


def verilator_env() -> dict:
    """The environment of a Verilator build: no object cache unless
    CHIALU_OBJCACHE names one (`ccache`), and then a CCACHE_SLOPPINESS
    that holds every entry of CCACHE_SLOPPINESS. The flow's own build
    cache (one compiled model per design) already serves a repeated
    design, and a new design's cross-design hits are the three runtime
    objects, worth under a second of a parallel build."""
    env = dict(os.environ)
    cache = env.get("CHIALU_OBJCACHE")
    if cache:
        env["OBJCACHE"] = cache
        have = [x for x in env.get("CCACHE_SLOPPINESS", "").split(",") if x]
        env["CCACHE_SLOPPINESS"] = ",".join(have + [x for x in CCACHE_SLOPPINESS if x not in have])
    else:
        env.pop("OBJCACHE", None)
    return env
_N_RE = re.compile(r"localparam\s+(?:integer\s+)?[MN]\s*=\s*(\d+)")


@dataclass
class Result:
    simulator: str
    ok: bool
    phase: str = ""                  # "" on success; compile | sim on failure
    detail: str = ""
    stdout: str = ""
    compile_s: float = 0.0           # Verilator's verilate plus the C++ build
    run_s: float = 0.0
    returncode: int = 0
    files: dict = field(default_factory=dict)
    note: str = ""                   # e.g. a combinational loop Verilator reported at compile


def run_group(cmd, cwd, timeout: int, preexec_fn=None, env=None) -> subprocess.CompletedProcess:
    """`cmd` in its own process group with captured text output; a timeout
    kills the whole group (verilator forks a parallel C++ build and
    Verilator a make tree, which would otherwise outlive the driver) and
    returns code 124 with the timeout in stderr."""
    import signal
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            start_new_session=True, preexec_fn=preexec_fn, env=env)
    timeout = scaled(timeout)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            proc.kill()
        out, err = proc.communicate()
        return subprocess.CompletedProcess(cmd, 124, out or "", f"timeout after {timeout} s")
    return subprocess.CompletedProcess(cmd, proc.returncode, out, err)


def available(simulator: str = "verilator") -> bool:
    return shutil.which("verilator") is not None


def choose(simulator: str | None = None, sources=(), tb_text: str | None = None,
           cwd: Path | None = None) -> str:
    """The simulator a call uses, which is Verilator. `auto` and the
    simulator name itself resolve to it; any other name is an error."""
    sim = simulator or DEFAULT
    if sim not in SIMULATORS:
        raise ValueError(f"simulator {sim!r}: one of {SIMULATORS}")
    if not available():
        raise RuntimeError("verilator is not on PATH, and it is the flow's one simulator")
    return "verilator"


def simulate(sources, tb, cwd, simulator: str | None = None, top: str = "tb", compile_timeout: int = 900,
             run_timeout: int = 1800, work: str = "obj_sim", preexec_fn=None) -> Result:
    """Compile and run `sources` + `tb` under `cwd`; the dump files the
    bench writes land in `cwd` whatever the simulator."""
    cwd = Path(cwd)
    tb_text = None
    tb_path = cwd / tb
    if tb_path.is_file():
        try:
            tb_text = tb_path.read_text()
        except OSError:
            tb_text = None
    sim = choose(simulator, sources, tb_text, cwd)
    srcs = [str(tb)] + [str(s) for s in sources]
    t0 = time.time()
    note = ""
    if sim == "verilator":
        mdir = cwd / work
        shutil.rmtree(mdir, ignore_errors=True)
        cmd = ["verilator", *VERILATOR_FLAGS, "-j", str(VERILATOR_JOBS), "--top-module", top,
               "-Mdir", work, "-o", "sim", *srcs]
        r = run_group(cmd, cwd=cwd, timeout=compile_timeout, preexec_fn=preexec_fn, env=verilator_env())
        if r.returncode == 124:
            return Result(sim, False, "compile", f"verilator timeout after {compile_timeout}s", compile_s=time.time() - t0)
        exe = mdir / "sim"
        if r.returncode or not exe.is_file():
            return Result(sim, False, "compile", (r.stderr or r.stdout)[-4000:], r.stdout, time.time() - t0, returncode=r.returncode)
        compile_s = time.time() - t0
        loops = loop_note(r.stderr)
        t1 = time.time()
        s = run_group([str(exe)], cwd=cwd, timeout=run_timeout, preexec_fn=preexec_fn)
        if s.returncode == 124:
            return Result(sim, False, "sim", f"simulation timeout after {run_timeout}s", compile_s=compile_s, run_s=time.time() - t1)
        run_s = time.time() - t1
        if crashed(s):
            return Result(sim, False, "sim", "; ".join(x for x in (CRASH_NOTE.format(rc=s.returncode), loops) if x),
                          s.stdout, compile_s, run_s, s.returncode)
        if s.returncode:
            return Result(sim, False, "sim", (s.stderr or s.stdout)[-4000:], s.stdout, compile_s, run_s, s.returncode, note=loops)
        return Result(sim, True, "", "", s.stdout, compile_s, run_s, note=loops)
    raise RuntimeError(f"simulator {sim!r}: Verilator is the flow's one simulator")


@dataclass
class Build:
    simulator: str
    ok: bool
    exe: str = ""                    # the Verilator binary
    phase: str = ""
    detail: str = ""
    compile_s: float = 0.0
    cached: bool = False
    sources: list = field(default_factory=list)   # what a rebuild under the other simulator needs
    tb: str = ""
    cwd: str = ""
    top: str = "tb"
    note: str = ""                   # e.g. a combinational loop Verilator reported at compile


def crashed(r) -> bool:
    """A model that died by a signal, or that left Verilator's time loop
    at 0 s without a bench line (every campaign of the flow's benches
    prints one before $finish): a model built from a stale object."""
    return r.returncode < 0 or r.returncode >= 128 or (r.returncode == 0 and not bench_lines(r.stdout or ""))


CRASH_NOTE = "the Verilator model died by a signal or ended without output (rc {rc})"
LOOP_NOTE = "verilator UNOPTFLAT (circular combinational logic, real or an unsplit array): {where}"


def loop_note(stderr: str) -> str:
    """The circular combinational logic Verilator reports at compile
    (UNOPTFLAT, a performance warning outside the lint group the flow
    silences): a real loop, or a vector or an unpacked array whose
    elements a chain of assigns writes and reads (the shifter's stage
    arrays before their split_var metacomments). The first signal named."""
    for line in (stderr or "").splitlines():
        if "UNOPTFLAT" in line:
            m = re.search(r"Signal[^:]*:\s*'([^']+)'", line)
            return LOOP_NOTE.format(where=m.group(1) if m else line.strip()[:120])
    return ""


def build(sources, tb, cwd, simulator: str | None = None, top: str = "tb", compile_timeout: int = 900,
          work: str = "obj_sim", preexec_fn=None) -> Build:
    """Compile `sources` + `tb` under `cwd` once; `run` executes the
    result per campaign with plusargs (the universal testbench of
    tb_gen.emit_tb_universal reads its campaign and files from them)."""
    cwd = Path(cwd)
    tb_text = None
    if (cwd / tb).is_file():
        try:
            tb_text = (cwd / tb).read_text()
        except OSError:
            pass
    sim = choose(simulator, sources, tb_text, cwd)
    srcs = [str(tb)] + [str(s) for s in sources]
    t0 = time.time()
    if sim == "verilator":
        mdir = cwd / work
        shutil.rmtree(mdir, ignore_errors=True)
        cmd = ["verilator", *VERILATOR_FLAGS, "-j", str(VERILATOR_JOBS), "--top-module", top,
               "-Mdir", work, "-o", "sim", *srcs]
        r = run_group(cmd, cwd=cwd, timeout=compile_timeout, preexec_fn=preexec_fn, env=verilator_env())
        if r.returncode == 124:
            return Build(sim, False, "", "compile", f"verilator timeout after {compile_timeout}s", time.time() - t0)
        exe = mdir / "sim"
        if r.returncode or not exe.is_file():
            return Build(sim, False, "", "compile", (r.stderr or r.stdout)[-4000:], time.time() - t0)
        return Build(sim, True, str(exe), compile_s=time.time() - t0, sources=list(sources), tb=str(tb), cwd=str(cwd), top=top,
                     note=loop_note(r.stderr))
    raise RuntimeError(f"simulator {sim!r}: Verilator is the flow's one simulator")


def run(b: Build, cwd, plusargs=(), run_timeout: int = 1800, preexec_fn=None) -> Result:
    """One run of a build under `cwd` (where the campaign's files are and
    its dump lands), with `plusargs` as `+name=value` strings."""
    if not b.ok:
        return Result(b.simulator, False, b.phase, b.detail, compile_s=b.compile_s)
    args = [str(a) if str(a).startswith("+") else f"+{a}" for a in plusargs]
    cmd = [b.exe, *args]
    t1 = time.time()
    s = run_group(cmd, cwd=cwd, timeout=run_timeout, preexec_fn=preexec_fn)
    if s.returncode == 124:
        return Result(b.simulator, False, "sim", f"simulation timeout after {run_timeout}s", compile_s=b.compile_s, run_s=time.time() - t1)
    run_s = time.time() - t1
    if crashed(s):
        return Result(b.simulator, False, "sim",
                      "; ".join(x for x in (CRASH_NOTE.format(rc=s.returncode), b.note) if x),
                      s.stdout, b.compile_s, run_s, s.returncode)
    if s.returncode:
        return Result(b.simulator, False, "sim", (s.stderr or s.stdout)[-4000:], s.stdout, b.compile_s, run_s, s.returncode, note=b.note)
    return Result(b.simulator, True, "", "", s.stdout, b.compile_s, run_s, note=b.note)


def bench_lines(stdout: str) -> list:
    """The bench's own lines, which Verilator ends with `- tb.sv:N: Verilog $finish`."""
    return [ln for ln in stdout.strip().splitlines()
            if "$finish called" not in ln and not ln.startswith("- ") and "Verilog $finish" not in ln]
