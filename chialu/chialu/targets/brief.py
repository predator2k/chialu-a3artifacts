"""The unit brief: the prompt texts of a derived target (title, the
contract table of the ops, the frozen interface, the levers), written
from the verify-layer spec and the bundle's vector count. The verify
layer's ops.py is the machine authority these describe."""
from __future__ import annotations


# One line per op, the wording the prompt's contract table uses; the
# verify layer's ops.py is the machine authority these describe.
OP_SEMANTICS = {
    "add": "y = a + b, wrapped to the lane width",
    "sub": "y = a - b, wrapped",
    "adc": "y = a + b + 1, wrapped",
    "sbb": "y = a - b - 1, wrapped",
    "neg": "y = -a, wrapped (b ignored)",
    "abs": "y = |a|, wrapped (b ignored)",
    "add_sat": "y = a + b saturated to the representable range",
    "sub_sat": "y = a - b saturated",
    "mul": "y = the low lane-width bits of a * b",
    "mul_wide": "y = the exact double-width product a * b",
    "mul_high": "y = the high lane-width bits of the exact product",
    "mul_sat": "y = a * b saturated to the lane width",
    "div": "y = a / b truncated toward zero; b = 0 gives the all-ones pattern",
    "quot": "y = a / b truncated toward zero; b = 0 gives the all-ones pattern",
    "rem": "y = a - b * quot(a, b), the sign of the dividend; b = 0 gives a",
    "mod": "y = a - b * floor(a / b), the sign of the divisor; b = 0 gives a",
    "min": "y = min(a, b)",
    "max": "y = max(a, b)",
    "cmp": "y = {gt, eq, lt} in bits 2:0 (a > b -> 4, a == b -> 2, a < b -> 1), upper bits 0",
    "shl": "y = a << (b mod lane width)",
    "shr_logical": "y = a >> (b mod lane width), zero fill",
    "shr_arith": "y = a >>> (b mod lane width), sign fill",
    "rol": "y = a rotated left by (b mod lane width)",
    "ror": "y = a rotated right by (b mod lane width)",
    "and": "y = a & b", "or": "y = a | b", "xor": "y = a ^ b",
    "not": "y = ~a (b ignored)",
    "popcount": "y = the number of set bits of a (b ignored)",
    "clz": "y = the number of leading zero bits of a (b ignored)",
    "ctz": "y = the number of trailing zero bits of a; lane width when a = 0",
    "fadd": "y = a + b, IEEE 754 on the mode's float format, rounded under the rounding option",
    "fsub": "y = a - b, rounded",
    "fmul": "y = a * b, rounded",
    "fdiv": "y = a / b, correctly rounded; x/0 = inf with the sign of a xor b, 0/0 = NaN",
    "fsqrt": "y = sqrt(a), correctly rounded (b ignored); a negative a gives NaN",
    "fcmp": "y = {gt, eq, lt} in bits 2:0 by value (+0 == -0); a NaN operand gives 0",
    "fmin": "y = the smaller operand's pattern (-0 below +0); a NaN operand gives the canonical NaN (minmax_nan: propagate)",
    "fmax": "y = the larger operand's pattern; a NaN operand gives the canonical NaN",
    "fabs": "y = a with the sign bit cleared (b ignored); NaN gives the canonical NaN",
    "fneg": "y = a with the sign bit flipped (b ignored); NaN gives the canonical NaN",
}


def _cvt_semantics(op: str, fmt) -> str:
    from chialu.verify.alu_ref import cvt_target, family_of
    tgt = cvt_target(op)
    tf = family_of(tgt)
    if tf in ("integer", "fixed"):
        return (f"y = the value of a re-encoded in {tgt.name} ({tgt.width} bits): rounded under "
                f"the rounding option, saturated to the target's range; NaN gives the nan_to_int "
                f"value, +-inf saturate (b ignored)")
    if tf in ("float", "posit"):
        return (f"y = the value of a re-encoded in {tgt.name} ({tgt.width} bits), rounded under "
                f"the rounding option where inexact; NaN gives {tgt.name}'s canonical NaN, "
                f"overflow gives inf (RNE) or the largest finite value (directed modes) (b ignored)")
    return f"y = a quantized into {tgt.name} (spec section 2.6) (b ignored)"


def unit_texts(spec: dict, n_vectors: int, protected: list | None = None) -> dict:
    from chialu.verify import alu_ref as A
    from chialu.verify.formats import parse_format
    spec = A.normalize_spec(spec)
    lay = A.alu_layout(spec)
    modes, ops, legal = lay["modes"], lay["ops"], lay["legal"]
    top = spec["dut_name"]
    y_w = lay["y_w"]
    ports = list(lay["core_in"]) + list(lay["core_out"])
    iface = [f"    module {top} ("]
    for k, p in enumerate(ports):
        comma = "," if k < len(ports) - 1 else ""
        iface.append(f"      {'input ' if p.direction == 'in' else 'output'} logic [{p.width-1}:0] {p.name}{comma}")
    iface.append("    );")
    table = "\n".join(f"* op {k}, {op.upper()}: "
                      + (_cvt_semantics(op, modes[0][1]) if op.startswith("cvt(") else OP_SEMANTICS.get(op, op))
                      for k, op in enumerate(ops))
    table += ("\n\nInteger ops act on the mode's integer format (wrap to the width unless the op "
              "saturates); the float ops act on the mode's float format with IEEE 754 semantics "
              "(subnormals kept, canonical NaN = sign 0, exponent all ones, mantissa MSB 1); an op "
              "is legal only in the modes listed above, and its output on an illegal mode is unconstrained.")
    opw = max(1, (len(ops) - 1).bit_length())
    mode_lines = []
    for mi, (n, f) in enumerate(modes):
        legal_ops = [op for op in ops if (mi, op) in legal]
        mode_lines.append(f"* mode {mi}: {n} x {f.name} ({n * f.width} bits of a and b "
                          f"used, value i at bits [i*{f.width} +: {f.width}]); legal ops: "
                          f"{', '.join(legal_ops)}")
    chk = ""
    if spec.get("checker_name"):
        chk = (f" A frozen checker (residue mod {spec['modulus']} for "
               f"{', '.join(protected or [])}; behavioral duplication for the "
               f"other ops) wraps your module from the outside and a "
               f"fault-injection gate corrupts y at the seam: every single-bit "
               f"corruption must be flagged and the checker must raise no false "
               f"alarm on any vector. You cannot see or edit the checker.")
    wide_txt = (f" y is {y_w} bits (the widest result); every (mode, op) leaves "
                f"the bits above its own result width at 0.")
    opts = []
    if lay["sr"]:
        opts.append(f"sr_rnd carries {lay['v_max']} random words of {lay['sr_bits']} bits (word i "
                    f"belongs to result i in packing order) for stochastic rounding")
    for name, vals in lay["controls"].items():
        opts.append(f"{name}_sel selects among {vals} (index into the list)")
    for name in ("rounding", "daz_in", "ftz_out", "unary_dual"):
        vals = spec.get(name)
        if vals and len(vals) == 1 and name not in lay["controls"]:
            opts.append(f"{name} = {vals[0]}")
    if lay["d_w"]:
        opts.append("d carries the second result of a unary op under unary_dual")
    if lay["flags"]:
        opts.append(f"flags carries {lay['v_max']} words of {len(lay['flags'])} bits "
                    f"({', '.join(lay['flags'])} in bit order), one per result")
    conv = {k: spec[k] for k in A.CONVENTION_NAMES if k in spec}
    opts.append("convention options: " + ", ".join(f"{k}={v}" for k, v in conv.items()))
    if spec.get("quotient_semantics"):
        opts.append(f"quotient_semantics = {spec['quotient_semantics']}")
    wide_txt += "\n\nOptions (docs/formats-and-options.md):\n\n" + "\n".join(f"* {o}" for o in opts)
    brief = (f"You are optimizing ONLY the module `{top}` on the\n${{PDK_DESCRIPTION}}. "
             f"It serves {len(modes)} mode(s) and {len(ops)} ops; the conformance "
             f"gate compares its output against the exact reference for every "
             f"legal (mode, op) pair and vector, so any internal architecture is "
             f"legal — shared datapaths, one adder serving several ops and modes, "
             f"any multiplier or divider structure, any result-select network — "
             f"because the gate checks values, not structure.{chk}\n\n"
             f"## Hard contract (enforced mechanically)\n\n"
             f"Modes (the `mode` input selects one; a mode's values are packed from "
             f"bit 0 upward):\n\n" + "\n".join(mode_lines) + "\n\n"
             f"Ops (the `op` input selects one):\n\n{table}\n\n{wide_txt}\n\n"
             f"Candidates are simulated over every legal (mode, op) pair with "
             f"corner and directed pairs plus fixed-seed random pairs "
             f"({n_vectors} vectors in total); a single mismatch rejects the "
             f"candidate.\n\n"
             f"## What you may change\n\n"
             f"Anything inside `{top}` that preserves the (mode, op) table exactly. "
             f"The interface is frozen:\n\n" + "\n".join(iface))
    levers = ("different ALU organizations (a shared add/sub/compare adder with "
              "operand inversion, multiplier partial-product encodings and reduction "
              "geometries, a divider structure and its reuse of the multiplier, "
              "MIN/MAX and CMP from the subtractor's sign, shifter and bit-count "
              "structures, how the modes share one datapath, mux-tree versus "
              "one-hot result selection, gating unused datapaths per op)")
    interface = "\n".join(l[4:] for l in iface) + "\n  // body: the reference realization, not your structure\nendmodule"
    return {"title": f"a {len(modes)}-mode {len(ops)}-op ALU core", "top": top,
            "marker": f"module {top}", "brief": brief, "levers": levers, "extra": "",
            "interface": interface}


def unit_texts_other(spec: dict, n_vectors: int, protected: list | None = None) -> dict:
    """Prompt texts of the SFU and dot classes: the frozen interface, the
    modes and the contract in words."""
    top = spec["dut_name"]
    if spec["unit"] == "vec_sfu":
        from chialu.verify import sfu_ref as S
        lay = S.sfu_layout(spec)
        ports = list(lay["core_in"]) + list(lay["core_out"])
        modes = lay["modes"]
        title = f"a {len(modes)}-mode SFU ({', '.join(lay['functions']) or 'no fixed function'}"
        title += f", {len(lay['slots'])} reconfigurable slot(s))"
        lines = [f"* mode {mi}: {n} x {f.name}" for mi, (n, f) in enumerate(modes)]
        fns = [f"* fn_sel {i}: {fn}" for i, fn in enumerate(lay["functions"])]
        fns += [f"* fn_sel {len(lay['functions']) + i}: reconfigurable slot {i} ({sl['approx']}, "
                f"{sl['segments']} segments; table entry k = c0 | c1 << w{' | c2 << 2w' if sl['approx'] == 'pwq' else ''}, "
                f"y = c0 + c1 (x - x_k){' + c2 (x - x_k)^2' if sl['approx'] == 'pwq' else ''} over segment k of the "
                f"value-ordered patterns, loaded through clk / tbl_we[{i}] / tbl_addr / tbl_data)"
                for i, sl in enumerate(lay["slots"])]
        budget = spec.get("budget") or {"max_ulp": 1.0}
        contract = (f"Named functions are accuracy-bounded against the correctly rounded ideal "
                    f"({', '.join(f'{k} <= {v}' for k, v in budget.items())}); slot outputs must be "
                    f"bit-exact to the loaded table's polynomial rounded once under the rounding option.")
        levers = ("approximation families (tables, bipartite/multipartite, piecewise polynomials, "
                  "CORDIC, Newton iterations, range reduction), coefficient precisions, sharing of "
                  "evaluators across functions and modes, how blocks are re-quantized")
    else:
        from chialu.verify import dot_ref as D
        lay = D.dot_layout(spec)
        ports = list(lay["core_in"]) + list(lay["core_out"])
        modes = lay["modes"]
        title = f"a {len(modes)}-mode dot unit ({spec.get('dot_contract', 'fused')} contract)"
        lines = [f"* mode {mi}: {m['elements']} x {m['fab'].name}"
                 + (f" + {m['fc'].name}" if lay["accumulate"] and m['fc'] else "")
                 + f" -> {m['fd'].name}" for mi, m in enumerate(modes)]
        fns = []
        contract = (f"d = c + sum(a_i * b_i) under the {spec.get('dot_contract', 'fused')} contract "
                    f"(fused: exact products and sum, one rounding into format_d; sequential: every "
                    f"product and addition rounded), overflow = {spec.get('overflow', 'wrap')} for integer "
                    f"and fixed-point d; the conformance gate is bit-exact.")
        levers = ("multiplier encodings, reduction trees versus fused carry-save accumulation, "
                  "alignment strategies for floating-point terms, exact wide accumulators, sharing "
                  "across modes")
    iface = [f"    module {top} ("]
    for k, p in enumerate(ports):
        comma = "," if k < len(ports) - 1 else ""
        iface.append(f"      {'input ' if p.direction == 'in' else 'output'} logic [{p.width-1}:0] {p.name}{comma}")
    iface.append("    );")
    chk = ""
    if spec.get("checker_name"):
        chk = (f" A frozen checker (residue mod {spec['modulus']} where the exact relation holds, a "
               f"duplicate of the reference elsewhere) wraps your module and a fault-injection gate "
               f"corrupts the data output at the seam; every single-bit corruption must be flagged "
               f"with no false alarm on any vector.")
    brief = (f"You are optimizing ONLY the module `{top}` on the\n${{PDK_DESCRIPTION}}. "
             f"It serves the modes below; the gate compares its outputs against the exact "
             f"reference for every vector, so any internal architecture is legal.{chk}\n\n"
             f"## Hard contract (enforced mechanically)\n\nModes:\n\n" + "\n".join(lines)
             + ("\n\nFunctions:\n\n" + "\n".join(fns) if fns else "")
             + f"\n\n{contract} Options: rounding={spec.get('rounding')}, daz_in={spec.get('daz_in')}, "
             f"ftz_out={spec.get('ftz_out')}, flags={spec.get('flags')}, sr_bits={spec.get('sr_bits')}; "
             f"see docs/formats-and-options.md.\n\n{n_vectors} vectors in total; a violation rejects the "
             f"candidate.\n\n## What you may change\n\nAnything inside `{top}` that preserves the contract. "
             f"The interface is frozen:\n\n" + "\n".join(iface))
    interface = "\n".join(l[4:] for l in iface) + "\n  // body: the reference realization, not your structure\nendmodule"
    return {"title": title, "top": top, "marker": f"module {top}", "brief": brief,
            "levers": levers, "extra": "", "interface": interface}
