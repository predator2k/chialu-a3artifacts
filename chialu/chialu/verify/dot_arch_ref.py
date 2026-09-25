"""Independent arithmetic contracts for dot architectures that round partials.

These contracts are selected explicitly with ``dot_contract=architecture``
and ``dot_architecture={family, pins}``. They do not replace the fused dot
contract. Products and unrounded additions below use exact Fractions;
only the named architectural boundaries quantize a value.
"""
from __future__ import annotations

from fractions import Fraction

from chialu.verify.formats import FloatFormat, Special, NAN, PINF, NINF, _mask
from chialu.verify.rounding import Rounder, flag_word


FAMILIES = ("tensor_core_mixed_precision_mac", "fp8_training_datapath", "bridge_fma",
            "mixed_precision_cascade_fma", "bf16_fma_datapath", "streaming_accurate_accumulator",
            "pairwise_tree", "multi_term_fused_dot")

DEFAULT_PINS = {
    "tensor_core_mixed_precision_mac": dict(dot_width_per_pe=4, partial_sum_rounding="rne",
                                             alignment_target="largest_exponent", subnormal_support=True),
    "fp8_training_datapath": dict(op_shape="scalar_fma", format_policy="single_e4m3",
                                  accumulate_precision="fp16", chunk_based_accumulation=False,
                                  stochastic_rounding=False, per_tensor_scaling=False, unified_internal_format=False),
    "bf16_fma_datapath": dict(op_shape="scalar_fma", rounding_mode="rne", flush_subnormals=False,
                              multi_word_composition=False),
    "bridge_fma": dict(composition_style="bridge_reuse", cascade_product_rounding="rne"),
    "mixed_precision_cascade_fma": dict(exact_product_preserved=True, two_term_expansion_output=False,
                                        error_term_normalization="dedicated", error_term_ops="addition"),
    "streaming_accurate_accumulator": dict(approach="shifted_fixed_point_window", window_bits=33,
                                           in_loop_normalization=False),
    "pairwise_tree": {"per_level_truncation": False, "accum.family": "linear_chain"},
    "multi_term_fused_dot": dict(term_source="products", alignment_strategy="per_level",
                                 sign_handling="post_add_complement", cancellation_handling="none",
                                 normalize_before_add=False, rounding_contract="correctly_rounded",
                                 guard_bits_per_level=0, normalization_deferral="per_term"),
}


def resolved_architecture(architecture):
    """Freeze algorithm defaults independently of the selected RTL binding."""
    family, supplied = selection({"dot_architecture": architecture})
    from chialu.targets.rtl.families.dot import dot_active_parameters
    pins = dict(DEFAULT_PINS[family], **supplied)
    if pins.get("mul.family") == "truncated_fixed_width":
        from chialu.verify.truncated_multiplier_ref import DEFAULTS
        for key, value in DEFAULTS.items():
            pins.setdefault("mul."+key, value)
    inactive = dot_active_parameters(family, pins)
    for path, reason in inactive.items():
        if any(key == path or key.startswith(path+".") for key in supplied):
            raise ValueError(f"{family}.{path}: inactive ({reason})")
    pins = {key: value for key, value in pins.items()
            if not any(key == path or key.startswith(path+".") for path in inactive)}
    return {"family": family, "pins": pins}


def _precision(fmt):
    from chialu.verify.formats import BlockFormat, PositFormat, X87Format
    if isinstance(fmt, BlockFormat):
        return (fmt.elem.man_bits+1 if isinstance(fmt.elem, FloatFormat) else fmt.elem.width) + fmt.scale.man_bits+1
    if isinstance(fmt, X87Format):
        return fmt.core.man_bits+1
    if isinstance(fmt, FloatFormat):
        return fmt.man_bits+1
    if isinstance(fmt, PositFormat):
        return fmt.width
    return fmt.width+1


def _stored(fmt, bits, daz=False):
    """Stored significand and its binary weight, without RTL field logic."""
    from chialu.verify.formats import PositFormat, X87Format, _floor_log2
    if isinstance(fmt, X87Format):
        bits = ((bits >> 79) << 78) | (((bits >> 64) & 32767) << 63) | (bits & ((1 << 63)-1))
        fmt = fmt.core
    if isinstance(fmt, FloatFormat):
        exponent = (bits >> fmt.man_bits) & ((1 << fmt.exp_bits)-1)
        if fmt.exp_only:
            return 1, exponent-fmt.bias, (bits >> (fmt.width-1)) if fmt.signed else 0
        fraction = bits & ((1 << fmt.man_bits)-1)
        magnitude = fraction + ((1 << fmt.man_bits) if exponent else 0)
        if daz and exponent == 0:
            magnitude = 0
        return magnitude, max(1, exponent)-fmt.bias-fmt.man_bits, (bits >> (fmt.width-1)) if fmt.signed else 0
    value = fmt.decode(bits)
    if isinstance(fmt, PositFormat):
        exponent = _floor_log2(abs(value))-(fmt.width-1) if value else 0
    else:
        exponent = -getattr(fmt, "frac_bits", 0)
    return int(abs(value)/Fraction(2)**exponent), exponent, int(value < 0)


def _stored_values(fmt, bits, count, daz):
    from chialu.verify.formats import BlockFormat
    values = []
    for index in range(count):
        pattern = (bits >> (index*fmt.width)) & ((1 << fmt.width)-1)
        if isinstance(fmt, BlockFormat):
            elements, scale_bits = fmt.split(pattern)
            sm, se, ss = _stored(fmt.scale, scale_bits)
            for element in elements:
                em, ee, es = _stored(fmt.elem, element, daz)
                values.append((em*sm, ee+se, es ^ ss))
        else:
            values.append(_stored(fmt, pattern, daz))
    return values


def _truncated_child(family, pins):
    """Select the composed multiplier contract, with explicit uncovered cases."""
    from chialu.verify.truncated_multiplier_ref import APPROXIMATE_FAMILIES, require_exact_reducers
    approximate = {path: value for path, value in pins.items() if path.endswith(".family") and value in APPROXIMATE_FAMILIES}
    if not approximate:
        return None
    if family != "pairwise_tree" or pins.get("mul.family") != "truncated_fixed_width":
        raise ValueError(f"uncovered Dot component contract: {family}, {approximate}")
    require_exact_reducers({path: value for path, value in pins.items() if path != "mul.family"})
    return {key[len("mul."):]: value for key, value in pins.items() if key.startswith("mul.") and key != "mul.family"}


def _component_products(spec, mode, pins, child, a_bits, b_bits, ctrl):
    """Actual child word scaled into the Dot's numerical operand contract."""
    from chialu.verify.formats import IntFormat, FixedFormat, ScaledIntFormat
    from chialu.verify.truncated_multiplier_ref import product
    fab, fc = mode["fab"], mode["fc"]
    binary = lambda fmt: isinstance(fmt, (IntFormat, FixedFormat)) and not (isinstance(fmt, ScaledIntFormat) and not isinstance(fmt, FixedFormat)) and fmt.encoding in ("twos_complement", "unsigned")
    raw = not pins.get("per_level_truncation", False) and binary(fab) and (not spec["accumulate"] or binary(fc))
    if raw:
        width, signed = fab.width, fab.encoding == "twos_complement"
        exponent = -2*getattr(fab, "frac_bits", 0)
        values = []
        for index in range(mode["elements"]):
            a, b = (a_bits >> (index*width)) & _mask(width), (b_bits >> (index*width)) & _mask(width)
            word = product(width, signed, child, a, b)
            integer = word-(1 << (2*width)) if signed and word >> (2*width-1) else word
            values.append(Fraction(integer)*Fraction(2)**exponent)
        return values, [int(value < 0) for value in values]
    width = _precision(fab)
    daz = bool(ctrl.get("daz_in", False))
    aa = _stored_values(fab, a_bits, mode["elements"], daz)
    bb = _stored_values(fab, b_bits, mode["elements"], daz)
    return ([Fraction(product(width, False, child, a, b)) * Fraction(2)**(ae+be) * (-1 if sa ^ sb else 1)
             for (a, ae, sa), (b, be, sb) in zip(aa, bb)],
            [sa ^ sb for (_, _, sa), (_, _, sb) in zip(aa, bb)])


def _window_value(spec, mode, family, pins, a_bits, b_bits, c_bits, ctrl):
    """The signed, finite-width window algorithm as exact integer arithmetic."""
    from chialu.verify import dot_ref as D
    fab, fc, fd = mode["fab"], mode["fc"], mode["fd"]
    daz = bool(ctrl.get("daz_in", False))
    aa = _stored_values(fab, a_bits, mode["elements"], daz)
    bb = _stored_values(fab, b_bits, mode["elements"], daz)
    n, S = len(aa), _precision(fab)
    Sc = _precision(fc) if spec["accumulate"] else 0
    child = _truncated_child(family, pins)
    if child is not None:
        from chialu.verify.truncated_multiplier_ref import product
        terms = [(product(S, False, child, a, b), ae+be, sa ^ sb) for (a, ae, sa), (b, be, sb) in zip(aa, bb)]
    else:
        terms = [(a*b, ae+be, sa ^ sb) for (a, ae, sa), (b, be, sb) in zip(aa, bb)]
    prenormalize = (family == "multi_term_fused_dot" and
                    (pins.get("normalize_before_add", False) or pins.get("normalization_deferral", "per_term") == "per_term"))
    if prenormalize:
        terms = [(m << (2*S-m.bit_length()), e-(2*S-m.bit_length()), s) if m else (m, e, s) for m, e, s in terms]
    if spec["accumulate"]:
        terms += _stored_values(fc, c_bits, 1, daz)
    L = max(1, (len(terms)-1).bit_length())
    Wt = max(2*S, Sc)
    loop_norm = False
    keep_sticky = True
    if family == "streaming_accurate_accumulator":
        width = int(pins.get("window_bits", 33))
        per_level = True
        tree = "binary_tree" if pins.get("approach", "shifted_fixed_point_window") == "tree_reduce_with_refinement" else "linear_chain"
        loop_norm = pins.get("in_loop_normalization", False)
        compressor = "3:2"
    elif family == "pairwise_tree":
        width = 2*S+Sc+4+max(1, n.bit_length())
        per_level = True
        tree = pins.get("accum.family", "linear_chain")
        compressor = pins.get("accum.compressor", "3:2")
    else:
        width = max(2*S, Sc)+int(pins.get("guard_bits_per_level", 0))+max(1, n.bit_length())+2
        per_level = pins.get("alignment_strategy", "per_level") == "per_level"
        tree = pins.get("reduction.family", "linear_chain")
        compressor = pins.get("reduction.compressor", "3:2")
        keep_sticky = pins.get("rounding_contract", "faithful") != "truncated_with_guard"
    if width < Wt+L+2:
        raise ValueError(f"window_bits={width} is below the {Wt+L+2}-bit minimum")
    head = width-Wt-L-1

    def wrap(value):
        value &= (1 << width)-1
        return value-(1 << width) if value >> (width-1) else value

    def combine(group):
        active = [e for q, e, st in group if q or st]
        anchor = max(active) if active else max(e for _, e, _ in group)
        q, sticky = 0, False
        for value, exponent, old_sticky in group:
            shift = max(0, anchor-exponent)
            aligned = value >> shift
            q += aligned
            sticky |= old_sticky or value != aligned*(1 << shift)
        q = wrap(q)
        if loop_norm and not sticky and q:
            shift = max(0, width-abs(q).bit_length()-1)
            q, anchor = wrap(q << shift), anchor-shift
        return q, anchor, sticky

    if per_level:
        nodes = [((-m if s else m) << head, e-head, False) for m, e, s in terms]
        bypass = None
        if family == "multi_term_fused_dot" and pins.get("cancellation_handling") == "detect_and_bypass_smallest_operand":
            cancel = any(terms[i][1] == terms[j][1] and terms[i][2] != terms[j][2]
                         for i in range(n) for j in range(i+1, n))
            if cancel:
                index = min(range(n), key=lambda k: (terms[k][1], k))
                bypass = nodes[index]
                nodes[index] = (0, nodes[index][1], False)
            else:
                bypass = (0, 0, False)
        if tree == "linear_chain":
            node = nodes[0]
            for other in nodes[1:]:
                node = combine((node, other))
        else:
            fanin = {"3:2": 3, "4:2": 4, "7:3": 7}[compressor] if tree == "csa_tree" else 2
            while len(nodes) > 1:
                nodes = [combine(nodes[i:i+fanin]) if len(nodes[i:i+fanin]) > 1 else nodes[i] for i in range(0, len(nodes), fanin)]
            node = nodes[0]
        if bypass is not None:
            node = combine((node, bypass))
        q, exponent, dropped = node
    else:
        anchor = max((e for m, e, _ in terms if m), default=0)
        q, dropped, negative_loss = 0, False, False
        for m, e, sign in terms:
            shift = max(0, anchor-e)
            full = m << head
            value = full >> shift
            lost = full != value*(1 << shift)
            q += -value if sign else value
            dropped |= lost
            negative_loss |= bool(sign and lost)
        dual = pins.get("sign_handling") == "dual_reduction_positive_pair_select"
        if keep_sticky and not dual:
            q -= int(negative_loss)
        q, exponent = wrap(q), anchor-head
    sticky = bool(dropped and keep_sticky)
    if not isinstance(fd, FloatFormat):
        # Integer/fixed destinations consume the signed window word in
        # their accumulator frame. Lost-window information is a flag.
        return Fraction(q)*Fraction(2)**exponent, bool(dropped)
    sign = q < 0
    magnitude = abs(q)-int(sign and sticky)
    targets = [fd] + ([fc] if spec["accumulate"] else [])
    sr_extra = int(spec["sr_bits"])+2 if "SR" in spec["rounding"] else 0
    precision = max(_precision(fab), *(_precision(fmt) for fmt in targets))
    xw = max(2*precision+4, max(fmt.width+2 for fmt in targets)+4) + sr_extra
    # X is a normalized significand plus a positive tail below its low
    # retained bit. This is the numeric contract of its sticky bit.
    if magnitude:
        shift = max(0, magnitude.bit_length()-xw)
        sig = magnitude >> shift
        sticky |= magnitude != sig*(1 << shift)
        exp = exponent+shift
        if magnitude.bit_length() < xw:
            shift = xw-magnitude.bit_length()
            sig <<= shift
            exp -= shift
    elif sticky:
        sig, exp = 1, exponent+width-2*xw
    else:
        return Fraction(0), bool(dropped)
    value = Fraction(sig)*Fraction(2)**exp
    if sticky:
        value += Fraction(2)**(exp-xw)
    return -value if sign else value, bool(dropped)


def selection(spec):
    arch = spec.get("dot_architecture")
    if not isinstance(arch, dict) or set(arch) != {"family", "pins"} or not isinstance(arch["pins"], dict):
        raise ValueError("architecture dot contract requires dot_architecture={family, pins}")
    if arch["family"] not in FAMILIES:
        raise ValueError(f"no independent architecture contract for {arch['family']}")
    return arch["family"], arch["pins"]


def extra_outputs(spec):
    if spec.get("dot_contract") != "architecture":
        return ()
    family, pins = selection(spec)
    _truncated_child(family, pins)
    if family != "mixed_precision_cascade_fma" or not pins.get("two_term_expansion_output", False):
        return ()
    result = ["d_error"]
    operators = pins.get("error_term_ops", "addition")
    if operators in ("addition", "both"):
        result.append("d_add_error")
    if operators in ("multiplication", "both"):
        result.append("d_mul_error")
    return tuple(result)


def _expected_main(spec, lay, mi, a_bits, b_bits, c_bits, ctrl, words):
    from chialu.verify import dot_ref as D
    from chialu.verify.alu_ref import _fp2
    from chialu.verify.formats import parse_format
    family, pins = selection(spec)
    child = _truncated_child(family, pins)
    m = lay["modes"][mi]
    fab, fc, fd = m["fab"], m["fc"], m["fd"]
    window_family = family in ("streaming_accurate_accumulator", "pairwise_tree", "multi_term_fused_dot")
    if not isinstance(fd, FloatFormat) and not window_family:
        raise ValueError("architecture dot contracts currently require a scalar floating-point destination")
    n = D.n_products(m)
    if D.n_outputs(m) != 1:
        raise ValueError("architecture dot contracts require a scalar output")
    daz = bool(ctrl.get("daz_in", False))
    aa = D._values_of(fab, a_bits, m["elements"], daz)
    bb = D._values_of(fab, b_bits, m["elements"], daz)
    cv = D._values_of(fc, c_bits, 1, daz)[0] if lay["accumulate"] else (Fraction(0), 0, False)
    # Input special-value propagation is independent of finite datapath
    # organization and retains the unit's existing convention contract.
    if any(isinstance(value, Special) for value, _, _ in aa + bb + [cv]):
        return D.dot_expected(dict(spec, dot_contract="fused"), lay, mi, a_bits, b_bits, c_bits, ctrl, words)
    mathematical_products = [a[0] * b[0] for a, b in zip(aa, bb)]
    products, product_signs = (mathematical_products, [a[1] ^ b[1] for a, b in zip(aa, bb)])
    if child is not None:
        products, product_signs = _component_products(spec, m, pins, child, a_bits, b_bits, ctrl)
    flags = {"denormal"} if any(x[2] for x in aa + bb + [cv]) else set()
    word = (words or [0])[0]
    mode = ctrl.get("rounding", "RNE")
    final = Rounder(mode, spec["sr_bits"], spec.get("sr_compare", "gt"),
                    spec.get("tininess", "after"), ftz=bool(ctrl.get("ftz_out", False)))

    def rounded(value, fmt, rounding):
        r = Rounder(rounding, spec["sr_bits"], spec.get("sr_compare", "gt"), spec.get("tininess", "after"), ftz=False)
        bits, fl = r.float(fmt, value, word, int(not isinstance(value, Special) and value < 0))
        flags.update(fl)
        return fmt.decode(bits)

    def add(a, b):
        value = _fp2("fadd", a, b) if isinstance(a, Special) or isinstance(b, Special) else a + b
        if value is NAN:
            flags.add("invalid")
        return value

    partials = []
    exact_contract = ((family == "pairwise_tree" and not pins.get("per_level_truncation", False)) or
                      (family == "multi_term_fused_dot" and pins.get("rounding_contract", "correctly_rounded") == "correctly_rounded"))
    if exact_contract:
        if child is None:
            return D.dot_expected(dict(spec, dot_contract="fused"), lay, mi, a_bits, b_bits, c_bits, ctrl, words)
        window_family = False  # Exact reduction of the approximate child words.
    if window_family:
        value, dropped = _window_value(spec, m, family, pins, a_bits, b_bits, c_bits, ctrl)
        if dropped:
            flags.add("inexact")
        partials = [value]
    elif family == "tensor_core_mixed_precision_mac":
        width = int(pins.get("dot_width_per_pe", 4))
        if n < width:
            raise ValueError(f"dot_width_per_pe={width} requires at least {width} products")
        rm = "RNE" if pins.get("partial_sum_rounding", "rne") == "rne" else "RTZ"
        pairwise = pins.get("alignment_target", "largest_exponent") == "pairwise_sequential"
        for start in range(0, n, width):
            group = products[start:start+width]
            value = group[0]
            for product in group[1:]:
                value = add(value, product)
                if pairwise:
                    value = rounded(value, fd, rm)
            partials.append(rounded(value, fd, rm))
    elif family == "fp8_training_datapath":
        if pins.get("chunk_based_accumulation", False):
            precision = parse_format(str(pins.get("accumulate_precision", "fp16")))
            partials = [rounded(sum(products[start:start+4], Fraction(0)), precision, mode)
                        for start in range(0, n, 4)]
        else:
            partials = products
    elif family in ("bridge_fma", "mixed_precision_cascade_fma"):
        if n != 1:
            raise ValueError("a cascade FMA has one product")
        preserve = (pins.get("composition_style", "bridge_reuse") != "cascade_mul_then_add" if family == "bridge_fma"
                    else pins.get("exact_product_preserved", True))
        rm = "RTZ" if pins.get("cascade_product_rounding", "rne") == "truncate" else "RNE"
        partials = products if preserve else [rounded(products[0], fd, rm)]
    else:
        partials = products
    total = Fraction(0) if window_family else cv[0]
    for value in partials:
        total = add(total, value)
    signs = set(product_signs) | ({cv[1]} if lay["accumulate"] else set())
    nonzero = any(x != 0 for x in products) or cv[0] != 0
    zero_sign = int(signs == {1} or (mode == "RDN" and nonzero)) if total == 0 else int(total is NINF)
    odd = family == "bf16_fma_datapath" and pins.get("rounding_mode") == "round_to_odd"
    if odd:
        final.mode = "RTZ"
        final.ftz = False
    bits, fl = D._round_d(fd, total, zero_sign, final, word, spec)
    if odd and "inexact" in fl and not isinstance(fd.decode(bits), Special):
        bits |= 1
    if odd and ctrl.get("ftz_out", False):
        from chialu.verify.rounding import is_subnormal
        if is_subnormal(fd, bits):
            bits &= 1 << (fd.width-1)
            fl |= {"underflow", "inexact"}
    flags.update(fl)
    return bits & _mask(lay["d_w"]), flag_word(flags, lay["flags"])


def outputs(spec, lay, mi, a_bits, b_bits, c_bits, ctrl, words):
    """Main result and optional rounded residuals of the selected operators.

    d_error is round(exact(a*b+c)-d). d_mul_error is the residual of
    rounding the product to d's format. d_add_error is the residual of
    the final addition, using the exact or rounded product selected by
    exact_product_preserved. Special inputs or a nonfinite main result
    have zero residuals. Flags include the exposed residual roundings.
    """
    d, flags = _expected_main(spec, lay, mi, a_bits, b_bits, c_bits, ctrl, words)
    result = dict(d=d, flags=flags)
    names = extra_outputs(spec)
    if not names:
        return result
    from chialu.verify import dot_ref as D
    _, pins = selection(spec)
    m = lay["modes"][mi]
    fab, fc, fd = m["fab"], m["fc"], m["fd"]
    if D.n_products(m) != 1:
        raise ValueError("a two-term FMA expansion has one product")
    daz = bool(ctrl.get("daz_in", False))
    av = D._values_of(fab, a_bits, 1, daz)[0][0]
    bv = D._values_of(fab, b_bits, 1, daz)[0][0]
    cv = D._values_of(fc, c_bits, 1, daz)[0][0] if lay["accumulate"] else Fraction(0)
    main = fd.decode(d)
    if any(isinstance(v, Special) for v in (av, bv, cv, main)):
        result.update({key: 0 for key in names})
        return result
    product_value = av*bv
    r = Rounder("RNE", spec["sr_bits"], spec.get("sr_compare", "gt"), spec.get("tininess", "after"), ftz=False)
    projection_needed = not pins.get("exact_product_preserved", True) or "d_mul_error" in names
    product_bits, product_flags = r.float(fd, product_value, (words or [0])[0], int(product_value < 0)) if projection_needed else (0, set())
    product_rounded = fd.decode(product_bits) if projection_needed else product_value
    projection_finite = not isinstance(product_rounded, Special)
    used = product_value if pins.get("exact_product_preserved", True) else product_rounded
    residuals = {"d_error": product_value+cv-main,
                 "d_add_error": used+cv-main if not isinstance(used, Special) else None,
                 "d_mul_error": product_value-product_rounded if projection_finite else None}
    r = Rounder(ctrl.get("rounding", "RNE"), spec["sr_bits"], spec.get("sr_compare", "gt"),
                spec.get("tininess", "after"), ftz=bool(ctrl.get("ftz_out", False)))
    # The product projection is part of the multiplication-error operator.
    if "d_mul_error" in names:
        flags |= flag_word(product_flags, lay["flags"])
    for name in names:
        if residuals[name] is None:
            result[name] = 0
            continue
        bits, fl = r.float(fd, residuals[name], (words or [0])[0], int(residuals[name] < 0))
        result[name] = bits
        flags |= flag_word(fl, lay["flags"])
    result["flags"] = flags
    return result


def expected(spec, lay, mi, a_bits, b_bits, c_bits, ctrl, words):
    result = outputs(spec, lay, mi, a_bits, b_bits, c_bits, ctrl, words)
    return result["d"], result["flags"]
