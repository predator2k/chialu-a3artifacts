"""The coverage check of the family library against the family spaces
(docs/work-plan.md item 2): a selftest that answers, mechanically, the
questions of docs/slot-audit.md.

    python3 -m chialu.targets.rtl.families.coverage [--kinds k,...] [--families f,...]
                                                    [--checks c,...] [--json out.json] [--all]

It walks every space a unit template opens (the ALU's structure slots,
the redundant core's representation and channels slots, the dot
accumulator's and the SFU's core spaces, the checker), including the
sub-slot spaces, renders every family through the library with a pins
dictionary that logs every key the generator reads, and reports one row
per finding under seven checks:

* family: the family renders a module (`has_module` and the realizer
  agree), or a registered seed-level realization exists;
* slot: every declared slot is read by the consumer (`<slot>.family`)
  and every member of its domain renders; a member the consumer rejects
  or that renders the same text as another member is reported;
* pin: every pin the generator reads is declared by the space (the
  planner can bind it, the database can characterize it);
* choice: every member of every design choice changes the module text
  (comments and the module name aside); a member that renders the text
  of another member falls through to it;
* component: inside the generated module, a library instance whose kind
  no read slot pin chose is hard-coded (class B of the audit), and a
  behavioral operator of a library kind at a width of MIN_WIDTH bits or
  more (an add, a subtract, a multiply, a variable shift, a modulo, a
  procedural block) is class C;
* name: two pin sets that render different texts never share a module
  name;
* menu: `has_module` (the `[library]` mark) and the realizer agree.

A row is clean, allowlisted (ALLOWLIST names its reason) or a finding;
the exit status is 1 when a finding remains. The sweep is bounded: a
slot whose space is a root kind of its own (adders, multipliers,
dividers, shifters, counters, ...) is swept at its members and their
first-level choices, since the deeper keys are swept under that root;
every other sub-slot space is swept in full.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

from adir import Bool, Enum, Range
from chialu.targets.rtl import families as FAM

W = 16                      # the width every integer kind renders at
MIN_WIDTH = 8               # a behavioral operator below this width is not reported
RANGE_SAMPLES = 3           # lo, mid, hi of a Range choice

SPACE_DIR = Path(__file__).resolve().parents[3] / "spaces"

# ---- the seed-level realizations: families `has_module` marks [library] that the seed realizes by
# construction rather than as a library module the realizer returns
SEED_REALIZED = {
    ("logic", "alu_pg_fused"): "the lane's and / xor / or are the adder's generate and propagate expressions (alu_int.py)",
    ("subword", "replicated_lanes"): "one lane module per lane, the seed's own shape",
}

# ---- the allowlist: (pattern over `check|kind|family|item`, reason). A finding whose id matches a pattern
# is reported as allowed with the reason; the list holds the documented exceptions alone.
ALLOWLIST = [
    ("choice|adder|parallel_prefix|topology=kogge_stone|harris", "harris at log2_sparsity 0 and fanout_cap 2 is Kogge-Stone by definition (Harris 2003)"),
    ("choice|adder|compound_flagged_prefix|topology=kogge_stone|harris", "harris at log2_sparsity 0 and fanout_cap 2 is Kogge-Stone by definition (Harris 2003)"),
    ("choice|adder|end_around_carry|topology=kogge_stone|harris", "harris at log2_sparsity 0 and fanout_cap 2 is Kogge-Stone by definition (Harris 2003)"),
    ("component|multiplier|behavioral_star|*", "the family is the language's multiply by definition (mul_spaces.py)"),
    ("choice|multiplier|behavioral_star|*", "the family has no structure of its own"),
    ("component|checker|direct_compare|*", "the family is the word equality by definition"),
    ("component|checker|*|`!=`*", "the checker's final compare under direct_compare is the word equality"),
    # the multiplier slots a non-default choice value opens (the slot check sweeps the members at the default pins)
    ("slot|multiplier|segmented_grid|merge_tree.family", "the reduction merge exists under merge_form carry_save_tree"),
    ("pin|multiplier|truncated_fixed_width|correction",
     "the approximate space declares `correction` on its own family of this name; the multiplier generator "
     "reads the pin to tell the two apart, since a declaration that binds it asks for the approximate "
     "space's correction ladder (families/__init__.py mul_module)"),
    # the dot accumulators (dot.py): the datapath's own adders and shifters go through the cpa, align and
    # norm_shifter slots, which the slot check exercises; what the component check sees at the default pins
    # is the slots' own undeclared default and the exponent path, which the dot space does not slot
    ("component|dot|*|`multiply`*",
     "the mul slot's default family is behavioral_star, the language's multiply by definition (mul_spaces.py); "
     "a declared family renders the library multiplier"),
    ("component|dot|*|`variable shift`*",
     "the align and norm_shifter slots at their undeclared default use the language's shift, which synthesis "
     "maps to the mux tree the library shifter builds (families/dot.py `_sh` states the substitution); a "
     "declared family renders the library module"),
    ("component|dot|*|`procedural`*",
     "the leading-zero count at its undeclared default is a function with a loop (a procedural block with a "
     "break re-triggers under a converter); a declared lza.counter or lza.encoder family renders the library counter "
     "with its own pins"),
    ("choice|dot|block_fp_accumulation|lza.*",
     "the anticipator reads the final adder's two operands, and this family sums into the frame through a "
     "reduction that does not expose them, so the count is after the add and the anticipator's own choices "
     "do not reach the text (the module comment states the substitution)"),
    ("choice|dot|mx_microscaling_dot|lza.*", "the same: the scaled products sum into the frame"),
    ("choice|dot|streaming_accurate_accumulator|lza.*", "the same: the terms sum into a window"),
    ("choice|dot|*|reduction.compressor=3:2|4:2",
     "the geometry the sweep probes has two products, and a 4:2 compressor over two terms is the 3:2's one "
     "add; the compressors part at three terms and more"),
    ("choice|dot|*|align.sticky_method",
     "the sticky method is bounded_align's choice: it names how the bits below the near window are collected, "
     "and a family whose align slot stands at full_align truncates no term, so no sticky is formed"),
    ("slot|dot|*|align.tzc.*",
     "the trailing-zero counter serves the bounded alignment's sticky under sticky_method "
     "trailing_zero_compare; a family that places its terms in the frame or a window never builds it"),
    ("slot|dot|streaming_accurate_accumulator|lza.family",
     "the anticipator reads the final adder's two operands and this family sums into a window whose adder "
     "does not expose them, so lza counts after the add as lzc_after_add does; the module comment says so"),
    ("component|dot|*|`subtract`*",
     "the alignment's exponent distances (emax - e_k) and the borrow adjustment of a truncated negative term; "
     "the dot space declares no exp_adder slot, so the exponent path is inline"),
    ("component|dot|*|`increment`*",
     "the two's complement of a negative term (its inverted word plus one) and the exponent's plus one; the "
     "dot space declares no incrementer slot and the reduction's own adder, which the cpa slot chooses, "
     "carries the datapath's adds"),
    ("component|dot|*|`add`*",
     "the magnitude of a two's complement word and the sticky's carry-in; the datapath's own adds go through "
     "the cpa slot"),
    ("slot|dot|*|*shifter.family=butterfly_network",
     "the butterfly network needs a power-of-two width; the dot's windows and frames are not powers of two "
     "(33 and 53 bits at the fp16 x fp32 geometry)"),
    # the float families (fp.py)
    ("choice|fp_fma|*|sharing=*",
     "the sharing is the seed's: dedicated_per_mode builds one instance per mode and lane, shared_across_formats "
     "one per lane at the widest geometry over the modes that select it (alu_seed.py); the module text is the same"),
    ("choice|fp_adder|*|*lz.string_form=dual_pos_neg_strings",
     "the dual strings serve the unswapped datapath (operand_order shift_each_operand), whose difference is taken "
     "both ways; under the swap the single string of the non-negative difference suffices, so the generator rejects "
     "the pair"),
    ("choice|fp_adder|*|*lz.split_string_select",
     "acts under string_form dual_pos_neg_strings, which itself needs operand_order shift_each_operand: two "
     "conditions at once, beyond the one-key retry (the harness runs both selections)"),
    ("slot|fp_*|*|*shifter.family=butterfly_network",
     "the butterfly network needs a power-of-two width; the fp16 engine's window (27 bits) and significand field "
     "(26 bits) are not, so the generator rejects it (a power-of-two geometry admits it)"),
    ("slot|rounder|*|*shifter.family=butterfly_network", "the same: the rounder's words are XW+1 and XW+sr_bits+1 bits"),
    # the decimal dividers' multiply with no `multiplier` slot declared (families/decimal.py)
    ("component|divider|decimal_newton|`multiply`*",
     "the behavioral decimal product of an undeclared multiplier slot: a partial-product tree per multiply dominates "
     "the divider (a Newton divider instantiates several, and the harness times out), so the library multiplier "
     "renders when the slot names its family (the binary functional dividers' rule)"),
    ("component|divider|decimal_newton|`procedural`*", "the same: the behavioral decimal product is a function"),
    ("component|divider|decimal_newton|`modulo`*", "the same: the function's digit carries"),
    ("component|divider|decimal_newton|`add`*", "the same: the function's column sums"),
    # the posit unit: the choices and slots the seed realizes around the decoder and encoder (alu_float.py)
    ("choice|posit_unit|posit_adder_multiplier|approximation",
     "logarithmic_fraction puts the seed's PLAM module in the lane's fp multiplier (alu_float.py), outside the "
     "unit's decoder and encoder"),
    ("choice|posit_unit|posit_adder_multiplier|operator_set",
     "add_mul_div adds the lane's divider and square root (the sig_div slot) at the seed, outside the decoder "
     "and encoder"),
    ("slot|posit_unit|posit_adder_multiplier|sig_datapath.family*",
     "the significand adder of the lane's fp add path, which the seed builds (alu_float.py)"),
    ("slot|posit_unit|posit_adder_multiplier|sig_div.family*",
     "the divider of the lane's fdiv and fsqrt under operator_set add_mul_div, which the seed builds"),
    ("choice|posit_unit|posit_ieee_interop|interop_style",
     "boundary_converters makes the seed instantiate the converter modules; the other styles share the lane's X "
     "datapath (alu_float.py), outside the unit's decoder and encoder"),
    ("choice|posit_unit|posit_ieee_interop|conversion_direction", "the same: the directions the seed builds converters for"),
    # the special functions (sfu.py): the Net primitives take their family from the adder, multiplier,
    # shifter and lzc slots, and the module the sweep renders serves one function of one format
    ("choice|sfu|*|sharing",
     "the sharing choice places the evaluators across the unit's functions (a datapath per function, a shared "
     "evaluator, a shared range reduction, a shared ROM); the module the sweep renders serves one function, "
     "so the placement cannot reach its text"),
    ("component|sfu|*|`add`*",
     "the Net primitives at their undeclared default use the language's operator; a declared adder family "
     "renders the library module, which the pin check confirms"),
    ("component|sfu|*|`subtract`*", "the same primitives under the adder slot"),
    ("component|sfu|*|`multiply`*", "the same, under the multiplier slot whose default is behavioral_star"),
    ("component|sfu|*|`variable shift`*", "the same, under the shifter slot"),
    ("component|sfu|*|`increment`*", "the same: the operator's plus one under the adder slot"),
    # the checkers' reference arithmetic (alu_checker.py)
    ("component|checker|reduced_precision|*",
     "the float replica evaluates the engine's own reference functions (targets/rtl/engine.py: the X add, "
     "multiply, divide and square root), a behavioral model by construction: the checker's reference is what "
     "the datapath is checked against, and its narrow integer replica's own difference goes through the "
     "replica_adder slot"),
    ("component|checker|rns_redundant|`modulo`*",
     "the residue of a channel's product mod m: the code's own arithmetic, whose structure is the residue "
     "module's (targets/rtl/residue.py) for a 2^a - 1 modulus and a modulo for the rest"),
    ("component|channels|*|`add`*",
     "the channel arithmetic with no `modular_adder` family declared: the operator, since a library adder at every "
     "modular add, end-around carry and residue sum of three channels and both conversions takes the lane's "
     "multiplier past the harness's simulation budget; the slot's family renders them all"),
    ("component|channels|*|`subtract`*", "the same: the constant multiply's negative terms"),
    ("component|representation|generalized_signed_digit|`procedural`*",
     "the digit's encode and decode are constant case tables of the digit set (a function over one digit, no loop "
     "over data and no arithmetic of a library kind)"),
    ("slot|converter|*|*shifter.family=butterfly_network", "the same: the converter is the target's rounder"),
    ("slot|unpacker|*|*shifter.family=butterfly_network", "the same: the stored significand is SW bits (11 at fp16)"),
    ("slot|posit_unit|*|*shifter.family=butterfly_network", "the same: the posit body is n-1 bits and the X significand XW (15 and 36 at posit16_1)"),
    # the divider families (div.py): the selection slot's choices a host recurrence leaves no room for
    ("choice|divider|online_msdf|digit_select.speculative_candidate_residuals",
     "the on-line stage subtracts the digit's multiple of the divisor known so far into the same 3:2 row that "
     "takes the on-line terms, after the digit is known; there is no separate candidate set to select from"),
    ("choice|divider|srt_radix2|digit_select.divisor_truncation_bits",
     "the radix-2 selection with the digit set -1..1 needs no divisor bits (the overlap of its intervals covers "
     "every divisor in [1/2, 1)); the table has one divisor row"),
    ("choice|divider|online_msdf|digit_select.divisor_truncation_bits",
     "the same at radix 2 (the choice acts at radix 4)"),
    ("choice|divider|*|seed.magic_constant_selection",
     "the Newton step for the reciprocal carries the seed's relative error e to -e^2 exactly, so the "
     "correction-aware minimax constant is the zeroth-error one and the divider renders one text; the "
     "reciprocal square root's step carries e to -(3/2)e^2 - (1/2)e^3, whose optimum differs, and the "
     "square-root realizer renders the two constants apart"),
]

# ---- the instance prefixes of the library modules, by kind
INSTANCE_KINDS = [
    ("fam_adder_", "adder"), ("fam_add_", "adder"), ("fam_prefix_", "adder"), ("fam_incr_", "incrementer"),
    ("fam_count_popcount", "bitcount"), ("fam_count_trailing", "bitcount"), ("fam_count_", "lzc"),
    ("fam_shift_", "shifter"), ("fam_cmp_", "comparator"), ("fam_mul_", "multiplier"),
    ("fam_div_", "divider"), ("fam_divs_", "divider"), ("fam_sqrt_", "divider"), ("fam_fp_", "fp"),
    ("fam_bcd_", "bcd"), ("fam_posit_", "posit"), ("fam_rns_", "rns"), ("fam_sd_", "representation"),
    ("fam_hsd_", "representation"), ("fam_csd_", "representation"), ("fam_logic_", "logic"),
    ("fam_sfu_", "sfu"), ("fam_dot_", "dot"),
]
# the kind a slot's sub-space serves, by the sub-space's family set (filled by _space_registry)
_SPACE_KIND: dict = {}
_SPACE_NAME: dict = {}


class LoggingPins(dict):
    """A pins dictionary that records every key a generator looks up
    (`.get`, `[]`, `in`), and a scan (`items`, `keys`, iteration) as
    `*`; a copy shares the log."""

    def __init__(self, *a, log=None, **k):
        super().__init__(*a, **k)
        self.log = log if log is not None else set()

    def get(self, key, default=None):
        self.log.add(key)
        return super().get(key, default)

    def __getitem__(self, key):
        self.log.add(key)
        return super().__getitem__(key)

    def __contains__(self, key):
        self.log.add(key)
        return super().__contains__(key)

    def items(self):
        self.log.add("*")
        return super().items()

    def keys(self):
        self.log.add("*")
        return super().keys()

    def values(self):
        self.log.add("*")
        return super().values()

    def __iter__(self):
        self.log.add("*")
        return super().__iter__()

    def copy(self):
        return LoggingPins(dict.items(self), log=self.log)


# ---- the roots: the spaces the templates open ------------------------------------------------------
def _alu_roots() -> dict:
    """{kind: [(space, opener)]} of the ALU template's structure slots, the
    union over the mode sets a run can name (exact, approximate, BCD,
    float, posit, block, converting, several modes)."""
    from chialu.modules.alu import core_families, core_slots
    from chialu.verify.alu_ref import OPS, op_class
    from chialu.verify.formats import parse_format
    ops = list(OPS) + ["cvt(fp32)"]
    classes = {op_class(op) for op in ops}
    out: dict = defaultdict(list)
    seen: dict = defaultdict(set)

    def add(kind, space, opener):
        key = frozenset(f.name for f in space.families)
        if key in seen[kind]:
            return
        seen[kind].add(key)
        out[kind].append((space, opener))

    configs = [
        ("int", [("m0", parse_format("int16"))], {"int"}, False, False),
        ("approx", [("m0", parse_format("int16"))], {"int"}, True, False),
        ("bcd", [("m0", parse_format("int16"))], {"int"}, False, True),
        ("float", [("m0", parse_format("fp16"))], {"float"}, False, False),
        ("posit", [("m0", parse_format("posit16_1"))], {"posit"}, False, False),
        ("block", [("m0", parse_format("blksfp8e4m3efp4e2m1s16"))], {"block"}, False, False),
        ("multi", [("m0", parse_format("int16")), ("m1", parse_format("int8"))], {"int"}, False, False),
    ]
    for label, modes, fams, approx, bcd in configs:
        slots = core_slots(modes, ops, classes, fams, approx, bcd, 16)
        for kind, space in slots.items():
            add(kind, space, f"chialu.ALU ({label})")
        if label == "int":
            for f in core_families(slots):
                for kind, space in f.components.items():
                    if kind not in slots:
                        add(kind, space, f"chialu.ALU core.family={f.name}")
    return out


def roots() -> dict:
    """{kind: [(space, opener)]} of every unit template."""
    from chialu.spaces.checker_spaces import checker_space
    from chialu.spaces.fma_dot_spaces import dot_acc_space
    from chialu.spaces.sfu_spaces import sfu_approx_space
    out = _alu_roots()
    out["dot"] = [(dot_acc_space(16), "chialu.VecDotAcc core")]
    out["sfu"] = [(sfu_approx_space(True), "chialu.VecSFU core")]
    out["checker"] = [(checker_space(), "checker.family of a checked unit")]
    return out


def _space_registry():
    """Every space factory of chialu/spaces, keyed by its family set, so a
    slot's sub-space can be named and given a kind."""
    if _SPACE_KIND:
        return
    import importlib
    kinds = {"cpa_space": "adder", "block_adder_space": "adder", "mul_space": "multiplier", "div_space": "divider",
             "shifter_space": "shifter", "bitcount_space": "bitcount", "lzc_space": "lzc",
             "incrementer_space": "incrementer", "comparator_space": "comparator", "logic_space": "logic",
             "subword_space": "subword", "fp_add_space": "fp_adder", "fp_mul_space": "fp_multiplier",
             "fp_fma_space": "fp_fma",
             "fp_div_space": "fp_divider", "fp_cmp_space": "fp_comparator", "fp_cvt_space": "converter",
             "rounder_space": "rounder", "unpacker_space": "unpacker", "posit_unit_space": "posit_unit",
             "signed_digit_space": "representation", "rns_space": "channels", "dot_acc_space": "dot",
             "sfu_approx_space": "sfu", "checker_space": "checker", "two_rail_space": "cmp_checker",
             "approx_adder_space": "adder", "approx_mul_space": "multiplier", "approx_div_space": "divider",
             "decimal_adder_space": "adder", "decimal_mul_space": "multiplier", "decimal_div_space": "divider",
             "adder_tree_space": "adder_tree", "reduction_space": "reduction", "final_cpa_space": "final_cpa",
             "rounding_space": "rounding", "align_space": "align", "dot_align_space": "align",
             "component_mul_space": "multiplier",
             "dot_window_align_space": "align", "lza_space": "lza", "norm_space": "norm",
             "exponent_space": "exponent", "subnormal_space": "subnormal", "seed_table_space": "seed_table",
             "qds_space": "qds", "mult_final_round_space": "final_round", "segment_space": "segment",
             "poly_datapath_space": "evaluator", "range_reduction_space": "range_reduction",
             "rotator_space": "rotator", "saturation_space": "saturation", "popcount_space": "bitcount",
             # the float slots' filtered root spaces (fp_spaces.py): checked as their root kinds
             "tzc_space": "bitcount", "flagged_adder_space": "adder", "division_space": "divider",
             "sqrt_space": "divider"}
    for f in sorted(SPACE_DIR.glob("*_spaces.py")):
        mod = importlib.import_module(f"chialu.spaces.{f.stem}")
        for name in dir(mod):
            if not name.endswith("_space") or name.startswith("_"):
                continue
            fn = getattr(mod, name)
            try:
                sp = fn(16) if fn.__code__.co_argcount and fn.__defaults__ is None else fn()
            except Exception:
                continue
            key = frozenset(x.name for x in sp.families)
            _SPACE_NAME.setdefault(key, f"{name}()")
            _SPACE_KIND.setdefault(key, kinds.get(name, name.replace("_space", "")))


def space_kind(space) -> str:
    _space_registry()
    return _SPACE_KIND.get(frozenset(f.name for f in space.families), "?")


def space_name(space) -> str:
    _space_registry()
    return _SPACE_NAME.get(frozenset(f.name for f in space.families), "?")


ROOT_KINDS = {"adder", "multiplier", "divider", "shifter", "bitcount", "subword", "fp_adder", "fp_multiplier", "fp_fma",
              "fp_divider", "fp_comparator", "converter", "rounder", "unpacker", "posit_unit", "logic", "comparator",
              "representation", "channels", "dot", "sfu", "checker"}


# ---- the realizers ------------------------------------------------------------------------------
def _fp_geom():
    from chialu.characterize import fp_geom
    return fp_geom(W)


def _dot_geoms(family: str) -> list:
    """[(DotGeom, block)] a dot family is probed on: the FMA lineage on a
    scalar fp32 mode, the block families on a block mode, the two-term dot
    on two products, integer_mac on its integer mode and on the float mode
    (its organization serves both), the rest on fp16 x fp32 with four
    products."""
    from chialu.targets.rtl.families import dot
    from chialu.verify.formats import parse_format
    if family in dot.FMA_FAMILIES:
        modes = [("fp32", "fp32", "fp32", 1)]
    elif family in dot.BLOCK_FAMILIES:
        modes = [("blksfp8e4m3efp4e2m1s16", "fp16", "fp16", 2)]
    elif family == "integer_mac":
        modes = [("int8", "int32", "int32", 4), ("fp16", "fp32", "fp32", 4)]
    elif family == "fused_two_term_dot":
        modes = [("fp16", "fp32", "fp32", 2)]
    else:
        modes = [("fp16", "fp32", "fp32", 4)]
    return [(dot.geom_of(parse_format(fab), parse_format(fc), parse_format(fd), n, True), family in dot.BLOCK_FAMILIES)
            for fab, fc, fd, n in modes]


def _sfu_fn(family: str) -> str:
    from chialu.characterize import SFU_FN_OF
    fns = SFU_FN_OF.get(family, ("exp2",))
    return fns[0]


def _checker_spec(family: str, pins: dict) -> dict:
    # an integer mode and a float mode: a family's float replica, residue and parity paths live in the second
    spec = {"unit": "alu", "modes": [{"count": 1, "format": "int16"}, {"count": 1, "format": "fp16"}],
            "ops": ["add", "sub", "mul_wide", "and", "shl", "fadd", "fsub", "fmul"], "check_en": True,
            "checker_family": family}
    # the keys the checker consumes are read through the pins (so the read log sees them): the family's own pins,
    # the moduli, the comparator's family and its pins; a key the checker has no use for stays unread
    from chialu.targets.rtl.alu_checker import COMPARATOR_PIN_DEFAULTS, PIN_DEFAULTS
    own = PIN_DEFAULTS.get(family, {})
    cp, cmp_ = {}, {}
    cfam = pins.get("comparator.family") if "comparator.family" in dict.keys(pins) else None
    for k in list(dict.keys(pins)):
        if k in ("modulus", "moduli_count"):
            spec[k] = pins[k]
        elif k == "comparator.family":
            cmp_["family"] = cfam
        elif k.split(".")[0] in ("carry_replica", "row_adder", "coded_adder", "replica_adder"):
            slot, rest = k.split(".", 1)
            spec.setdefault(slot, {})[rest] = pins[k]
        elif k.startswith("comparator."):
            if cfam and k[len("comparator."):] in COMPARATOR_PIN_DEFAULTS.get(str(cfam), {}):
                cmp_[k[len("comparator."):]] = pins[k]
        elif k in own:
            cp[k] = pins[k]
    spec["checker_pins"] = cp
    if cmp_:
        spec["comparator"] = cmp_
    return spec


def realize(kind: str, family: str, pins: dict, W: int = W):
    """(module name, text, params) of a family of a kind under pins, or
    raises ValueError with the generator's reason; None when the kind has
    no realizer. `W` is the width of the integer kinds."""
    from chialu.targets.rtl.families import decimal, redundant
    if kind == "adder":
        if family in decimal.DECIMAL_FAMILIES.get("adder", ()):
            m = FAM.bcd_adder_module(family, pins, max(W, 32) // 4)      # eight digits: a four-digit word is one lookahead group
        else:
            m = FAM.adder_module(family, pins, W)
    elif kind == "multiplier":
        if family in decimal.DECIMAL_FAMILIES.get("multiplier", ()):
            m = FAM.bcd_mul_module(family, pins, max(W, 32) // 4)
        elif family == "twin_precision_subword":
            m = FAM.twin_precision_module([8, 8], [True, True], pins, W)
        else:
            m = FAM.mul_module(family, pins, W, True)
    elif kind == "divider":
        if family in decimal.DECIMAL_FAMILIES.get("divider", ()):
            m = FAM.bcd_div_module(family, pins, max(W, 32) // 4)
        else:
            m = FAM.div_module(family, pins, W, W, W)
            if m is None and family == "digit_recurrence_sqrt_combined":
                m = FAM.sqrt_module(family, pins, W)
    elif kind == "shifter":
        m = FAM.shifter_module(family, pins, W)
    elif kind == "comparator":
        m = FAM.comparator_module(family, pins, W, True) or FAM.adder_module(family, pins, W)
    elif kind == "bitcount":
        m = FAM.popcount_module(family, pins, W) or FAM.lzc_module(family, pins, W) or FAM.tzc_module(family, pins, W)
    elif kind == "lzc":
        m = FAM.lzc_module(family, pins, W)
    elif kind == "incrementer":
        m = FAM.incrementer_module(family, pins, W)
    elif kind == "logic":
        m = FAM.logic_module(family, pins, W)
    elif kind == "subword":
        m = FAM.partitioned_adder_module([8, 8], pins, W) if family == "partitioned_carry_chain" else None
    elif kind in ("fp_adder", "fp_multiplier", "fp_fma", "fp_comparator", "fp_divider", "rounder", "unpacker", "converter"):
        fmt, g, e = _fp_geom()
        k = "fp_sqrt" if family == "sig_sqrt_then_round" else kind
        m = FAM.fp_module(k, family, pins, g, fmt=fmt, M=fmt.man_bits, bias=fmt.bias, tokens=e.tokens)
    elif kind == "posit_unit":
        from chialu.characterize import posit_geom
        fmt, g, e = posit_geom(W)
        m = FAM.posit_module("unit", family, pins, fmt, g, tokens=e.tokens)
    elif kind == "representation":
        if family == "redundant_binary_multiplier":
            m = FAM.mul_module(family, pins, W, True)
        else:
            n, t = redundant.representation_adder_sv(W, family, pins)
            m = FAM.Module(n, {}, t)
    elif kind == "channels":
        # the lane's three RNS datapaths: the channel adder, the channel multiplier and the comparator (a
        # family's pins reach the one its own structures live in)
        names, texts = [], []
        for lane in ("adder", "multiplier", "comparator"):
            n, t = redundant.rns_sv(lane, W, family, pins, True)
            names.append(n)
            texts.append(t)
        m = FAM.Module("+".join(names), {}, "\n".join(texts))
    elif kind == "dot":
        from chialu.targets.rtl.families import dot
        names, texts = [], []
        for dg, block in _dot_geoms(family):
            n, t, _ = dot.dot_sv(dg, family, pins, block=block)
            names.append(n)
            texts.append(t)
        m = FAM.Module("+".join(names), {}, "\n".join(texts))
    elif kind == "sfu":
        from chialu.targets.rtl.engine import Conventions, Engine
        from chialu.targets.rtl.families import sfu
        from chialu.targets.rtl.families.fp import Geom
        from chialu.verify.formats import parse_format
        # a value table serves a format of at most 12 bits, so the table families are probed at fp8
        fmt = parse_format("fp8e4m3" if family in ("direct_lut", "compressed_lut") else "fp16")
        e = Engine("c", fmt, 8, False, targets=[fmt], conv=Conventions())
        if family == "softmax_layernorm":
            n, t, _ = sfu.vector_sv("softmax", fmt, Geom.of_engine(e), 4, family, pins)
        else:
            n, t, _ = sfu.sfu_sv(_sfu_fn(family), fmt, Geom.of_engine(e), family, pins)
        m = FAM.Module(n, {}, t)
    elif kind == "checker":
        from chialu.targets.rtl.alu_checker import alu_checker_sv
        rtl, _ = alu_checker_sv(_checker_spec(family, pins))
        m = FAM.Module("alu_checker", {}, rtl)
    else:
        return None
    if m is None:
        return None
    text = m.text if m.text is not None else FAM.module_text(m.name)
    return m.name, text, dict(m.params)


# ---- the space walk -----------------------------------------------------------------------------
def samples(dom) -> list:
    """The values a choice is swept at: every enum and bool member, the
    low, middle and high of a range."""
    if isinstance(dom, Enum):
        return dom.members()
    if isinstance(dom, Bool):
        return [False, True]
    if isinstance(dom, Range):
        ms = dom.members() if dom.finite() and dom.count() <= RANGE_SAMPLES else None
        if ms is not None:
            return ms
        return sorted({dom._at(0), dom._at(dom.count() // 2), dom._at(dom.count() - 1)})
    return []


def declared_keys(family, prefix: str = "", depth: int = 0, out: set | None = None) -> set:
    """Every pin key a family declares, relative to its structure: its
    choices, `<slot>.family` and, for every family of every slot,
    recursively."""
    out = set() if out is None else out
    if depth > 8:
        return out
    for c in family.design_choices:
        out.add(prefix + c)
    for slot, sub in family.components.items():
        out.add(f"{prefix}{slot}.family")
        for f in sub.families:
            declared_keys(f, f"{prefix}{slot}.", depth + 1, out)
    return out


def sweep_points(family, prefix: str = "", base: dict | None = None, depth: int = 0, full: bool = True) -> list:
    """[(label, pins)] of the renders that sweep a family: for each choice
    its samples, for each slot each member and, one level down, the
    member's choices and slots. A slot whose space is a root kind is
    swept at its members and their first-level choices alone (`full`
    False), since the deeper keys are swept under that root."""
    base = base or {}
    out = []
    for c, dom in family.design_choices.items():
        for v in samples(dom):
            out.append((f"{prefix}{c}={v}", dict(base, **{prefix + c: v})))
    if depth > 6:
        return out
    for slot, sub in family.components.items():
        key = f"{prefix}{slot}.family"
        sub_root = space_kind(sub) in ROOT_KINDS
        for f in sub.families:
            pins = dict(base, **{key: f.name})
            out.append((f"{key}={f.name}", pins))
            if full or not sub_root:
                # the member's own choices (and, for a non-root sub-space, its slots in full)
                out += sweep_points(f, f"{prefix}{slot}.", pins, depth + 1, full=not sub_root and full)
            else:
                for c, dom in f.design_choices.items():
                    for v in samples(dom):
                        out.append((f"{prefix}{slot}.{c}={v}", dict(pins, **{f"{prefix}{slot}.{c}": v})))
    return out


# ---- the text analysis --------------------------------------------------------------------------
_INST_RE = re.compile(r"^\s*(fam_\w+)\s*(?:#\s*\((.*?)\))?\s*(\w+)\s*\(", re.M | re.S)
_DECL_RE = re.compile(r"\b(?:logic|wire|reg|input|output|inout)\s+(?:logic\s+)?(?:signed\s+)?\[\s*([^:\]]+)\s*:\s*([^\]]+)\]\s+([\w, ]+?)\s*(?:;|,|\)|=)")
# a declaration without a range is one bit
_DECL1_RE = re.compile(r"\b(?:logic|wire|reg|input|output|inout)\s+(?:logic\s+)?(?:signed\s+)?([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\s*(?:;|,|\)|=)")
_ASSIGN_RE = re.compile(r"\bassign\s+(\w+)(?:\s*\[[^\]]*\])?\s*=\s*(.*?);", re.S)
_ALWAYS_ASSIGN_RE = re.compile(r"^\s*(\w+)(?:\s*\[[^\]]*\])?\s*(?:<=|=)\s*(.*?);", re.M | re.S)
_LIT = r"\d+\s*'\s*[sS]?[bdhoBDHO][0-9a-fA-F_xXzZ?]+"          # a sized literal is one operand, not a width and a tail
_OPERAND = rf"({_LIT}|\{{[^{{}}]*(?:\{{[^{{}}]*\}}[^{{}}]*)*\}}|\w+(?:\s*\[[^\]]*\])?|\([^()]*\))"
_OP_RE = re.compile(rf"{_OPERAND}\s*(<<<|>>>|<<|>>|\*|\+|-|%|/)\s*{_OPERAND}")
_CONST_RE = re.compile(r"^\(?\s*(\d+'[sS]?[bdhoBDHO][0-9a-fA-F_xXzZ?]+|\d+)\s*\)?$")


def normalize(name: str, text: str) -> str:
    """The module text without its comments and with its own name masked,
    for the sensitivity and the naming checks."""
    t = re.sub(r"//[^\n]*", "", text)
    t = t.replace(name, "@")
    return re.sub(r"\s+", " ", t).strip()


def _is_one(s: str) -> bool:
    """Whether a constant operand is one (the library's incrementer adds a
    carry-in; any other constant folds into the surrounding logic)."""
    s = s.strip().strip("()").strip()
    m = re.match(r"^\d*\s*'\s*[sS]?[bdhoBDHO]?([0-9a-fA-F_]+)$", s)
    body = m.group(1).replace("_", "") if m else s
    try:
        return int(body, 16 if (m and "h" in s.lower()) else (2 if (m and "b" in s.lower()) else 10)) == 1
    except ValueError:
        return False


def _const(s: str) -> bool:
    s = s.strip()
    return bool(_CONST_RE.match(s)) or s in ("1'b0", "1'b1")


def _width_expr(hi: str, lo: str) -> int | None:
    try:
        return int(eval(hi.strip(), {"__builtins__": {}}, {})) - int(eval(lo.strip(), {"__builtins__": {}}, {})) + 1
    except Exception:
        return None


def widths_of(text: str) -> dict:
    out = {}
    for m in _DECL1_RE.finditer(text):
        for n in m.group(1).split(","):
            n = n.strip()
            if n and n not in ("logic", "signed", "wire", "reg"):
                out.setdefault(n, 1)
    for m in _DECL_RE.finditer(text):
        w = _width_expr(m.group(1), m.group(2))
        for n in m.group(3).split(","):
            n = n.strip()
            if n:
                out[n] = w
    return out


_CONST_NAME_RE = re.compile(r"\b(?:genvar|parameter|localparam|integer|int)\s+(?:\w+\s+)?([\w, ]+?)\s*(?:=|;)")
_LOOP_VAR_RE = re.compile(r"\bfor\s*\(\s*(?:int\s+|integer\s+|genvar\s+)?(\w+)\s*=")


def behavioral_ops(text: str) -> list:
    """[(op, width, line)] of the behavioral operators of a library kind in
    a module text: adds and subtracts of two non-constant operands,
    multiplies with a non-constant operand, shifts by a non-constant
    amount, modulo and divide, at a destination width of MIN_WIDTH or more
    (unknown widths are reported as `?`); and the procedural blocks. An
    operand that is a parameter, a genvar or a loop variable is a
    constant of the elaboration."""
    body = re.sub(r"//[^\n]*", "", text)
    ws = widths_of(body)
    consts = set()
    for m in _CONST_NAME_RE.finditer(body):
        for n in m.group(1).split(","):
            consts.add(n.strip())
    consts |= set(_LOOP_VAR_RE.findall(body))
    out = []
    seen = set()

    def const(s):
        s = s.strip()
        return _const(s) or re.sub(r"\s*\[.*", "", s).strip("() ") in consts

    def operand_width(x):
        """The width of an operand expression: the widest part-select it carries ([hi:lo], [base +: n], a bit),
        else the widest declared wire it names (a shifted or parenthesized slice keeps its width)."""
        x = x.strip()
        if x.startswith("{"):
            # a concatenation: the sum of its parts' widths (a replication stands for an unknown width)
            body = x[1:-1] if x.endswith("}") else x[1:]
            if "REPL" in body:
                return None
            total, depth, cur, parts = 0, 0, "", []
            for ch in body:
                if ch == "," and depth == 0:
                    parts.append(cur); cur = ""
                    continue
                depth += (ch == "{") - (ch == "}")
                cur += ch
            parts.append(cur)
            for part in parts:
                part = part.strip()
                m3 = re.match(r"^(\d+)\s*'", part)
                w3 = int(m3.group(1)) if m3 else operand_width(part)
                if not w3:
                    return None
                total += w3
            return total or None
        widths = []
        for m2 in re.finditer(r"\[\s*(\d+)\s*:\s*(\d+)\s*\]", x):
            widths.append(abs(int(m2.group(1)) - int(m2.group(2))) + 1)
        for m2 in re.finditer(r"\[[^\[\]]*\+:\s*(\d+)\s*\]", x):
            widths.append(int(m2.group(1)))
        if not widths and re.search(r"\w\s*\[[^:\[\]]+\]", x):
            widths.append(1)
        if widths:
            return max(widths)
        names = [ws.get(n) for n in re.findall(r"[A-Za-z_]\w*", x)]
        names = [n for n in names if n]
        return max(names) if names else None

    def dest_width(dst, a, b):
        """The operation's width: the widest non-constant operand (a digit slice of a wider word is a digit
        operation), else the destination's."""
        cands = [operand_width(x) for x in (a, b) if not const(x)]
        cands = [c for c in cands if c]
        if cands:
            return max(cands)
        return ws.get(dst)

    for rx in (_ASSIGN_RE, _ALWAYS_ASSIGN_RE):
        for m in rx.finditer(body):
            dst, rhs = m.group(1), m.group(2)
            if dst in consts or dst in ("parameter", "localparam", "genvar", "integer", "int"):
                continue
            rhs = re.sub(r"\{\s*[^{}]*\{[^{}]*\}\s*\}", "REPL", rhs)       # replication is wiring
            # an operator inside an index is addressing (a table row `[i * W +: W]`), not arithmetic: the index
            # expression goes, a part-select keeps its width
            rhs = re.sub(r"\[[^\[\]]*\+:\s*(\d+)\s*\]", r"[+:\1]", rhs)
            rhs = re.sub(r"\[(?!\+:)([^\[\]]*[*+\-/%][^\[\]]*)\]", "[IDX]", rhs)
            for om in _OP_RE.finditer(rhs):
                a, op, b = om.group(1), om.group(2), om.group(3)
                if op in ("<<", ">>", "<<<", ">>>"):
                    if const(b):
                        continue
                    label = "variable shift"
                elif op == "*":
                    # a constant multiply is shifts and adds of the constant's bits, which synthesis builds and
                    # no library multiplier takes (its ports are two variable operands)
                    if const(a) or const(b):
                        continue
                    label = "multiply"
                elif op in ("+", "-"):
                    if const(a) and const(b):
                        continue
                    if const(a) or const(b):
                        # the library's incrementer is a + cin: an increment or decrement by one is a component of
                        # that kind, and any other constant folds into the surrounding logic
                        lit = b.strip() if const(b) else a.strip()
                        if not _is_one(lit):
                            continue
                        label = "increment" if op == "+" else "decrement"
                    else:
                        label = "add" if op == "+" else "subtract"
                else:
                    if const(a) and const(b):
                        continue
                    label = "modulo" if op == "%" else "divide"
                w = dest_width(dst, a, b)
                if w is not None and w < MIN_WIDTH:
                    continue
                key = (label, w, dst)
                if key in seen:
                    continue
                seen.add(key)
                line = body[:m.start()].count("\n") + 1
                out.append((label, w, f"{dst} = ... {a.strip()} {op} {b.strip()} ... (line {line})"))
    for m in re.finditer(r"^\s*(function\b[^\n]*|for\s*\([^\n]*)", body, re.M):
        line = body[:m.start()].count("\n") + 1
        out.append(("procedural", None, f"{m.group(1).strip()[:70]} (line {line})"))
    return out


def instances(text: str) -> list:
    """[(module, kind)] of the library instances of a module text (the
    module's own definition excluded)."""
    out = []
    defined = set(re.findall(r"^module\s+(\w+)", text, re.M))
    for m in _INST_RE.finditer(text):
        name = m.group(1)
        if name in defined and m.group(3) == name:
            continue
        kind = next((k for p, k in INSTANCE_KINDS if name.startswith(p)), "?")
        out.append((name, kind))
    return out


# ---- the source locator -------------------------------------------------------------------------
_SRC_CACHE: dict = {}


def locate(family: str, key: str | None = None) -> str:
    """`file:line` of a family's block in chialu/spaces, or of a choice or
    slot key inside it; a best-effort text search."""
    ck = (family, key)
    if ck in _SRC_CACHE:
        return _SRC_CACHE[ck]
    start = re.compile(r"(?:Family\(\s*|_f\(\s*|_a\(\s*)\"" + re.escape(family) + r"\"")
    nxt = re.compile(r"(?:Family\(\s*|_f\(\s*|_a\(\s*)\"\w+\"|^def ")
    found = ""
    for f in sorted(SPACE_DIR.glob("*_spaces.py")):
        text = f.read_text()
        m = start.search(text)
        if not m:
            continue
        line0 = text[:m.start()].count("\n") + 1
        if key is None:
            found = f"{f.name}:{line0}"
            break
        rest = text[m.end():]
        n = nxt.search(rest)
        block = rest[:n.start()] if n else rest
        km = re.search(r"\"" + re.escape(key) + r"\"\s*:|(?:^|[\s(,])" + re.escape(key) + r"\s*=", block, re.M)
        found = f"{f.name}:{line0 + block[:km.start()].count(chr(10)) if km else line0}"
        break
    _SRC_CACHE[ck] = found
    return found


# ---- the check ----------------------------------------------------------------------------------
class Finding:
    __slots__ = ("check", "kind", "family", "item", "detail", "where", "allowed")

    def __init__(self, check, kind, family, item, detail, where=""):
        self.check, self.kind, self.family, self.item, self.detail, self.where = check, kind, family, item, detail, where
        self.allowed = None

    @property
    def id(self):
        return f"{self.check}|{self.kind}|{self.family}|{self.item}"

    def row(self):
        return {"check": self.check, "kind": self.kind, "family": self.family, "item": self.item,
                "detail": self.detail, "where": self.where, "allowed": self.allowed}


def _key(pins: dict) -> str:
    return json.dumps(pins, sort_keys=True, default=str)


_ROOT_GROUPS: dict = {}
_INST_W_RE = re.compile(r"(fam_\w+?)(?:_w(\d+)\b)?\s*(?:#\s*\(\s*\.W\((\d+)\))?")


def instance_width(text: str, module_prefixes: tuple) -> int | None:
    """The width of the first library instance of a kind in a module text:
    its `.W(n)` parameter or the `_w<n>` of a generated module's name."""
    for m in re.finditer(r"^\s*(fam_\w+)\s*(#\s*\((.*?)\))?\s*\w+\s*\(", text, re.M | re.S):
        name = m.group(1)
        if not name.startswith(module_prefixes):
            continue
        pm = re.search(r"\.W\((\d+)\)", m.group(3) or "")
        if pm:
            return int(pm.group(1))
        nm = re.search(r"_w(\d+)(?:_|$)", name)
        if nm:
            return int(nm.group(1))
    return None


def root_groups(kind: str, family: str, choice: str, vals: list, width: int = W) -> dict:
    """{normalized text: [values]} of a root kind's family rendered on its
    own over one choice at a width (cached): the reference for the
    forwarding check of a consumer's sub-slot."""
    ck = (kind, family, choice, width)
    if ck in _ROOT_GROUPS:
        return _ROOT_GROUPS[ck]
    groups: dict = defaultdict(list)
    for v in vals:
        try:
            r = realize(kind, family, {choice: v}, width)
        except Exception:                                      # noqa: BLE001
            continue
        if r is None:
            continue
        mname, text, params = r
        groups[normalize(mname, text) + " " + json.dumps(params, sort_keys=True)].append(v)
    _ROOT_GROUPS[ck] = groups
    return groups


# how far the slot sweep descends through a slot's own slots. A slot's family choices are swept at
# every level it reaches, which is what catches a composite that does not forward a slot's pins; the
# levels below that are the sub-kind's own sweep, and they are what makes a dot family's sweep hours
# long (pairwise_tree reaches 685 choices through its multiplier slot's eleven families).
SLOT_DEPTH = [2]

# how many sibling and ancestor contexts an insensitive choice is retried under before the check
# gives up and reports it. The retry is what tells a choice that acts under a sibling's value from
# one that acts nowhere, and it costs one render per context, so a family reaching hundreds of
# choices spends the sweep here rather than on its own text.
RETRY_CAP = [32]


class Budget(BaseException):
    """A family's render budget ran out: the family reports one row saying
    so and its sweep stops. It derives from BaseException, since the
    checks catch Exception around a render and would otherwise carry on
    against a generator that now refuses every call, which reads as a
    finding per choice value."""


def check_family(kind: str, fam, opener: str, checks: set, verbose: bool = False, budget_s: float = 0) -> tuple:
    """The findings of one family of a root kind, and the render count.
    `budget_s` bounds the family's renders in seconds (0: no bound); a
    family that passes it reports one row and its sweep stops there."""
    F = []
    name = fam.name
    renders = 0
    declared = declared_keys(fam)
    read: set = set()
    texts: dict = {}          # pins key -> (module name, normalized text) or ("!", error)
    names: dict = defaultdict(set)
    deadline = (time.time() + budget_s) if budget_s else None

    def render(pins):
        nonlocal renders
        k = _key(pins)
        if k in texts:
            return texts[k]
        if deadline is not None and time.time() > deadline:
            raise Budget(f"{renders} renders in {budget_s:.0f}s")
        lp = LoggingPins(pins, log=read)
        renders += 1
        try:
            r = realize(kind, name, lp)
        except Exception as e:                                 # noqa: BLE001 - the generator's own reason
            texts[k] = ("!", f"{type(e).__name__}: {str(e)[:160]}")
            return texts[k]
        if r is None:
            texts[k] = ("!", "no module")
            return texts[k]
        mname, text, params = r
        pj = json.dumps(params, sort_keys=True)
        norm = normalize(mname, text) + " " + pj
        texts[k] = (mname, norm, text, params)
        # a parametric .sv module is identified by its name and parameters; a generated one by its name
        names[(mname, pj if params else "")].add(norm)
        return texts[k]

    def groups_of(base: dict, key: str, vals: list) -> tuple:
        """({normalized text: [values]}, [(value, error)]) of the renders of a choice key over its values."""
        groups: dict = defaultdict(list)
        rejected = []
        for v in vals:
            t = render(dict(base, **{key: v}))
            if t[0] == "!":
                rejected.append((v, t[1]))
            else:
                groups[t[1]].append(v)
        return groups, rejected

    # -- family and menu (the menu asks has_module with the slot's last path component: `core` for the
    # dot accumulator's and the SFU's family; the checker's menu is built by hand and marks nothing)
    base = render({})
    ok = base[0] != "!"
    menu_kind = {"dot": "core", "sfu": "core"}.get(kind, kind)
    has = FAM.has_module(menu_kind, name) if kind != "checker" else ok
    seed = SEED_REALIZED.get((kind, name))
    if not ok:
        f = Finding("family", kind, name, "-", f"no module: {base[1]}" if not seed else f"realized in the seed: {seed}", locate(name))
        f.allowed = seed
        F.append(f)
    if "menu" in checks:
        if has and not ok and not seed:
            F.append(Finding("menu", kind, name, "-", "has_module says [library], the realizer returns none", locate(name)))
        if not has and (ok or seed):
            F.append(Finding("menu", kind, name, "-", "the realizer returns a module, has_module says no [library] mark", locate(name)))
    if not ok:
        return F, renders
    base_text = base[2]
    # the component scan reads the module's own text: the library modules it instantiates follow it in the
    # same text and are scanned under their own root kinds
    own_text = FAM.split_modules(base_text).get(base[0], base_text)
    leaf = base[0] in FAM._module_texts_of_files()        # a parametric module of the .sv files

    # -- the sweep
    for _label, pins in sweep_points(fam):
        render(pins)

    # -- choice sensitivity (the family's own choices; a choice insensitive at the defaults is retried
    # under every value of each sibling choice: a choice that only acts under a sibling's value is
    # reported as conditional, which counts as allowed)
    def choice_check(f, prefix: str, base: dict, ancestors: list):
        """`ancestors`: [(key, domain)] of the choices of the families above `f` (the root's own for the
        root), under whose values an insensitive choice is retried."""
        own = [(prefix + c2, dom2) for c2, dom2 in f.design_choices.items()]
        for c, dom in f.design_choices.items():
            vals = samples(dom)
            if len(vals) < 2:
                continue
            key = prefix + c
            groups, rejected = groups_of(base, key, vals)
            for v, why in rejected:
                F.append(Finding("choice", kind, name, f"{key}={v}", f"rejected: {why}", locate(f.name, c)))
            live = len(vals) - len(rejected)
            if len(groups) == 1 and live > 1:
                cond = None
                ctx = [(k2, dom2) for k2, dom2 in own + ancestors if k2 != key][:RETRY_CAP[0]]
                capped = len(own + ancestors) - 1 > RETRY_CAP[0]
                for k2, dom2 in ctx:
                    for v2 in samples(dom2):
                        g2, _r2 = groups_of(dict(base, **{k2: v2}), key, vals)
                        if len(g2) > 1:
                            cond = f"{k2}={v2}"
                            break
                    if cond:
                        break
                if not cond and len(ctx) <= 8:
                    # a choice that acts under two siblings' values at once (a correction under a scheme)
                    for a_i in range(len(ctx)):
                        for b_i in range(a_i + 1, len(ctx)):
                            (ka, da), (kb, db) = ctx[a_i], ctx[b_i]
                            for va in samples(da):
                                for vb in samples(db):
                                    g2, _r2 = groups_of(dict(base, **{ka: va, kb: vb}), key, vals)
                                    if len(g2) > 1:
                                        cond = f"{ka}={va}, {kb}={vb}"
                                        break
                                if cond:
                                    break
                            if cond:
                                break
                        if cond:
                            break
                fi = Finding("choice", kind, name, key, f"every member renders one text ({', '.join(map(str, vals))})"
                             + (f"; sensitive under {cond}" if cond else "")
                             + ("" if cond or not capped else f"; retried under {len(ctx)} of "
                                f"{len(own + ancestors) - 1} contexts"), locate(f.name, c))
                if cond:
                    fi.allowed = f"conditional: the choice acts under {cond}"
                F.append(fi)
            elif len(groups) > 1 and isinstance(dom, (Enum, Bool)):
                for norm, members in groups.items():
                    if len(members) > 1:
                        # members alike at the defaults may part under a sibling's or an ancestor's value (an encoder
                        # whose forms differ at another radix)
                        cond = None
                        ctx = [(k2, dom2) for k2, dom2 in own + ancestors if k2 != key][:RETRY_CAP[0]]
                        for k2, dom2 in ctx:
                            for v2 in samples(dom2):
                                g2, _r2 = groups_of(dict(base, **{k2: v2}), key, list(members))
                                if len(g2) > 1:
                                    cond = f"{k2}={v2}"
                                    break
                            if cond:
                                break
                        fi = Finding("choice", kind, name, f"{key}={'|'.join(map(str, members))}",
                                     "these members render one text" + (f"; they part under {cond}" if cond else ""), locate(f.name, c))
                        if cond:
                            fi.allowed = f"conditional: the members part under {cond}"
                        F.append(fi)

    if "choice" in checks:
        choice_check(fam, "", {}, [])

    # -- slot coverage (every slot at every depth the sweep reached; `base` activates the family)
    def slot_check(f, prefix: str, base: dict, depth: int = 0, ancestors: list | None = None):
        ancestors = list(ancestors or []) + [(prefix + c2, dom2) for c2, dom2 in f.design_choices.items()]
        # the sibling slots' families join the retry context (a final adder used under one tree family alone)
        siblings = [(f"{prefix}{s2}.family", Enum(tuple(x.name for x in sub2.families))) for s2, sub2 in f.components.items()]
        for slot, sub in f.components.items():
            key = f"{prefix}{slot}.family"
            ancestors_here = ancestors + [(k2, d2) for k2, d2 in siblings if k2 != key]
            members = [x.name for x in sub.families]
            sbase = dict(base)
            groups, rejected = groups_of(sbase, key, members)
            read_here = key in read or any(k.startswith(prefix + slot + ".") for k in read)
            where = locate(f.name, slot)
            dead = False
            if not read_here and "*" not in read:
                F.append(Finding("slot", kind, name, key, f"never read ({space_name(sub)}, {len(members)} members)", where))
                dead = True
            for mn, why in rejected:
                F.append(Finding("slot", kind, name, f"{key}={mn}", f"rejected: {why}", where))
            if len(groups) == 1 and len(members) - len(rejected) > 1:
                # a slot that exists under a non-default value of an ancestor's choice alone (the hard multiples
                # under a Booth radix, a merge tree under a merge form): retried under every value of each
                # ancestor choice, and probed under the first that uses it
                cond = None
                for k2, dom2 in ancestors_here:
                    for v2 in samples(dom2):
                        g2, r2 = groups_of(dict(sbase, **{k2: v2}), key, members)
                        if len(g2) > 1:
                            cond = f"{k2}={v2}"
                            sbase = dict(sbase, **{k2: v2})
                            groups, rejected = g2, r2
                            break
                    if cond:
                        break
                if cond:
                    fi = Finding("slot", kind, name, key, f"every member renders one text at the defaults; used under {cond}", where)
                    fi.allowed = f"conditional: the slot is used under {cond}"
                    F.append(fi)
                else:
                    if not dead:
                        F.append(Finding("slot", kind, name, key, f"every member renders one text ({space_name(sub)}: {', '.join(members)})", where))
                    dead = True
            if len(groups) > 1:
                for norm, ms in groups.items():
                    if len(ms) > 1:
                        F.append(Finding("slot", kind, name, f"{key}={'|'.join(ms)}", "these members render one text", where))
            if dead:
                continue                                          # a dead slot is one row
            sub_kind = space_kind(sub)
            sub_root = sub_kind in ROOT_KINDS
            for sf in sub.families:
                mbase = dict(sbase, **{key: sf.name})
                if render(mbase)[0] == "!":
                    continue
                if sub_root:
                    # the member's own choices are the root kind's business; here the question is
                    # whether the consumer forwards them: a choice the root renders differently (at
                    # the width the consumer instantiates it) and the consumer renders alike is not
                    # forwarded; a choice the consumer's context leaves unused is retried under the
                    # ancestors' choices
                    mtext = render(mbase)[2]
                    iw = instance_width(mtext, tuple(p for p, k in INSTANCE_KINDS if k == sub_kind)) or W
                    for c, dom in sf.design_choices.items():
                        vals = samples(dom)
                        if len(vals) < 2 or len(root_groups(sub_kind, sf.name, c, vals, iw)) < 2:
                            continue
                        ck = f"{prefix}{slot}.{c}"
                        g2, _r2 = groups_of(mbase, ck, vals)
                        if len(g2) == 1 and sum(len(x) for x in g2.values()) > 1:
                            cond = None
                            for k2, dom2 in ancestors:
                                for v2 in samples(dom2):
                                    g3, _r3 = groups_of(dict(mbase, **{k2: v2}), ck, vals)
                                    if len(g3) > 1:
                                        cond = f"{k2}={v2}"
                                        break
                                if cond:
                                    break
                            fi = Finding("slot", kind, name, f"{ck} under {sf.name}",
                                         f"not forwarded: the {sub_kind} at {iw} bits renders {', '.join(map(str, vals))} "
                                         f"differently, the consumer alike" + (f"; forwarded under {cond}" if cond else ""), where)
                            if cond:
                                fi.allowed = f"conditional: the slot is used under {cond}"
                            F.append(fi)
                else:
                    choice_check(sf, f"{prefix}{slot}.", mbase, ancestors)
                    if depth < SLOT_DEPTH[0]:
                        slot_check(sf, f"{prefix}{slot}.", mbase, depth + 1, ancestors)

    if "slot" in checks:
        slot_check(fam, "", {})

    # -- undeclared pins
    if "pin" in checks:
        for k in sorted(read):
            if k == "*" or k.startswith("_") or k in declared:
                continue
            F.append(Finding("pin", kind, name, k, "read by the generator, declared by no space", locate(name)))

    # -- component realization (the baseline text; a parametric .sv leaf module is the library's own structure)
    if "component" in checks and not leaf:
        # the kinds a read slot pin chose: the sub-space kind of every slot key read
        slot_kinds = set()

        def slot_kinds_of(f, prefix=""):
            for slot, sub in f.components.items():
                key = f"{prefix}{slot}.family"
                if key in read or any(k.startswith(prefix + slot + ".") for k in read):
                    slot_kinds.add(space_kind(sub))
                for sf in sub.families:
                    slot_kinds_of(sf, f"{prefix}{slot}.")
        slot_kinds_of(fam)
        kind_alias = {"lzc": {"lzc", "bitcount", "lza"}, "bitcount": {"bitcount", "lzc"}, "adder": {"adder", "final_cpa", "adder_tree"},
                      "incrementer": {"incrementer", "adder"}, "divider": {"divider"}, "multiplier": {"multiplier"},
                      "shifter": {"shifter", "align", "norm"}, "comparator": {"comparator"}}
        for mod, ikind in instances(own_text):
            if ikind in ("fp", "bcd", "posit", "rns", "representation", "sfu", "dot", "logic", "?"):
                continue
            ok_inst = bool(kind_alias.get(ikind, {ikind}) & slot_kinds) or ikind == kind
            if not ok_inst:
                F.append(Finding("component", kind, name, f"instance {mod}", f"a {ikind} instance no read slot pin chose (class B)", locate(name)))
        for label, w, ev in behavioral_ops(own_text):
            F.append(Finding("component", kind, name, f"`{label}` {w if w else '?'} bits", ev, locate(name)))

    # -- module naming (the checker's module name is the seed's, not a library key)
    if "name" in checks and kind != "checker":
        for (mname, pj), norms in names.items():
            if len(norms) > 1:
                F.append(Finding("name", kind, name, mname + (f" #{pj}" if pj else ""),
                                 f"{len(norms)} different texts under one module name", locate(name)))
    if verbose:
        print(f"  {kind}/{name}: {renders} renders, {len(F)} rows", file=sys.stderr, flush=True)
    return F, renders


def apply_allowlist(findings: list) -> None:
    for f in findings:
        if f.allowed:
            continue
        for pat, reason in ALLOWLIST:
            if fnmatch.fnmatchcase(f.id, pat):
                f.allowed = reason
                break


def run(kinds=None, families=None, checks=None, verbose=False, progress=False, budget_s: float = 0) -> tuple:
    checks = set(checks or ("family", "slot", "pin", "choice", "component", "name", "menu"))
    findings = []
    n_fam = renders = 0
    t_start = time.time()
    for kind, spaces in roots().items():
        if kinds and kind not in kinds:
            continue
        seen = set()
        for space, opener in spaces:
            for fam in space.families:
                if fam.name in seen or (families and fam.name not in families):
                    continue
                seen.add(fam.name)
                n_fam += 1
                t0 = time.time()
                try:
                    F, r = check_family(kind, fam, opener, checks, verbose, budget_s)
                except Budget as b:
                    F, r = [Finding("budget", kind, fam.name, "the sweep",
                                    f"not swept: {b}", "")], 0
                findings += F
                renders += r
                if progress:                     # a long sweep prints as it goes, so a run is watchable
                    print(f"  [{time.time() - t_start:6.0f}s] {kind}/{fam.name}: {r} renders, {len(F)} rows"
                          f" ({time.time() - t0:.0f}s)", file=sys.stderr, flush=True)
    apply_allowlist(findings)
    return findings, n_fam, renders


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--kinds", help="comma list of root kinds")
    ap.add_argument("--families", help="comma list of family names")
    ap.add_argument("--checks", help="comma list of checks (family, slot, pin, choice, component, name, menu)")
    ap.add_argument("--json", help="write the rows to this file")
    ap.add_argument("--all", action="store_true", help="print the allowed rows too")
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--progress", action="store_true", help="print each family as it is checked (a sweep runs for tens of minutes)")
    ap.add_argument("--family-timeout", type=float, default=0,
                    help="seconds a family's sweep may take (0: no bound); one past it reports a `budget` row")
    ap.add_argument("--slot-depth", type=int, default=SLOT_DEPTH[0],
                    help="how far the slot sweep descends through a slot's own slots (its family choices "
                         "are swept at every level it reaches)")
    ap.add_argument("--retry-cap", type=int, default=RETRY_CAP[0],
                    help="sibling and ancestor contexts an insensitive choice is retried under")
    a = ap.parse_args(argv)
    SLOT_DEPTH[0] = a.slot_depth
    RETRY_CAP[0] = a.retry_cap
    t0 = time.time()
    findings, n_fam, renders = run(a.kinds.split(",") if a.kinds else None, a.families.split(",") if a.families else None,
                                   a.checks.split(",") if a.checks else None, a.verbose, a.progress,
                                   a.family_timeout)
    open_ = [f for f in findings if not f.allowed]
    rows = [f for f in findings if a.all or not f.allowed]
    rows.sort(key=lambda f: (f.check, f.kind, f.family, f.item))
    wk = max([len(f.kind) for f in rows] + [4])
    wf = max([len(f.family) for f in rows] + [6])
    wi = max([min(len(f.item), 60) for f in rows] + [4])
    for f in rows:
        flag = "allowed" if f.allowed else "FINDING"
        print(f"{f.check:9s} {f.kind:{wk}s} {f.family:{wf}s} {f.item[:60]:{wi}s} {flag:7s} {f.detail}" + (f"  [{f.where}]" if f.where else ""))
    by = defaultdict(int)
    for f in open_:
        by[f.check] += 1
    summary = ", ".join(f"{k} {v}" for k, v in sorted(by.items())) or "none"
    print(f"[coverage] {n_fam} families, {renders} renders, {len(findings)} rows, {len(findings) - len(open_)} allowed, "
          f"{len(open_)} findings ({summary}) in {time.time() - t0:.0f}s")
    if a.json:
        Path(a.json).write_text(json.dumps([f.row() for f in findings], indent=1))
    return 1 if open_ else 0


if __name__ == "__main__":
    sys.exit(main())
