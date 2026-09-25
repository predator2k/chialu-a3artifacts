"""Simulate the engine package against Python over every pattern through 16 bits.

    python3 -m chialu.verify.engine_selftest
    python3 -m chialu.verify.engine_selftest --formats fp8e4m3 --mutate-rounding
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import random
import shutil
import subprocess
import tempfile

from chialu.targets.rtl.engine import Engine, Conventions, FW
from chialu.verify import ops
from chialu.verify.engine_ref import ROUNDING, binary_ref, probe_value, round_ref, unpack_ref, x_ref
from chialu.verify.family_ref import Port
from chialu.verify.family_tb import emit_text, pack_ports
from chialu.verify.formats import FloatFormat, PositFormat, parse_format
from chialu.verify.tb_gen import write_hex

FORMATS = ("fp16", "bf16", "fp8e4m3", "fp32", "posit8_0", "posit16_1", "posit32_2")
FUNCTIONS = ("unpack", "add", "mul", "lt", "eq", "pack")


def patterns(fmt, sample, seed, limit=None):
    """Cover every small-format pattern and a seeded sample of larger formats."""
    rng = random.Random(seed)
    values = list(range(1 << fmt.width)) if fmt.width <= 16 else [rng.getrandbits(fmt.width) for _ in range(sample)]
    if limit is not None:
        values = values[:limit]
    top = 1 << (fmt.width - 1)
    corners = {0, 1, 2, top - 1, top, top + 1, 2 * top - 1}
    if isinstance(fmt, FloatFormat):
        for field in (0, 1, fmt.bias, fmt._top(), fmt.emax_code):
            for mantissa in (0, 1, (1 << fmt.man_bits) - 1):
                value = (field << fmt.man_bits) | mantissa
                corners.update((value, value | top))
    else:
        for shift in range(fmt.width):
            corners.update((1 << shift, (1 << shift) - 1))
    return values, sorted(corners)


def package(engine, fmt, mutate=False):
    unpack = engine.unpack_posit(fmt, "s") if isinstance(fmt, PositFormat) else engine.unpack_float(fmt, "s")
    pack = engine.pack_posit(fmt, "s") if isinstance(fmt, PositFormat) else engine.pack_float(fmt, "s")
    if mutate:
        original = "mag = {1'b0, topb} + up;" if isinstance(fmt, PositFormat) else "mag = keep + up;"
        assert original in pack
        pack = pack.replace(original, original[:-1] + " + 1'b1;", 1)
    return "\n".join(("package epkg;", engine.vdecl(), engine.rup_fn(), engine.arith(), unpack, pack, "endpackage"))


def run_format(fname, work, sample=2048, seed=7, limit=None, mutate=False):
    fmt = parse_format(fname)
    e = Engine("t", fmt, 8, False, targets=[fmt], conv=Conventions())
    zero_positive = e.tokens["ZERO_POSITIVE"] == "1"
    width = fmt.width
    inputs = [Port("a", "input", width), Port("b", "input", width), Port("daz", "input", 1), Port("sub", "input", 1),
              Port("xa", "input", e.XT), Port("xb", "input", e.XT), Port("xp", "input", e.XT),
              Port("rnd", "input", 3), Port("word", "input", 8), Port("ftz", "input", 1)]
    outputs = [Port("unpack", "output", e.VW + 1), Port("add", "output", width),
               Port("mul", "output", width), Port("lt", "output", 1), Port("eq", "output", 1), Port("pack", "output", width)]
    values, corners = patterns(fmt, sample, seed, limit)
    mask = (1 << width) - 1
    pairs = [(a, (a * 40503 + 17) & mask) for a in values]
    pairs += [(a, b) for a in corners for b in corners]
    rng = random.Random(seed)
    vectors, expected = [], []
    for a, b in pairs:
        xa, xb = x_ref(fmt.decode(a), e.XW, e.EW), x_ref(fmt.decode(b), e.XW, e.EW)
        comparison = ops.fp_ref("fcmp", fmt, a, b)
        probes = (fmt.decode(a), probe_value(fmt, a))
        for rnd, mode in enumerate(ROUNDING):
            word, daz, ftz = rng.randrange(256), rnd & 1, int(rnd % 3 == 2)
            result = {"unpack": unpack_ref(fmt, a, e.SW, e.EW, bool(daz)),
                      "add": binary_ref("fadd", fmt, a, b, mode, word, bool(ftz), zero_positive),
                      "mul": binary_ref("fmul", fmt, a, b, mode, word, bool(ftz), zero_positive),
                      "lt": comparison & 1, "eq": (comparison >> 1) & 1}
            for sub, value in enumerate(probes):
                vector = dict(a=a, b=b, daz=daz, sub=sub, xa=xa, xb=xb, xp=x_ref(value, e.XW, e.EW), rnd=rnd, word=word, ftz=ftz)
                if sub:
                    result["add"] = binary_ref("fsub", fmt, a, b, mode, word, bool(ftz), zero_positive)
                result["pack"] = round_ref(fmt, value, mode, word, ftz=bool(ftz))
                vectors.append(pack_ports(vector, inputs))
                expected.append(pack_ports(result, outputs))
    directory = Path(work) / (fname + ("_mutant" if mutate else ""))
    directory.mkdir(parents=True, exist_ok=True)
    write_hex(directory / "vectors.hex", vectors, sum(p.width for p in inputs))
    write_hex(directory / "expected.hex", expected, sum(p.width for p in outputs))
    ports = inputs + outputs
    declarations = ", ".join(f"{p.direction} wire [{p.width-1}:0] {p.name}" for p in ports)
    module = f"""
module engine_dut({declarations});
  import epkg::*;
  wire [{e.XT-1}:0] sum_x = t_add(xa, xb, sub);
  wire [{e.XT-1}:0] product_x = t_mul(xa, xb);
  wire [{FW+width-1}:0] sum_p = t_pack_s(sum_x, rnd, word, ftz);
  wire [{FW+width-1}:0] product_p = t_pack_s(product_x, rnd, word, ftz);
  wire [{FW+width-1}:0] packed_p = t_pack_s(xp, rnd, word, ftz);
  assign unpack = t_unpack_s(a, daz);
  assign add = sum_p[{width-1}:0]; assign mul = product_p[{width-1}:0];
  assign lt = t_lt(xa, xb); assign eq = t_eq(xa, xb);
  assign pack = packed_p[{width-1}:0];
endmodule
"""
    bench = emit_text("engine_dut", {}, ports, len(vectors))
    source = package(e, fmt, mutate) + module + bench
    (directory / "all.sv").write_text(source)
    # Verilator reads the SystemVerilog as written, so nothing is converted
    from chialu.verify import simulate as SIM
    try:
        compiled = subprocess.run(["verilator", *SIM.VERILATOR_FLAGS, "-j", str(SIM.VERILATOR_JOBS),
                                   "--top-module", "tb", "-Mdir", "obj_sim", "-o", "sim", "all.sv"],
                                  cwd=directory, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        return fname, "SKIP", len(vectors), f"verilator timed out on {len(source.encode())} bytes"
    if compiled.returncode:
        return fname, "FAIL", len(vectors), f"verilator: {compiled.stderr[:300]}"
    result = subprocess.run(["./obj_sim/sim"], cwd=directory, capture_output=True, text=True, timeout=7200)
    (directory / "simulation.log").write_text(result.stdout + result.stderr)
    ok = result.returncode == 0 and "PASS" in result.stdout and "FAIL" not in result.stdout
    return fname, "PASS" if ok else "FAIL", len(vectors), result.stdout[-1500:]


def _run(job):
    return run_format(*job)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--formats", default=",".join(FORMATS))
    ap.add_argument("--sample", type=int, default=2048, help="random patterns above 16 bits")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--limit", type=int, help="restrict primary patterns for diagnosis; the default is exhaustive through 16 bits")
    ap.add_argument("--mutate-rounding", action="store_true", help="add one ulp in the generated engine's rounding")
    args = ap.parse_args(argv)
    if args.jobs < 1 or args.sample < 1 or (args.limit is not None and args.limit < 1):
        ap.error("jobs, sample and limit must be positive")
    for tool in ("verilator",):
        if not shutil.which(tool):
            ap.error(f"{tool} is not on PATH")
    work = Path(tempfile.mkdtemp(prefix="chialu_engine_"))
    print(f"[engine] functions={','.join(FUNCTIONS)} rounding={','.join(ROUNDING)} ({work})", flush=True)
    jobs = [(name, work, args.sample, args.seed, args.limit, args.mutate_rounding) for name in args.formats.split(",")]
    failures = 0
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for name, status, count, detail in pool.map(_run, jobs):
            print(f"{status} {name}: {count} vectors, all six functions and rounding modes, both add/sub controls", flush=True)
            if status != "PASS":
                print(detail, flush=True)
                failures += 1
    if failures == 0 and not args.mutate_rounding:
        name, status, count, detail = run_format("fp8e4m3", work, 32, args.seed, 32, True)
        detected = status == "FAIL" and "MISMATCH" in detail
        print(f"{'PASS' if detected else 'FAIL'} one-ulp rounding mutation rejected", flush=True)
        failures += not detected
    print(f"[engine] {'FAIL' if failures else 'PASS'} ({work})", flush=True)
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
