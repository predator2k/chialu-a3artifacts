"""The generated checker of a checked unit class: dispatch by unit
(chialu.targets.rtl.alu_checker, dot_checker)."""
from __future__ import annotations

from adir import BindError
from chialu.targets.rtl.alu_checker import (PATTERN_OPS, RESIDUE_OPS,  # noqa: F401
                                             alu_checker_sv, residue_eligible)
from chialu.targets.rtl.dot_checker import dot_checker_sv  # noqa: F401
from chialu.targets.rtl.residue import residue_module  # noqa: F401


def checker_for(spec: dict) -> tuple[str, list]:
    """(checker RTL, residue-protected ops) of any checked unit class."""
    if spec.get("unit") == "alu":
        return alu_checker_sv(spec, spec.get("checker_name", "alu_checker"))
    if spec.get("unit") == "vec_dot_acc":
        if (spec.get("checker_family") or "residue") != "residue":
            from chialu.targets.rtl.alu_checker import FAMILIES
            raise BindError(f"generated checker: VecDotAcc realizes the residue family alone, not "
                            f"{spec.get('checker_family')!r} (the ALU checker realizes {', '.join(FAMILIES)})")
        return dot_checker_sv(spec, spec["modulus"], spec.get("checker_name", "dot_checker"))
    raise BindError(f"generated checker: unit {spec.get('unit')!r} not implemented")
