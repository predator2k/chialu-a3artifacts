"""Generate and verify complete family pin products, with resumable coverage records."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import shutil

from chialu.variants import catalog, canonical
from chialu.verify.variant_coverage import Coverage


def native_kind(kind, family):
    from chialu.targets.rtl.families.decimal import DECIMAL_FAMILIES
    if family in DECIMAL_FAMILIES.get(kind, ()):
        return "bcd_" + kind
    if kind == "representation":
        return "multiplier" if family == "redundant_binary_multiplier" else "sd_adder"
    return kind


def seed_fixture(kind, family, pins, width):
    """Exercise a family through ALU pattern ports where the unit exposes its contract."""
    from chialu.verify.alu_ref import normalize_spec
    integer = {"adder": ["add", "sub", "adc", "sbb"], "multiplier": ["mul", "mul_wide", "mul_high"],
               "divider": ["div", "rem"], "shifter": ["shl", "shr_logical", "shr_arith", "rol", "ror"],
               "comparator": ["cmp", "min", "max"], "logic": ["and", "or", "xor", "not"]}
    floating = {"fp_adder": ["fadd", "fsub"], "fp_multiplier": ["fmul"],
                # a fused family serves the fused multiply-add too (the separate one computes it under the
                # sequential contract alone, which this fixture does not bind)
                "fp_fma": ["fadd", "fsub", "fmul"] + (["fmadd"] if family != "separate_multiplier_and_adder" else []),
                "fp_comparator": ["fcmp", "fmin", "fmax"],
                "fp_divider": ["fsqrt"] if family == "sig_sqrt_then_round" else ["fdiv"],
                "rounder": ["fadd", "fsub", "fmul"], "unpacker": ["fadd", "fsub", "fmul", "fcmp"]}
    fmt = f"int{width}"
    slot = kind
    extra_modes = []
    first_mode_ops = None
    if kind in integer:
        operations = integer[kind]
        if family == "end_around_carry":
            if pins.get("modulus") != "mod_2n_minus_1":
                return None
            fmt = f"int{width}_ones"
    elif kind == "bitcount":
        operations = ["popcount" if family == "popcount_counter_tree" else "ctz" if family == "trailing_zero" else "clz"]
    elif kind in floating:
        fmt = {8: "fp8e4m3", 16: "fp16", 32: "fp32"}.get(width)
        if fmt is None:
            return None
        operations = floating[kind]
        # a datapath shared across formats needs a second float mode of another format that selects the same
        # sharing (the rounder's and the unpacker's family, the fused multiply-add's `sharing` pin)
        if (kind in ("rounder", "unpacker") and family == "shared_across_formats") or \
                (kind == "fp_fma" and pins.get("sharing") == "shared_across_formats"):
            companion = {8: "fp8e5m2", 16: "bf16", 32: "fps1e7m24NI"}[width]
            extra_modes.append({"format": companion, "count": 1})
    elif kind == "posit_unit":
        from chialu.characterize import POSIT_FORMATS
        fmt = POSIT_FORMATS.get(width)
        if fmt is None:
            return None
        operations = ["fadd", "fsub", "fmul"]
        if pins.get("operator_set") == "add_mul_div":
            operations += ["fdiv", "fsqrt"]
        if family == "posit_ieee_interop":
            direction = pins.get("conversion_direction", "posit_to_ieee")
            style = pins.get("interop_style", "boundary_converters")
            arithmetic = list(operations)
            if direction in ("posit_to_ieee", "bidirectional"):
                operations.append("cvt(fp16)")
            first_mode_ops = list(operations)
            if direction in ("ieee_to_posit", "bidirectional"):
                operations.append(f"cvt({fmt})")
            if direction in ("ieee_to_posit", "bidirectional") or style == "unified_dual_format_datapath":
                ieee_ops = arithmetic if style == "unified_dual_format_datapath" else []
                if direction in ("ieee_to_posit", "bidirectional"):
                    ieee_ops.append(f"cvt({fmt})")
                extra_modes.append({"format": "fp16", "count": 1, "ops": ieee_ops})
    elif kind == "dot":
        from chialu.characterize import DOT_GEOMS
        from chialu.verify.dot_ref import normalize_dot_spec
        if width not in DOT_GEOMS:
            return None
        fab, fc, fd, elements = DOT_GEOMS[width]
        from chialu.targets.rtl.families.dot import FMA_FAMILIES
        floating_format = {8: "fp8e4m3", 16: "fp16", 32: "fp32"}[width]
        if family in FMA_FAMILIES:
            fab, fc, fd, elements = floating_format, "fp32", "fp32", 1
        elif family == "fused_two_term_dot":
            elements = 2
        elif family in ("block_fp_accumulation", "mx_microscaling_dot"):
            scale = "e8m0" if family == "mx_microscaling_dot" else "fp8e4m3"
            fab, fc, fd, elements = f"blks{scale}e{floating_format}s4", "fp32", "fp32", 1
        spec = normalize_dot_spec({"unit": "vec_dot_acc", "dut_name": "dot_core", "check_en": False,
                                   "modes": [{"format_ab": fab, "format_c": fc, "format_d": fd, "elements": elements}]})
        return spec, (family, pins)
    elif kind.startswith("bcd_"):
        if width % 4:
            return None
        fmt, slot = f"bcd{width//4}", kind[4:]
        operations = integer[slot]
    else:
        return None
    first_mode = {"format": fmt, "count": 1, **({"ops": first_mode_ops} if first_mode_ops is not None else {})}
    spec = normalize_spec({"unit": "alu", "modes": [first_mode] + extra_modes, "ops": operations,
                           "check_en": False, "dut_name": "alu_core"})
    selections = {f"core.{slot}.m0": (family, pins)}
    if extra_modes and kind in ("rounder", "unpacker", "fp_fma"):
        selections["core." + slot + ".m1"] = (family, pins)
    return spec, selections


def check_seed(spec, selections, directory, vectors, seed, coverage=None):
    from chialu.targets.derive import seed_alu_text, seed_for, verify_files
    from adir.registry import underlying
    from chialu import eda
    conformance = underlying(eda.conformance)          # an in-process call
    spec = dict(spec, n_random=vectors, seed=seed)
    from chialu.targets.rtl.families.fidelity import Audit
    with Audit() as audit:
        generated = seed_alu_text(spec, families=selections) if spec["unit"] == "alu" else seed_for(spec, family=selections)
    text = generated.text if hasattr(generated, "text") else str(generated)
    fidelity = getattr(generated, "fidelity", audit.report())
    key = hashlib.sha256(canonical(["seed", text, spec]).encode()).hexdigest()
    if coverage is not None:
        previous = coverage.evidence(key)
        if previous and previous.get("pass") is True:
            return dict(previous, reuse_sha256=key)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "seed.sv").write_text(text)
    files = verify_files(spec, directory)
    result = conformance(text, files)
    result["source_bytes"] = len(text.encode())
    result["source_sha256"] = hashlib.sha256(text.encode()).hexdigest()
    result["vectors_sha256"] = hashlib.sha256(files["vectors.hex"].encode()).hexdigest()
    if "expected.hex" in files:
        result["expected_sha256"] = hashlib.sha256(files["expected.hex"].encode()).hexdigest()
    result["fidelity"] = fidelity
    (directory / "result.json").write_text(json.dumps(result, indent=2))
    if coverage is not None:
        coverage.evidence(key, result)
    return result


def seed_status(result):
    if result.get("accuracy_mode") == "report_error" and result.get("algorithm_pass") is not True:
        return "unproved"
    if result.get("pass") is True:
        return "pass"
    if "timeout" in result.get("detail", "").lower():
        return "unproved"
    return "failed" if result.get("pass") is False else "unproved"


def check_point(entry, ordinal, width, coverage, vectors=256, seed=1, formal=False, timeout=60):
    from chialu.characterize import realize
    from chialu.targets.rtl.families.selftest import run_python_case
    from chialu.verify.family_ref import golden, no_golden_reason
    from chialu.verify.family_tb import emit
    from chialu.verify.formal import module_source, prove
    family = entry.product.name
    pins = entry.product.at(ordinal)
    kind = native_kind(entry.kind, family)
    result = {"kind": entry.kind, "family": family, "width": width, "ordinal": str(ordinal), "pins": pins,
              "generation": "unproved", "golden": "unproved", "status": "unproved"}
    from chialu.variant_legality import reason
    invalid = reason(family, pins, width, entry.kind)
    if not invalid:
        # the width contract the ALU's slots apply (alu_contracts): a pin that needs a wider word, such as a
        # ripple chunk above the width, is refused by the generator and kept out of the slot
        from chialu.targets.rtl.families.alu_contracts import alu_family_requirements
        need = alu_family_requirements(entry.kind, family, pins)
        if width < need["minimum_width"] or (need.get("power_of_two") and width & (width - 1)):
            invalid = f"width {width} outside the family's contract (minimum {need['minimum_width']}" + \
                      (", a power of two" if need.get("power_of_two") else "") + ")"
    if invalid:
        return dict(result, status="excluded", legality=invalid)
    if kind == "sfu":
        return dict(result, detail="an SFU contract needs its function and format; the width-only scope does not bind that geometry")
    if kind == "checker":
        return dict(result, detail="checker variants need a Python syndrome and fault-injection contract")
    if kind.startswith("fp_") or kind in ("rounder", "unpacker", "converter"):
        from chialu.characterize import FP_FORMATS
        if width not in FP_FORMATS:
            return dict(result, detail="no floating format is bound to this width; the legacy fp16 fallback cannot establish coverage")
    key = hashlib.sha256(canonical([entry.id, ordinal, width]).encode()).hexdigest()
    directory = coverage.directory / "cases" / key
    try:
        adapter = golden(kind, family, pins, width)
        module = realize(kind, family, pins, width)
        fixture = seed_fixture(kind, family, pins, width)
        if fixture is not None:
            result["seed_geometry"] = {k: fixture[0][k] for k in ("unit", "modes", "ops") if k in fixture[0]}
        if module is None and fixture is None:
            return dict(result, detail="no native generator or ALU fixture")
        if adapter is None or module is None:
            if fixture is None:
                return dict(result, detail=no_golden_reason(kind, family, pins, width) or "native generator rejected the complete binding")
            checked = check_seed(*fixture, directory / "seed", vectors, seed, coverage)
            status = seed_status(checked)
            return dict(result, generation="pass", golden=status,
                        status="unproved" if formal and status == "pass" else status, seed=checked,
                        source_bytes=checked.get("source_bytes"),
                        detail="native formal contract is absent" if formal else checked.get("detail", ""))
        source = module_source(module)
        result.update(generation="pass", source_bytes=len(source.encode()))
        # Identical source, parameters, contract and vectors have identical verification obligations.
        from chialu.verify.symbolic import compile_reference, Unsupported
        try:
            contract = compile_reference(adapter)
        except Unsupported:
            contract = canonical([kind, family, pins, width])
        evidence_key = hashlib.sha256(canonical([source, module.name, module.params, contract,
                                                vectors, seed, formal]).encode()).hexdigest()
        previous = coverage.evidence(evidence_key)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "dut.sv").write_text(source)
        if previous and previous.get("golden") == "pass":
            result.update(previous, reuse_sha256=evidence_key)
        else:
            bench = emit(module.name, module.params, adapter, vectors, seed)
            verdict = run_python_case("", "native", bench, directory, module.text or "")
            result["simulation"] = verdict
            if not verdict.endswith(": PASS"):
                return dict(result, status="failed", detail=verdict)
            result["golden"] = "pass"
            if formal:
                proof = prove(module, adapter, directory / "formal", timeout)
                result["formal"] = proof
                if proof["status"] != "proved":
                    return dict(result, status=proof["status"], detail=proof.get("detail"))
            coverage.evidence(evidence_key, {k: result[k] for k in ("golden", "simulation", "formal") if k in result})
        if fixture is not None:
            checked = check_seed(*fixture, directory / "seed", vectors, seed, coverage)
            result["seed"] = checked
            if checked.get("pass") is not True:
                return dict(result, status=seed_status(checked), detail=checked.get("detail"))
        result["status"] = "pass"
        return result
    except subprocess.TimeoutExpired as error:
        return dict(result, status="unproved",
                    detail=f"{error.cmd[0]} timeout after {error.timeout}s")
    except (ValueError, KeyError, TypeError, AssertionError) as error:
        return dict(result, status="unproved", detail=f"{type(error).__name__}: {error}")


def main(argv=None):
    from chialu.synthdb import DENSE_WIDTHS
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kinds")
    ap.add_argument("--families")
    ap.add_argument("--index", choices=("active", "raw"), default="active",
                    help="active omits inactive aliases; raw preserves the legacy Cartesian ordinals")
    ap.add_argument("--widths", default=",".join(map(str, DENSE_WIDTHS)))
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--stop", type=int)
    ap.add_argument("--limit", type=int, help="bound new work; an incomplete product still fails acceptance")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--vectors", type=int, default=256)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--formal", action="store_true")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--retry-unproved", action="store_true")
    args = ap.parse_args(argv)
    if args.index == "active":
        from chialu.active_variants import catalog as selected_catalog
    else:
        selected_catalog = catalog
    entries = list(selected_catalog(args.kinds.split(",") if args.kinds else None, args.families.split(",") if args.families else None))
    if not entries:
        ap.error("the requested scope contains no family schemas")
    for raw, available in ((args.kinds, {entry.kind for entry in entries}),
                           (args.families, {entry.product.name for entry in entries})):
        if raw and set(raw.split(",")) - available:
            ap.error(f"requested names are absent from the selected scope: {sorted(set(raw.split(',')) - available)}")
    if args.limit is not None and args.limit < 0:
        ap.error("--limit must be nonnegative")
    missing = [tool for tool in ("verilator",) if not shutil.which(tool)]
    if missing and not args.report_only:
        ap.error("verification tools are absent: " + ", ".join(missing))
    coverage = Coverage(args.out)
    scopes, jobs = [], []
    for width in map(int, args.widths.split(",")):
        for entry in selected_catalog(args.kinds.split(",") if args.kinds else None,
                             args.families.split(",") if args.families else None, width):
            if width < 1:
                ap.error("widths must be positive")
            geometry = {"width": width, "formal": args.formal, "vectors": args.vectors, "seed": args.seed,
                        "index": args.index}
            scope = coverage.scope(entry, geometry)
            scopes.append(scope)
            jobs.append((entry, width, scope))
    worked = 0
    if not args.report_only:
        for entry, width, scope in jobs:
            for ordinal in entry.product.ordinals(args.start, args.stop, args.shard, args.shards):
                previous = coverage.get(scope, ordinal)
                if previous is not None and (not args.retry_unproved or previous["status"] in ("pass", "excluded")):
                    continue
                if args.limit is not None and worked >= args.limit:
                    break
                result = check_point(entry, ordinal, width, coverage, args.vectors, args.seed, args.formal, args.timeout)
                coverage.record(scope, ordinal, result)
                worked += 1
                print(canonical(result), flush=True)
            if args.limit is not None and worked >= args.limit:
                break
    report = coverage.report(scopes)
    (coverage.directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(canonical(report), flush=True)
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
