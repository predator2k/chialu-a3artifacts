"""The family RTL library: the microarchitecture families of chiALU as
parametric SystemVerilog modules (adder.sv, shifter.sv,
comparator.sv, logic.sv), the prefix graphs prefix.py emits per instance, and
the registry that maps a declared family with its pins to a module and
its parameters. The seed's lane modules instantiate a library module
behind the ops of a structure whose declared family has one, so a
declaration is realized by construction; a family without a module
stays behavioral, for the coding agent to realize.

    python3 -m chialu.targets.rtl.families.selftest   # every module against its behavioral reference
    python3 -m chialu.targets.rtl.families.prefix --width 32 --graph harris:l1f1 --report
"""
from __future__ import annotations

import math
import re
import threading
from pathlib import Path
from typing import NamedTuple
from .module_library import ModuleLibrary, collect_modules, split_modules

HERE = Path(__file__).resolve().parent
SV_FILES = ("adder.sv", "shifter.sv", "comparator.sv", "logic.sv")


class Module(NamedTuple):
    """A library module realizing a family at a width: its name, its
    parameter overrides, for a module the library generates per instance
    (a prefix graph) its SystemVerilog text (None for the modules of the
    .sv files), and the control inputs the unit drives beside the
    operands as (port name, width) (the accuracy mode of a
    runtime-controlled approximate structure)."""
    name: str
    params: dict
    text: str | None = None
    ctrl: tuple = ()


def library_text() -> str:
    """Every SystemVerilog module of the .sv files."""
    return "\n".join((HERE / f).read_text() for f in SV_FILES)


_MODULE_TEXT: dict = ModuleLibrary()
_MODULE_LOCK = threading.Lock()


def _module_texts_of_files() -> dict:
    """{module name: text} of every module of the .sv files, parsed once
    (under a lock: the characterization threads share the table)."""
    with _MODULE_LOCK:
        if not _MODULE_TEXT:
            found = ModuleLibrary()
            for f in SV_FILES:
                text = (HERE / f).read_text()
                found.update(split_modules(text))
            _MODULE_TEXT.update(found)
    return _MODULE_TEXT


def module_text(name: str) -> str:
    """One module of the .sv files, with its header comment, for a seed
    that instantiates it."""
    return _module_texts_of_files()[name]


def module_texts(name: str, text: str | None = None) -> dict:
    """{module name: text} of a library module and the library modules
    it instantiates (transitively), the module itself first; a generated
    text holding several modules contributes each under its own name."""
    if text is None:
        out = ModuleLibrary({name: module_text(name)})
    else:
        parts = split_modules(text)
        if name not in parts:
            raise ValueError(f'generated RTL text does not define its requested module {name!r}')
        out = ModuleLibrary({name: parts.pop(name)})
        out.update(parts)
    todo = list(out)
    while todo:
        n = todo.pop()
        table = _module_texts_of_files()
        for dep in sorted(set(re.findall(r"\b(fam_\w+)\b", out[n]))):
            if dep != n and dep not in out and dep in table:
                out[dep] = table[dep]
                todo.append(dep)
    return out


def library_closure(text: str) -> str:
    """The texts of the .sv-file modules a text references (`fam_*` names),
    transitively, in dependency order: what a bench or a wrapper needs
    beside the text itself, instead of the whole library."""
    table = _module_texts_of_files()
    supplied = set(split_modules(text))
    out: dict = ModuleLibrary()
    todo = sorted(set(re.findall(r"\b(fam_\w+)\b", text)))
    while todo:
        n = todo.pop()
        if n in out or n not in table or n in supplied:
            continue
        out[n] = table[n]
        todo += sorted(set(re.findall(r"\b(fam_\w+)\b", table[n])))
    return "\n".join(out[n] for n in sorted(out))


def has_module(kind: str, family: str) -> bool:
    """Whether the library realizes a family of a structure kind (a
    comparator family may be an adder family: the subtractor). False for
    every family while the library's realization is switched off."""
    if not LIBRARY_REALIZATION:
        return False
    w = 16
    # the decimal families of a BCD mode's adder, multiplier and divider slots (families/decimal.py)
    from chialu.targets.rtl.families.decimal import DECIMAL_FAMILIES
    if family in DECIMAL_FAMILIES.get(kind, ()):
        return True
    if kind == "adder":
        return adder_module(family, {}, w) is not None
    if kind == "shifter":
        return shifter_module(family, {}, w) is not None
    if kind == "comparator":
        return comparator_module(family, {}, w, True) is not None
    if kind == "bitcount":
        return any(f(family, {}, w) is not None for f in (popcount_module, lzc_module, tzc_module))
    if kind == "lzc":
        return lzc_module(family, {}, w) is not None
    if kind == "incrementer":
        return incrementer_module(family, {}, w) is not None
    if kind == "multiplier":
        # twin_precision_subword is realized at the unit level (one gated matrix over the lane packings)
        return family in MUL_FAMILIES or family == "twin_precision_subword"
    if kind in ("fp_adder",):
        return family in ("single_path", "two_path", "delay_optimized_unified", "low_power_gated")
    if kind == "fp_fma":
        # separate_multiplier_and_adder is realized by the fp_adder's and the fp_multiplier's own modules
        from chialu.targets.rtl.families.fp import FMA_FAMILIES
        return family in FMA_FAMILIES or family == "separate_multiplier_and_adder"
    if kind == "fp_multiplier":
        return family in ("sig_mul_then_round", "round_fused_in_reduction")
    if kind == "fp_comparator":
        return family in ("integer_compare_on_bits", "dedicated_magnitude_comparator")
    if kind == "rounder":
        return family in ("dedicated_per_op", "shared_per_lane", "shared_across_formats")
    if kind == "unpacker":
        return family in ("per_unit_unpack", "shared_per_lane", "shared_across_formats")
    if kind == "converter":
        return family in ("shift_round_convert",)
    if kind == "divider":
        from chialu.targets.rtl.families.div import DIV_FAMILIES
        return family in DIV_FAMILIES or family in ("approximate_recurrence", "approximate_functional")
    if kind == "logic":
        return family in ("lane_replicated_gates", "wide_gate_row", "alu_pg_fused")
    if kind == "subword":
        return family in ("partitioned_carry_chain", "replicated_lanes")
    if kind == "fp_divider":
        return family in ("sig_div_then_round", "sig_sqrt_then_round")
    # the decimal, posit, dot, SFU and redundant-representation families: each generator module
    # exports {kind: families} of what it realizes (a kind is a structure kind, the posit unit,
    # `core` for the dot accumulator's and the SFU's core-level family, `representation` and
    # `channels` for the redundant and residue cores)
    import importlib
    for modname, attr in (("decimal", "DECIMAL_FAMILIES"), ("posit", "POSIT_FAMILIES"), ("dot", "DOT_FAMILIES"),
                          ("sfu", "SFU_FAMILIES"), ("redundant", "REDUNDANT_FAMILIES")):
        try:
            mod = importlib.import_module(f"chialu.targets.rtl.families.{modname}")
        except ImportError:
            continue
        if family in (getattr(mod, attr, None) or {}).get(kind, ()):
            return True
    return False


def _checker_schema(kind: str, family: str):
    """The compiled schema of a checker family or of a checker comparator
    family (chialu.spaces.checker_spaces), or None where the space
    declares no family of that name. `chialu.variant_contracts.
    family_schemas` covers the structure kinds of a unit alone, so the
    two checker kinds are compiled here."""
    from chialu.spaces.checker_spaces import checker_space, two_rail_space
    from chialu.variants import compile_family
    space = two_rail_space() if kind == "checker_comparator" else checker_space()
    for declared in space.families:
        if declared.name == family:
            return compile_family(declared)
    return None


def validate_pins(kind: str, family: str, pins) -> None:
    """Raise where `pins` holds a key the declared family of `kind` does
    not declare, or a value outside a declared domain.

    * A key that begins with `_` is a generator control rather than a
      declared pin, so it is not validated.
    * A `family` key names the family itself, which every caller passes
      as its own argument, so it is not validated.
    * `kind` is a structure kind of `chialu.variant_contracts.
      family_schemas`, or `checker` or `checker_comparator`.
    * A pair of `kind` and `family` that no space declares carries no
      domain to check against, so it passes. A factory is also used as a
      probe of what it serves, and it answers None for a family of
      another kind, so a missing schema is not itself an error.

    The ADIR path validates a declaration through
    `chialu.variant_contracts.validate_partial` before a factory sees it.
    The checker rule table, the sharing plans, the coverage sweep and the
    selftests call a factory directly, so the factory validates the pins
    it is given. Without the check a misspelled key is dropped and an
    out-of-domain value falls back to the default, and the module renders
    the default in silence."""
    from chialu.variant_contracts import family_schemas, validate_partial
    supplied = {key: value for key, value in (pins or {}).items()
                if not str(key).startswith("_") and key != "family"}
    if not supplied:
        return
    if kind in ("checker", "checker_comparator"):
        schemas = tuple(s for s in (_checker_schema(kind, str(family)),) if s is not None)
    else:
        schemas = family_schemas(kind, str(family))
    failures = []
    for schema in schemas:
        try:
            validate_partial(schema, supplied)
            return
        except ValueError as error:
            failures.append(str(error))
    if failures:
        raise ValueError("; ".join(dict.fromkeys(failures)))


def _approx_ctrl(family: str, amodes: int) -> tuple:
    """The control inputs a runtime-controlled approximate module takes:
    the accuracy-mode port, for the families whose card offers a runtime
    quality control (chialu.targets.rtl.families.approx.RUNTIME_FAMILIES)."""
    from chialu.targets.rtl.families.approx import RUNTIME_FAMILIES
    if not amodes or family not in RUNTIME_FAMILIES:
        return ()
    return (("amode", max(1, (amodes - 1).bit_length())),)


def _int_pin(pins: dict, name: str, default, admitted=None):
    v = pins.get(name, default)
    try:
        v = int(v)
    except (TypeError, ValueError):
        return default
    if admitted is not None and v not in admitted:
        return default
    return v


PREFIX_FAMILIES = ("parallel_prefix", "ling_prefix", "compound_flagged_prefix", "prefix_synthesis_nonuniform_arrival")


ARRIVAL_PROFILES = ("uniform", "multiplier_vee", "lsb_late", "msb_late")


def arrival_profile(name: str, width: int) -> list[int]:
    """Per-bit arrival times in levels for the named profile of the
    prefix_synthesis_nonuniform_arrival family: uniform (all 0), the
    multiplier's final adder (the middle columns last, the peak L =
    log2 width), lsb_late / msb_late (a ramp of L over the word)."""
    L = max(1, (width - 1).bit_length())
    if name == "multiplier_vee":
        mid = width / 2
        return [max(0, round(L * (1 - abs(i - mid) / mid))) for i in range(width)]
    if name == "lsb_late":
        return [round(L * (width - 1 - i) / max(1, width - 1)) for i in range(width)]
    if name == "msb_late":
        return [round(L * i / max(1, width - 1)) for i in range(width)]
    return [0] * width


def prefix_spec(family: str, pins: dict, width: int) -> str:
    """The prefix graph spec (families/prefix.py's build()) of a prefix
    family's pins: a named topology, or `harris` read from the
    log2_sparsity (l) and fanout_cap (2^f + 1) choices, with the wire
    tracks following; prefix_synthesis_nonuniform_arrival builds the
    arrival-driven graph of its arrival_profile (a named profile or a
    comma list of per-bit times, bit 0 first). `validate_pins` raises on
    a key the family does not declare and on a value outside a declared
    domain, so a misspelled topology key no longer selects the default
    graph in silence."""
    validate_pins("adder", family, pins)
    if family == "prefix_synthesis_nonuniform_arrival":
        topo = "arrival"
    elif family == "sparse_prefix_hybrid":
        topo = str(pins.get("tree_topology", "sklansky"))
    else:
        topo = str(pins.get("topology", "sklansky" if family == "parallel_prefix" else "kogge_stone"))
    if family == "prefix_synthesis_nonuniform_arrival":
        arrival = str(pins.get("arrival_profile", "uniform"))
        if arrival in ARRIVAL_PROFILES:
            vals = arrival_profile(arrival, width)
        else:
            vals = [int(x) for x in arrival.replace(";", ",").split(",")]
            vals = (vals + [vals[-1]] * width)[:width]
        return "arrival:" + ",".join(str(v) for v in vals)
    if topo == "harris":
        l = _int_pin(pins, "log2_sparsity", 0)
        fanout = _int_pin(pins, "fanout_cap", 2)
        f = max(0, int(math.log2(max(1, fanout - 1))))
        return f"harris:l{l}f{f}"
    return topo


def prefix_module(family: str, pins: dict, width: int) -> Module | None:
    """The prefix adder of a family: the graph of its topology at its
    valency (parallel_prefix), the Ling pre-processing over blocks of
    pseudo_carry_group bits with its sum recovery (ling_prefix), the
    flagged outputs, implementation and late carry-in
    (compound_flagged_prefix), the arrival-driven graph."""
    from chialu.targets.rtl.families import prefix
    spec = prefix_spec(family, pins, width)
    kw = {}
    if family == "parallel_prefix":
        kw["valency"] = _int_pin(pins, "valency", 2, (2, 3, 4))
    if family == "ling_prefix":
        kw.update(ling=True, ling_group=_int_pin(pins, "pseudo_carry_group", 1, (1, 2, 3, 4)),
                  sum_recovery=str(pins.get("sum_recovery", "late_select_mux")))
    if family == "compound_flagged_prefix":
        kw.update(flagged=True, flag_outputs=str(pins.get("outputs", "sum_sum1")),
                  flag_impl=str(pins.get("implementation", "dual_carry_tree")),
                  late_cin=pins.get("late_carry_in") in (True, "True", 1))
    try:
        name, text, _ = prefix.adder_sv(width, spec, **kw)
    except ValueError:
        return None
    return Module(name, {}, text)


def adder_module(family: str, pins: dict, width: int) -> Module | None:
    """The Module realizing an adder family at a width, or None when the
    library has no module for it (the family stays behavioral)."""
    pins = pins or {}
    from chialu.targets.rtl.families.fidelity import effective
    if family in PREFIX_FAMILIES:
        return prefix_module(family, pins, width)
    if family == "ripple_carry":
        form = {"generate_propagate": 0, "two_half_adders_or": 1, "xor_majority": 2, "half_sum_mux_carry": 3}.get(
            str(pins.get("full_adder_logic", "generate_propagate")), 0)
        chunk = _int_pin(pins, "chunk_width_bits", 1)
        chunk = effective(pins, "chunk_width_bits", max(1, min(chunk, width)), "full ripple chunk width", {"width": width})
        return Module("fam_adder_ripple_carry", {"W": width, "CHUNK": chunk, "FORM": form})
    if family == "fpga_carry_chain":
        if pins.get("prefix_over_chain") in (True, "True", 1):
            from chialu.targets.rtl.families import adder_ext
            try:
                name, text = adder_ext.adder_ext_sv(width, family, pins)
            except ValueError:
                return None
            return Module(name, {}, text)
        seg = _int_pin(pins, "chain_segment_length", 8)
        seg = effective(pins, "chain_segment_length", max(1, min(seg, width)), "full carry-chain segment", {"width": width})
        return Module("fam_adder_ripple_carry", {"W": width, "CHUNK": seg, "FORM": 0})
    if family == "manchester_carry_chain":
        seg = effective(pins, "chain_segment_length", min(width, _int_pin(pins, "chain_segment_length", 4)), "full Manchester segment", {"width": width})
        return Module("fam_adder_manchester_carry_chain", {"W": width, "SEG": seg,
                                                           "VARSKIP": 1 if pins.get("variable_skip") in (True, "True", 1) else 0})
    if family == "carry_lookahead":
        group = effective(pins, "group_size", min(width, _int_pin(pins, "group_size", 4)), "full lookahead group", {"width": width})
        if "intergroup_carry" in pins and width <= group:
            raise ValueError("intergroup_carry requires at least two actual lookahead groups")
        levels = _int_pin(pins, "levels", 1, (1, 2, 3, 4))
        groups, actual = (width + group - 1) // group, 1
        while actual < levels and groups > group:
            groups = (groups + group - 1) // group
            actual += 1
        effective(pins, "levels", actual, "instantiated recursive lookahead levels", {"width": width, "group_size": group})
        return Module("fam_adder_carry_lookahead", {"W": width, "G": group,
                                             "INTER": {"ripple": 0, "lookahead": 1, "select": 2}.get(str(pins.get("intergroup_carry", "ripple")), 0),
                                             "LEVELS": levels})
    if family == "conditional_sum":
        base = effective(pins, "base_block_width", min(width, _int_pin(pins, "base_block_width", 1, (1, 2, 3, 4))), "full conditional-sum base block", {"width": width})
        radix = _int_pin(pins, "selection_radix", 2, (2, 4))
        if "selection_radix" in pins and (width + base - 1) // base < radix:
            raise ValueError("selection_radix requires that many real base blocks before padding")
        return Module("fam_adder_conditional_sum", {"W": width, "BASE": base,
                                             "RADIX": radix})
    if family in ("segmented_carry_speculative", "lower_part_approximate", "accuracy_configurable"):
        from chialu.targets.rtl.families import approx
        amodes = _int_pin(pins, "_accuracy_modes", 0)
        try:
            name, text = approx.approx_sv("adder", family, pins, width, amodes=amodes)
        except ValueError:
            return None
        return Module(name, {}, text, _approx_ctrl(family, amodes))
    if family in ("end_around_carry", "approximate_truncated", "carry_skip", "carry_select", "carry_increment",
                  "sparse_prefix_hybrid"):
        # the generated adders: the end-around-carry and truncated families, and the block-composed families
        # around the library adders and incrementers their slots name
        from chialu.targets.rtl.families import adder_ext
        try:
            name, text = adder_ext.adder_ext_sv(width, family, pins)
        except ValueError:
            return None
        return Module(name, {}, text)
    return None


MUL_FAMILIES = ("direct_pp_parallel", "booth_recoded_parallel", "carry_save_array", "recursive_karatsuba",
                "behavioral_star", "squarer", "truncated_fixed_width", "logarithmic_mitchell", "approximate_compressor",
                "segmented_grid", "redundant_binary_multiplier",
                # the approximate space's multipliers (truncated_fixed_width is in both; the approximate one carries
                # the correction ladder and is reached through its own pins)
                "dynamic_segment", "operand_rounding", "logarithmic", "pp_perforation", "approximate_compressor_tree", "approximate_booth")
APPROX_MUL = ("dynamic_segment", "operand_rounding", "logarithmic", "pp_perforation", "approximate_compressor_tree", "approximate_booth")


def mul_module(family: str, pins: dict, width: int, signed: bool) -> Module | None:
    """The generated multiplier of a family at a width and signedness
    (families/mul.py for the partial-product trees, families/mul_ext.py
    for the rest), or None; the sequential families have none."""
    if family == "twin_precision_subword":
        # A component uses the matrix's full-width packing. The unit-level
        # generator still exposes its selector when it serves several modes.
        matrix = twin_precision_module([width], [signed], pins, width)
        if matrix is None:
            return None
        name = matrix.name + "_binary"
        text = (f"module {name}(input [{width-1}:0] a,b, output [{2*width-1}:0] p);\n"
                f"{matrix.name} matrix(.a(a), .b(b), .sel(1'b0), .p(p));\nendmodule\n" + matrix.text)
        return Module(name, {}, text)
    if family not in MUL_FAMILIES:
        return None
    try:
        if family in ("direct_pp_parallel", "booth_recoded_parallel", "carry_save_array", "recursive_karatsuba"):
            from chialu.targets.rtl.families import mul
            name, text, _ = mul.mul_sv(width, signed, family, pins or {})
        elif family in APPROX_MUL or (family == "truncated_fixed_width" and "correction" in (pins or {})):
            from chialu.targets.rtl.families import approx
            name, text = approx.approx_sv("multiplier", family, pins or {}, width, signed,
                                          amodes=_int_pin(pins or {}, "_accuracy_modes", 0))
        else:
            from chialu.targets.rtl.families import mul_ext
            name, text, _ = mul_ext.mul_ext_sv(width, signed, family, pins or {})
    except ValueError:
        return None
    return Module(name, {}, text, _approx_ctrl(family, _int_pin(pins or {}, "_accuracy_modes", 0)))


def div_module(family: str, pins: dict, N: int, D: int, Q: int, S: int = 0, normalized: bool = False,
               name: str | None = None) -> Module | None:
    """The generated divider of a family (families/div.py): q = floor(a 2^S / b)
    and r for an N-bit dividend, a D-bit divisor and a Q-bit quotient;
    None for a family the library lacks or a sequential one."""
    from chialu.targets.rtl.families import div
    if family in ("approximate_recurrence", "approximate_functional"):
        from chialu.targets.rtl.families import approx
        try:
            n, t = approx.approx_sv("divider", family, pins or {}, D, name=name, N=N + S, D=D, Q=Q)
        except ValueError:
            return None
        return Module(n, {}, t)
    if family not in div.DIV_FAMILIES:
        return None
    try:
        n, t = div.div_sv(N, D, Q, family, pins or {}, name=name, S=S, normalized=normalized)
    except ValueError:
        return None
    return Module(n, {}, t)


def sqrt_module(family: str, pins: dict, Q: int, normalized: bool = False, name: str | None = None) -> Module | None:
    """The generated square root of a divider family (families/div.py):
    a 2Q-bit radicand to a Q-bit root and the remainder."""
    from chialu.targets.rtl.families import div
    if family not in div.DIV_FAMILIES:
        return None
    try:
        n, t = div.sqrt_sv(Q, family, pins or {}, name=name, normalized=normalized)
    except ValueError:
        return None
    return Module(n, {}, t)


FP_KINDS = ("fp_adder", "fp_multiplier", "fp_comparator", "fp_divider", "fp_sqrt", "rounder", "unpacker", "converter")


def fp_shared_module(kind: str, family: str, pins: dict, formats, geom, mode_ids, tokens=None, name=None,
                     normalized_input: bool = False):
    from chialu.targets.rtl.families.fp_shared import shared_sv
    from chialu.targets.rtl.families.fidelity import shared
    module_name, text, witnesses = shared_sv(kind, formats, geom, family, pins, tokens, mode_ids, name,
                                             normalized_input=normalized_input)
    shared(getattr(pins, "owner", kind), family, witnesses, [f"mode{mi}" for mi in mode_ids])
    return Module(module_name, {}, text)


def fp_module(kind: str, family: str, pins: dict, geom, fmt=None, M: int | None = None, bias: int | None = None,
              tokens: dict | None = None, name: str | None = None, scale_feedback: bool = False, scale_format=None,
              external_sig_adder: bool = False, normalized_input: bool = False) -> Module | None:
    """The generated float module of a kind's family for an engine
    geometry (families/fp.py): the unpacker and the rounder take the
    format, the multiplier the target precision under
    round_fused_in_reduction, the fp_fma kind the fused multiply-add
    serving fadd, fsub and fmul, the rounder `normalized_input` when
    every producer of the mode normalizes; None for a family the library
    lacks."""
    from chialu.targets.rtl.families import fp
    explicit_owner = getattr(pins, "owner", None)
    pins = pins or {}
    try:
        if kind == "unpacker":
            n, t = fp.unpack_sv(fmt, geom, family, pins, name=name)
        elif kind == "fp_adder":
            # external_sig_adder: the significand adder as ports (a CPA shared with the integer adders); a switch of
            # the unit rather than a declared pin, so the selection keeps the pins it asked for
            n, t = fp.add_sv(geom, family, pins, name=name, external=external_sig_adder)
        elif kind == "fp_fma":
            n, t = fp.fma_sv(geom, family, pins, name=name, fmt=fmt)
        elif kind == "fp_multiplier":
            n, t = fp.mul_sv(geom, family, pins, M=M, bias=bias, name=name, scale_feedback=scale_feedback,
                            scale_format=scale_format, target_format=fmt, tokens=tokens)
        elif kind == "fp_comparator":
            n, t = fp.cmp_sv(geom, family, pins, name=name)
        elif kind == "fp_divider":
            n, t = fp.div_sv(geom, family, pins, name=name)
        elif kind == "fp_sqrt":
            n, t = fp.sqrt_sv(geom, family, pins, name=name)
        elif kind in ("rounder", "converter"):
            from chialu.verify.formats import IntFormat, FixedFormat, BCDFormat
            if isinstance(fmt, (IntFormat, FixedFormat, BCDFormat)):
                n, t = fp.round_int_sv(fmt, geom, family, pins, tokens or {}, name=name)
            else:
                n, t = fp.round_sv(fmt, geom, family, pins, tokens or {}, name=name, normalized_input=normalized_input)
        else:
            return None
    except ValueError:
        if explicit_owner is not None:
            raise
        return None
    return Module(n, {}, t)


def sfu_module(fn: str, fmt, geom, family: str, pins: dict | None = None, name: str | None = None) -> Module | None:
    """The generated special-function module of a family for one function
    on one format at an engine geometry (families/sfu.py); None when the
    family has no engine for the function."""
    from chialu.targets.rtl.families import sfu
    explicit_owner = getattr(pins, "owner", None)
    if family not in sfu.SFU_FAMILIES["core"]:
        return None
    try:
        n, t, _net = sfu.sfu_sv(fn, fmt, geom, family, pins or {}, name=name)
    except (ValueError, KeyError, AssertionError):
        if explicit_owner is not None:
            raise
        return None
    return Module(n, {}, t)


def sfu_vector_module(fn: str, fmt, geom, count: int, family: str, pins: dict | None = None, name: str | None = None) -> Module | None:
    """The generated module of the softmax_layernorm family for a vector
    function over `count` lanes (families/sfu.py); None when the family
    or its pins do not serve the function."""
    from chialu.targets.rtl.families import sfu
    explicit_owner = getattr(pins, "owner", None)
    try:
        n, t, _net = sfu.vector_sv(fn, fmt, geom, count, family, pins or {}, name=name)
    except (ValueError, KeyError, AssertionError):
        if explicit_owner is not None:
            raise
        return None
    return Module(n, {}, t)


def posit_module(kind: str, family: str, pins: dict, fmt, geom, tokens: dict | None = None, target=None,
                 name: str | None = None) -> Module | None:
    """The generated posit unit module of a kind for a posit format and an
    engine geometry (families/posit.py): decode (pattern -> V), encode
    (X -> pattern), unit (both, for the characterization), plam (the
    logarithm-approximate multiplier on X), cvt (the boundary converter of
    a decoded `fmt` value into `target`); None for a family the library
    lacks."""
    from chialu.targets.rtl.families import posit
    pins = pins or {}
    try:
        if kind == "decode":
            n, t = posit.decode_sv(fmt, geom, family, pins, name=name)
        elif kind == "encode":
            n, t = posit.encode_sv(fmt, geom, family, pins, tokens, name=name)
        elif kind == "unit":
            n, t = posit.unit_sv(fmt, geom, family, pins, tokens, name=name)
        elif kind == "plam":
            n, t = posit.plam_sv(geom, name=name)
        elif kind == "cvt":
            n, t = posit.cvt_sv(fmt, target, geom, family, pins, tokens, name=name)
        else:
            return None
    except ValueError:
        return None
    return Module(n, {}, t)


RADIX_LOG2 = {"2": 1, "4": 2, "8": 3, "full_width_single_stage": 0}


def shifter_module(family: str, pins: dict, width: int, sticky: bool | None = None) -> Module | None:
    """The shifter of a family at a width (shifter.sv; every module has the
    sticky output): the barrel's stage radix, select encoding, direction
    handling and stage order, the funnel's window radix and amount
    preprocessing, the masked family's mask generator, merge style and
    rotator pins, the butterfly's network. `sticky` forces the sticky
    collection (an alignment shifter); None leaves it to sticky_collect."""
    pins = pins or {}
    st = 1 if sticky else (0 if sticky is False else (1 if pins.get("sticky_collect") in (True, "True", 1) else 0))
    if family == "barrel_mux_tree":
        return Module("fam_shift_barrel_mux_tree", {
            "W": width, "RADIX_LOG2": RADIX_LOG2.get(str(pins.get("stage_radix", 2)), 1),
            "ONE_HOT": 1 if pins.get("select_encoding") == "one_hot_decoded" else 0,
            "DIR": {"mirrored_datapath": 0, "data_reversal": 1, "amount_negation": 2}.get(str(pins.get("direction_handling", "data_reversal")), 1),
            "ORDER": 1 if pins.get("stage_order") == "large_shift_first" else 0, "STICKY": st})
    if family == "funnel":
        return Module("fam_shift_funnel", {
            "W": width, "RADIX_LOG2": RADIX_LOG2.get(str(pins.get("window_mux_radix", 2)), 1),
            "AMT_PRE": 0 if pins.get("amount_preprocess") == "ones_complement_for_right" else 1, "STICKY": st})
    if family == "masked_merged":
        return Module("fam_shift_masked_merged", {
            "W": width, "MASKGEN": {"thermometer_decode": 0, "two_thermometer_and": 1, "lut": 2}.get(str(pins.get("mask_generator", "thermometer_decode")), 0),
            "MERGE": 1 if pins.get("merge_style") == "per_bit_mux" else 0,
            "R_RADIX_LOG2": RADIX_LOG2.get(str(pins.get("rotator.stage_radix", 2)), 1),
            "R_ONE_HOT": 1 if pins.get("rotator.select_encoding") == "one_hot_decoded" else 0,
            "R_ORDER": 1 if pins.get("rotator.stage_order") == "large_shift_first" else 0, "STICKY": st})
    if family == "butterfly_network":
        if width & (width - 1):
            return None                           # the switch network needs a power-of-two width
        return Module("fam_shift_butterfly_network", {"W": width, "NETWORK": 1 if pins.get("network") == "butterfly" else 0,
                                                      "STICKY": st})
    return None


def comparator_module(family: str, pins: dict, width: int, signed: bool) -> Module | None:
    """The comparator of a family (lt, eq of a and b): prefix_comparator in
    comparator.sv (the msb-first scan or the tree over groups of `radix`
    bits), subtractor_comparator generated around its `subtractor` slot's
    adder (families/comparator.py)."""
    pins = pins or {}
    if family == "prefix_comparator":
        st = {"msb_first_prefix": 0, "tree_reduction": 1}.get(str(pins.get("structure", "msb_first_prefix")))
        if st is None:
            return None
        return Module("fam_cmp_prefix_comparator", {"W": width, "SIGNED": 1 if signed else 0, "STRUCTURE": st,
                                                   "RADIX": _int_pin(pins, "radix", 2, (2, 3, 4))})
    if family == "subtractor_comparator":
        from chialu.targets.rtl.families import comparator
        try:
            n, t = comparator.subtractor_comparator_sv(width, pins, signed)
        except ValueError:
            return None
        return Module(n, {}, t)
    return None


def popcount_module(family: str, pins: dict, width: int) -> Module | None:
    """The population counter of a bit-count family (families/count.py)."""
    from chialu.targets.rtl.families import count
    if family not in count.POPCOUNT_FAMILIES:
        return None
    try:
        n, t = count.popcount_sv(width, pins or {})
    except ValueError:
        return None
    return Module(n, {}, t)


def lzc_module(family: str, pins: dict, width: int) -> Module | None:
    """The leading-zero counter of a family (families/count.py: the cell
    tree, the prefix form, the priority encoder)."""
    from chialu.targets.rtl.families import count
    if family not in count.LZC_FAMILIES:
        return None
    try:
        n, t = count.count_sv(family, width, pins or {})
    except ValueError:
        return None
    return Module(n, {}, t)


def logic_module(family: str, pins: dict, width: int) -> Module | None:
    """The bitwise gate row of the logic space (and, or, xor, not by an op
    code): lane_replicated_gates is one row per lane and mode (the
    generated lane module's shape), wide_gate_row one full-width row in
    the unit serving every lane packing (the seed's unit module
    instantiates it once; not_via_xor folds the not into the xor row),
    alu_pg_fused the and / xor / or taken as the adder's generate,
    propagate and their or in the lane module."""
    pins = pins or {}
    if family in ("lane_replicated_gates", "wide_gate_row"):
        nvx = 1 if family == "wide_gate_row" and pins.get("not_via_xor") in (True, "True", 1) else 0
        return Module("fam_logic_gate_row", {"W": width, "NOT_VIA_XOR": nvx})
    return None


def dot_module(dg, family: str, pins: dict, block: bool = False, name: str | None = None) -> Module | None:
    """The generated dot-accumulate module of a core family for a mode
    geometry (families/dot.py: a DotGeom from dot.geom_of), or None when
    the family or a pin has no combinational module for the mode."""
    from chialu.targets.rtl.families import dot
    try:
        n, t, _info = dot.dot_sv(dg, family, pins or {}, name=name, block=block)
    except ValueError:
        return None
    return Module(n, {}, t)


def twin_precision_module(lane_widths: list, signed: list, pins: dict, W: int, name: str | None = None) -> Module | None:
    """The twin-precision multiplier of a unit over its served modes (families/subword.py)."""
    from chialu.targets.rtl.families import subword
    try:
        n, t = subword.twin_precision_sv(W, lane_widths, signed, pins or {}, name=name)
    except ValueError:
        return None
    return Module(n, {}, t)


def partitioned_adder_module(lane_widths: list, pins: dict, W: int, name: str | None = None, segment=None) -> Module | None:
    """The lane-partitioned adder of a unit over its served modes
    (families/subword.py); `segment` is the (family, pins) of the served
    lanes' declared adder, which the segments are built from."""
    from chialu.targets.rtl.families import subword
    try:
        n, t = subword.partitioned_adder_sv(W, lane_widths, pins or {}, name=name, segment=segment)
    except ValueError:
        return None
    return Module(n, {}, t)


def bcd_adder_module(family: str, pins: dict, digits: int, name: str | None = None) -> Module | None:
    """The generated decimal adder of a BCD mode's adder family at a digit
    count (families/decimal.py: a, b, sub, cin -> s, cout), or None."""
    from chialu.targets.rtl.families import decimal
    try:
        n, t = decimal.bcd_adder_sv(digits, family, pins or {}, name=name)
    except ValueError:
        return None
    return Module(n, {}, t)


def bcd_mul_module(family: str, pins: dict, digits: int, name: str | None = None) -> Module | None:
    """The generated decimal multiplier (a, b -> p of 2 * digits) of a BCD
    mode's multiplier family, or None (the iterative family is sequential)."""
    from chialu.targets.rtl.families import decimal
    try:
        n, t = decimal.bcd_mul_sv(digits, family, pins or {}, name=name)
    except ValueError:
        return None
    return Module(n, {}, t)


def bcd_div_module(family: str, pins: dict, digits: int, name: str | None = None) -> Module | None:
    """The generated decimal divider (a, b -> q, r) of a BCD mode's divider
    family, or None."""
    from chialu.targets.rtl.families import decimal
    try:
        n, t = decimal.bcd_div_sv(digits, family, pins or {}, name=name)
    except ValueError:
        return None
    return Module(n, {}, t)


def incrementer_module(family: str, pins: dict, width: int) -> Module | None:
    """The incrementer of the incrementer_space (s = a + cin)."""
    pins = pins or {}
    if family == "prefix_and_incrementer":
        st = {"ripple_and_chain": 0, "prefix_and_tree": 1, "select_blocks": 2}.get(str(pins.get("structure", "prefix_and_tree")), 1)
        topo = {"sklansky": 0, "brent_kung": 1, "kogge_stone": 2}.get(str(pins.get("topology", "sklansky")), 0)
        return Module("fam_incr_prefix_and", {"W": width, "STRUCTURE": st, "B": 4, "TOPO": topo})
    return None


def tzc_module(family: str, pins: dict, width: int) -> Module | None:
    """The trailing-zero counter of a family (families/count.py)."""
    from chialu.targets.rtl.families import count
    if family not in count.TZC_FAMILIES:
        return None
    try:
        n, t = count.trailing_zero_sv(width, pins or {})
    except ValueError:
        return None
    return Module(n, {}, t)


from chialu.targets.rtl.families.selection import install as _install_selection_trace
_install_selection_trace(globals())


# ---- the realization switch -------------------------------------------------
# The seed generator realizes a declared family from this library; with the switch off every
# factory answers None and `has_module` False, so every structure renders as the behavioral
# text it would have without a library module (the library ablation of the evaluation plan,
# `realization: behavioral` in a chialu.ALU run file). The switch is a process-wide flag set for
# the duration of one render through `library_realization`.
LIBRARY_REALIZATION = True

_FACTORIES = ("prefix_module", "adder_module", "mul_module", "div_module", "sqrt_module", "fp_shared_module",
              "fp_module", "sfu_module", "sfu_vector_module", "posit_module", "shifter_module", "comparator_module",
              "popcount_module", "lzc_module", "logic_module", "dot_module", "twin_precision_module",
              "partitioned_adder_module", "bcd_adder_module")


class library_realization:
    """`with library_realization(False): render` renders without the library."""

    def __init__(self, enabled: bool = True):
        self.enabled = bool(enabled)
        self.previous = True

    def __enter__(self):
        global LIBRARY_REALIZATION
        self.previous = LIBRARY_REALIZATION
        LIBRARY_REALIZATION = self.enabled
        return self

    def __exit__(self, *exc):
        global LIBRARY_REALIZATION
        LIBRARY_REALIZATION = self.previous
        return False


def _guarded(fn):
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not LIBRARY_REALIZATION:
            return None
        return fn(*args, **kwargs)
    return wrapper


def _argument(index: int, name: str):
    """Read one declared argument of a factory call, from the positional
    arguments or from the keywords."""
    def read(args, kwargs):
        return args[index] if len(args) > index else kwargs.get(name)
    return read


# The pins every factory validates: (kind, the family reader, the pins reader). A kind of None
# reads the kind from the call's own `kind` argument, and a family reader of None names the one
# family the factory serves.
_VALIDATED = {
    "prefix_module": ("adder", _argument(0, "family"), _argument(1, "pins")),
    "adder_module": ("adder", _argument(0, "family"), _argument(1, "pins")),
    "mul_module": ("multiplier", _argument(0, "family"), _argument(1, "pins")),
    "div_module": ("divider", _argument(0, "family"), _argument(1, "pins")),
    "sqrt_module": ("divider", _argument(0, "family"), _argument(1, "pins")),
    "shifter_module": ("shifter", _argument(0, "family"), _argument(1, "pins")),
    "comparator_module": ("comparator", _argument(0, "family"), _argument(1, "pins")),
    "popcount_module": ("bitcount", _argument(0, "family"), _argument(1, "pins")),
    "lzc_module": ("lzc", _argument(0, "family"), _argument(1, "pins")),
    "tzc_module": ("bitcount", _argument(0, "family"), _argument(1, "pins")),
    "incrementer_module": ("incrementer", _argument(0, "family"), _argument(1, "pins")),
    "logic_module": ("logic", _argument(0, "family"), _argument(1, "pins")),
    "fp_module": (None, _argument(1, "family"), _argument(2, "pins")),
    "fp_shared_module": (None, _argument(1, "family"), _argument(2, "pins")),
    "posit_module": ("posit_unit", _argument(1, "family"), _argument(2, "pins")),
    "sfu_module": ("sfu", _argument(3, "family"), _argument(4, "pins")),
    "sfu_vector_module": ("sfu", _argument(4, "family"), _argument(5, "pins")),
    "dot_module": ("dot", _argument(1, "family"), _argument(2, "pins")),
    "twin_precision_module": ("subword", None, _argument(2, "pins")),
    "partitioned_adder_module": ("subword", None, _argument(1, "pins")),
    "bcd_adder_module": ("bcd_adder", _argument(0, "family"), _argument(1, "pins")),
    "bcd_mul_module": ("bcd_multiplier", _argument(0, "family"), _argument(1, "pins")),
    "bcd_div_module": ("bcd_divider", _argument(0, "family"), _argument(1, "pins")),
}
# the one family a factory whose family reader is None serves
_SOLE_FAMILY = {"twin_precision_module": "twin_precision_subword",
                "partitioned_adder_module": "partitioned_carry_chain"}


def _validated(name, fn):
    import functools
    kind, read_family, read_pins = _VALIDATED[name]
    read_kind = _argument(0, "kind")

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        family = _SOLE_FAMILY[name] if read_family is None else read_family(args, kwargs)
        validate_pins(kind if kind is not None else read_kind(args, kwargs),
                      family, read_pins(args, kwargs))
        return fn(*args, **kwargs)
    return wrapper


for _name in set(_FACTORIES) | set(_VALIDATED):
    if _name not in globals():
        continue
    _fn = globals()[_name]
    if _name in _VALIDATED:
        _fn = _validated(_name, _fn)
    if _name in _FACTORIES:
        _fn = _guarded(_fn)
    globals()[_name] = _fn
del _name
