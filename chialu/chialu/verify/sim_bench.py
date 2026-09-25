"""What a candidate costs the flow's simulator, on the flow's own benches.

    python3 -m chialu.verify.sim_bench [--cases a,b,...]
                                       [--n-random N] [--out DIR] [--json FILE]

Every case is a unit spec the verify layer turns into a seed, a checker
where checked, and the verification files; the conformance node (and
the fault node of a checked unit) then runs, so the measurement covers
what a run pays per candidate: the verilate plus the C++ build, and the
run. Two native family benches (a 32-bit Booth multiplier, a 64-bit
prefix adder) go through `families.selftest.run_case` the same way. The
table reports the phase times, the vector count and the design size;
the JSON keeps every number.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path


def alu(modes, ops, **kw):
    spec = {"unit": "alu", "dut_name": "alu_core", "modes": modes, "ops": ops, "check_en": False}
    spec.update(kw)
    return spec


def checked(spec, modulus=31, family="residue"):
    spec = dict(spec, check_en=True, checker_family=family, modulus=modulus, checker_name="alu_checker",
                comparator={"family": "direct_compare"}, generator_style="csa_tree")
    return spec


CASES = {
    "int16_small": alu([{"count": 1, "format": "int16"}], ["add", "sub", "mul_wide", "and"]),
    "int16_checked": checked(alu([{"count": 1, "format": "int16"}], ["add", "sub", "mul_wide", "and", "shl"])),
    "int32_full": alu([{"count": 1, "format": "int32"}, {"count": 2, "format": "int16"}],
                      ["add", "sub", "adc", "mul", "mul_wide", "div", "rem", "cmp", "min", "shl", "shr_arith", "and", "popcount"]),
    "fp16_sr_window_checked": checked(alu([{"count": 1, "format": "fp16"}], ["fadd", "fmul", "fsqrt"],
                                          rounding=["SR"], sr_bits=10, check_sr=[False]), modulus=15),
    "fp32_div_sqrt": alu([{"count": 1, "format": "fp32"}], ["fadd", "fmul", "fdiv", "fsqrt"], rounding=["RNE", "RDN"]),
    "posit16_arith": alu([{"count": 1, "format": "posit16_1"}], ["fadd", "fmul", "fmin"]),
    "dot_fp16x4": {"unit": "vec_dot_acc", "dut_name": "dot_core", "check_en": False,
                   "modes": [{"elements": 4, "format_ab": "fp16", "format_c": "fp32", "format_d": "fp32"}]},
    "dot_int8x4": {"unit": "vec_dot_acc", "dut_name": "dot_core", "check_en": False,
                   "modes": [{"elements": 4, "format_ab": "int8", "format_c": "int32", "format_d": "int32"}]},
    "sfu_fp8x4": {"unit": "vec_sfu", "dut_name": "sfu_core", "check_en": False,
                  "modes": [{"count": 4, "format": "fp8e4m3"}], "functions": ["exp2", "recip"]},
    # the matrix's slow cases: every runtime control on fp16 with SR and a flag-checking checker (716 s on the
    # host), the fp64 unit with divide and square root, and the seven-mode mixed unit
    "everything_runtime_fp16": checked(alu([{"count": 1, "format": "fp16"}], ["fadd", "fmul", "fsqrt", "fabs", "cvt(int8)"],
                                           rounding=["RNE", "RTZ", "RDN", "RUP", "SR"], sr_bits=10, daz_in=[False, True],
                                           ftz_out=[False, True], unary_dual=[False, True], check_sr=[True, False],
                                           flags=["invalid", "div_zero", "overflow", "underflow", "inexact", "nan", "denormal"],
                                           check_flags=True), modulus=15),
    "fp64_all": alu([{"count": 1, "format": "fp64"}], ["fadd", "fsub", "fmul", "fdiv", "fsqrt", "fcmp"]),
    "mixed32_reduced": alu([{"count": 1, "format": "int32"}, {"count": 2, "format": "int16"}, {"count": 4, "format": "int8"},
                            {"count": 1, "format": "fp32"}, {"count": 2, "format": "fp16"}, {"count": 2, "format": "bf16"},
                            {"count": 4, "format": "fp8e4m3"}],
                           ["add", "sub", "mul_wide", "quot", "min", "cmp", "shl", "xor", "popcount", "fadd", "fmul", "fdiv",
                            "fcmp", "fabs", "cvt(int32)", "cvt(fp32)", "cvt(fp16)"], rounding=["RNE", "RTZ", "RDN", "RUP"]),
}
HEAVY = ("everything_runtime_fp16", "fp64_all", "mixed32_reduced")
NATIVE = ("mul_booth32", "prefix_ks64")


def bundle(name, spec, n_random, out):
    """(rtl, files, checker_rtl, vectors) of a case."""
    from chialu.targets.derive import checker_rtl, seed_for, verify_files
    if spec["unit"] == "alu":
        from chialu.verify.alu_ref import normalize_spec
        spec = normalize_spec(spec)
    elif spec["unit"] == "vec_dot_acc":
        from chialu.verify.dot_ref import normalize_dot_spec
        spec = normalize_dot_spec(spec)
    else:
        from chialu.verify.sfu_ref import normalize_sfu_spec
        spec = normalize_sfu_spec(spec)
    spec = dict(spec, n_random=n_random, seed=7)
    if spec.get("check_en"):
        from chialu.targets.derive import detect_budget
        spec.setdefault("n_random_masks", 600)
        spec["detect"] = detect_budget(spec, spec["n_random_masks"])
    rtl = str(seed_for(spec))
    chk = checker_rtl(spec) if spec.get("checker_name") else None
    files = verify_files(spec, out / name / "verify", chk)
    vectors = len(files["vectors.hex"].split())
    return rtl, files, chk, vectors


def run_node(fn, *args, simulator):
    from adir.registry import underlying              # the plain function: an in-process call, no cluster
    from chialu import eda
    from chialu.verify import simulate as SIM
    before = SIM.DEFAULT
    SIM.DEFAULT = simulator
    try:
        t0 = time.time()
        r = underlying(fn)(*args)
        wall = time.time() - t0
    finally:
        SIM.DEFAULT = before
    last = dict(eda.LAST_SIM)
    return r, wall, last


def native_cases(width_mul=32, width_add=64):
    from chialu.targets.rtl.families import selftest as FS
    out = {}
    for module, text, signed in FS.mul_cases(width_mul):
        if "booth" in module:
            out["mul_booth32"] = (module, FS.tb_mul(module, width_mul, signed), text)
            break
    for module, text, flagged in FS.prefix_cases(width_add):
        if "kogge" in module:
            out["prefix_ks64"] = (module, FS.tb_adder(module, {}, width_add, flagged), text)
            break
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases", default=",".join([c for c in CASES if c not in HEAVY] + list(NATIVE)),
                    help="the case names; `heavy` adds the matrix's slow cases")
    ap.add_argument("--matrix-cases", default="", help="alu_matrix case names, bound through ADIR: the instance's own "
                                                       "seed (the plan's library families), checker and bundle")
    ap.add_argument("--simulators", default="verilator")
    ap.add_argument("--n-random", type=int, default=300)
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)
    from chialu import eda
    from chialu.verify import simulate as SIM
    sims = [s.strip() for s in args.simulators.split(",") if s.strip()]
    for s in sims:
        if not SIM.available(s):
            print(f"[sim_bench] {s} is not on the PATH", file=sys.stderr)
            return 2
    out = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="chialu_sim_bench_"))
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    wanted = [c.strip() for c in args.cases.split(",") if c.strip()]
    if "heavy" in wanted:
        wanted = [c for c in wanted if c != "heavy"] + list(HEAVY)
    bound = {}
    for name in [c.strip() for c in args.matrix_cases.split(",") if c.strip()]:
        from chialu.verify import alu_matrix as M
        case = {c.name: c for c in M.cases()}.get(name)
        if case is None:
            print(f"[sim_bench] unknown matrix case {name}", file=sys.stderr)
            continue
        try:
            (out / f"matrix_{name}").mkdir(parents=True, exist_ok=True)
            inst = M.load_case(case, out / f"matrix_{name}")
        except Exception as e:  # noqa: BLE001
            rows.append({"case": name, "error": f"load: {type(e).__name__}: {str(e)[:200]}"})
            print(f"{name}: load failed: {type(e).__name__}: {str(e)[:160]}", flush=True)
            continue
        bound[f"matrix:{name}"] = (inst.artifacts["core"].text, inst.artifacts["verify_bundle"].texts,
                                   inst.artifacts["checker"].text if "checker" in inst.artifacts else None)
    wanted += list(bound)
    natives = native_cases() if any(c in NATIVE for c in wanted) else {}
    for name in wanted:
        if name in CASES or name in bound:
            if name in bound:
                rtl, files, chk = bound[name]
                vectors = len(files["vectors.hex"].split())
            else:
                try:
                    rtl, files, chk, vectors = bundle(name, CASES[name], args.n_random, out)
                except Exception as e:  # noqa: BLE001  a case the generators reject is reported, not fatal
                    rows.append({"case": name, "error": f"{type(e).__name__}: {str(e)[:200]}"})
                    print(f"{name}: generation failed: {type(e).__name__}: {str(e)[:160]}", flush=True)
                    continue
            for sim in sims:
                # a fresh build cache per case and simulator: the first node call pays the build (cold), the
                # repeated conformance call shows the run alone (warm)
                eda.SIM_BUILD_CACHE_DIR = out / f"cache_{name}_{sim}"
                r, wall, last = run_node(eda.conformance, rtl, files, simulator=sim)
                row = {"case": name, "node": "conformance", "simulator": last.get("simulator", sim), "pass": bool(r.get("pass")),
                       "detail": str(r.get("detail", ""))[:200], "vectors": vectors, "rtl_bytes": len(rtl.encode()),
                       "compile_s": last.get("compile_s"), "run_s": last.get("run_s"),
                       "node_s": round(wall, 2), "flow": "universal" if "cached" in last else "per-bench"}
                r2, wall2, last2 = run_node(eda.conformance, rtl, files, simulator=sim)
                row["warm_node_s"] = round(wall2, 2)
                row["warm_run_s"] = last2.get("run_s")
                rows.append(row)
                print(f"{name:22s} conformance {row['simulator']:9s} pass={row['pass']!s:5s} vectors={vectors:6d} rtl={row['rtl_bytes']//1024:5d}KB "
                      f"compile={row['compile_s']} run={row['run_s']} node={row['node_s']}s warm={row['warm_node_s']}s {row['detail'][:50]}", flush=True)
                if chk:
                    r, wall, last = run_node(eda.fault, rtl, files, chk, simulator=sim)
                    row = {"case": name, "node": "fault", "simulator": last.get("simulator", sim), "pass": bool(r.get("pass")),
                           "detail": str(r.get("detail", ""))[:200], "vectors": vectors, "rtl_bytes": len(rtl.encode()),
                           "compile_s": last.get("compile_s"), "run_s": last.get("run_s"),
                           "node_s": round(wall, 2), "sites": r.get("sites"), "flow": "universal" if "cached" in last else "per-bench"}
                    r2, wall2, last2 = run_node(eda.fault, rtl, files, chk, simulator=sim)
                    row["warm_node_s"] = round(wall2, 2)
                    rows.append(row)
                    print(f"{name:22s} fault       {row['simulator']:9s} pass={row['pass']!s:5s} node={row['node_s']}s warm={row['warm_node_s']}s "
                          f"(build compile={row['compile_s']} last run={row['run_s']}) {row['detail'][:50]}", flush=True)
        elif name in natives:
            from chialu.targets.rtl.families import selftest as FS
            module, tb, text = natives[name]
            for sim in sims:
                before = SIM.DEFAULT
                SIM.DEFAULT = sim
                t0 = time.time()
                try:
                    status = FS.run_case("", module, tb, out / f"{name}_{sim}", text)
                finally:
                    SIM.DEFAULT = before
                wall = time.time() - t0
                row = {"case": name, "node": "native", "simulator": sim, "pass": status.endswith(": PASS"), "detail": status[:200],
                       "rtl_bytes": len(text.encode()), "node_s": round(wall, 2)}
                rows.append(row)
                print(f"{name:22s} native      {sim:9s} pass={row['pass']!s:5s} rtl={row['rtl_bytes']//1024:5d}KB total={row['node_s']}s {status[:60]}", flush=True)
        else:
            print(f"{name}: unknown case", file=sys.stderr)
    path = Path(args.json) if args.json else out / "sim_bench.json"
    path.write_text(json.dumps(rows, indent=1))
    # the agreement of the verdicts, per case and node
    by = {}
    for r in rows:
        if "simulator" in r:
            by.setdefault((r["case"], r["node"]), {})[r["simulator"]] = r["pass"]
    disagree = [k for k, v in by.items() if len(set(v.values())) > 1]
    print(f"[sim_bench] {len(rows)} rows; verdict disagreements: {disagree or 'none'}; {path}")
    return 1 if disagree else 0


if __name__ == "__main__":
    sys.exit(main())
