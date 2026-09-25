"""The chialu.ALU seed matrix: every parameter dimension of the unit class
through the instance path and the three machine models.

Each case is an instance yaml (every parameter bound, as the front end
demands), loaded through adir into a bound instance,
whose registered generators write the seed and the checker; the derived
verify bundle then runs under Verilator:

  conformance   the seed against the Python reference (bit-exact
                testbench), or the arithmetic-error model with the
                instance's ArithmeticError budget for approximate units
  fault gate    the generated checker under the fault harness: false
                alarms, single-bit coverage, random alias rate
  mutants       a wrapped seed (a flipped result bit, a dropped flag, a
                set unused bit) and a mute checker: each named gate must
                fail, which proves the gate is live
  load errors   the front end's load-time checks on invalid instances

    python3 -m chialu.verify.alu_matrix [-j N] [--work DIR] [--list]
                                        [--tag TAG ...] [--only NAME ...]
                                        [--json FILE]
"""
from __future__ import annotations

import argparse
import json
import re
import multiprocessing
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

CONVENTION_DEFAULTS = {
    "nan_payload": "canonical", "invalid_result": "saturate",
    "nan_to_int": "zero", "minmax_nan": "propagate", "tininess": "after",
    "int_div_zero": "riscv", "zero_sign": "positive",
    "quire_overflow": "wrap", "block_scale_rounding": "nearest",
    "block_element_overflow": "saturate", "sr_compare": "gt",
    "check_flags": False,
}
INT_FLAGS = ["carry", "int_overflow", "overflow", "div_zero"]
FP_FLAGS = ["invalid", "div_zero", "overflow", "underflow", "inexact",
            "nan", "denormal", "unordered"]
ALL_FLAGS = ["invalid", "div_zero", "overflow", "underflow", "inexact",
             "nan", "denormal", "carry", "int_overflow", "unordered"]
DIV_OPS = {"div", "quot", "rem", "mod"}


@dataclass
class Case:
    name: str
    tags: tuple
    modes: list                     # [{count, format}]
    ops: list
    params: dict = field(default_factory=dict)   # yaml parameter overrides
    modulus: int | None = None      # a checked unit pins residue mod M
    n_random: int = 40
    n_masks: int = 600
    alias: float | None = None      # random_alias bound (default 1.1 / M)
    constraints: list = field(default_factory=list)   # yaml constraints
    mutant: str | None = None       # seed wrapper: lsb | flag | hi_bit
    checker_mutant: str | None = None   # mute: check_err stuck at 0
    expect: str = "pass"            # pass | fail | load_error
    etc_single: bool = False        # bind a one-element modes/ops as ETC
    note: str = ""


def _fmt_sr_bits(modes) -> int:
    from chialu.verify.alu_ref import default_sr_bits
    from chialu.verify.formats import parse_format
    return default_sr_bits([(m["count"], parse_format(m["format"]))
                            for m in modes])


def _sel_prefix(sel: str) -> str:
    """A structure selector of the seed (a kind, an id, a glob over ids)
    as the variable prefix of that structure's family space."""
    if "." in sel:
        parts = sel.split(".")
        # the lanes of a mode share their decisions: the variable index carries no lane part
        # (`m1.*.adder` and `m1.l0.adder` both name core.adder.m1)
        idx = [q for q in parts[:-1] if q != "*" and not re.fullmatch(r"l\d+", q)]
        return f"core.{parts[-1]}." + ".".join(idx)
    return f"core.{sel}.*"


def _arch_variables(extra_arch: dict, variables: dict):
    """The old per-structure controls of a case as variable bindings."""
    core = dict((extra_arch or {}).get("core") or {})
    if "family" in core:
        variables["core.family"] = {"fixed": core["family"]}
    for sel, spec in (core.get("structures") or {}).items():
        prefix = _sel_prefix(sel)
        spec = dict(spec or {})
        if "variant" in spec:
            from chialu.archdocs import resolve_variant
            v = resolve_variant(spec.pop("variant"))
            spec["family"] = v.family
            for k, val in v.pin.items():
                variables[f"{prefix}.{k}"] = {"fixed": val}
        if "family" in spec:
            variables[f"{prefix}.family"] = {"fixed": spec["family"]}
        for k, val in (spec.get("pin") or {}).items():
            variables[f"{prefix}.{k}"] = {"fixed": val}
    chk = (extra_arch or {}).get("checker") or {}
    if "family" in chk:
        variables["checker.family"] = {"fixed": chk["family"]}
    for k, val in (chk.get("pin") or {}).items():
        variables[f"checker.{k}"] = {"fixed": val}


def instance_doc(c: Case) -> dict:
    """The run file of a case: every variable of chialu.ALU bound, the
    checker pinned when the unit is checked, the evaluation graph the
    declaration check alone (the matrix runs the simulators itself)."""
    p = dict(c.params)
    extra_arch = p.pop("_arch", None)

    def fixed(name, default):
        return {"fixed": p.pop(name, default)}

    def fixed_or_runtime(name, default):
        v = p.pop(name, default)
        if isinstance(v, (list, tuple)):
            return {"runtime": list(v)} if len(v) > 1 else {"fixed": v[0]}
        return {"fixed": v}

    v = {}
    v["modes"] = {"runtime": list(c.modes)} if len(c.modes) > 1 else {"fixed": c.modes[0]}
    v["ops"] = {"runtime": list(c.ops)} if len(c.ops) > 1 else {"fixed": c.ops[0]}
    check_block = p.pop("check", None)                 # the rule table (docs/checker-spec-plan.md)
    checked = c.modulus is not None or check_block is not None
    if check_block is not None:
        v["check"] = {"fixed": check_block}
        p.pop("check_en", None)
    else:
        v["check_en"] = fixed_or_runtime("check_en", [True] if checked else [False])
    if DIV_OPS & set(c.ops):
        v["quotient_semantics"] = fixed_or_runtime("quotient_semantics", "truncate_zero")
    else:
        p.pop("quotient_semantics", None)
    v["accuracy"] = fixed("accuracy", "exact")
    approx = v["accuracy"]["fixed"] == "approximate"
    if approx:
        v["accuracy_ctl"] = fixed("accuracy_ctl", "static")
        one = {k["metric"].split(".")[-1]: k["le"] for k in c.constraints if "le" in k} or {"max_ulp": 1.0}
        if v["accuracy_ctl"]["fixed"] == "runtime":
            # one budget per accuracy mode, the case's own list or the same bound in every mode
            n = int(p.pop("accuracy_modes", 2))
            v["accuracy_modes"] = {"fixed": n}
            v["error_budget"] = {"fixed": p.pop("mode_budgets", None) or [one] * n}
        else:
            v["error_budget"] = {"fixed": one}
    v["rounding"] = fixed_or_runtime("rounding", "RNE")
    v["daz_in"] = fixed_or_runtime("daz_in", [False])
    v["ftz_out"] = fixed_or_runtime("ftz_out", [False])
    v["unary_dual"] = fixed_or_runtime("unary_dual", False)
    v["flags"] = fixed("flags", [])
    v["sr_bits"] = fixed("sr_bits", _fmt_sr_bits(c.modes))
    v["clock_ps"] = fixed("clock_ps", 3000)
    for name, dflt in CONVENTION_DEFAULTS.items():
        v[name] = fixed(name, dflt)
    v["check_sr"] = fixed_or_runtime("check_sr", True)
    v["verify.n_random"] = {"fixed": int(c.n_random)}
    v["verify.seed"] = {"fixed": 7}
    if checked or True in ((v.get("check_en") or {}).get("runtime") or [(v.get("check_en") or {}).get("fixed")]):
        v["verify.n_random_masks"] = {"fixed": int(c.n_masks)}
    if p:
        raise ValueError(f"{c.name}: unknown parameter overrides {sorted(p)}")
    v["core.family"] = {"fixed": "unit_per_class"}
    v["core.*"] = {"search": "all"}
    if checked and check_block is None:
        v["checker.family"] = {"fixed": "residue"}
        v["checker.modulus"] = {"fixed": c.modulus}
        v["checker.generator_style"] = {"fixed": "csa_tree"}
        v["checker.comparator.family"] = {"fixed": "direct_compare"}
    if extra_arch:
        _arch_variables(extra_arch, v)
    artifacts = {"core": {"role": "seed", "kind": "text", "source": "generated",
                          "language": "systemverilog", "evolve": ["alu_core", "alu_core_u_*"]},
                 "verify_bundle": {"role": "fixed", "kind": "text", "source": "generated",
                                   "indexed_by": "verify_files"}}
    if checked or True in ((v.get("check_en") or {}).get("runtime") or []):
        artifacts["checker"] = {"role": "fixed", "kind": "text", "source": "generated",
                                "language": "systemverilog"}
    constraints = [{"metric": "declaration.ok", "eq": True, "hard": True}]
    if approx:
        constraints.append({"metric": "declaration.ok", "eq": True, "satisfies": "error_bound"})
    return {"module": "chialu.ALU", "variables": v, "artifacts": artifacts,
            "evaluate": {"nodes": {"declaration": {"node": "adir.declaration"}}, "feedback": []},
            "constraints": constraints, "goal": {"maximize": "declaration.ok"},
            "search": {"backend": "adaevolve", "iterations": 1,
                       "seeds": {"generated": ["baseline"]},
                       "models": {"solution": {"agent": "claude", "model": "claude-opus-5"}}},
            "archive": {"store": "jsonl", "path": "results_db.jsonl"}}


def load_case(c: Case, out: Path):
    from adir.instance import load
    doc = instance_doc(c)
    path = out / "run.yaml"
    path.write_text(yaml.safe_dump({"cluster_name": c.name, "adir": doc}, sort_keys=False))
    return load(path, run_dir_override=str(out / "run"))


def _port_decls(ports):
    return ",\n".join(f"  {'input ' if p.direction == 'in' else 'output'} "
                      f"logic [{p.width-1}:0] {p.name}" for p in ports)


def wrap_seed(seed: str, lay: dict, top: str, kind: str) -> str:
    """The seed renamed to <top>_orig inside a wrapper <top> that corrupts
    one thing: `lsb` flips y[0]; `flag` clears flags[0]; `hi_bit` sets the
    top bit of y (an unused bit for every op narrower than y)."""
    orig = seed.replace(f"module {top} ", f"module {top}_orig ", 1) \
               .replace(f"module {top}(", f"module {top}_orig(", 1)
    ports = list(lay["core_in"]) + list(lay["core_out"])
    y_w = lay["y_w"]
    conns = []
    decl = []
    for p in ports:
        if p.direction == "in":
            conns.append(f".{p.name}({p.name})")
        else:
            decl.append(f"  logic [{p.width-1}:0] {p.name}_o;")
            conns.append(f".{p.name}({p.name}_o)")
    assigns = []
    for p in lay["core_out"]:
        expr = f"{p.name}_o"
        if p.name == "y" and kind == "lsb":
            expr = f"{p.name}_o ^ {y_w}'d1"
        elif p.name == "y" and kind == "hi_bit":
            expr = f"{p.name}_o | ({y_w}'d1 << {y_w - 1})"
        elif p.name == "flags" and kind == "flag":
            expr = f"{p.name}_o & ~{p.width}'d1"
        assigns.append(f"  assign {p.name} = {expr};")
    wrapper = "\n".join([f"module {top} (", _port_decls(ports), ");"] + decl
                        + [f"  {top}_orig u_orig ({', '.join(conns)});"]
                        + assigns + ["endmodule", ""])
    return orig + "\n" + wrapper


def mute_checker(lay: dict, spec: dict, name: str) -> str:
    """A checker with the generated checker's ports whose check_err never
    rises: the fault gate must reject it on single-bit coverage."""
    from chialu.verify.ports import Port
    ports = list(lay["core_in"]) + list(lay["chk_extra"])
    ports.append(Port("y", "in", lay["y_w"]))
    if lay["d_w"]:
        ports.append(Port("d", "in", lay["d_w"]))
    if lay["flags"] and spec.get("check_flags"):
        ports.append(Port("flags", "in", lay["v_max"] * len(lay["flags"])))
    ports.append(Port("check_err", "out", 1))
    return "\n".join([f"module {name} (", _port_decls(ports), ");",
                      "  assign check_err = 1'b0;", "endmodule", ""])


# ---------------------------------------------------------------- run --


def _source(out: Path, name: str) -> str:
    """The candidate as the simulator reads it, which is the file itself:
    Verilator takes the generated SystemVerilog as written, and the flow
    converts nothing (chialu.eda does the same)."""
    return name


def _run(cmd, cwd, timeout=1800):
    """A tool run in its own process group, which a timeout kills whole
    (verilator forks a parallel C++ build that would otherwise outlive
    the timed-out driver)."""
    from chialu.verify.simulate import run_group
    return run_group(cmd, cwd=cwd, timeout=timeout)


def run_case(c: Case, work: str) -> dict:
    """One case: load, generate, simulate; returns the result record."""
    t0 = time.time()
    out = Path(work) / c.name
    out.mkdir(parents=True, exist_ok=True)
    rec = {"name": c.name, "tags": list(c.tags), "expect": c.expect,
           "note": c.note}
    try:
        inst = load_case(c, out)
    except (Exception, SystemExit) as e:  # noqa: BLE001
        rec["load_error"] = f"{type(e).__name__}: {str(e)[:300]}"
        rec["ok"] = c.expect == "load_error"
        rec["seconds"] = round(time.time() - t0, 1)
        return rec
    if c.expect == "load_error":
        rec["ok"] = False
        rec["detail"] = "loaded without error"
        rec["seconds"] = round(time.time() - t0, 1)
        return rec
    from chialu.targets import bundles, derive
    from chialu.verify import alu_ref as A
    overrides = {}
    if c.modulus is not None:
        overrides["detect"] = {"random_alias": ["<=", c.alias if c.alias is not None
                                                else 1.1 / c.modulus]}
    spec = derive.spec_from_bindings(inst.template.name, inst.bindings)
    seed_text = inst.artifacts["core"].text
    checker_text = inst.artifacts["checker"].text if "checker" in inst.artifacts else None
    b = bundles.build_from_spec(c.name, spec, out / "verify", {}, seed_text, "",
                                checker_text, overrides)
    spec = A.normalize_spec(b.spec)
    lay = A.alu_layout(spec)
    top = b.dut
    seed = b.seed_text
    if c.mutant:
        seed = wrap_seed(seed, lay, top, c.mutant)
    checker = b.checker_rtl or ""
    if c.checker_mutant and checker:
        checker = mute_checker(lay, spec, b.checker_name)
    (out / "seed.sv").write_text(seed)
    for f, txt in b.files.items():
        (out / f).write_text(txt)
    rec.update({"n_vectors": b.n_vectors, "seed_chars": len(seed),
                "exact": b.exact, "checked": bool(checker),
                "structures": len(inst.elaboration.info.get("manifest") or []),
                "searched": len(inst.searched()),
                "modes": [f"{n}x{f.name}" for n, f in lay["modes"]],
                "ops": list(lay["ops"])})
    try:
        src = _source(out, "seed.sv")
    except RuntimeError as e:
        rec["ok"] = False
        rec["detail"] = str(e)
        rec["seconds"] = round(time.time() - t0, 1)
        return rec
    from chialu.verify import simulate as SIM
    res = SIM.simulate([src], "tb.sv", out, work="c", compile_timeout=1800, run_timeout=1800)
    rec["simulator"] = res.simulator
    rec["sim_seconds"] = {"compile": round(res.compile_s, 1), "run": round(res.run_s, 1)}
    if not res.ok and res.phase == "compile":
        rec["ok"] = False
        rec["detail"] = "seed compile error: " + res.detail[:400]
        rec["seconds"] = round(time.time() - t0, 1)
        return rec
    r = res
    (out / "sim.log").write_text(res.stdout + res.detail)
    gates = {}
    if b.exact:
        conf = [l for l in r.stdout.splitlines() if "CONFORMANCE" in l]
        ok = bool(conf) and "PASS" in conf[0]
        gates["conformance"] = {"pass": ok, "detail": conf[0] if conf else "no verdict"}
        if not ok:
            mism = [l for l in r.stdout.splitlines() if "MISMATCH" in l][:3]
            gates["conformance"]["mismatches"] = [b.explain(l) if b.explain else l
                                                  for l in mism]
    else:
        dump = out / "dump.hex"
        if not dump.exists():
            gates["accuracy"] = {"pass": False, "detail": "no dump"}
        else:
            ok, viol, rep = b.conf_check(dump.read_text())
            gates["accuracy"] = {"pass": ok, "detail": viol,
                                 "metrics": rep.summary()}
    if checker:
        # the fault gate as the EDA worker runs it: the seed, the checker and
        # the shipped fault files alone, in their own directory
        fdir = out / "fault"
        fdir.mkdir(exist_ok=True)
        (fdir / "seed.sv").write_text(seed)
        (fdir / "checker.sv").write_text(checker)
        for f, txt in b.fault_files.items():
            (fdir / f).write_text(txt)
        fres = SIM.simulate([_source(fdir, "seed.sv"), "checker.sv"], "fault_tb.sv", fdir, work="f",
                            compile_timeout=1800, run_timeout=1800)
        if not fres.ok and fres.phase == "compile":
            gates["fault"] = {"pass": False,
                              "detail": "checker compile error: " + fres.detail[:400]}
        else:
            (fdir / "sim.log").write_text(fres.stdout + fres.detail)
            if "Unable to open" in fres.stdout + fres.detail:
                gates["fault"] = {"pass": False, "detail": "the fault testbench could not "
                                  "read a shipped file: " + (fres.stdout + fres.detail)[:300]}
                rec["gates"] = gates
                rec["ok"] = False
                rec["seconds"] = round(time.time() - t0, 1)
                return rec
            fd = fdir / "fault_dump.hex"
            if not fd.exists():
                gates["fault"] = {"pass": False, "detail": "no fault dump"}
            else:
                fok, viol, rep = b.fault_check(fd.read_text())
                gates["fault"] = {"pass": fok, "detail": viol,
                                  "metrics": rep.summary()}
        rec["protected"] = _protected(b)
    rec["gates"] = gates
    all_pass = all(g["pass"] for g in gates.values())
    if c.expect == "pass":
        rec["ok"] = all_pass
    else:                                   # a mutant: the named gates fail
        want_fail = _gates_that_must_fail(c)
        rec["ok"] = all(not gates[g]["pass"] for g in want_fail if g in gates) \
            and all(g in gates for g in want_fail)
        rec["must_fail"] = want_fail
    rec["seconds"] = round(time.time() - t0, 1)
    return rec


def _protected(b) -> list:
    txt = b.unit.get("brief", "") if isinstance(b.unit, dict) else ""
    import re
    m = re.search(r"residue mod \d+ for ([^;]*);", txt)
    return [s.strip() for s in m.group(1).split(",") if s.strip()] if m else []


def _gates_that_must_fail(c: Case) -> list:
    if c.checker_mutant:
        return ["fault"]
    if c.mutant in ("lsb", "hi_bit"):
        gates = ["accuracy"] if c.params.get("accuracy") == "approximate" \
            else ["conformance"]
        if c.modulus is not None:
            gates.append("fault")           # false alarms on the clean pass
        return gates
    if c.mutant == "flag":
        return ["conformance"]
    return ["conformance"]


def _worker(args):
    c, work = args
    try:
        return run_case(c, work)
    except (Exception, SystemExit) as e:  # noqa: BLE001 — a SystemExit
        # inside a pool worker would otherwise hang the pool
        return {"name": c.name, "tags": list(c.tags), "expect": c.expect,
                "ok": False, "detail": f"ERROR {type(e).__name__}: {str(e)[:300]}",
                "trace": traceback.format_exc()[-1500:]}


# --------------------------------------------------------------- cases --

def _m(count, fmt):
    return {"count": count, "format": fmt}


def cases() -> list:
    C = []
    add = C.append
    # ---- A. integer family
    add(Case("int8_arith_checked", ("int",), [_m(1, "int8")],
             ["add", "sub", "adc", "sbb", "neg", "abs", "add_sat", "sub_sat"],
             modulus=15))
    add(Case("int16_mul_checked", ("int",), [_m(1, "int16")],
             ["mul", "mul_wide", "mul_high", "mul_sat"], modulus=15))
    add(Case("int16_div_trunc_flags", ("int",), [_m(1, "int16")],
             ["div", "quot", "rem", "mod"],
             params={"quotient_semantics": "truncate_zero", "flags": INT_FLAGS}))
    add(Case("int16_div_floor", ("int",), [_m(1, "int16")],
             ["div", "quot", "rem", "mod"], params={"quotient_semantics": "floor"}))
    add(Case("int16_div_both_divzero_zero", ("int",), [_m(1, "int16")],
             ["quot", "rem", "div", "mod"],
             params={"quotient_semantics": ["truncate_zero", "floor"],
                     "int_div_zero": "zero", "flags": ["div_zero"]}))
    add(Case("uint8_all_classes_checked", ("int",), [_m(1, "uint8")],
             ["add", "sub", "mul", "mul_wide", "quot", "rem", "min", "max", "cmp",
              "shl", "shr_logical", "rol", "ror", "and", "or", "xor", "not",
              "popcount", "clz", "ctz"], modulus=15))
    add(Case("int8_ones_preserve_checked", ("int",), [_m(1, "int8_ones")],
             ["add", "sub", "adc", "sbb", "neg", "abs", "mul", "mul_wide",
              "mul_high", "quot", "rem", "min", "cmp", "shr_arith", "not"],
             params={"zero_sign": "preserve"}, modulus=15))
    add(Case("int8_sm_positive_checked", ("int",), [_m(1, "int8_sm")],
             ["add", "sub", "neg", "abs", "mul", "mul_wide", "mul_sat", "div", "mod",
              "max", "cmp", "xor", "popcount"], modulus=15))
    add(Case("bcd3_checked", ("int",), [_m(1, "bcd3")],
             ["add", "sub", "adc", "sbb", "mul", "mul_wide", "mul_high", "quot",
              "rem", "min", "max", "cmp"], modulus=15))
    add(Case("int_subword_3modes_runtime_check_en", ("int", "multi"),
             [_m(1, "int32"), _m(2, "int16"), _m(4, "int8")],
             ["add", "sub", "neg", "min", "max", "cmp", "shl", "shr_arith",
              "and", "xor", "popcount", "clz"],
             params={"check_en": [True, False]}, modulus=15, n_random=20))
    add(Case("odd_widths_uint4x4_int12", ("int", "multi"),
             [_m(4, "uint4"), _m(1, "int12")],
             ["shl", "shr_logical", "shr_arith", "rol", "ror", "and", "or",
              "popcount", "clz", "ctz", "add", "mul_wide"], modulus=7))
    add(Case("int16_all_int_flags_check_flags", ("int",), [_m(1, "int16")],
             ["add", "sub", "adc", "sbb", "neg", "abs", "mul", "mul_high", "quot",
              "rem", "add_sat"],
             params={"flags": INT_FLAGS, "check_flags": True}, modulus=15))
    # ---- B. fixed point
    add(Case("fixed_s1i7f8_checked", ("fixed",), [_m(1, "fxs1i7f8")],
             ["add", "sub", "neg", "abs", "mul", "mul_wide", "div", "rem"],
             modulus=15))
    add(Case("fixed_u4f4_sat_rtz", ("fixed",), [_m(1, "fxs0i4f4")],
             ["add_sat", "sub_sat", "mul_sat", "mul", "quot"],
             params={"rounding": "RTZ"}))
    add(Case("fixed_s1i3f12_directed_roundings", ("fixed", "runtime"),
             [_m(1, "fxs1i3f12")], ["mul", "div", "mul_sat", "rem"],
             params={"rounding": ["RNE", "RTZ", "RDN", "RUP"],
                     "flags": ["inexact", "overflow"]}))
    add(Case("fixed_sr_exact_checked", ("fixed", "sr"), [_m(1, "fxs1i7f8")],
             ["mul", "div", "add"],
             params={"rounding": "SR", "sr_bits": 8}, modulus=15))
    add(Case("fixed_cvt_out", ("fixed", "cvt"), [_m(1, "fxs1i7f8")],
             ["cvt(int8)", "cvt(fp16)", "cvt(fxs1i3f4)", "cvt(uint16)", "add"],
             params={"rounding": ["RNE", "RDN"]}))
    # ---- C. floats
    add(Case("fp16_arith_all_flags", ("float",), [_m(1, "fp16")],
             ["fadd", "fsub", "fmul"], params={"flags": FP_FLAGS}))
    add(Case("fp16x2_div_sqrt", ("float",), [_m(2, "fp16")], ["fdiv", "fsqrt"]))
    add(Case("bf16_compare_minmax_number", ("float",), [_m(1, "bf16")],
             ["fcmp", "fmin", "fmax", "fabs", "fneg"],
             params={"minmax_nan": "number", "flags": ["unordered", "nan", "invalid"]}))
    add(Case("fp32_directed_roundings_tininess_before", ("float", "runtime"),
             [_m(1, "fp32")], ["fadd", "fmul", "fdiv"],
             params={"rounding": ["RNE", "RTZ", "RDN", "RUP"],
                     "tininess": "before", "flags": ["underflow", "inexact"]},
             n_random=30))
    add(Case("fp16_sr_window_checked", ("float", "sr"), [_m(1, "fp16")],
             ["fadd", "fmul", "fsqrt"],
             params={"rounding": "SR", "sr_bits": 10, "check_sr": False},
             modulus=15, alias=0.6))
    add(Case("fp16_sr_runtime_check_sr", ("float", "sr", "runtime"),
             [_m(1, "fp16")], ["fadd", "fmul", "cvt(int8)"],
             params={"rounding": ["RNE", "SR"], "sr_bits": 6,
                     "check_sr": [True, False]}, modulus=15, alias=0.6))
    add(Case("fp8e4m3_no_inf_invalid_zero", ("float",), [_m(2, "fp8e4m3")],
             ["fadd", "fmul", "fdiv", "fsqrt", "fmax"],
             params={"invalid_result": "zero", "flags": ["invalid", "overflow", "nan"]}))
    add(Case("fp8e5m2_nan_propagate", ("float",), [_m(1, "fp8e5m2")],
             ["fadd", "fmul", "fdiv", "fmin", "fabs"],
             params={"nan_payload": "propagate", "flags": ["nan", "invalid"]}))
    add(Case("fp4e2m1_no_specials", ("float",), [_m(1, "fp4e2m1")],
             ["fadd", "fmul", "fdiv", "fsqrt", "fmin", "fcmp", "fneg"],
             params={"flags": ["overflow", "inexact", "invalid"]}, n_random=60))
    add(Case("fp6_two_formats_cvt", ("float", "multi", "cvt"),
             [_m(1, "fp6e3m2"), _m(1, "fp6e2m3")],
             ["fadd", "fmul", "cvt(fp6e3m2)", "cvt(fp6e2m3)", "cvt(fp16)"]))
    add(Case("unsigned_float_fps0e5m6", ("float",), [_m(1, "fps0e5m6NI")],
             ["fadd", "fsub", "fmul", "fdiv", "fsqrt", "fcmp", "cvt(fp16)"],
             params={"flags": ["invalid", "nan", "inexact"]}))
    add(Case("e8m0_exp_only", ("float",), [_m(1, "e8m0")],
             ["fmul", "fdiv", "fadd", "cvt(fp16)", "cvt(int16)"],
             params={"flags": ["inexact", "overflow"]}))
    add(Case("fp64", ("float", "slow"), [_m(1, "fp64")],
             ["fadd", "fsub", "fmul", "fdiv", "fsqrt", "fcmp"], n_random=20))
    add(Case("fp80", ("float", "slow"), [_m(1, "fp80")],
             ["fadd", "fmul", "fdiv", "cvt(fp64)", "cvt(int32)"], n_random=20))
    add(Case("fp16_daz_ftz_runtime", ("float", "runtime"), [_m(1, "fp16")],
             ["fadd", "fmul", "fdiv", "cvt(bf16)"],
             params={"daz_in": [False, True], "ftz_out": [False, True],
                     "flags": ["underflow", "denormal", "inexact"]}))
    add(Case("fp16x4_unary_dual_d_port", ("float", "dual"), [_m(4, "fp16")],
             ["fabs", "fneg", "fsqrt", "cvt(int16)", "fadd"],
             params={"unary_dual": True, "flags": ["invalid", "inexact"]}))
    add(Case("dual_in_y_int_mul_wide_fp_unary", ("float", "int", "dual", "multi"),
             [_m(1, "int16"), _m(1, "fp16")],
             ["mul_wide", "fabs", "fneg", "neg", "cvt(int16)"],
             params={"unary_dual": [False, True]}, modulus=15))
    # ---- D. posit
    add(Case("posit16_1_arith_checked", ("posit",), [_m(1, "posit16_1")],
             ["fadd", "fsub", "fmul", "fdiv", "fsqrt"], modulus=15, n_random=40))
    add(Case("posit8_0_all_fp_ops", ("posit",), [_m(1, "posit8_0")],
             ["fadd", "fsub", "fmul", "fdiv", "fsqrt", "fcmp", "fmin", "fmax",
              "fabs", "fneg"], params={"flags": ["nan", "invalid", "inexact"]},
             n_random=60))
    add(Case("posit32_2_cvt", ("posit", "cvt", "slow"), [_m(1, "posit32_2")],
             ["fadd", "fmul", "cvt(fp32)", "cvt(int32)", "cvt(posit16_1)"],
             n_random=20))
    # ---- E. blocks
    add(Case("mxfp4_block_ops", ("block", "slow"),
             [_m(1, "blksfps0e8m0Nefp4e2m1s32")],
             ["fadd", "fmul", "fabs", "fneg", "fcmp", "fmin"], n_random=6))
    add(Case("block_fp8e5m2_elem_inf_scale_up", ("block",),
             [_m(1, "blksfps1e4m3Nefp8e5m2s8")],
             ["fadd", "fmul", "fdiv", "fmax"],
             params={"block_scale_rounding": "up", "block_element_overflow": "inf",
                     "flags": ["overflow", "inexact", "invalid"]}, n_random=8))
    add(Case("mxint8_block", ("block",), [_m(1, "blksfps0e8m0Neint8s32")],
             ["fadd", "fmul", "fneg"], n_random=6))
    add(Case("block_scalar_cvt_both_ways", ("block", "cvt", "multi", "slow"),
             [_m(1, "blksfp8e4m3efp4e2m1s16"), _m(16, "fp16")],
             ["fadd", "fmul", "cvt(blksfp8e4m3efp4e2m1s16)", "cvt(fp16)", "cvt(int8)"],
             modulus=15, n_random=6))
    # ---- F. conversions
    add(Case("int16_cvt_everything", ("int", "cvt", "runtime"), [_m(1, "int16")],
             ["cvt(fp16)", "cvt(bf16)", "cvt(fp32)", "cvt(int8)", "cvt(uint8)",
              "cvt(int32)", "cvt(fxs1i7f8)", "cvt(posit16_1)"],
             params={"rounding": ["RNE", "RTZ"], "flags": ["inexact", "overflow"]}))
    add(Case("fp16_cvt_to_int_nan_max", ("float", "cvt"), [_m(1, "fp16")],
             ["cvt(int16)", "cvt(uint16)", "cvt(int8)", "cvt(fxs1i7f8)"],
             params={"nan_to_int": "max", "flags": ["invalid", "inexact", "overflow"]}))
    add(Case("fp16_cvt_to_int_nan_min_rdn", ("float", "cvt"), [_m(1, "fp16")],
             ["cvt(int16)", "cvt(int8)", "cvt(uint8)"],
             params={"nan_to_int": "min", "rounding": "RDN"}))
    add(Case("fp32_cvt_narrow_directed", ("float", "cvt", "runtime"), [_m(1, "fp32")],
             ["cvt(fp16)", "cvt(bf16)", "cvt(fp8e4m3)", "cvt(fp8e5m2)",
              "cvt(fp4e2m1)", "cvt(posit16_1)", "cvt(e8m0)"],
             params={"rounding": ["RNE", "RDN", "RUP", "RTZ"],
                     "flags": ["overflow", "inexact", "invalid"]}, n_random=30))
    add(Case("posit_fp_cvt_two_modes", ("posit", "float", "cvt", "multi"),
             [_m(1, "posit16_1"), _m(1, "fp16")],
             ["cvt(fp16)", "cvt(posit16_1)", "cvt(int16)", "fadd"]))
    add(Case("exotic_encodings_cvt", ("int", "cvt", "multi"),
             [_m(1, "int8_ones"), _m(1, "int8_sm"), _m(1, "bcd2")],
             ["cvt(int8)", "cvt(fp16)", "cvt(uint8)", "add", "mul_wide"],
             modulus=15))
    # ---- G. approximate (the error model)
    # an approximate unit with a bounded error: a lower-part-OR adder (4 approximate low bits, no carry into
    # the exact upper part: at most 16 off on the ring of errors.compare) and the default truncated
    # fixed-width multiplier, whose high product half is within a few LSBs. The low product half (`mul`)
    # is where the truncation falls, and the space's default adder (segmented_carry_speculative with 4-bit
    # sub-adders and no speculation) drops every inter-segment carry, so neither is asserted here; a
    # relative metric (mred) is dominated by results near zero, so the case asserts med and max_abs
    add(Case("approx_int16_med", ("approx",), [_m(1, "int16")],
             ["add", "sub", "mul_high"],
             params={"accuracy": "approximate",
                     "_arch": {"core": {"structures": {"adder": {
                         "family": "lower_part_approximate",
                         "pin": {"lower_width": 4, "lower_cell": "or_gate", "carry_to_upper": "none"}}}}}},
             constraints=[{"metric": "ArithmeticError.med", "le": 8.0},
                          {"metric": "ArithmeticError.max_abs", "le": 32}]))
    add(Case("approx_fp16_ulp_rate", ("approx",), [_m(1, "fp16")],
             ["fadd", "fmul", "fdiv"],
             params={"accuracy": "approximate"},
             constraints=[{"metric": "ArithmeticError.max_ulp", "le": 2},
                          {"metric": "ArithmeticError.error_rate", "le": 0.1}]))
    add(Case("approx_with_checker_is_load_error", ("approx", "load"), [_m(1, "int16")],
             ["add", "mul"], params={"accuracy": "approximate"}, modulus=15,
             constraints=[{"metric": "ArithmeticError.mred", "le": 0.01}],
             expect="load_error"))
    # ---- H. mutants: the gates must fail
    add(Case("mutant_lsb_int_checked", ("mutant", "int"), [_m(1, "int16")],
             ["add", "sub", "mul_wide", "min"], modulus=15, mutant="lsb",
             expect="fail", note="y[0] flipped: conformance and false alarms"))
    add(Case("mutant_flag_fp_check_flags", ("mutant", "float"), [_m(1, "fp16")],
             ["fadd", "fmul"], params={"flags": ["inexact", "invalid"],
                                       "check_flags": True},
             modulus=15, mutant="flag", expect="fail",
             note="flags[0] cleared: conformance"))
    add(Case("mutant_lsb_approx_tight", ("mutant", "approx"), [_m(1, "int16")],
             ["add", "mul"], params={"accuracy": "approximate"},
             constraints=[{"metric": "ArithmeticError.error_rate", "le": 0.0}],
             mutant="lsb", expect="fail",
             note="the error model measures a nonzero error rate"))
    add(Case("mutant_mute_checker", ("mutant", "int"), [_m(1, "int16")],
             ["add", "sub", "shl", "cmp"], modulus=15, checker_mutant="mute",
             expect="fail", note="check_err stuck at 0: single-bit coverage"))
    add(Case("mutant_hi_bit_checked", ("mutant", "int"), [_m(1, "int8"), _m(1, "int16")],
             ["add", "sub", "min", "and"], modulus=15, mutant="hi_bit",
             expect="fail", note="an unused y bit set: conformance and the checker's zero check"))
    # ---- I. load-time checks
    add(Case("load_bcd_shift_only", ("load",), [_m(1, "bcd3")],
             ["shl", "shr_logical"], expect="load_error"))
    add(Case("load_fp_op_on_int", ("load",), [_m(1, "int16")],
             ["add", "fadd"], expect="load_error"))
    add(Case("load_block_cvt_count", ("load",), [_m(3, "fp16")],
             ["cvt(blksfp8e4m3efp4e2m1s16)", "fadd"], expect="load_error"))
    # the check rule table (docs/checker-spec-plan.md): two rules over one unit, the logic class unchecked
    add(Case("check_rules_int16_arith_logic", ("int", "check_rules"), [_m(1, "int16")],
             ["and", "xor", "shl", "add", "sub", "mul_wide", "cmp"],
             params={"check": {"default": {"detect": "none"}, "fallback": "duplicate", "rules": [
                 {"name": "int_arith", "formats": ["int16"], "ops": ["add", "sub", "mul_wide"],
                  "detect": {"random_alias": 5.0e-2, "single_bit": 1.0},
                  "choices": [{"family": "residue", "modulus": [31, 63], "generator_style": "csa_tree",
                               "comparator.family": "direct_compare"},
                              {"family": "multi_residue", "moduli_count": [2, 3]}]},
                 {"name": "int_logic", "formats": ["int16"], "ops": ["and", "xor", "shl"], "detect": "none"},
                 {"name": "compare", "formats": ["int16"], "ops": ["cmp"],
                  "choices": [{"family": "duplication", "replication": 2, "comparator.family": "direct_compare"}]}]}},
             note="a residue rule under a bound, an unchecked logic class, a duplicated compare"))
    add(Case("check_rules_fp16_int16_two_families", ("float", "int", "multi", "check_rules"), [_m(1, "fp16"), _m(1, "int16")],
             ["add", "mul_wide", "fadd", "fmul"],
             params={"check": {"default": {"detect": "none"}, "rules": [
                 {"name": "int_arith", "formats": ["int16"], "ops": ["add", "mul_wide"], "fallback": "error",
                  "detect": {"random_alias": 5.0e-2},
                  "choices": [{"family": "multi_residue", "moduli_count": [2, 3], "moduli_set": "low_cost_2a_minus_1"}]},
                 {"name": "float", "formats": ["fp16"], "ops": ["fadd", "fmul"],
                  "choices": [{"family": "reduced_precision", "replica_width_bits": 8, "bound_type": "absolute",
                               "replica_adder.family": ["parallel_prefix", "carry_select"]}]}]}},
             note="an integer rule that forbids a replica, a float rule with a narrow replica and no bound"))
    add(Case("load_check_rule_format_not_a_mode", ("load", "check_rules"), [_m(1, "int16")], ["add"],
             params={"check": {"rules": [{"name": "r", "formats": ["fp16"], "ops": ["add"],
                                          "choices": [{"family": "residue"}]}]}},
             expect="load_error"))
    add(Case("load_check_rule_infeasible_bound", ("load", "check_rules"), [_m(1, "int16")], ["add"],
             params={"check": {"rules": [{"name": "r", "formats": ["int16"], "ops": ["add"],
                                          "detect": {"random_alias": 1.0e-3},
                                          "choices": [{"family": "residue", "modulus": [7, 15]}]}]}},
             expect="load_error"))
    add(Case("load_checked_without_residue_pin", ("load",), [_m(1, "int16")],
             ["add"], params={"check_en": [True], "_arch": {"checker": {"family": "residue"}}},
             expect="load_error"))
    add(Case("load_mode_serves_no_op", ("load", "multi"), [_m(1, "int16"), _m(1, "fp16")],
             ["shl", "and"], expect="load_error"))
    # ---- J. multi-mode mixes
    add(Case("mixed32_reduced", ("multi", "slow", "int", "float"),
             [_m(1, "int32"), _m(2, "int16"), _m(4, "int8"), _m(1, "fp32"),
              _m(2, "fp16"), _m(2, "bf16"), _m(4, "fp8e4m3")],
             ["add", "sub", "mul_wide", "quot", "min", "cmp", "shl", "xor",
              "popcount", "fadd", "fmul", "fdiv", "fcmp", "fabs", "cvt(int32)",
              "cvt(fp32)", "cvt(fp16)"],
             params={"rounding": ["RNE", "RTZ", "RDN", "RUP"],
                     "flags": ["invalid", "div_zero", "overflow", "inexact",
                               "carry", "int_overflow"],
                     "quotient_semantics": ["truncate_zero", "floor"]},
             modulus=15, n_random=4, n_masks=300))
    add(Case("int16_fp16_x2_cvt_checked", ("multi", "int", "float", "cvt"),
             [_m(2, "int16"), _m(2, "fp16")],
             ["add", "fadd", "min", "fmin", "cvt(int16)", "cvt(fp16)"], modulus=15))
    add(Case("fixed_float_mul_cvt", ("multi", "fixed", "float", "cvt"),
             [_m(2, "fxs1i7f8"), _m(2, "fp16")],
             ["mul", "fmul", "cvt(fp16)", "cvt(fxs1i7f8)"]))
    add(Case("tri_family_sr_window", ("multi", "posit", "float", "int", "sr"),
             [_m(1, "posit16_1"), _m(1, "fp16"), _m(1, "int16")],
             ["fadd", "fmul", "add", "mul", "cvt(fp16)"],
             params={"rounding": ["RNE", "SR"], "sr_bits": 12, "check_sr": False},
             modulus=15, alias=0.6, n_random=20))
    add(Case("uint8x4_bcd2x2_checked", ("multi", "int"),
             [_m(4, "uint8"), _m(2, "bcd2")],
             ["add", "sub", "mul_wide", "min", "cmp"], modulus=15))
    # ---- K. runtime option combinations
    add(Case("everything_runtime_fp16", ("runtime", "float", "sr", "dual"),
             [_m(1, "fp16")], ["fadd", "fmul", "fsqrt", "fabs", "cvt(int8)"],
             params={"rounding": ["RNE", "RTZ", "RDN", "RUP", "SR"], "sr_bits": 10,
                     "daz_in": [False, True], "ftz_out": [False, True],
                     "unary_dual": [False, True], "check_sr": [True, False],
                     "flags": FP_FLAGS, "check_flags": True},
             modulus=15, alias=0.6, n_random=12))
    add(Case("sr_bits_1_fixed_mul", ("sr", "fixed"), [_m(1, "fxs1i3f4")],
             ["mul", "div"], params={"rounding": "SR", "sr_bits": 1}))
    add(Case("sr_bits_23_fp32_ge", ("sr", "float"), [_m(1, "fp32")],
             ["fadd", "fmul"], params={"rounding": "SR", "sr_bits": 23,
                                       "sr_compare": "ge"}, n_random=30))
    add(Case("sr_window_unary_dual", ("sr", "float", "dual"), [_m(2, "fp16")],
             ["fsqrt", "cvt(int8)", "fadd"],
             params={"rounding": "SR", "sr_bits": 10, "check_sr": False,
                     "unary_dual": True}, modulus=15, alias=0.6))
    add(Case("flags_subset_mixed_families", ("multi", "int", "float"),
             [_m(1, "int16"), _m(1, "fp16")],
             ["add", "fadd", "mul", "fmul"], params={"flags": ["inexact", "carry"]}))
    add(Case("etc_single_mode_single_op", ("float",), [_m(1, "fp16")], ["fadd"],
             etc_single=True, note="no op and no mode port"))
    add(Case("etc_single_int_op_checked", ("int",), [_m(2, "int8")], ["mul_wide"],
             etc_single=True, modulus=15))
    # ---- L. per-structure control (architectures: core: structures/shared)
    sub3 = [_m(1, "int32"), _m(2, "int16"), _m(4, "int8")]
    sub_ops = ["add", "sub", "min", "cmp", "mul_wide", "shl", "and", "popcount"]
    add(Case("structures_kind_glob_id", ("structures", "multi", "int"), sub3, sub_ops,
             params={"_arch": {"core": {"structures": {
                 "adder": {"family": "parallel_prefix"},
                 "m1.*.adder": {"variant": "parallel_prefix/kogge_stone"},
                 "m0.l0.multiplier": {"family": "booth_recoded_parallel"},
                 "shifter": {}}}}},
             modulus=15, n_random=10,
             note="kind default, a glob and an exact id, plus an open selector"))
    add(Case("load_structures_unknown_id", ("structures", "load"), sub3, sub_ops,
             params={"_arch": {"core": {"structures": {"m9.l0.adder": {"family": "parallel_prefix"}}}}},
             expect="load_error"))
    add(Case("load_structures_family_outside_slot", ("structures", "load"), sub3, sub_ops,
             params={"_arch": {"core": {"structures": {"adder": {"family": "wallace_tree"}}}}},
             expect="load_error"))
    add(Case("load_structures_kind_without_slot", ("structures", "load"), sub3, sub_ops,
             params={"_arch": {"core": {"structures": {"logic": {"family": "parallel_prefix"}}}}},
             expect="load_error"))
    return C


# ---------------------------------------------------------------- main --

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-j", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--work", default=None)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--tag", nargs="*", default=None)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    C = cases()
    if a.tag:
        C = [c for c in C if set(a.tag) & set(c.tags)]
    if a.only:
        C = [c for c in C if any(c.name == n or c.name.startswith(n) for n in a.only)]
    if a.list:
        for c in C:
            print(f"{c.name:44s} {','.join(c.tags):28s} {c.expect}")
        print(f"{len(C)} cases")
        return 0
    work = a.work or tempfile.mkdtemp(prefix="alu_matrix_")
    Path(work).mkdir(parents=True, exist_ok=True)
    print(f"[alu_matrix] {len(C)} cases, {a.j} workers, under {work}", flush=True)
    t0 = time.time()
    order = sorted(C, key=lambda c: ("slow" not in c.tags, c.name))   # slow first
    results = {}
    with multiprocessing.Pool(a.j) as pool:
        for rec in pool.imap_unordered(_worker, [(c, work) for c in order]):
            results[rec["name"]] = rec
            print("  " + _line(rec), flush=True)
    fails = [r for r in results.values() if not r.get("ok")]
    print(f"[alu_matrix] {len(results) - len(fails)}/{len(results)} pass "
          f"in {time.time() - t0:.0f}s")
    for r in fails:
        print(f"  FAIL {r['name']}: {_why(r)}")
    if a.json:
        Path(a.json).write_text(json.dumps([results[c.name] for c in C if c.name in results],
                                           indent=1, default=str))
    return 1 if fails else 0


def _line(r: dict) -> str:
    mark = "ok  " if r.get("ok") else "FAIL"
    if "load_error" in r:
        return f"{mark} {r['name']}: load error ({r['load_error'][:90]})"
    if "gates" not in r:
        return f"{mark} {r['name']}: {r.get('detail', '')[:160]}"
    g = r["gates"]
    parts = [f"{r['n_vectors']} vectors"]
    for name, v in g.items():
        tag = "PASS" if v["pass"] else "FAIL"
        extra = ""
        if name == "fault" and "metrics" in v:
            m = v["metrics"]
            extra = f" (alias {m['random_alias']:.3f}, cov {m['single_bit_coverage']:.3f}, fa {m['false_alarms']})"
        if name == "accuracy" and "metrics" in v:
            m = v["metrics"]
            extra = f" (ulp {m['max_ulp']}, wrong {m['n_wrong']}/{m['n']})"
        parts.append(f"{name} {tag}{extra}")
    if r.get("protected"):
        parts.append("residue " + "/".join(r["protected"]))
    elif r.get("checked"):
        parts.append("duplication only")
    if r.get("structure_units"):
        parts.append(f"{r['structures']} structures -> "
                     + ", ".join(f"{k} {v} units" for k, v in r["structure_units"].items()))
    exp = "" if r["expect"] == "pass" else f" [expect {r['expect']}]"
    return f"{mark} {r['name']}: " + "; ".join(parts) + exp + f" [{r.get('seconds', 0)}s]"


def _why(r: dict) -> str:
    if "load_error" in r:
        return r["load_error"]
    if "detail" in r and "gates" not in r:
        return str(r["detail"])[:300]
    out = []
    for name, v in (r.get("gates") or {}).items():
        if not v["pass"]:
            out.append(f"{name}: {str(v.get('detail'))[:200]} "
                       + " | ".join(str(m)[:160] for m in v.get("mismatches", [])[:2]))
    if r["expect"] != "pass":
        out.append(f"expected {r['expect']} on {r.get('must_fail')}")
    return "; ".join(out) or str(r)


if __name__ == "__main__":
    raise SystemExit(main())
