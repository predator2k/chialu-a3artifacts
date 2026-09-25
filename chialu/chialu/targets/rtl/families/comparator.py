"""The subtractor form of the comparator (adder_spaces.comparator_space's
subtractor_comparator) as a generated module: the comparator is the
carry-propagate adder of its `subtractor` slot with the sum path
unused, a + ~b + 1's carry-out giving greater-or-equal and the
whole-word equality read from the sum being zero (zero_detect: the OR
tree over the sum) or from the operands' XNOR tree (zero_detect:
operand_xnor, which needs no adder output).

    fam_cmp_subtractor_<adder>_<zero>_w<W> (input [W-1:0] a, b, output lt, eq)
"""
from __future__ import annotations

from chialu.targets.rtl.families.mul import dedupe_modules


def _pin(pins: dict, key: str, default):
    v = pins.get(key, default) if pins else default
    return default if v in (None, "") else v


def _sub(pins: dict, prefix: str) -> dict:
    return {k[len(prefix):]: v for k, v in (pins or {}).items() if k.startswith(prefix)}


def subtractor_comparator_sv(W: int, pins: dict, signed: bool, name: str | None = None) -> tuple:
    """(name, text) of the subtractor comparator at W bits: lt and eq of a
    signed or unsigned compare through the `subtractor` slot's adder."""
    from .binary_cpa import adder_module
    pins = pins or {}
    fam = str(_pin(pins, "subtractor.family", "ripple_carry"))
    zd = str(_pin(pins, "zero_detect", "sum_or_tree"))
    if zd not in ("sum_or_tree", "operand_xnor"):
        raise ValueError(f"subtractor_comparator: zero_detect {zd!r}")
    m = adder_module(fam, _sub(pins, "subtractor."), W)
    if m is None:
        raise ValueError(f"subtractor_comparator: the adder family {fam!r} has no library module")
    sp = _sub(pins, "subtractor.")
    tag = ""
    if sp:
        import hashlib
        import json
        tag = "_p" + hashlib.sha256(json.dumps(sp, sort_keys=True, default=str).encode()).hexdigest()
    name = name or f"fam_cmp_subtractor_{fam}{tag}_{zd}_{'s' if signed else 'u'}_w{W}"
    ps = ", ".join(f".{k}({v})" for k, v in m.params.items())
    L = [f"// subtractor_comparator ({fam}, {zd}, {'signed' if signed else 'unsigned'}): a - b through the adder's "
         f"carry-out, the sum path unused",
         f"module {name} (input logic [{W-1}:0] a, input logic [{W-1}:0] b, output logic lt, output logic eq);",
         f"  logic [{W-1}:0] ax, bx, nb, s;",
         "  logic co;",
         # a signed compare is an unsigned one with the sign bits inverted
         f"  assign ax = {{a[{W-1}] ^ 1'b{1 if signed else 0}, a[{W-2}:0]}};" if W > 1 else f"  assign ax = a ^ 1'b{1 if signed else 0};",
         f"  assign bx = {{b[{W-1}] ^ 1'b{1 if signed else 0}, b[{W-2}:0]}};" if W > 1 else f"  assign bx = b ^ 1'b{1 if signed else 0};",
         "  assign nb = ~bx;",
         f"  // the subtractor: the adder ({fam}) on a and ~b with a carry in; no carry out means a < b",
         f"  {m.name} " + (f"#({ps}) " if ps else "") + "u_sub (.a(ax), .b(nb), .cin(1'b1), .s(s), .cout(co));",
         "  assign lt = ~co;"]
    if zd == "sum_or_tree":
        L.append("  assign eq = (s == '0);       // the difference is zero")
    else:
        L.append("  assign eq = &(ax ~^ bx);     // the operands' XNOR tree")
    L += ["endmodule", ""]
    return name, "\n".join(L) + dedupe_modules(m.text or "")
