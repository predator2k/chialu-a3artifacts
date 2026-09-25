"""The special-function library's harness: every family's module for a
set of functions and formats, measured against the verify layer's
reference by the generator's bit-accurate model (max ulp over every
pattern of a format up to 16 bits, a sample above), and a subset of
the modules simulated under Verilator against the model bit
for bit.

    python3 -m chialu.targets.rtl.families.sfutest [--formats fp8e4m3,fp16]
        [--families ...] [--functions ...] [--variants default|all] [--sim N] [--jobs 8]
"""
from __future__ import annotations

import argparse
import os
import random
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from chialu.targets.rtl.families import sfu as SF
from chialu.targets.rtl.families.fp import Geom

# per family: the pin variants the harness covers (the default first)
# the arithmetic slots bound to library families (every evaluator family carries them; families/sfu.py Net.bind)
BOUND = {"multiplier.family": "booth_recoded_parallel", "adder.family": "parallel_prefix", "adder.topology": "kogge_stone",
         "shifter.family": "barrel_mux_tree", "lzc.family": "lzd_cell_tree"}
BOUND2 = {"multiplier.family": "direct_pp_parallel", "adder.family": "carry_select", "shifter.family": "funnel",
          "lzc.family": "prefix_lzc"}

VARIANTS = {
    "direct_lut": [{}],
    "compressed_lut": [{}],
    "bipartite": [{}, {"symmetric": True}, dict(BOUND)],
    "stam": [{}, {"tables": 3}],
    "multipartite": [{}, {"tables": 3, "hierarchical": True}, {"accuracy_target": "sub_ulp_guard_bits"}],
    "add_table_add": [{}, {"truncation_order": 2, "final_reduction": "multioperand_tree"},
                      {"table_access": "dual_port", "offset_partitioning": "split_subwords", "symmetry": True}],
    "pwl": [{}, {"segments": 32, "segmentation": "nonuniform"}, {"segments": 16, "segmentation": "power_of_two"},
            {"segments": 16, "slope_encoding": "power_of_two"}, {"segments": 16, "slope_encoding": "csd"},
            {"segments": 32, "coeff_frac_bits": 16, "x_frac_bits": 14}],
    "pwl_residual_lut": [{}, {"residual_bits": 4}],
    "piecewise_poly": [{}, dict(BOUND), dict(BOUND2, segments=16, degree=2), {"segments": 16, "degree": 2, "guard_bits": 3},
                       {"segments": 16, "degree": 2, "basis": "chebyshev", "evaluator.family": "estrin"},
                       {"segments": 8, "degree": 3, "basis": "minimax_remez", "evaluator.family": "coefficient_adapted"},
                       {"segments": 16, "degree": 2, "evaluator.family": "parallel_monomial", "coeff_encoding": "csd"},
                       {"segments": 16, "degree": 2, "evaluator.family": "factored"},
                       {"segments": 16, "degree": 2, "evaluator.family": "fma_based", "rounding_contract": "exact"},
                       {"segments": 16, "degree": 1, "evaluator.family": "shift_add_coeff", "coeff_encoding": "power_of_two"},
                       {"segments": 16, "degree": 2, "coeff_encoding": "per_coeff_width", "coefficient_optimization": "joint_wordlength_search"},
                       {"segments": 16, "degree": 2, "coeff_encoding": "shared"},
                       {"segments": 16, "degree": 2, "segmenter.family": "nonuniform", "segmenter.addressing": "direct_address_bits"},
                       {"segments": 16, "degree": 2, "segmenter.family": "nonuniform", "segmenter.addressing": "priority_encoder",
                        "segmenter.boundary_search": "dynamic_programming"},
                       {"segments": 16, "degree": 2, "segmenter.family": "nonuniform", "segmenter.addressing": "comparator_tree",
                        "segmenter.boundary_search": "analytic_curvature"},
                       {"segments": 16, "degree": 2, "segmenter.family": "nonuniform", "segmenter.addressing": "power_of_two_cascade"},
                       {"segments": 16, "degree": 2, "segmenter.family": "hierarchical"},
                       {"segments": 16, "degree": 2, "segmenter.family": "power_of_two"},
                       {"segments": 16, "degree": 2, "segmenter.family": "ralut"}],
    "single_poly": [{}, {"degree": 4, "basis": "minimax_remez"}, {"degree": 3, "evaluator.family": "coefficient_adapted"}],
    "rational_approximation": [{}, {"numerator_degree": 2, "denominator_degree": 2, "segments": 2},
                               {"numerator_degree": 2, "denominator_degree": 1, "construction": "pade", "expression_form": "decomposed"},
                               {"symmetry_form": "odd", "objective_norm": "relative_minimax"},
                               {"numerator_degree": 2, "denominator_degree": 2, "divider.family": "restoring_nonrestoring"}],
    "lut_plus_poly": [{}, {"degree": 2, "index_bits": 6, "multiplier_shape": "truncated"}],
    "table_factor_refinement": [{}, {"factor_bits": 10, "residual_stages": 2, "tail_degree": 2, "terminal_correction": "table_square"}],
    "region_dependent": [{}, {"regions": 4}],
    "mixed_degree": [{}, {"max_degree": 3}],
    "gpu_multifunction_interpolator": [{}, {"interpolation_degree": 2, "coefficient_precision_grading": "per_function"}],
    "logarithmic_converters": [{}, {"correction": "pwl_correction", "regions": 4, "lns_full_alu": True},
                               {"correction": "constant_per_region", "regions": 4}, {"correction": "rom_free_shift_add"}, {k: v for k, v in BOUND.items() if not k.startswith("multiplier")}],
    "cordic": [{}, {"iterations": 24, "scale_compensation": "scaling_iterations"}, {"scale_compensation": "none"}, dict(BOUND2)],
    "redundant_high_radix_cordic": [{}, {"residual_arithmetic": "signed_digit", "scale_handling": "correcting_iterations"},
                                    {"coarse_fine_hybrid": True}],
    "digit_recurrence_exp_log": [{}, {"radix": 4, "digit_set": "signed_redundant", "selection": "rounding_of_scaled_residual",
                                      "termination": "linear_extrapolation"}],
    "newton_raphson": [{}, {"steps": 2}, dict(BOUND)],
    "goldschmidt": [{}, {"steps": 2}, dict(BOUND2)],
    "sigmoid_tanh_pwl": [{}, {"segments": 16, "approximation": "piecewise_quadratic"},
                         {"segments": 8, "approximation": "probability_weighted_pwl", "symmetry_folding": False},
                         {"segments": 16, "approximation": "shift_add_powers_of_two"}, {"approximation": "bit_level_mapping"},
                         {"segments": 8, "approximation": "step_sum"}],
    "transformer_activation_lut": [{}, {"method": "learned_lut_pwl", "calibration": "learned_from_data"}],
    "softmax_layernorm": [{}, {"normalization_division": "reciprocal_multiply", "exp_evaluation": "base2_shift_add"},
                          {"normalization_division": "log_domain_subtraction", "exp_evaluation": "integer_polynomial"},
                          {"exp_evaluation": "group_lookup_table", "max_subtraction": False},
                          {"layernorm_support": True}, dict(BOUND)],
}
# the functions each family is exercised on (the whole set for the general families)
ALL_FNS = ("exp2", "exp", "log2", "log", "recip", "sqrt", "rsqrt", "sin", "cos", "tanh", "erf", "sigmoid", "silu", "softplus", "gelu")
FN_SETS = {
    "newton_raphson": ("recip", "sqrt", "rsqrt", "sigmoid"), "goldschmidt": ("recip", "sqrt", "rsqrt"),
    "sigmoid_tanh_pwl": ("sigmoid", "silu", "tanh"), "transformer_activation_lut": ("gelu", "silu", "erf", "softplus", "sigmoid", "tanh"),
    "digit_recurrence_exp_log": ("exp2", "exp", "log2", "log", "softplus"),
    "table_factor_refinement": ("recip", "rsqrt", "sqrt", "exp2", "log2", "sigmoid"),
    "logarithmic_converters": ("exp2", "log2", "recip", "sqrt", "rsqrt", "sigmoid"),
    "cordic": ("sin", "cos", "exp2", "log2", "recip", "sqrt", "rsqrt", "tanh"),
    "redundant_high_radix_cordic": ("sin", "cos", "exp2", "log2", "recip", "tanh"),
    "softmax_layernorm": ("softmax", "layernorm"),
}


def geom_of(fmt) -> Geom:
    from chialu.targets.rtl.engine import Engine
    return Geom.of_engine(Engine("m0", fmt, 8, False, targets=[fmt]))


def _one(job):
    """(fmt name, fn, family, pins) -> a result dict."""
    from chialu.verify.formats import parse_format
    fname, fn, family, pins, limit, count = job
    fmt = parse_format(fname)
    g = geom_of(fmt)
    t0 = time.time()
    try:
        if fn in ("softmax", "layernorm"):
            name, text, net = SF.vector_sv(fn, fmt, g, count, family, pins)
            r = SF.measure_vector(fn, fmt, g, count, net, limit=limit or 300)
        else:
            name, text, net = SF.sfu_sv(fn, fmt, g, family, pins)
            r = SF.measure(fn, fmt, g, net, limit=limit)
        r.update(ok=True, kb=len(text) // 1000, rom=net.rom_bits, secs=round(time.time() - t0, 1), text=text, name=name)
    except Exception as ex:  # noqa: BLE001 - the harness reports every failure
        r = {"ok": False, "err": f"{type(ex).__name__}: {str(ex)[:120]}", "secs": round(time.time() - t0, 1)}
    r.update(fmt=fname, fn=fn, family=family, pins=pins)
    return r


def simulate(fmt, fn, family, pins, text, name, net, n_vec: int, work: Path) -> str:
    """The module against the model bit for bit under Verilator."""
    from chialu.verify.formats import Special
    g = geom_of(fmt)
    rng = random.Random(7)
    pats = []
    while len(pats) < n_vec:
        b = rng.getrandbits(fmt.width)
        if fmt.valid(b) and not isinstance(fmt.decode(b), Special):
            pats.append(b)
    pattern = family in SF.PATTERN_FAMILIES
    vector = fn in ("softmax", "layernorm")
    if vector:
        XT = g.XT
        count = sum(1 for d, r in net.ports if d == "input")
        ports = ", ".join(f".x{i}(x{i}), .y{i}(y{i})" for i in range(count))
        tb = [f"module tb; logic [{XT-1}:0] " + ", ".join(f"x{i}" for i in range(count)) + "; logic [" + f"{XT-1}:0] "
              + ", ".join(f"y{i}" for i in range(count)) + f"; logic inv; {name} u({ports}, .inv(inv)); integer errs; initial begin errs = 0;"]
        rng2 = random.Random(11)
        for _ in range(n_vec):
            vec = [pats[rng2.randrange(len(pats))] for _ in range(count)]
            if rng2.random() < 0.3:
                vec = [vec[0] ^ rng2.getrandbits(2) for _ in range(count)]
                vec = [b if fmt.valid(b) and not isinstance(fmt.decode(b), Special) else pats[0] for b in vec]
            ins = {f"x{i}": SF.x_of_bits(fmt, b, g) for i, b in enumerate(vec)}
            env = net.run(ins)
            sets = " ".join(f"x{i} = {XT}'d{ins[f'x{i}']};" for i in range(count))
            cond = " || ".join(f"y{i} !== {XT}'d{env[f'y{i}']}" for i in range(count)) + f" || inv !== 1'b{env['inv']}"
            tb.append(f"{sets} #1; if ({cond}) begin errs = errs + 1; if (errs < 4) $display(\"FAIL x0=%h y0=%h exp=%h\", x0, y0, {XT}'d{env['y0']}); end")
    elif pattern:
        W = fmt.width
        tb = [f"module tb; logic [{W-1}:0] x; logic [{W-1}:0] y; {name} u(.x(x), .y(y)); integer errs; initial begin errs = 0;"]
        for b in pats:
            env = net.run({"x": b})
            tb.append(f"x = {W}'d{b}; #1; if (y !== {W}'d{env['y']}) begin errs = errs + 1; if (errs < 4) $display(\"FAIL x=%h y=%h exp=%h\", x, y, {W}'d{env['y']}); end")
    else:
        XT = g.XT
        tb = [f"module tb; logic [{XT-1}:0] x; logic [{XT-1}:0] y; logic inv, dz; {name} u(.x(x), .y(y), .inv(inv), .dz(dz)); integer errs; initial begin errs = 0;"]
        for b in pats:
            xin = SF.x_of_bits(fmt, b, g)
            env = net.run({"x": xin})
            tb.append(f"x = {XT}'d{xin}; #1; if (y !== {XT}'d{env['y']} || inv !== 1'b{env['inv']} || dz !== 1'b{env['dz']}) begin errs = errs + 1; "
                      f"if (errs < 4) $display(\"FAIL x=%h y=%h exp=%h\", x, y, {XT}'d{env['y']}); end")
    tb.append('if (errs == 0) $display("PASS"); else $display("FAIL %0d", errs); $finish; end endmodule')
    d = work / f"{family}_{fn}_{fmt.name}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "lib.sv").write_text(text)
    (d / "tb.sv").write_text("\n".join(tb))
    # Verilator reads the generated SystemVerilog as written, so nothing is converted
    from chialu.verify import simulate as SIM
    r = subprocess.run(["verilator", *SIM.VERILATOR_FLAGS, "-j", str(SIM.VERILATOR_JOBS),
                        "--top-module", "tb", "-Mdir", "obj_sim", "-o", "sim", "tb.sv", "lib.sv"],
                       cwd=d, capture_output=True, text=True, timeout=900)
    if r.returncode:
        return f"COMPILE FAIL {r.stderr.strip()[:200]}"
    try:
        r = subprocess.run(["./obj_sim/sim"], cwd=d, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        return "SIM TIMEOUT"
    out = r.stdout.strip().splitlines()
    return out[-2] if len(out) > 1 and "PASS" not in out[-2] and "FAIL" in out[-2] else (out[-2] if len(out) > 1 else "no output")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--formats", default="fp8e4m3,fp16")
    ap.add_argument("--families", default=",".join(SF.SFU_FAMILIES["core"]))
    ap.add_argument("--functions", default=None)
    ap.add_argument("--variants", default="default", choices=("default", "all"))
    ap.add_argument("--limit", type=int, default=2000, help="sampled patterns above 16 bits (and for the vector functions)")
    ap.add_argument("--sim", type=int, default=0, help="simulate this many patterns per (family, function) at the first format")
    ap.add_argument("--count", type=int, default=4, help="lanes of the vector functions")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    args = ap.parse_args(argv)
    from chialu.verify.formats import parse_format
    fmts = args.formats.split(",")
    fams = [f for f in args.families.split(",") if f]
    jobs = []
    for fam in fams:
        variants = VARIANTS.get(fam, [{}])
        if args.variants == "default":
            variants = variants[:1]
        fns = args.functions.split(",") if args.functions else FN_SETS.get(fam, ALL_FNS)
        for pins in variants:
            for fname in fmts:
                for fn in fns:
                    if (fn in ("softmax", "layernorm")) != (fam == "softmax_layernorm"):
                        continue
                    if fam == "softmax_layernorm" and fn == "layernorm" and not pins.get("layernorm_support", False):
                        continue
                    if fam in SF.PATTERN_FAMILIES and parse_format(fname).width > SF.PATTERN_MAX_BITS:
                        continue
                    jobs.append((fname, fn, fam, pins, args.limit, args.count))
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for r in pool.map(_one, jobs, chunksize=1):
            results.append(r)
            pins = ",".join(f"{k}={v}" for k, v in r["pins"].items()) or "-"
            if r["ok"]:
                print(f"  {r['fmt']:9s} {r['fn']:9s} {r['family']:30s} {pins:60s} max_ulp {r['max_ulp']:>4} wrong {r['wrong']}/{r['n']} "
                      f"{r['kb']} KB rom {r['rom']} {r['secs']}s", flush=True)
            else:
                print(f"  {r['fmt']:9s} {r['fn']:9s} {r['family']:30s} {pins:60s} FAIL {r['err']} {r['secs']}s", flush=True)
    n_ok = sum(1 for r in results if r["ok"])
    within = sum(1 for r in results if r["ok"] and r["max_ulp"] <= 1)
    print(f"[sfu harness] {n_ok}/{len(results)} modules built, {within} within one ulp, {time.time()-t0:.0f}s")
    if args.sim:
        work = Path(tempfile.mkdtemp(prefix="chialu_sfu_"))
        n_pass = n_all = 0
        from chialu.verify.formats import parse_format
        seen = set()
        for r in results:
            if not r["ok"] or r["fmt"] != fmts[0] or (r["family"], r["fn"]) in seen:
                continue
            seen.add((r["family"], r["fn"]))
            fmt = parse_format(r["fmt"])
            g = geom_of(fmt)
            if r["fn"] in ("softmax", "layernorm"):
                name, text, net = SF.vector_sv(r["fn"], fmt, g, args.count, r["family"], r["pins"])
            else:
                name, text, net = SF.sfu_sv(r["fn"], fmt, g, r["family"], r["pins"])
            v = simulate(fmt, r["fn"], r["family"], r["pins"], text, name, net, args.sim, work)
            n_all += 1
            n_pass += "PASS" in v
            print(f"  sim {r['family']:30s} {r['fn']:9s} {r['fmt']}: {v}", flush=True)
        print(f"[sfu harness] simulation {n_pass}/{n_all} pass ({work})")
        return 0 if n_pass == n_all else 1
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
