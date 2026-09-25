"""A target derived from the bound variables: the verify-layer spec, the
behavioral seed and the generated checker all come from the unit class
and the bindings (modes, ops, options), so no hand-written target is
needed. The exact semantics are the verify layer's
(chialu/verify/ops.py); the seed realizes them with the language's
operators, one lane packing per provisioned lane count."""
from __future__ import annotations

import json
from pathlib import Path


def spec_from_bindings(unit: str, bindings: dict) -> dict:
    """The verify-layer spec of a template's bindings: for chialu.ALU
    its modes, ops and every option, plus the checker fields when the
    unit is checked; the SFU and dot classes build theirs the same way.
    An approximate unit's budget comes from its `error_budget` variable
    (the SFU's default is max_ulp 1.0)."""
    from chialu.modules.common import vals, value
    checked = True in vals(bindings, "check_en")
    if unit == "chialu.ALU":
        from chialu.modules.alu import spec_from_bindings as sfb
        from chialu.verify.alu_ref import family_of, normalize_spec
        from chialu.verify.formats import parse_format
        spec = normalize_spec(sfb(bindings, checked if value(bindings, "check") is None else None))
        checked = bool(spec.get("check_en"))
        spec.update({"dut_name": "alu_core"})
        spec["families"] = sorted({family_of(parse_format(m["format"])) for m in spec["modes"]})
        if spec.get("accuracy") == "approximate":
            def _b(one):
                return {k: (True if k == "bit_exact" else float(v)) for k, v in (one or {}).items()}
            raw = value(bindings, "error_budget") or {}
            spec["budget"] = [_b(x) for x in raw] if isinstance(raw, (list, tuple)) else _b(raw)
    elif unit == "chialu.VecSFU":
        from chialu.modules.sfu import spec_from_bindings as sfb
        from chialu.verify.sfu_ref import normalize_sfu_spec
        spec = normalize_sfu_spec(sfb(bindings))
        spec.update({"dut_name": "sfu_core"})
        spec["budget"] = {k: (True if k == "bit_exact" and v is True else float(v)) for k, v in spec["budget"].items()}
        checked = False
    elif unit == "chialu.VecDotAcc":
        from chialu.modules.dot import spec_from_bindings as sfb
        spec = sfb(bindings, checked)
        spec.update({"dut_name": "dot_core"})
    else:
        raise ValueError(f"no derived target for {unit}")
    spec["n_random"] = int(value(bindings, "verify.n_random", 20000))
    spec["seed"] = int(value(bindings, "verify.seed", 1))
    if checked and spec.get("check"):
        # the rule table (spec["check"]) carries the families and pins; the fault gate is unit-wide until the
        # per-group campaign (docs/checker-spec-plan.md, staging 4)
        n_masks = int(value(bindings, "verify.n_random_masks", 2000))
        spec.update({"checker_name": spec["dut_name"].replace("core", "checker"),
                     "n_random_masks": n_masks, "detect": detect_budget(spec, n_masks)})
    elif checked:
        from chialu.targets.rtl.alu_checker import FAMILIES, checker_params
        fam = value(bindings, "checker.family", "residue")
        if fam not in FAMILIES:
            raise ValueError(f"derived target: the checker family {fam!r} has no generator "
                             f"(the generators: {', '.join(FAMILIES)})")
        spec["checker_family"] = fam
        if fam in ("residue", "inverse_residue"):
            M = vals(bindings, "checker.modulus")
            if not M:
                raise ValueError(f"derived target: checker {fam} needs checker.modulus")
            spec["modulus"] = int(M[0])
        elif fam == "multi_residue":
            spec["moduli_count"] = int(value(bindings, "checker.moduli_count", 2))
        # the family's other pins and the comparator slot (fixed bindings; a searched one stands at its default)
        pins = {}
        for k in bindings:
            if k.startswith("checker.") and not k.startswith("checker.comparator.") \
                    and k not in ("checker.family", "checker.modulus", "checker.moduli_count"):
                v = value(bindings, k)
                if v is not None:
                    pins[k[len("checker."):]] = v
        if pins:
            spec["checker_pins"] = pins
        cfam = value(bindings, "checker.comparator.family")
        if cfam:
            comp = {"family": cfam}
            for k in bindings:
                if k.startswith("checker.comparator.") and k != "checker.comparator.family":
                    v = value(bindings, k)
                    if v is not None:
                        comp[k[len("checker.comparator."):]] = v
            spec["comparator"] = comp
        n_masks = int(value(bindings, "verify.n_random_masks", 20000))
        spec.update({"checker_name": spec["dut_name"].replace("core", "checker"),
                     "n_random_masks": n_masks,
                     "detect": detect_budget(spec, n_masks)})
    return spec


def detect_budget(spec: dict, n_masks: int) -> dict:
    """The fault-gate budget of a checked spec: no false alarm, every
    single-bit corruption caught, and the random-alias rate at most the
    family's escape probability plus three standard deviations of its
    measurement over n_masks masks (the measured rate scatters by
    sqrt(p(1-p)/n))."""
    from chialu.targets.rtl.alu_checker import alias_probability, checker_params, single_bit_floor
    from chialu.verify.formats import parse_format
    floor = 1.0
    if spec.get("unit") == "alu" and spec.get("check"):
        # the rule table: the worst code over the groups (a rule's own bound where it states one, the model's
        # output_alias where it does not), the lowest single-bit floor; a replica pair aliases at 0
        from chialu.targets.rtl.alu_checker import check_manifest
        rows = [r for r in check_manifest(spec) if r["mechanism"] == "code"]
        p = max([float((r.get("detect") or {}).get("random_alias", r["output_alias"])) for r in rows], default=0.0)
        floor = min([float(r["single_bit"]) for r in rows], default=1.0)
        bound = p + 3 * (p * (1 - p) / max(1, n_masks)) ** 0.5
        return {"false_alarms": ("==", 0), "single_bit_coverage": ("==", 1.0) if floor >= 1.0 else (">=", floor),
                "random_alias": ("<=", round(bound, 5))}
    family, moduli = checker_params(spec)
    if spec.get("unit") == "alu":
        modes = [(int(m["count"]), parse_format(str(m["format"]))) for m in spec["modes"]]
        p = alias_probability(family, moduli, modes, spec.get("checker_pins"), spec.get("comparator"))
        floor = single_bit_floor(family, modes, spec.get("checker_pins"), spec.get("comparator"))
    else:
        p = 1.0 / (moduli[0] if moduli else 15)
    bound = p + 3 * (p * (1 - p) / max(1, n_masks)) ** 0.5
    # a family that misses some one-bit corruptions by construction (a narrow replica, a weight compare)
    # is held to the coverage it guarantees rather than to every bit
    return {"false_alarms": ("==", 0), "single_bit_coverage": ("==", 1.0) if floor >= 1.0 else (">=", floor),
            "random_alias": ("<=", round(bound, 5))}


# ------------------------------------------------------------------ seed

def seed_alu(spec: dict, partition=None) -> str:
    return seed_alu_text(spec, partition).text


def seed_alu_text(spec: dict, partition=None, families=None):
    """The SeedText (text, manifest, top, unit modules) of an ALU spec;
    `families` names the declared family of every structure the lane
    modules realize through the family library (alu_seed)."""
    from chialu.targets.rtl.alu_seed import alu_seed
    return alu_seed(spec, spec.get("dut_name", "alu_core"), partition=partition, families=families)


def seed_for(spec: dict, partition=None, family=None, families=None) -> str:
    """The behavioral seed of any unit class; `family` is the declared
    (family, pins) of a unit whose architecture is one family at the
    core (the dot accumulator, the SFU), which its seed realizes through
    the family library where it has a module, and `families` the declared
    (family, pins) per structure of an ALU."""
    if spec.get("unit") == "alu":
        return seed_alu_text(spec, partition, families).text if families else seed_alu(spec, partition)
    if spec.get("unit") == "vec_dot_acc":
        from chialu.targets.rtl.dot_seed import dot_ref_module
        return dot_ref_module(spec, spec.get("dut_name", "dot_core"), family=family)
    if spec.get("unit") == "vec_sfu":
        from chialu.targets.rtl.sfu_seed import sfu_ref_module
        return sfu_ref_module(spec, spec.get("dut_name", "sfu_core"), family=family)
    raise ValueError(f"derived seed: unit {spec.get('unit')!r} not implemented")


def checker_rtl(spec: dict) -> str:
    """The generated checker of a checked spec."""
    from chialu.targets.rtl import checkers
    if not spec.get("checker_name"):
        raise ValueError("checker_rtl: the spec is not checked (check_en false)")
    return checkers.checker_for(spec)[0]


def verify_files(spec: dict, out_dir, checker: str | None = None) -> dict:
    """The verification files of a spec as {name: text}: tb.sv,
    vectors.hex, expected.hex (bit-exact units), fault_tb.sv and
    masks.hex (checked units), plus spec.json, which the nodes read to
    rebuild the dump-mode and fault judges."""
    from chialu.targets import bundles
    b = bundles.build_from_spec("derived", spec, out_dir, {}, "", "", checker, None)
    files = dict(b.files)
    files.update(b.fault_files)
    if spec.get("unit") == "alu" and spec.get("checker_name"):
        from chialu.targets.rtl.alu_checker import check_manifest
        files["check_manifest.json"] = json.dumps(check_manifest(spec), indent=1, default=str)
    files["spec.json"] = json.dumps(b.spec, indent=1, default=str)
    return files


def verify_file_names(spec: dict) -> list:
    """The member names `verify_files` produces, known before it runs."""
    names = ["tb.sv", "vectors.hex"]
    if not spec.get("budget"):
        names.append("expected.hex")
    if spec.get("checker_name"):
        names += ["fault_tb.sv", "masks.hex"]
    names.append("spec.json")
    return names
