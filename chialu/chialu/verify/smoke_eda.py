"""Local regression of the generated seeds and checkers against the
verify layer: builds the derived bundle of a compact matrix of specs
over the three unit classes, simulates the seed under the conformance
testbench with Verilator, and runs the fault harness with the generated
checker where the spec is checked. Needs verilator on PATH.

    python3 -m chialu.verify.smoke_eda [work_dir] [case ...]
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path

from chialu.targets import bundles, derive
from chialu.targets.rtl import checkers

CASES = {
    # ---- chialu.ALU
    "alu_int": {"unit": "alu", "modes": [{"count": 1, "format": "int16"}, {"count": 2, "format": "int8"}],
                "ops": ["add", "sub", "adc", "sbb", "neg", "abs", "mul_wide", "mul", "quot", "rem", "min",
                        "cmp", "shl", "popcount", "cvt(int8)", "cvt(fp16)"],
                "quotient_semantics": ["truncate_zero", "floor"], "check": True},
    **{f"alu_int_{fam}": {"unit": "alu", "modes": [{"count": 1, "format": "int16"}, {"count": 2, "format": "int8"}],
                          "ops": ["add", "sub", "adc", "sbb", "neg", "abs", "mul_wide", "min", "shl"],
                          "check": True, "checker_family": fam, "n_random_masks": 1500}
       for fam in ("inverse_residue", "multi_residue", "parity_prediction_adder", "berger", "duplication")},
    # the checker families of the later library step and the comparator slot
    **{f"alu_int_{fam}": {"unit": "alu", "modes": [{"count": 1, "format": "int16"}, {"count": 2, "format": "int8"}],
                          "ops": ["add", "sub", "adc", "sbb", "neg", "abs", "mul_wide", "mul", "min", "shl"],
                          "check": True, "checker_family": fam, "n_random_masks": 1500, **extra}
       for fam, extra in (("an_code", {}), ("an_code_a7_d3", {"checker_family": "an_code",
                                                              "checker_pins": {"A": 7}}),
                          ("rns_redundant", {}), ("rns_redundant_corr", {"checker_family": "rns_redundant",
                                                                          "checker_pins": {"base_moduli_count": 4, "redundant_moduli": 2}}),
                          ("parity_prediction_multiplier", {}),
                          ("ppm_booth2", {"checker_family": "parity_prediction_multiplier", "checker_pins": {"recoding": "booth2"}}),
                          ("reduced_precision", {}),
                          ("reduced_precision_r8", {"checker_family": "reduced_precision",
                                                    "checker_pins": {"replica_width_bits": 8, "bound_type": "relative_ulp"}}),
                          ("residue_two_rail", {"checker_family": "residue", "comparator": {"family": "two_rail_tree", "tree_arity": 3}}),
                          ("berger_two_rail", {"checker_family": "berger", "comparator": {"family": "two_rail_tree"}}),
                          ("residue_k2k", {"checker_family": "residue", "comparator": {"family": "m_out_of_n_checker"}}),
                          ("residue_k2k_cell", {"checker_family": "residue",
                                                "comparator": {"family": "m_out_of_n_checker", "realization": "multilevel_unate"}}),
                          ("residue_k2k_tc", {"checker_family": "residue",
                                              "comparator": {"family": "m_out_of_n_checker", "realization": "translator_cascade"}}),
                          ("residue_1ofn", {"checker_family": "residue",
                                            "comparator": {"family": "m_out_of_n_checker", "code_class": "one_out_of_n"}}),
                          ("dup_k2k", {"checker_family": "duplication", "comparator": {"family": "m_out_of_n_checker"}}),
                          ("dup_two_rail", {"checker_family": "duplication", "comparator": {"family": "two_rail_tree"}}),
                          ("dup_majority", {"checker_family": "duplication", "comparator": {"family": "majority_voter"}}),
                          ("dup_majority5", {"checker_family": "duplication", "comparator": {"family": "majority_voter", "inputs": 5}}),
                          ("dup_rep3", {"checker_family": "duplication", "checker_pins": {"replication": 3}}))},
    "alu_fp16_reduced_precision": {"unit": "alu", "modes": [{"count": 2, "format": "fp16"}],
                                   "ops": ["fadd", "fsub", "fmul", "fmin", "fabs"], "rounding": ["RNE", "RTZ"],
                                   "check": True, "checker_family": "reduced_precision", "n_random_masks": 1500},
    "alu_fp16_reduced_precision_rel": {"unit": "alu", "modes": [{"count": 1, "format": "bf16"}, {"count": 2, "format": "fp16"}],
                                       "ops": ["fadd", "fsub", "fmul"], "daz_in": [False, True], "ftz_out": [False, True],
                                       "check": True, "checker_family": "reduced_precision", "n_random_masks": 1500,
                                       "checker_pins": {"replica_width_bits": 8, "bound_type": "relative_ulp"}},
    "alu_fixed": {"unit": "alu", "modes": [{"count": 1, "format": "fxs1i7f8"}],
                  "ops": ["add", "mul", "mul_wide", "div", "cvt(fp16)"], "rounding": ["RNE", "RTZ"], "check": True},
    "alu_fp16": {"unit": "alu", "modes": [{"count": 2, "format": "fp16"}],
                 "ops": ["fadd", "fsub", "fmul", "fdiv", "fsqrt", "fmin", "fcmp", "fabs", "cvt(int16)", "cvt(bf16)"],
                 "flags": ["inexact", "invalid", "overflow"], "check_flags": True, "check": True},
    "alu_sr": {"unit": "alu", "modes": [{"count": 1, "format": "bf16"}], "ops": ["fadd", "fmul", "cvt(int8)"],
               "rounding": ["RNE", "SR"], "sr_bits": 5, "check_sr": [True, False], "check": True, "alias": 0.5},
    "alu_dual": {"unit": "alu", "modes": [{"count": 2, "format": "int8"}], "ops": ["neg", "abs", "not", "add", "cvt(fp8e4m3)"],
                 "unary_dual": [False, True], "check": True},
    "alu_block": {"unit": "alu", "modes": [{"count": 1, "format": "blksfp8e4m3efp4e2m1s16"}, {"count": 16, "format": "fp16"}],
                  "ops": ["fadd", "fmul", "fabs", "cvt(blksfp8e4m3efp4e2m1s16)", "cvt(fp16)"], "n_random": 20, "check": True},
    "alu_posit": {"unit": "alu", "modes": [{"count": 1, "format": "posit16_1"}], "ops": ["fadd", "fmul", "fdiv", "fsqrt"],
                  "n_random": 60, "check": True},
    "alu_exotic": {"unit": "alu", "modes": [{"count": 1, "format": "int8_ones"}, {"count": 1, "format": "bcd3"}],
                   "ops": ["add", "sub", "mul_wide", "div", "cvt(int12)"], "zero_sign": "preserve", "check": True},
    "alu_fp64": {"unit": "alu", "modes": [{"count": 1, "format": "fp64"}], "ops": ["fadd", "fmul", "fdiv", "fsqrt"], "n_random": 40},
    "alu_fp80": {"unit": "alu", "modes": [{"count": 1, "format": "fp80"}], "ops": ["fadd", "fmul", "cvt(fp64)"], "n_random": 40},
    # ---- chialu.VecDotAcc
    "dot_int": {"unit": "vec_dot_acc", "modes": [{"elements": 4, "format_ab": "int8", "format_c": "int32", "format_d": "int32"}],
                "check": True, "n_random_masks": 3000},
    "dot_fp": {"unit": "vec_dot_acc", "modes": [{"elements": 2, "format_ab": "fp16", "format_c": "fp32", "format_d": "fp32"}],
               "flags": ["inexact"], "rounding": ["RNE", "RTZ"], "check": True},
    "dot_seq": {"unit": "vec_dot_acc", "modes": [{"elements": 3, "format_ab": "fp16", "format_c": "fp16", "format_d": "fp16"}],
                "dot_contract": "sequential", "rounding": ["SR"], "sr_bits": 5},
    "dot_quire": {"unit": "vec_dot_acc", "modes": [{"elements": 2, "format_ab": "posit16_1", "format_c": "quire16_1", "format_d": "quire16_1"}],
                  "n_random": 30, "check": True},
    "dot_block": {"unit": "vec_dot_acc", "modes": [{"elements": 4, "format_ab": "int8", "format_c": "fp16", "format_d": "blksfp8e4m3efp4e2m1s16"}],
                  "n_random": 20},
    "dot_mxfp4": {"unit": "vec_dot_acc", "modes": [{"elements": 2, "format_ab": "blksfps0e8m0Nefp4e2m1s32", "format_c": "fp16", "format_d": "fp16"}],
                  "n_random": 20},
    # the runtime accuracy control: the mode port selects the ACA adder's correction stages,
    # the judge applies the budget of the mode each vector drove (work-plan item 7)
    "alu_approx_runtime": {"unit": "alu", "modes": [{"count": 1, "format": "int16"}],
                           "ops": ["add", "sub"], "accuracy": "approximate", "accuracy_ctl": "runtime",
                           "accuracy_modes": 3,
                           "budget": [{"error_rate": 0.6}, {"error_rate": 0.5}, {"bit_exact": True}],
                           "core_families": {"core.adder.m0": ("accuracy_configurable",
                                                               {"mode_count": 3, "reconfig_grain": "correction_stage",
                                                                "sub_adder.family": "ripple_carry"})},
                           "n_random": 60},
    # the checked form: the checker checks the exact mode and is held low in the approximate
    # one, and the fault gate scores the masks landing on the exact mode's vectors
    "alu_approx_runtime_checked": {"unit": "alu", "modes": [{"count": 1, "format": "int16"}],
                                   "ops": ["add", "sub"], "accuracy": "approximate", "accuracy_ctl": "runtime",
                                   "accuracy_modes": 2,
                                   "budget": [{"error_rate": 0.6}, {"bit_exact": True}],
                                   "core_families": {"core.adder.m0": ("accuracy_configurable",
                                                                       {"mode_count": 2,
                                                                        "reconfig_grain": "correction_stage",
                                                                        "sub_adder.family": "ripple_carry"})},
                                   "n_random": 40, "check": True, "n_random_masks": 800},
    # ---- chialu.VecSFU
    "sfu_rom": {"unit": "vec_sfu", "modes": [{"count": 2, "format": "fp8e4m3"}], "functions": ["sigmoid", "recip", "exp2"],
                "exhaustive": True, "flags": ["inexact", "invalid", "div_zero"]},
    "sfu_pwl": {"unit": "vec_sfu", "modes": [{"count": 1, "format": "fp16"}], "functions": ["exp2", "recip"], "n_random": 100,
                "budget": {"max_ulp": 128}},
    "sfu_slots": {"unit": "vec_sfu", "modes": [{"count": 1, "format": "bf16"}, {"count": 2, "format": "fp16"}], "functions": [],
                  "slots": [{"approx": "pwl", "segments": 64}, {"approx": "pwq", "segments": 8}],
                  "rounding": ["SR", "RNE"], "sr_bits": 6, "n_random": 60, "flags": ["inexact", "invalid"]},
    "sfu_posit_slot": {"unit": "vec_sfu", "modes": [{"count": 1, "format": "posit16_1"}], "functions": [],
                       "slots": [{"approx": "pwq", "segments": 24}], "n_random": 60},
}


def _run(cmd, cwd, timeout=900):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 124, "", f"timeout after {timeout} s")


def run_case(name, spec, work):
    spec = dict(spec)
    check = spec.pop("check", False)
    alias = spec.pop("alias", None)
    core_families = spec.pop("core_families", None)
    unit = spec["unit"]
    spec.setdefault("n_random", 40)
    spec.setdefault("seed", 7)
    spec["dut_name"] = {"alu": "alu_core", "vec_sfu": "sfu_core", "vec_dot_acc": "dot_core"}[unit]
    if check:
        from chialu.targets.derive import detect_budget
        spec.setdefault("checker_family", "residue")
        spec.update({"checker_name": spec["dut_name"].replace("core", "checker"), "modulus": 15,
                     "n_random_masks": spec.get("n_random_masks", 600)})
        spec["detect"] = detect_budget(spec, spec["n_random_masks"])
        if alias is not None:
            spec["detect"]["random_alias"] = ("<=", alias)
    if unit == "alu":
        from chialu.verify.alu_ref import normalize_spec
        spec = normalize_spec(spec)
    elif unit == "vec_dot_acc":
        from chialu.verify.dot_ref import normalize_dot_spec
        spec = normalize_dot_spec(spec)
    else:
        from chialu.verify.sfu_ref import normalize_sfu_spec
        spec = normalize_sfu_spec(spec)
    out = Path(work) / name
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    seed = derive.seed_for(spec, families=core_families)
    chk, prot = checkers.checker_for(spec) if check else ("", [])
    b = bundles.build_from_spec(name, spec, out, {}, seed, "", chk or None)
    (out / "seed.sv").write_text(seed)
    if chk:
        (out / "checker.sv").write_text(chk)
    from chialu.verify import simulate as SIM
    r = _run(["verilator", *SIM.VERILATOR_FLAGS, "-j", str(SIM.VERILATOR_JOBS),
              "--top-module", "tb", "-Mdir", "obj_conf", "-o", "sim", "tb.sv", "seed.sv"], out)
    if r.returncode:
        return f"{name}: seed compile error: {r.stderr[:300]}"
    r = _run(["./obj_conf/sim"], out)
    if b.exact:
        conf = [l for l in r.stdout.splitlines() if "CONFORMANCE" in l]
        ok = bool(conf) and "PASS" in conf[0]
        detail = conf[0] if conf else "no verdict"
    else:
        ok, viol, rep = b.conf_check((out / "dump.hex").read_text())
        detail = "accuracy PASS" if ok else f"accuracy FAIL {viol}"
        m = rep.summary()
        detail += f" (max_ulp {m['max_ulp']}, wrong {m['n_wrong']}/{m['n']})"
    line = f"{name}: {b.n_vectors} vectors, {detail}"
    if check:
        r = _run(["verilator", *SIM.VERILATOR_FLAGS, "-j", str(SIM.VERILATOR_JOBS),
                  "--top-module", "tb", "-Mdir", "obj_fault", "-o", "sim",
                  "fault_tb.sv", "seed.sv", "checker.sv"], out)
        if r.returncode:
            return line + f"; fault compile error: {r.stderr[:300]}"
        _run(["./obj_fault/sim"], out)
        fok, viol, rep = b.fault_check((out / "fault_dump.hex").read_text())
        line += f"; fault gate {'PASS' if fok else 'FAIL ' + str(viol)} (protected {prot})"
        ok = ok and fok
    return line + f" [{time.time() - t0:.0f}s]" + ("" if ok else "  <-- FAIL")


def main():
    args = sys.argv[1:]
    work = args[0] if args and Path(args[0]).is_dir() else tempfile.mkdtemp(prefix="chialu_smoke_")
    names = [a for a in args if a in CASES] or list(CASES)
    print(f"[smoke_eda] {len(names)} cases under {work}")
    fails = 0
    for name in names:
        try:
            line = run_case(name, CASES[name], work)
        except Exception as e:  # noqa: BLE001
            line = f"{name}: ERROR {type(e).__name__}: {str(e)[:200]}  <-- FAIL"
        print("  " + line, flush=True)
        fails += "<-- FAIL" in line
    print(f"[smoke_eda] {len(names) - fails}/{len(names)} pass")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
