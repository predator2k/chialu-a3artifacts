"""Shared helpers of the three unit-class templates: reading the bound
variables of a run file, and declaring the option variables every class
shares."""
from __future__ import annotations

from adir import Bool, Enum, Range, Set, Variable

FIXED = frozenset({"fixed"})
FIXED_OR_RUNTIME = frozenset({"fixed", "runtime"})
FIXED_OR_SEARCH = frozenset({"fixed", "search"})

ROUNDINGS = ("RNE", "RTZ", "RDN", "RUP", "SR")
FLAGS = ("invalid", "div_zero", "overflow", "underflow", "inexact", "nan",
         "denormal", "carry", "int_overflow", "unordered")
CONVENTIONS = {          # option -> (values, default, doc), spec section 3.9
    "nan_payload": (("canonical", "propagate"), "canonical",
                    "a NaN result of a float or block op carries the canonical pattern, or the first "
                    "NaN operand's payload"),
    "invalid_result": (("saturate", "zero"), "saturate",
                       "an invalid op in a format without NaN saturates, or gives zero"),
    "nan_to_int": (("zero", "max", "min"), "zero",
                   "NaN or NaR converted to an integer or fixed-point target gives zero, the target's "
                   "max (the RISC-V style) or its min"),
    "minmax_nan": (("propagate", "number"), "propagate",
                   "fmin and fmax with one NaN operand propagate the NaN, or return the number"),
    "tininess": (("after", "before"), "after",
                 "underflow of a float result is detected after rounding, or before"),
    "int_div_zero": (("riscv", "zero"), "riscv",
                     "integer and fixed-point division by zero gives the RISC-V results, or zero"),
    "zero_sign": (("positive", "preserve"), "positive",
                  "a zero result in ones' complement or sign-magnitude is +0, or keeps the sign of the "
                  "exact computation"),
    "quire_overflow": (("wrap", "saturate"), "wrap",
                       "quire accumulation beyond the carry guard wraps, or saturates"),
    "block_scale_rounding": (("nearest", "up"), "nearest",
                             "a block scale with a mantissa is quantized to nearest, or up"),
    "block_element_overflow": (("saturate", "inf"), "saturate",
                               "an element overflow in block quantization saturates, or gives inf (element "
                               "formats with inf)"),
    "sr_compare": (("gt", "ge"), "gt",
                   "stochastic rounding rounds up when the fraction is greater than the random word, "
                   "or greater or equal"),
    "check_flags": ((False, True), False,
                    "the generated checker also duplicates the flags output"),
    "flag_scope": (("per_result", "per_operation"), "per_result",
                   "the flags output carries one word per result, or one word for the whole "
                   "operation (the or of the results' flags), as FPnew reports one status per "
                   "vectorial op"),
    "fma_contract": (("fused", "sequential"), "fused",
                     "the fused multiply-add ops (fmadd, fmsub, fnmsub, fnmadd) round the exact product plus "
                     "addend once (a fused fp_fma family computes it), or round the product to the format "
                     "first and add it under a second rounding (the separate multiplier then adder)"),
}
UNARY_OPS = ("neg", "abs", "not", "popcount", "clz", "ctz", "fabs", "fneg", "fsqrt")


def vals(bindings: dict, name: str) -> list:
    """Every value a binding provisions: [value] for fixed, the members
    for runtime, [] when unbound."""
    b = bindings.get(name)
    if b is None:
        return []
    if b.time == "fixed":
        return [b.value]
    if b.time == "runtime":
        return list(b.members)
    return []


def value(bindings: dict, name: str, default=None):
    v = vals(bindings, name)
    return v[0] if v else default


def var(name: str, domain, times=FIXED, doc: str = "", when=None, requires=None) -> Variable:
    return Variable(name, domain, times, when=when, requires=requires, doc=doc)


def convention_variables(names=None) -> list:
    out = []
    for name, (values, _default, doc) in CONVENTIONS.items():
        if names is not None and name not in names:
            continue
        out.append(var(name, Enum(tuple(values)), FIXED, doc=doc))
    return out


def omitted_options(formats, ops, roundings, checked: bool, flags, unit: str = "alu") -> list:
    """The option variables that do not apply to a bound unit, for the
    elaboration's `prompt_omit`: ADIR's composer counts a fixed binding
    named here instead of listing it in the unit description. `formats`
    are the Format objects of the modes, `ops` the op names, `roundings`
    the provisioned rounding modes."""
    from chialu.verify.alu_ref import cvt_target, family_of, is_cvt
    from chialu.verify.formats import BlockFormat, IntFormat
    fams = {family_of(f) for f in formats}
    ops = list(ops)
    has_float = bool(fams & {"float", "block"})
    if unit == "alu" and "float" not in fams:
        out_x = ["x_form"]         # the X form is a float mode's; an integer, posit or block mode keeps the exact X
    else:
        out_x = []
    cvt = any(is_cvt(op) for op in ops)
    block = "block" in fams or any(isinstance(cvt_target(op), BlockFormat) for op in ops if is_cvt(op))
    sr = "SR" in set(roundings)
    signed_zero = any(isinstance(f, IntFormat) and f.encoding in ("ones_complement", "sign_magnitude")
                      for f in formats)
    out = ["verify.n_random", "verify.seed", "verify.n_random_masks"] + out_x
    if not has_float:
        out += ["daz_in", "ftz_out", "tininess", "nan_payload"]
    if "posit" not in fams and not cvt:
        out.append("invalid_result")
    if not cvt:
        out.append("nan_to_int")
    if not {"fmin", "fmax"} & set(ops):
        out.append("minmax_nan")
    if not {"div", "quot", "rem", "mod"} & set(ops):
        out.append("int_div_zero")
    if not signed_zero:
        out.append("zero_sign")
    if unit != "vec_dot_acc" or "posit" not in fams:
        out.append("quire_overflow")
    if not block:
        out += ["block_scale_rounding", "block_element_overflow"]
    if not sr:
        out += ["sr_compare", "sr_bits", "check_sr"]
    elif not checked:
        out.append("check_sr")
    if not checked or not flags:
        out.append("check_flags")
    if not flags or unit != "alu":
        out.append("flag_scope")
    if unit != "alu" or not {"fmadd", "fmsub", "fnmsub", "fnmadd"} & set(ops):
        out.append("fma_contract")
    if unit == "alu" and not any(op in UNARY_OPS or is_cvt(op) for op in ops):
        out.append("unary_dual")
    return out


def clock_variable() -> Variable:
    """`clock_ps`: the synthesis timing target. ABC's delay-driven mapper
    optimizes the area under it (with slack it takes smaller, slower
    cells), so every measured (area, delay) point stands under a target;
    the run file reads it into the synthesis nodes (`vars.clock_ps`) and
    bounds the delay by it as a soft constraint."""
    return var("clock_ps", Range(100, 1_000_000), FIXED,
               doc="the synthesis target in ps: under a reachable target the mapper optimizes area under it and a "
                   "delay constraint may bound it; a target below every design's reach (300 ps in the evaluation) "
                   "maps each design for its least delay, with no delay constraint")


def checker_variables(comparator: bool = True) -> list:
    """The checker's variables under a generated checker: the family the
    generator builds (chialu.targets.rtl.alu_checker: residue,
    inverse_residue, multi_residue, rns_redundant, an_code,
    parity_prediction_adder, parity_prediction_multiplier, berger,
    reduced_precision, duplication), the pins each reads (active under
    its family), and the comparator slot (`checker.comparator.family`,
    the two-rail space) with its pins, which every checked run file
    binds (the loader has no defaults; `checker.*: {search: all}` opens
    it at direct_compare, which the variables admit because they are
    declared FIXED_OR_SEARCH); the dot unit's checker realizes residue alone
    and leaves the slot out (`comparator=False`). The rest of the
    checker space's slots (the carry replica, the row adder, the coded
    adder, the replica adder) are the checker's own arithmetic; the
    choices the seam does not carry left the space on 2026-09-13
    (docs/deferred-families.md)."""
    from chialu.spaces.checker_spaces import checker_space, two_rail_space
    from chialu.targets.rtl.alu_checker import COMPARATORS, FAMILIES
    fams = {f.name: f for f in checker_space().families}
    rails = {f.name: f for f in two_rail_space().families}
    for f in checker_space().families:                     # the voter is duplication's comparator alone
        rails.update({x.name: x for x in f.components.get("comparator", two_rail_space()).families})
    residue = fams["residue"]

    def pin(family, choice, doc):
        return var(f"checker.{choice}", fams[family].design_choices[choice], FIXED_OR_SEARCH,
                   when=("checker.family", (family,)), doc=doc)

    def cpin(family, choice, doc):
        return var(f"checker.comparator.{choice}", rails[family].design_choices[choice], FIXED_OR_SEARCH,
                   when=("checker.comparator.family", (family,)), doc=doc)

    return [var("checker.family", Enum(FAMILIES), FIXED_OR_SEARCH,
                doc="the checker's family: residue (r(y) mod M predicted from the operands), "
                    "inverse_residue (the prediction carried as M - r), multi_residue (two or "
                    "three low-cost moduli), rns_redundant (base plus redundant low-cost moduli, "
                    "the disagreements as a syndrome), an_code (an AN-coded replica: operands times "
                    "A, the result times A compared, the replica self-checked by divisibility), "
                    "parity_prediction_adder (the result parity from the addends and a carry "
                    "replica), parity_prediction_multiplier (the product parity from the "
                    "partial-product rows and the replica reduction's carries), berger (the ones "
                    "count of the sum from the addends and the carries), reduced_precision (a "
                    "narrow replica, the result compared within a bound), duplication (a reference "
                    "copy compared bit for bit); the ops a family does not cover are duplicated"),
            var("checker.modulus", residue.design_choices["modulus"], FIXED_OR_SEARCH,
                when=("checker.family", ("residue", "inverse_residue")),
                doc="the residue modulus (2^a - 1)"),
            var("checker.moduli_count", Enum((2, 3)), FIXED_OR_SEARCH, when=("checker.family", ("multi_residue",)),
                doc="the low-cost moduli of multi_residue: 3 and 7, or 3, 7 and 31"),
            pin("rns_redundant", "base_moduli_count", "the base moduli 2^a - 1 (a the first primes)"),
            pin("rns_redundant", "redundant_moduli", "the redundant moduli after the base set"),
            pin("an_code", "A", "the code multiplier"),
            pin("residue", "generator_style", "the residue generator: a carry-save tree of the chunks, a chain of "
                "end-around-carry adders, or a table over the chunk pairs"),
            pin("inverse_residue", "inverse_on", "the complement on the check channel alone, or on both"),
            pin("multi_residue", "moduli_set", "the low-cost 2^a - 1 moduli, or a general coprime set"),
            pin("berger", "construction", "the ones count, or its low bits (bose_lin_method2)"),
            pin("parity_prediction_adder", "parity_groups", "the bit groups the parity is taken over"),
            pin("parity_prediction_adder", "carry_scheme", "the carries from a replica adder (duplicate_carry) or from "
                "the checked sum itself (carry_dependent_sum)"),
            pin("parity_prediction_adder", "interleaving", "the groups interleaved rather than contiguous"),
            pin("parity_prediction_multiplier", "recoding", "the replica's partial-product rows"),
            pin("reduced_precision", "replica_width_bits", "the replica's operand bits"),
            pin("reduced_precision", "bound_type", "absolute: the operands' scale; relative_ulp: the product's own scale"),
            pin("duplication", "replication", "the reference copies plus the datapath (3: two copies compared)")] + ([] if not comparator else [
            var("checker.comparator.family", Enum(COMPARATORS), FIXED_OR_SEARCH,
                doc="the final compare of every coded word and of the duplicated outputs: direct_compare "
                    "(a word equality), two_rail_tree (pairs (p, ~q) through a tree of two-rail cells), "
                    "m_out_of_n_checker (the pair word as a k-out-of-2k codeword: Anderson-Metze threshold "
                    "checker, a weight compare), majority_voter (under duplication: the copies and the "
                    "output voted bit for bit)"),
            cpin("two_rail_tree", "tree_arity", "pairs per tree node"),
            cpin("m_out_of_n_checker", "code_class", "k_out_of_2k over the pair word; one_out_of_n checks each pair as 1-out-of-2 (a two-rail tree)"),
            cpin("m_out_of_n_checker", "realization", "two_level_and_or (literal for k <= 5), multilevel_unate / cellular_threshold_array (a cellular AND/OR array), translator_cascade (2-out-of-4 cells into a two-rail tree)"),
            cpin("majority_voter", "inputs", "the voted inputs: the output and inputs - 1 reference copies")])


def option_variables(with_unary_dual: bool = True, with_check_sr: bool = True) -> list:
    out = [
        var("rounding", Enum(ROUNDINGS), FIXED_OR_RUNTIME, doc="the rounding mode; runtime: a rounding_sel port"),
        var("daz_in", Bool(), FIXED_OR_RUNTIME, doc="denormals-are-zero on inputs"),
        var("ftz_out", Bool(), FIXED_OR_RUNTIME, doc="flush-to-zero on outputs"),
        var("flags", Set(Enum(FLAGS)), FIXED, doc="flag bits exposed on the flags output, in list order"),
        var("sr_bits", Range(1, 4096), FIXED, doc="width of each sr_rnd word"),
    ]
    if with_unary_dual:
        out.append(var("unary_dual", Bool(), FIXED_OR_RUNTIME,
                       doc="unary ops as a 2-wide SIMD: op(a) in y, op(b) in the upper half"))
    if with_check_sr:
        out.append(var("check_sr", Bool(), FIXED_OR_RUNTIME,
                       doc="check a stochastically rounded result exactly or within its one-ulp window"))
    return out
