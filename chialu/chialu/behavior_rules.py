"""The behavior rules: which families and members compute the unit's
contract, and under which bound options (docs/behav_checker_plan.md).

Two mechanisms read this one registry:

* `plan_behav_checker`: `prune_slot` narrows the compiled variables of a
  slot at elaboration, so a family or a member whose realization would
  change the packed result, the flags or the specials the reference
  defines under the bound options never reaches the menu; a removed
  member keeps its reason in the domain (`adir.domains.Enum.excluded`),
  which ADIR reports beside `outside` when a run file, a plan or a
  declaration names it.
* `yaml_behav_checker`: `check_options` evaluates the rules over the unit
  options alone (`OPTION_RULES`) at load, before any artifact renders;
  the fixed core bindings, the plans' pins and the agents' VAR lines are
  checked against the pruned domains by ADIR and `chialu.plans`.

A family's classification is on the `Family` (`behavior`, `requires`,
`evidence`; adir.spaces). A member-level rule is a `Rule` here, keyed by
an fnmatch pattern over `family|choice|member` (archdocs' allowlist
style) and a slot pattern. Every condition is a named predicate of the
table below, so the report and the prompt quote its meaning. A predicate
over the bound contract is evaluated at elaboration; a predicate with a
`sibling` (another variable's value, which the search may decide) is
lowered into ADIR's member condition (`Variable.member_when`,
docs/adir_member_when_plan.md), and a `nested` rule into the choice's
`when` on a sibling choice.

    python3 -m chialu.behavior_rules lint        # 0 unregistered, 0 stale
    python3 -m chialu.behavior_rules rules       # the rule table
    python3 -m chialu.behavior_rules table       # every family's classification
    python3 -m chialu.behavior_rules report <run file>   # what a run file's elaboration removed
    python3 -m chialu.behavior_rules defects <results_db.jsonl>   # conformance failures the rules admitted
"""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field, replace

from adir.domains import Bool, Enum, Range
from adir.errors import BindError

KINDS = ("behavior", "selector", "interface", "nested", "deferred")
# an unregistered family (no `behavior` on its Family) leaves the search space; the lint gate keeps the count at 0
EXCLUDE_UNREGISTERED = True

_MODE_INDEX = re.compile(r"^m(\d+)")


# ---- the bound contract a predicate reads -----------------------------------------------------------------

class Contract:
    """The normalized spec of a unit and, for a per-mode predicate, the
    mode index the variable's structure index names."""

    def __init__(self, spec: dict, mode=None):
        self.spec = spec
        self.unit = spec.get("unit", "alu")
        self.mode = mode
        self._modes = None
        self._legal = None
        self._dot_modes = None

    def at(self, index):
        """The contract at a structure index (`m1`, `m1.int8_twos_complement`)."""
        m = _MODE_INDEX.match(str(index)) if index is not None else None
        return Contract(self.spec, int(m.group(1))) if m else self

    # -- the ALU's modes and ops
    @property
    def modes(self) -> list:
        if self._modes is None:
            from chialu.verify.formats import parse_format
            self._modes = [(int(m["count"]), parse_format(str(m["format"]))) for m in self.spec.get("modes", [])] \
                if self.unit == "alu" else []
        return self._modes

    @property
    def legal(self) -> set:
        if self._legal is None:
            from chialu.verify.alu_ref import legal_pairs
            self._legal = legal_pairs(self.modes, list(self.spec.get("ops", [])),
                                      [m.get("ops") for m in self.spec.get("modes", [])]) if self.unit == "alu" else set()
        return self._legal

    def ops_of(self, mi: int) -> set:
        return {op for i, op in self.legal if i == mi}

    def float_modes(self) -> list:
        from chialu.verify.alu_ref import family_of
        return [mi for mi, (_, f) in enumerate(self.modes) if family_of(f) == "float"]

    def mode_indexes(self) -> list:
        """The modes a per-mode predicate ranges over: the named one, else every float mode."""
        return [self.mode] if self.mode is not None else self.float_modes()

    # -- the dot's modes
    @property
    def dot_modes(self) -> list:
        if self._dot_modes is None:
            from chialu.verify.dot_ref import parse_modes
            self._dot_modes = parse_modes(self.spec["modes"]) if self.unit == "vec_dot_acc" else []
        return self._dot_modes

    def ab_elems(self) -> list:
        from chialu.verify.formats import BlockFormat
        return [m["fab"].elem if isinstance(m["fab"], BlockFormat) else m["fab"] for m in self.dot_modes]

    def c_d_names(self) -> list:
        out = []
        for m in self.dot_modes:
            out.append(m["fd"].name)
            if self.spec.get("accumulate", True) and m.get("fc") is not None:
                out.append(m["fc"].name)
        return out

    # -- the options
    @property
    def rounding(self) -> list:
        r = self.spec.get("rounding", ["RNE"])
        return list(r) if isinstance(r, (list, tuple)) else [r]

    def flag(self, name: str) -> list:
        v = self.spec.get(name, [False])
        return list(v) if isinstance(v, (list, tuple)) else [v]

    def describe(self, *names) -> str:
        """The options a reason quotes, in the YAML's terms."""
        parts = []
        for n in names:
            if n == "modes":
                if self.unit == "alu":
                    parts.append("modes " + ", ".join(f"{i}: {c}x{f.name} {sorted(self.ops_of(i))}"
                                                      for i, (c, f) in enumerate(self.modes)))
                else:
                    parts.append("modes " + ", ".join(f"{m['elements']}x{m['fab'].name} -> {m['fd'].name}"
                                                      for m in self.dot_modes))
            elif n == "rounding":
                parts.append(f"rounding {self.rounding}")
            elif n in ("daz_in", "ftz_out"):
                parts.append(f"{n} {self.flag(n)}")
            else:
                parts.append(f"{n} {self.spec.get(n)!r}")
        return "; ".join(parts)


# ---- the predicate table ---------------------------------------------------------------------------------

@dataclass(frozen=True)
class Predicate:
    name: str
    meaning: str
    holds: object = None        # callable(Contract) -> bool; None: not evaluable over the contract
    quotes: tuple = ()          # the options a failing reason quotes
    per_mode: bool = False      # evaluated per structure index (the mode the index names)
    sibling: tuple = ()         # (path, values): the predicate holds while the sibling variable at `path` holds one
                                # of `values` (a tuple, or a callable returning one); lowered into ADIR's member
                                # condition. `path` is `<slot>.<choice>` relative to the unit (`fp_fma.family`), or a
                                # bare choice name of the same family (`string_form`)

    @property
    def evaluable(self) -> bool:
        """Whether the elaboration can act on the predicate: over the contract, or as a member condition."""
        return self.holds is not None or bool(self.sibling)

    def sibling_values(self) -> tuple:
        path, values = self.sibling
        return tuple(values() if callable(values) else values)


def _is_int(f) -> bool:
    from chialu.verify.formats import FixedFormat, IntFormat
    return isinstance(f, (IntFormat, FixedFormat))


def _binary_adder_mode(c: Contract) -> bool:
    from chialu.plans import _binary
    return any(_binary(f.name) for _, f in c.modes)


def _no_float_cvt_target(c: Contract) -> bool:
    from chialu.targets.rtl.engine import _core
    from chialu.verify.alu_ref import cvt_target
    from chialu.verify.formats import BlockFormat, FloatFormat, X87Format
    for op in c.spec.get("ops", []):
        t = cvt_target(op)
        if t is None or isinstance(t, BlockFormat):
            continue
        if isinstance(_core(t), (FloatFormat, X87Format)):
            return False
    return True


def _no_cvt_in_float_modes(c: Contract) -> bool:
    from chialu.verify.alu_ref import is_cvt
    return not any(is_cvt(op) for mi in c.float_modes() for op in c.ops_of(mi))


def _fused_op_in_mode(c: Contract, mi: int) -> bool:
    from chialu.verify.alu_ref import FUSED_OPS
    return bool(c.ops_of(mi) & set(FUSED_OPS))


def _fma_contract_or_no_fused_op(contract_value: str):
    """The mode's fused ops, if it has any, are under `fma_contract: <contract_value>`."""
    return lambda c: all(not _fused_op_in_mode(c, mi) or c.spec.get("fma_contract", "fused") == contract_value
                         for mi in c.mode_indexes())


def _significand_in_mode(c: Contract) -> bool:
    from chialu.verify.formats import FloatFormat
    return all(isinstance(c.modes[mi][1], FloatFormat) and not getattr(c.modes[mi][1], "exp_only", False)
               for mi in c.mode_indexes())


def _two_float_formats(c: Contract) -> bool:
    return len({c.modes[mi][1].name for mi in c.float_modes()}) >= 2


def _c_d(name):
    return lambda c: bool(c.dot_modes) and all(n == name for n in c.c_d_names())


def _ab(name):
    return lambda c: bool(c.dot_modes) and all(f.name == name for f in c.ab_elems())


def _fused_fma_families() -> tuple:
    """The fp_fma families that are one fused datapath: every family of
    the slot's space but `separate_multiplier_and_adder`, the criterion
    `alu_mode.tight_x` applies, so a fused family a later change adds is
    admitted without a registry edit."""
    from chialu.spaces.fp_spaces import fp_fma_space
    return tuple(f.name for f in fp_fma_space(11).families if f.name != "separate_multiplier_and_adder")


PREDICATES = {p.name: p for p in (
    Predicate("float_mode", "the unit has a mode whose format family is float",
              lambda c: bool(c.float_modes()), ("modes",)),
    Predicate("no_sr", "rounding does not provision SR", lambda c: "SR" not in c.rounding, ("rounding",)),
    Predicate("no_cvt_in_float_modes", "no float mode has a legal cvt(...) op", _no_cvt_in_float_modes, ("modes",)),
    Predicate("x_form_exact", "x_form is exact", lambda c: c.spec.get("x_form", "exact") == "exact", ("x_form",)),
    Predicate("fma_contract_fused_or_no_fused_op_in_mode",
              "the mode's legal ops hold no fused multiply-add op (fmadd, fmsub, fnmsub, fnmadd), or fma_contract is fused: "
              "one rounding of the exact product plus addend, which a fused fp_fma datapath computes",
              _fma_contract_or_no_fused_op("fused"), ("modes", "fma_contract"), per_mode=True),
    Predicate("fma_contract_sequential_or_no_fused_op_in_mode",
              "the mode's legal ops hold no fused multiply-add op, or fma_contract is sequential: the product rounded to "
              "the format first, which the separate multiplier then adder compute",
              _fma_contract_or_no_fused_op("sequential"), ("modes", "fma_contract"), per_mode=True),
    Predicate("fma_contract_cascade_product_rounding",
              "fma_contract asks for the product rounded under the family's own fixed cascade_product_rounding before the "
              "add; neither fused (one rounding) nor sequential (the product rounded under the mode's rounding) does, so "
              "no ALU contract holds it", lambda c: False, ("fma_contract",)),
    Predicate("significand_in_mode", "the mode's float format has a significand (an exponent-only format such as e8m0 "
              "has none, and the fused rounding's position is the format's precision)", _significand_in_mode, ("modes",),
              per_mode=True),
    Predicate("two_float_formats", "two float modes or more, with distinct formats", _two_float_formats, ("modes",)),
    Predicate("exact_unit", "accuracy is exact", lambda c: c.spec.get("accuracy", "exact") == "exact", ("accuracy",)),
    Predicate("approximate_unit", "accuracy is approximate",
              lambda c: c.spec.get("accuracy", "exact") == "approximate", ("accuracy",)),
    Predicate("dot_contract_architecture", "dot_contract is architecture",
              lambda c: c.spec.get("dot_contract", "fused") == "architecture", ("dot_contract",)),
    Predicate("dot_contract_not_fused", "dot_contract is sequential or architecture",
              lambda c: c.spec.get("dot_contract", "fused") != "fused", ("dot_contract",)),
    Predicate("rounding_rne_only", "rounding is [RNE]", lambda c: c.rounding == ["RNE"], ("rounding",)),
    Predicate("rounding_rtz_only", "rounding is [RTZ]", lambda c: c.rounding == ["RTZ"], ("rounding",)),
    Predicate("sr_only", "rounding is [SR]", lambda c: c.rounding == ["SR"], ("rounding",)),
    Predicate("daz_and_ftz", "daz_in and ftz_out are both fixed true",
              lambda c: c.flag("daz_in") == [True] and c.flag("ftz_out") == [True], ("daz_in", "ftz_out")),
    Predicate("no_daz_no_ftz", "daz_in and ftz_out are both fixed false",
              lambda c: c.flag("daz_in") == [False] and c.flag("ftz_out") == [False], ("daz_in", "ftz_out")),
    Predicate("daz_true", "daz_in is fixed true", lambda c: c.flag("daz_in") == [True], ("daz_in",)),
    Predicate("daz_false", "daz_in is fixed false", lambda c: c.flag("daz_in") == [False], ("daz_in",)),
    Predicate("ab_bf16", "every dot mode's operand format is bf16", _ab("bf16"), ("modes",)),
    Predicate("ab_sig_wider_than_8", "every dot mode's operand significand is wider than 8 bits",
              lambda c: bool(c.dot_modes) and all(getattr(f, "man_bits", 0) + 1 > 8 for f in c.ab_elems()), ("modes",)),
    Predicate("ab_fp8e4m3", "every dot mode's operand format is fp8e4m3", _ab("fp8e4m3"), ("modes",)),
    Predicate("ab_fp8e5m2", "every dot mode's operand format is fp8e5m2", _ab("fp8e5m2"), ("modes",)),
    Predicate("ab_fp8_both", "the dot modes' operand formats include fp8e4m3 and fp8e5m2",
              lambda c: {"fp8e4m3", "fp8e5m2"} <= {f.name for f in c.ab_elems()}, ("modes",)),
    Predicate("c_d_fp16", "every dot mode's D, and its C where accumulated, is fp16", _c_d("fp16"), ("modes",)),
    Predicate("c_d_bf16", "every dot mode's D, and its C where accumulated, is bf16", _c_d("bf16"), ("modes",)),
    Predicate("c_d_fp32", "every dot mode's D, and its C where accumulated, is fp32", _c_d("fp32"), ("modes",)),
    Predicate("d_integer", "every dot mode's D is an integer or fixed-point format",
              lambda c: bool(c.dot_modes) and all(_is_int(m["fd"]) for m in c.dot_modes), ("modes",)),
    Predicate("overflow_saturate", "overflow is saturate", lambda c: c.spec.get("overflow", "wrap") == "saturate",
              ("overflow",)),
    Predicate("overflow_wrap_or_d_float", "overflow is wrap, or no D is an integer format",
              lambda c: c.spec.get("overflow", "wrap") == "wrap" or not any(_is_int(m["fd"]) for m in c.dot_modes),
              ("overflow", "modes")),
    Predicate("binary_integer_adder_mode", "a mode's format is a two's complement or unsigned integer or fixed point",
              _binary_adder_mode, ("modes",)),
    Predicate("ones_complement_adder_mode", "the lane adder uses a ones' complement format",
              lambda c: all(getattr(c.modes[i][1], "encoding", None) == "ones_complement"
                            for i in ([c.mode] if c.mode is not None else range(len(c.modes)))),
              ("modes",), per_mode=True),
    Predicate("no_float_cvt_target", "no cvt op targets a float format", _no_float_cvt_target, ("modes",)),
    Predicate("no_div_sqrt", "the ops hold neither fdiv nor fsqrt",
              lambda c: not ({"fdiv", "fsqrt"} & set(c.spec.get("ops", []))), ("modes",)),
    Predicate("x_form_tight", "x_form is guard_round_sticky",
              lambda c: c.spec.get("x_form", "exact") == "guard_round_sticky", ("x_form",)),
    # the sibling predicates: another variable's value, which the search decides; each becomes a member
    # condition on the compiled variable (adir Variable.member_when), checked wherever ADIR reads a value
    Predicate("fp_fma_fused_in_mode", "the mode's fp_fma family is a fused multiply-add datapath",
              sibling=("fp_fma.family", _fused_fma_families)),
    Predicate("operand_order_shift_each", "the adder's operand_order is shift_each_operand",
              sibling=("fp_adder.operand_order", ("shift_each_operand",))),
    Predicate("string_form_dual", "the anticipator's string_form is dual_pos_neg_strings",
              sibling=("string_form", ("dual_pos_neg_strings",))),
    Predicate("sharing_dedicated_per_mode", "the fused multiply-add's sharing is dedicated_per_mode (one datapath shared "
              "across formats has no one format to round for)", sibling=("sharing", ("dedicated_per_mode",))),
    Predicate("composition_style_cascade", "the bridge's composition_style is cascade_mul_then_add",
              sibling=("composition_style", ("cascade_mul_then_add",))),
    # a deferred rule's predicate: neither the contract nor one sibling's value decides it
    Predicate("pins_equal_across_sharing_modes",
              "every mode that selects the sharing declares the same pins (an equality across the modes' variables, "
              "which one member condition cannot state; an alias of the sharing modes' variables would)"),
    Predicate("subnormal_representation_read_by_bridge",
              "the choice reaches the netlist: under bridge_fma with composition_style bridge_reuse it does not (the "
              "multiplier reads the stored significands and the bridge's adder normalizes both addends at its entry), an "
              "inactivity under two siblings' values (the family and its composition_style) on a variable four families "
              "share, which one `when` does not state; alu_contracts.alu_active_parameters names it inactive there"),
)}


# ---- the rules -------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Rule:
    key: str                     # fnmatch over family|choice|member
    requires: tuple = ()         # predicate names, every one of which must hold for the member to stay
    kind: str = "behavior"       # behavior | selector | interface | nested | deferred
    slot: str = "*"              # fnmatch over the slot path the family stands at (fp_fma, dot, fp_adder.lz)
    evidence: str = ""
    retired: bool = False        # an interface rule on a member the space no longer holds
    retired_domain: dict = field(default_factory=dict)   # the former domain of a retired member ({values} or {range})
    reason: str = ""             # a retired rule's own text (no predicate)
    under: tuple = ()            # contract predicates under which the rule applies; where one fails the rule is inert

    @property
    def family(self) -> str:
        return self.key.split("|")[0]

    @property
    def choice(self) -> str:
        return self.key.split("|")[1]

    @property
    def member(self) -> str:
        return self.key.split("|")[2]

    def matches(self, slot_path: str, family: str, choice: str = "*", member="*") -> bool:
        return fnmatch.fnmatchcase(slot_path, self.slot) and \
            fnmatch.fnmatchcase(f"{family}|{choice}|{member}", self.key)

    def matches_choice(self, slot_path: str, family: str, choice: str) -> bool:
        """Whether the rule names the family's choice, whatever the member."""
        return fnmatch.fnmatchcase(slot_path, self.slot) and fnmatch.fnmatchcase(family, self.family) \
            and fnmatch.fnmatchcase(choice, self.choice)


def R(key, requires=(), kind="behavior", slot="*", evidence="", under=()):
    return Rule(key, tuple(requires), kind, slot, evidence, under=tuple(under))


def retired(key, reason, values=None, rng=None):
    return Rule(key, (), "interface", "dot", "families/dot.py:dot_sv rejects the member", retired=True,
                retired_domain={"values": list(values)} if values is not None else {"range": list(rng)}, reason=reason)


RULES = (
    # ---- behavior: the member computes the contract under the predicates alone
    R("*|subnormal_representation|as_stored", ("no_sr",), slot="fp_fma",
      evidence="families/fp.py:fma_sv raises under SR; fptest --sr runs the fused variants normalized"),
    R("round_fused_in_reduction|*|*", ("x_form_exact",), slot="fp_multiplier",
      evidence="families/fp.py:mul_sv raises at the tight X; fptest --tight skips it; alu_fidelity_selftest conforms at the exact X"),
    R("bridge_fma|composition_style|cascade_mul_then_add", ("fma_contract_cascade_product_rounding",), slot="fp_fma",
      evidence="families/fp.py:fma_sv raises (the last defense); variant_legality.own_reason keeps it out of the sweep; "
               "behavior_rules_selftest shows the removal and the raise"),
    R("bridge_fma|composition_style|bridge_reuse", ("x_form_exact",), slot="fp_fma",
      evidence="families/fp.py:fma_sv raises at the tight X (the last defense); fptest --tight skips the bridge; "
               "behavior_rules_selftest conforms with bridge_reuse at the exact X"),
    R("pairwise_tree|per_level_truncation|True", ("dot_contract_architecture",), slot="dot",
      evidence="dot_seed.py raises: changes intermediate values"),
    R("multi_term_fused_dot|rounding_contract|faithful", ("dot_contract_architecture",), slot="dot",
      evidence="dot_seed.py raises: changes intermediate values"),
    R("multi_term_fused_dot|rounding_contract|truncated_with_guard", ("dot_contract_architecture",), slot="dot",
      evidence="dot_seed.py raises: changes intermediate values"),
    R("bridge_fma|composition_style|cascade_mul_then_add", ("dot_contract_not_fused",), slot="dot",
      evidence="families/dot.py:dot_family_requirements (the sequential contract)"),
    R("mixed_precision_cascade_fma|exact_product_preserved|False", ("dot_contract_not_fused",), slot="dot",
      evidence="families/dot.py:dot_family_requirements (the sequential contract)"),
    R("mixed_precision_cascade_fma|two_term_expansion_output|True", ("dot_contract_architecture",), slot="dot",
      evidence="families/dot.py:validate_unit_binding"),
    R("bf16_fma_datapath|rounding_mode|rne", ("rounding_rne_only",), slot="dot", evidence="families/dot.py:validate_unit_binding"),
    R("bf16_fma_datapath|rounding_mode|rtz", ("rounding_rtz_only",), slot="dot", evidence="families/dot.py:validate_unit_binding"),
    R("bf16_fma_datapath|rounding_mode|round_to_odd", ("dot_contract_architecture",), slot="dot",
      evidence="families/dot.py:validate_unit_binding"),
    R("bf16_fma_datapath|flush_subnormals|True", ("daz_and_ftz",), slot="dot", evidence="families/dot.py:validate_unit_binding"),
    R("bf16_fma_datapath|flush_subnormals|False", ("no_daz_no_ftz",), slot="dot", evidence="families/dot.py:validate_unit_binding"),
    R("fp8_training_datapath|stochastic_rounding|True", ("sr_only",), slot="dot", evidence="families/dot.py:validate_unit_binding"),
    R("fp8_training_datapath|stochastic_rounding|False", ("no_sr",), slot="dot", evidence="families/dot.py:validate_unit_binding"),
    R("fp8_training_datapath|chunk_based_accumulation|True", ("dot_contract_architecture",), slot="dot",
      evidence="families/dot.py:dot_family_requirements"),
    R("tensor_core_mixed_precision_mac|subnormal_support|True", ("daz_false",), slot="dot",
      evidence="families/dot.py:validate_unit_binding"),
    R("tensor_core_mixed_precision_mac|subnormal_support|False", ("daz_true",), slot="dot",
      evidence="families/dot.py:validate_unit_binding"),
    R("integer_mac|saturating_accumulate|True", ("d_integer", "overflow_saturate"), slot="dot",
      evidence="families/dot.py:validate_unit_binding"),
    R("integer_mac|saturating_accumulate|False", ("overflow_wrap_or_d_float",), slot="dot",
      evidence="families/dot.py:validate_unit_binding"),
    # ---- selector: the member selects the behavior; an enum member leaves an exact unit, a numeric is never searched
    R("posit_adder_multiplier|approximation|logarithmic_fraction", ("approximate_unit",), kind="selector", slot="posit_unit",
      evidence="alu_float.py:declare_posit_library (the PLAM module, under the approximate contract)"),
    R("multi_term_fused_dot|window_bits|*", kind="selector", slot="dot",
      evidence="commit d76bd41; dot_window_selftest; families/dot.py raises below the minimum"),
    R("streaming_accurate_accumulator|window_bits|*", kind="selector", slot="dot",
      evidence="dot_arch_ref.py reads the pin; families/dot.py raises below the minimum"),
    R("kulisch_long_accumulator|accumulator_width_bits|*", kind="selector", slot="dot",
      evidence="families/dot.py raises below the exact frame"),
    R("integer_mac|accumulator_width_bits|*", kind="selector", slot="dot", evidence="families/dot.py raises below the exact frame"),
    # ---- interface: the member cannot be built under the unit's formats, ops or mode count
    R("shared_across_formats|*|*", ("two_float_formats",), kind="interface", slot="rounder",
      evidence="alu_seed.py raises: requires two distinct selected formats"),
    R("shared_across_formats|*|*", ("two_float_formats",), kind="interface", slot="unpacker",
      evidence="alu_seed.py raises: requires two distinct selected formats"),
    R("*|sharing|shared_across_formats", ("two_float_formats",), kind="interface", slot="fp_fma",
      evidence="alu_seed.py raises: requires two distinct selected formats"),
    R("partitioned_carry_chain|*|*", ("binary_integer_adder_mode",), kind="interface", slot="subword",
      evidence="generators.py:families_of"),
    R("end_around_carry|*|*", ("ones_complement_adder_mode",), kind="interface", slot="adder",
      evidence="alu_int.py constructs end-around carry only for ones' complement lanes; binary lanes require an ordinary CPA"),
    R("posit_ieee_interop|conversion_direction|ieee_to_posit", ("no_float_cvt_target",), kind="interface", slot="posit_unit",
      evidence="alu_float.py:declare_posit_library"),
    R("posit_adder_multiplier|operator_set|add_mul", ("no_div_sqrt",), kind="interface", slot="posit_unit",
      evidence="alu_float.py:declare_posit_library; generators.py:families_of"),
    R("bf16_fma_datapath|*|*", ("c_d_fp32",), kind="interface", slot="dot", evidence="families/dot.py:validate_unit_binding"),
    R("bf16_fma_datapath|multi_word_composition|False", ("ab_bf16",), kind="interface", slot="dot",
      evidence="families/dot.py:validate_unit_binding"),
    R("bf16_fma_datapath|multi_word_composition|True", ("ab_sig_wider_than_8",), kind="interface", slot="dot",
      evidence="families/dot.py:validate_unit_binding"),
    R("fp8_training_datapath|format_policy|single_e4m3", ("ab_fp8e4m3",), kind="interface", slot="dot",
      evidence="families/dot.py:validate_unit_binding"),
    R("fp8_training_datapath|format_policy|single_e5m2", ("ab_fp8e5m2",), kind="interface", slot="dot",
      evidence="families/dot.py:validate_unit_binding"),
    R("fp8_training_datapath|format_policy|hybrid_forward_e4m3_backward_e5m2", ("ab_fp8_both",), kind="interface", slot="dot",
      evidence="families/dot.py:validate_unit_binding"),
    R("fp8_training_datapath|accumulate_precision|fp16", ("c_d_fp16",), kind="interface", slot="dot",
      evidence="families/dot.py:validate_unit_binding"),
    R("fp8_training_datapath|accumulate_precision|bf16", ("c_d_bf16",), kind="interface", slot="dot",
      evidence="families/dot.py:validate_unit_binding"),
    R("fp8_training_datapath|accumulate_precision|fp32", ("c_d_fp32",), kind="interface", slot="dot",
      evidence="families/dot.py:validate_unit_binding"),
    # the former UNSUPPORTED_DOT_CHOICES: members that left the space with the combinational VecDotAcc contract
    retired("integer_mac|element_op|absolute_difference",
            "VecDotAcc computes product accumulation, not distance accumulation", values=["absolute_difference"]),
    retired("multi_term_fused_dot|term_source|fp_operands",
            "VecDotAcc has pairs of multiplicands, not an operand-sum operation", values=["fp_operands"]),
    retired("fused_two_term_dot|second_op|*", "the interface has no butterfly operation or sign control",
            values=["add_subtract_pair", "both"]),
    retired("classic_fma|pipeline_depth|*", "pipeline registers require a sequential latency contract", rng=[2, 8, 1]),
    retired("bridge_fma|bridge_extra_stages|*", "pipeline registers require a sequential latency contract", rng=[1, 4, 1]),
    retired("multi_term_fused_dot|pipeline_depth|*", "pipeline registers require a sequential latency contract", rng=[1, 3, 1]),
    retired("multipath_fma|accumulate_forwarding_loop|*",
            "a loop-carried forwarding path requires state and a cycle interface", values=[False, True]),
    retired("kulisch_long_accumulator|carry_resolution|periodic_sweep",
            "periodic carry sweeps require state and an iteration schedule", values=["periodic_sweep"]),
    # ---- behavior under a sibling's value: a member condition (adir Variable.member_when); the render-time raise
    #      stays the last defense behind ADIR's declaration check
    R("lza|string_form|dual_pos_neg_strings", ("operand_order_shift_each",), slot="fp_adder.*",
      evidence="families/fp.py:add_sv raises under operand_order swap_before_shift; behavior_rules_selftest conforms "
               "under shift_each_operand"),
    R("reduced_latency_fma|rounding_position|fused_with_cpa_dual_sum",
      ("x_form_exact", "significand_in_mode", "sharing_dedicated_per_mode"), slot="fp_fma",
      evidence="families/fp.py:fma_sv raises at the tight X, without a significand and under shared_across_formats (the "
               "last defense); fptest's two fused-rounding variants conform in the three roles at the exact X; "
               "behavior_rules_selftest shows the removal, the condition and the raise, and conforms under "
               "dedicated_per_mode"),
    # ---- nested: the choice is a decision under a sibling choice's member alone (the choice's `when`)
    R("lza|split_string_select|*", ("string_form_dual",), kind="nested", slot="fp_adder.*",
      evidence="families/fp.py:add_sv selects between the two strings alone; a single string reads no split select"),
    R("bridge_fma|cascade_product_rounding|*", ("composition_style_cascade",), kind="nested",
      evidence="families/dot.py:_bridge_sv reads cascade_product_rounding under the cascade alone (the bridge and the "
               "monolithic datapath round once, in the mode's rounder)"),
    # ---- deferred: an equality across the variables of several modes; the render-time raise stays the defense
    R("shared_across_formats|*|*", ("pins_equal_across_sharing_modes",), kind="deferred", slot="rounder",
      evidence="alu_seed.py raises: requires compatible pins on its one physical datapath"),
    R("shared_across_formats|*|*", ("pins_equal_across_sharing_modes",), kind="deferred", slot="unpacker",
      evidence="alu_seed.py raises: requires compatible pins on its one physical datapath"),
    R("*|sharing|shared_across_formats", ("pins_equal_across_sharing_modes",), kind="deferred", slot="fp_fma",
      evidence="alu_seed.py builds the shared datapath at the widest geometry; no pin check on the fp_fma sharing"),
    # ---- deferred: a choice inactive under two siblings' values on a variable several families share
    R("bridge_fma|subnormal_representation|*", ("subnormal_representation_read_by_bridge",), kind="deferred", slot="fp_fma",
      evidence="alu_contracts.alu_active_parameters names the choice inactive under bridge_reuse (the variant sweep "
               "rejects an explicit value); families/fp.py:fma_sv drops the pin there; the no_sr rule above narrows the "
               "shared variable under SR, which loses no design of the bridge"),
)


@dataclass(frozen=True)
class OptionRule:
    """A rule over the unit options alone: the value of `option` needs the predicates."""
    option: str
    value: object
    requires: tuple
    evidence: str = ""


OPTION_RULES = (
    OptionRule("x_form", "guard_round_sticky", ("float_mode", "no_cvt_in_float_modes", "no_sr"),
               "fptest --tight runs every float family at the tight X; alu_mode.py:tight_x raises otherwise"),
)


def retired_dot_choices() -> dict:
    """The former `UNSUPPORTED_DOT_CHOICES` shape: `family.pin` -> {values | range, reason}, for the dot
    generator's rejection of old inputs and the coverage audit."""
    out = {}
    for r in RULES:
        if r.retired:
            out[f"{r.family}.{r.choice}"] = dict(r.retired_domain, reason=r.reason)
    return out


# ---- evaluation ------------------------------------------------------------------------------------------

def _failing(requires, contract: Contract):
    """The first predicate of `requires` that does not hold, or None; a
    non-evaluable predicate never fails (its rule is deferred)."""
    for name in requires:
        p = PREDICATES[name]
        if p.holds is not None and not p.holds(contract):
            return p
    return None


def _reason(what: str, p: Predicate, contract: Contract) -> str:
    return f"{what} needs {p.name} ({p.meaning}); the unit has {contract.describe(*p.quotes)}"


def _condition_doc(what: str, p: Predicate, under: tuple, contract: Contract) -> str:
    """The doc of a member condition: the sibling predicate's meaning and
    the contract options the rule applies under."""
    doc = f"{what} needs {p.name} ({p.meaning})"
    quotes = tuple(q for n in under for q in PREDICATES[n].quotes)
    if quotes:
        doc += f" under {contract.describe(*quotes)}"
    return doc


def selector_admitted(contract: Contract) -> bool:
    """Where a behavior selector may stand: an approximate ALU (the budget
    is its gate), or a dot unit under the explicit architecture contract."""
    if contract.unit == "vec_dot_acc":
        return contract.spec.get("dot_contract", "fused") == "architecture"
    return contract.spec.get("accuracy", "exact") == "approximate"


def behavior_rules_apply(contract: Contract) -> bool:
    """The static behavior rules gate an exact contract; an approximate
    unit measures behavior as its error budget (plan pitfall 8)."""
    return not (contract.unit == "alu" and contract.spec.get("accuracy", "exact") == "approximate")


@dataclass
class Row:
    variable: str
    member: object
    kind: str
    reason: str
    indexes: tuple = ()          # the structure indexes the removal applies to; () for every one
    rule: str = ""


@dataclass
class Report:
    rows: list = field(default_factory=list)
    defaults: list = field(default_factory=list)      # (variable, indexes, old default, new default)
    deferred: list = field(default_factory=list)      # (variable, rule key, evidence)
    disagreements: list = field(default_factory=list)  # (variable, member, families admitting, families excluding)
    menu_excluded: dict = field(default_factory=dict)  # slot prefix -> {family: reason} excluded at every index
    conditions: list = field(default_factory=list)    # (variable, member, sibling, allowed, doc, rule key)
    nested: list = field(default_factory=list)        # (variable, sibling, allowed, doc, rule key)
    not_lowered: list = field(default_factory=list)   # (variable, rule key, why): a condition the prune could not place

    def add(self, row: Row):
        self.rows.append(row)

    def by_kind(self) -> dict:
        out: dict = {}
        for r in self.rows:
            out.setdefault(r.kind, []).append(r)
        return out

    def prompt_text(self, limit: int = 16) -> str:
        """One sentence for the unit section of the prompt: what the menu
        does not hold under this contract, and why. A behavior or an
        interface removal is named with its reason; the selectors an
        exact unit sheds are summarized per member; a member condition is
        named with the sibling it depends on."""
        named = [r for r in self.rows if r.kind in ("behavior", "interface")]
        summarized: dict = {}
        for r in self.rows:
            if r.kind in ("selector", "unregistered"):
                summarized.setdefault((r.kind, _fmt(r.member)), []).append(r)
        if not named and not summarized and not self.conditions:
            return ""
        parts = []
        for r in named[:limit]:
            where = f" ({', '.join(r.indexes)})" if r.indexes else ""
            parts.append(f"`{r.variable}`{where} does not offer `{_fmt(r.member)}`: {r.reason}")
        if len(named) > limit:
            parts.append(f"and {len(named) - limit} more behavior or interface removals (the elaboration report lists them)")
        for (kind, member), rs in sorted(summarized.items()):
            slots = sorted({r.variable for r in rs})
            what = ("selects the computed function and belongs to an approximate unit" if kind == "selector"
                    else "has no behavior classification")
            if len(slots) == 1 and rs[0].kind == "selector" and rs[0].reason.startswith("a numeric"):
                parts.append(f"`{slots[0]}` is never searched: {rs[0].reason}")
                continue
            parts.append(f"`{member}` {what}: removed from {len(slots)} slot{'s' if len(slots) != 1 else ''}"
                         + (f" ({slots[0]})" if len(slots) == 1 else ""))
        n = len(self.rows)
        text = ""
        if n:
            text = (f"{n} candidate{'s' if n != 1 else ''} removed from the menu under this contract "
                    f"(chialu.behavior_rules): " + "; ".join(parts)
                    + ". A VAR line naming one is rejected with that reason; the cards still describe it.")
        if self.conditions:
            conds = [f"`{v}` offers `{_fmt(m)}` while `{sib}` is one of {list(allowed)} ({doc})"
                     for v, m, sib, allowed, doc, _key in self.conditions[:limit]]
            text += (" " if text else "") + f"{len(self.conditions)} member condition" \
                + ("s" if len(self.conditions) != 1 else "") + " under this contract: " + "; ".join(conds) \
                + ". The sibling is your decision too; a VAR line naming the member under another value is rejected."
        return text

    def to_json(self) -> dict:
        return {"removed": [{"variable": r.variable, "member": r.member, "kind": r.kind, "reason": r.reason,
                             "indexes": list(r.indexes), "rule": r.rule} for r in self.rows],
                "defaults_changed": [{"variable": v, "indexes": list(ix), "from": a, "to": b} for v, ix, a, b in self.defaults],
                "deferred": [{"variable": v, "rule": k, "evidence": e} for v, k, e in self.deferred],
                "disagreements": [{"variable": v, "member": m, "admitting": a, "excluding": x}
                                  for v, m, a, x in self.disagreements],
                "conditioned": [{"variable": v, "member": m, "sibling": sib, "allowed": list(allowed), "reason": doc,
                                 "rule": key} for v, m, sib, allowed, doc, key in self.conditions],
                "nested": [{"variable": v, "sibling": sib, "allowed": list(allowed), "reason": doc, "rule": key}
                           for v, sib, allowed, doc, key in self.nested],
                "not_lowered": [{"variable": v, "rule": key, "why": why} for v, key, why in self.not_lowered]}


def _fmt(m) -> str:
    return str(m)


class _SlotPrune:
    """The prune of one top-level slot's compiled variables: one walk of
    the slot's space mirroring adir.spaces.Space.variables, the rules
    prefiltered to the slot, and the verdicts memoized per family and
    member (per path where a rule names a sub-slot). A verdict that
    evaluated a per-mode predicate is taken per structure index; every
    other verdict holds for the whole slot."""

    def __init__(self, kind: str, spec: dict, indexes, report: Report):
        self.kind = kind
        self.spec = spec
        self.contract = Contract(spec)
        self.indexes = [str(i) for i in indexes] if indexes else [None]
        self.contracts = {ix: self.contract.at(ix) for ix in self.indexes}
        self.report = report
        self.rules = [r for r in RULES if not r.retired and (r.slot == "*" or fnmatch.fnmatchcase(kind, r.slot)
                                                             or r.slot.split(".")[0] in (kind, "*"))]
        self.path_sensitive = any(r.slot not in ("*", kind) for r in self.rules)
        self.narrow: dict = {}       # variable name -> index (None: every one) -> {member: (kind, reason, key)}
        self.conditions: dict = {}   # variable name -> index -> {member: (sibling path, allowed, doc, key)}
        self.nested: dict = {}       # variable name -> (sibling path, allowed, doc, key)
        self.search_only: set = set()
        self.deferred: list = []
        self.disagreements: list = []
        self._per_mode_evals = 0
        self._fam_memo: dict = {}
        self._mem_memo: dict = {}

    def _key(self, path):
        return path if self.path_sensitive else ""

    def _applies(self, r: Rule, contract: Contract) -> bool:
        """Whether a rule applies under the contract: its `under` predicates hold."""
        return not r.under or self._failing(r.under, contract) is None

    @staticmethod
    def _sibling_predicate(requires) -> Predicate:
        return next((PREDICATES[n] for n in requires if PREDICATES[n].sibling), None)

    def sibling_name(self, prefix: str, path: str, own_name: str) -> str:
        """The compiled name of a sibling predicate's variable: a bare
        choice name is a choice of the same family as `own_name`
        (`core.fp_adder.*.lz.string_form` for `string_form`); a
        `<slot>.<rest>` path is relative to the unit, indexed as this slot
        is (`core.fp_fma.*.family` for `fp_fma.family` under
        `core.unpacker.*`), which holds where both slots index by the
        seed's structures; a sibling that resolves to no template is an
        absent sibling, which `bind_member_conditions` turns static."""
        if "." not in path:
            return own_name.rsplit(".", 1)[0] + "." + path
        slot, rest = path.split(".", 1)
        unit = prefix[: prefix.index("." + self.kind)] if "." + self.kind in prefix else prefix
        return f"{unit}.{slot}.*.{rest}" if "*" in prefix else f"{unit}.{slot}.{rest}"

    def _per_index(self, evaluate):
        """{None: verdict} where the verdict evaluated no per-mode
        predicate, else {index: verdict} over the slot's indexes."""
        before = self._per_mode_evals
        v = evaluate(self.contract)
        if self._per_mode_evals == before or self.indexes == [None]:
            return {None: v}
        return {ix: evaluate(self.contracts[ix]) for ix in self.indexes}

    def _failing(self, requires, contract):
        for name in requires:
            p = PREDICATES[name]
            if p.holds is None:
                continue
            if p.per_mode:
                self._per_mode_evals += 1
            if not p.holds(contract):
                return p
        return None

    # -- one family's admission
    def _family_verdict(self, path: str, fam, contract: Contract):
        if not fam.behavior:
            if EXCLUDE_UNREGISTERED:
                return ("unregistered", f"{fam.name} has no behavior classification (chialu/behavior_rules.py)", "")
            return None
        if fam.behavior == "selector" and not selector_admitted(contract):
            what = "the explicit architecture contract" if contract.unit == "vec_dot_acc" else "an approximate unit"
            return ("selector", f"{fam.name} selects the computed function and belongs to {what}; the unit has "
                                f"{contract.describe('dot_contract' if contract.unit == 'vec_dot_acc' else 'accuracy')}", "")
        if fam.behavior == "conditional" and behavior_rules_apply(contract):
            p = self._failing(fam.requires, contract)
            if p is not None:
                return ("behavior", _reason(fam.name, p, contract), f"{fam.name}|*|*")
        for r in self.rules:
            if r.kind in ("deferred", "nested") or r.choice != "*" or r.member != "*" \
                    or not r.matches(path, fam.name, "*", "*"):
                continue
            if r.kind in ("behavior", "selector") and not behavior_rules_apply(contract):
                continue
            if not self._applies(r, contract):
                continue
            p = self._failing(r.requires, contract)
            if p is not None:
                return (r.kind, _reason(fam.name, p, contract), r.key)
        return None

    def family_reason(self, path: str, fam) -> dict:
        memo = (self._key(path), fam.name)
        if memo not in self._fam_memo:
            self._fam_memo[memo] = self._per_index(lambda c: self._family_verdict(path, fam, c))
        return self._fam_memo[memo]

    def _member_verdict(self, path: str, fam, choice: str, member, contract: Contract):
        """An exclusion `(kind, reason, key)`, a member condition
        `("condition", (sibling path, allowed, doc), key)`, or None."""
        for r in self.rules:
            if r.kind in ("deferred", "nested") or (r.choice == "*" and r.member == "*") or not r.requires:
                continue
            if not r.matches(path, fam.name, choice, _fmt(member)):
                continue
            if r.kind in ("behavior", "selector") and not behavior_rules_apply(contract):
                continue
            if not self._applies(r, contract):
                continue
            p = self._failing(r.requires, contract)
            if p is not None:
                return (r.kind, _reason(f"{fam.name} {choice} {_fmt(member)}", p, contract), r.key)
            s = self._sibling_predicate(r.requires)
            if s is not None:
                doc = _condition_doc(f"{fam.name} {choice} {_fmt(member)}", s, r.under, contract)
                return ("condition", (s.sibling[0], s.sibling_values(), doc), r.key)
        return None

    def member_reason(self, path: str, fam, choice: str, member) -> dict:
        memo = (self._key(path), fam.name, choice, _fmt(member))
        if memo not in self._mem_memo:
            self._mem_memo[memo] = self._per_index(lambda c: self._member_verdict(path, fam, choice, member, c))
        return self._mem_memo[memo]

    def numeric_selector(self, path: str, fam, choice: str):
        for r in self.rules:
            if r.kind == "selector" and not r.requires and r.matches_choice(path, fam.name, choice):
                return r
        return None

    def deferred_rules(self, path: str, fam, choice: str):
        return [r for r in self.rules if r.kind == "deferred" and r.matches_choice(path, fam.name, choice)]

    def nested_rule(self, path: str, fam, choice: str):
        return next((r for r in self.rules if r.kind == "nested" and r.matches_choice(path, fam.name, choice)), None)

    # -- the walk, mirroring adir.spaces.Space.variables
    def walk(self, families: list, prefix: str, path: str):
        fam_var = f"{prefix}.family"
        fam_v = {f.name: self.family_reason(path, f) for f in families}
        choices: dict = {}
        for f in families:
            for choice, dom in f.design_choices.items():
                choices.setdefault(choice, []).append((f, dom))
        enum_members: dict = {}          # choice -> [members]
        mem_v: dict = {}                 # (family, choice, member) -> per-index verdicts
        for choice, entries in choices.items():
            doms = [d for _, d in entries]
            if not all(isinstance(d, (Enum, Bool)) for d in doms):
                continue
            members = []
            for d in doms:
                for m in (d.members() if isinstance(d, Bool) else d.members_):
                    if not any(m == x for x in members):
                        members.append(m)
            enum_members[choice] = members
            for f, d in entries:
                for m in members:
                    if d.contains(m):
                        mem_v[(f.name, choice, _fmt(m))] = self.member_reason(path, f, choice, m)
        per_index = any(set(d) != {None} for d in list(fam_v.values()) + list(mem_v.values()))
        idxs = self.indexes if per_index else [None]
        for idx in idxs:
            def pick(d):
                return d[idx] if idx in d else d.get(None)
            excluded = {n: pick(d) for n, d in fam_v.items() if pick(d) is not None}
            member_excl: dict = {}
            member_cond: dict = {}
            changed = True
            while changed:
                changed = False
                for choice, members in enum_members.items():
                    entries = choices[choice]
                    excl: dict = {}
                    cond: dict = {}
                    for m in members:
                        admitting = [f for f, d in entries if d.contains(m) and f.name not in excluded]
                        if not admitting:
                            continue
                        verdicts = [(f, pick(mem_v[(f.name, choice, _fmt(m))])) for f in admitting]
                        exclude = [f for f, v in verdicts if v is not None and v[0] != "condition"]
                        conditioned = [(f, v) for f, v in verdicts if v is not None and v[0] == "condition"]
                        if exclude and len(exclude) == len(admitting):
                            excl[m] = next(v for _f, v in verdicts if v is not None and v[0] != "condition")
                        elif exclude:
                            entry = (f"{prefix}.{choice}", m, [f.name for f, v in verdicts if v is None or v[0] == "condition"],
                                     [f.name for f in exclude])
                            if entry not in self.disagreements:
                                self.disagreements.append(entry)
                        elif conditioned and len(conditioned) == len(admitting) \
                                and len({(v[1][0], v[1][1]) for _f, v in conditioned}) == 1:
                            # every declaring family conditions the member on the same sibling and values
                            cond[m] = conditioned[0][1]
                        elif conditioned:
                            entry = (f"{prefix}.{choice}", m, [f.name for f, v in verdicts if v is None],
                                     [f.name for f, _v in conditioned])
                            if entry not in self.disagreements:
                                self.disagreements.append(entry)
                    member_excl[choice] = excl
                    member_cond[choice] = cond
                    for f, d in entries:
                        if f.name in excluded:
                            continue
                        own = d.members() if isinstance(d, Bool) else list(d.members_)
                        if own and all(any(m == x for x in excl) for m in own):
                            kind, why, key = excl[own[0]]
                            excluded[f.name] = (kind, f"no member of {f.name}'s {choice} is admitted: {why}", key)
                            changed = True
            if excluded:
                self.narrow.setdefault(fam_var, {})[idx] = dict(excluded)
            for choice, excl in member_excl.items():
                if excl:
                    self.narrow.setdefault(f"{prefix}.{choice}", {})[idx] = dict(excl)
            for choice, cond in member_cond.items():
                if cond:
                    self.conditions.setdefault(f"{prefix}.{choice}", {})[idx] = {
                        m: (sib, allowed, doc, key) for m, (_c, (sib, allowed, doc), key) in cond.items()}
        # the numeric selectors, the nested rules and the deferred rules of this node's choices and families
        for choice, entries in choices.items():
            name = f"{prefix}.{choice}"
            for f, d in entries:
                if isinstance(d, Range) and self.numeric_selector(path, f, choice) is not None:
                    self.search_only.add(name)
                for r in self.deferred_rules(path, f, choice):
                    if (name, r.key) not in {(v, k) for v, k, _ in self.deferred}:
                        self.deferred.append((name, r.key, r.evidence))
                r = self.nested_rule(path, f, choice)
                if r is not None and name not in self.nested:
                    s = self._sibling_predicate(r.requires)
                    if s is not None and self._applies(r, self.contract):
                        self.nested[name] = (s.sibling[0], s.sibling_values(),
                                             _condition_doc(f"{f.name} {choice}", s, r.under, self.contract), r.key)
        for f in families:
            for r in self.rules:
                if r.kind == "deferred" and r.choice == "*" and r.matches(path, f.name) \
                        and (fam_var, r.key) not in {(v, k) for v, k, _ in self.deferred}:
                    self.deferred.append((fam_var, r.key, r.evidence))
        # the component slots: one slot per name, the union of the sub-spaces' families
        slots: dict = {}
        for f in families:
            for slot, sub in f.components.items():
                fams = slots.setdefault(slot, [])
                for sf in sub.families:
                    if not any(x.name == sf.name for x in fams):
                        fams.append(sf)
        for slot, fams in slots.items():
            self.walk(fams, f"{prefix}.{slot}", f"{path}.{slot}")

    def apply(self, variables: list, prefix: str) -> list:
        """The variables with the narrowed domains: one domain where every
        index agrees, per-index domains otherwise; a numeric selector gets
        a one-member search domain at its default."""
        by_name = {v.name: v for v in variables}
        out = list(variables)
        rows: list = []
        for name, per_index in self.narrow.items():
            v = by_name.get(name)
            if v is None or not isinstance(v.domain, (Enum, Bool)):
                continue
            base = v.domain if isinstance(v.domain, Enum) else Enum((False, True))
            domains = {}
            for index in self.indexes:
                reasons = per_index.get(index) if index in per_index else per_index.get(None)
                reasons = {m: why for m, why in (reasons or {}).items() if base.contains(m)}
                if not reasons:
                    domains[index] = base
                    continue
                try:
                    domains[index] = base.without({m: why for m, (_k, why, _key) in reasons.items()})
                except BindError as e:
                    first = next(iter(reasons.values()))
                    raise BindError(name, first[1]) from e
            for key, reasons in per_index.items():
                for m, (kind, why, rule) in reasons.items():
                    if base.contains(m):
                        rows.append(Row(name, m, kind, why, () if key is None else (key,), rule))
            first = next(iter(domains.values()))
            same = all(list(d.members_) == list(first.members_) for d in domains.values())
            if same:
                if first.default() != base.default():
                    self.report.defaults.append((name, (), base.default(), first.default()))
                out[out.index(v)] = replace(v, domain=first)
            else:
                idx_doms = {ix: d for ix, d in domains.items() if list(d.members_) != list(base.members_)}
                for ix, d in idx_doms.items():
                    if d.default() != base.default():
                        self.report.defaults.append((name, (ix,), base.default(), d.default()))
                out[out.index(v)] = replace(v, index_domains=idx_doms)
        self.report.rows.extend(self._collapsed(rows))
        # the member conditions: one condition per member on the template, so the verdict must agree across the
        # slot's indexes (a sibling path with `*` carries the index itself)
        for name, per_index in self.conditions.items():
            v = by_name.get(name)
            if v is None or not isinstance(v.domain, (Enum, Bool)):
                continue
            verdicts = [per_index.get(ix) if ix in per_index else per_index.get(None) or {} for ix in self.indexes]
            if any(x != verdicts[0] for x in verdicts[1:]):
                key = next(iter(next(iter(per_index.values())).values()))[3]
                self.report.not_lowered.append((name, key, "the condition differs across the slot's indexes"))
                continue
            member_when = {m: (self.sibling_name(prefix, sib, name), tuple(allowed), doc)
                           for m, (sib, allowed, doc, _key) in verdicts[0].items()}
            try:
                out[out.index(v)] = replace(v, member_when=member_when)
            except BindError as e:
                key = next(iter(verdicts[0].values()))[3]
                self.report.not_lowered.append((name, key, e.msg))
                continue
            for m, (sib, allowed, doc, key) in verdicts[0].items():
                self.report.conditions.append((name, m, member_when[m][0], list(allowed), doc, key))
        # the nested choices: the choice's `when` moves to the sibling choice, which must exist in this slot under
        # the same family condition, so the family condition holds through the sibling
        for name, (path, allowed, doc, key) in self.nested.items():
            v = by_name.get(name)
            if v is None:
                continue
            sib = self.sibling_name(prefix, path, name)
            sv = by_name.get(sib)
            if sv is None or sv.when != v.when:
                self.report.not_lowered.append((name, key, f"no sibling {sib} under the same family condition"))
                continue
            out[out.index(v)] = replace(v, when=(sib, tuple(allowed)))
            self.report.nested.append((name, sib, list(allowed), doc, key))
        for name in sorted(self.search_only):
            v = by_name.get(name)
            if v is None or not isinstance(v.domain, Range):
                continue
            default = v.domain.default()
            out[out.index(v)] = replace(v, search_domain=Enum((default,)))
            self.report.add(Row(name, "*", "selector", f"a numeric behavior selector: never searched (the search "
                                                         f"domain is its default {default!r}); a run file fixes it and "
                                                         f"the conformance gate decides", (), ""))
        self.report.deferred.extend(x for x in self.deferred if x not in self.report.deferred)
        self.report.disagreements.extend(self.disagreements)
        # the menu: families excluded at every index
        fam_var = f"{prefix}.family"
        per_index = self.narrow.get(fam_var) or {}
        if per_index:
            sets = []
            for ix in self.indexes:
                reasons = per_index.get(ix) if ix in per_index else per_index.get(None) or {}
                sets.append(reasons)
            common = set.intersection(*(set(s) for s in sets)) if sets else set()
            self.report.menu_excluded[prefix] = {n: sets[0][n][1] for n in sorted(common)}
        return out

    def _collapsed(self, rows: list) -> list:
        """Rows that apply to every index of the slot collapse to one row."""
        n = len(self.indexes)
        if n <= 1:
            return rows
        seen: dict = {}
        order = []
        for r in rows:
            key = (r.variable, _fmt(r.member), r.kind, r.reason, r.rule)
            if key not in seen:
                order.append(key)
            seen.setdefault(key, []).append(r)
        out = []
        for key in order:
            rs = seen[key]
            if len(rs) == n and all(len(r.indexes) == 1 for r in rs):
                rs[0].indexes = ()
                out.append(rs[0])
            else:
                out.extend(rs)
        return out


def prune_slot(kind: str, space, prefix: str, variables: list, spec: dict, indexes=None, report: Report = None) -> list:
    """The variables of one slot (`space.variables(prefix, ...)`) after
    the behavior rules: `kind` is the slot's name (`fp_fma`, `dot`),
    `prefix` the variables' prefix (`core.fp_fma.*`), `indexes` the
    structure indexes an indexed slot expands over. The removals and the
    default changes go to `report`."""
    report = report if report is not None else Report()
    p = _SlotPrune(kind, spec, indexes, report)
    p.walk(list(space.families), prefix, kind)
    return p.apply(variables, prefix)


def bind_member_conditions(variables: list, report: Report = None, available=()) -> list:
    """The unit's compiled variables with every member condition resolved
    against the templates the unit compiles: a condition whose sibling
    template the unit does not hold (a unit without an `fp_fma` slot)
    becomes a static exclusion with the same reason, since an absent
    sibling fails the condition; the exclusion is reported as a removal.
    Runs once in `elaborate`, after every slot is pruned."""
    names = {v.name for v in variables} | set(available)
    out = list(variables)
    for i, v in enumerate(variables):
        if not v.member_when:
            continue
        gone = {m: cond for m, cond in v.member_when.items() if cond[0] not in names}
        if not gone:
            continue
        kept = {m: cond for m, cond in v.member_when.items() if m not in gone}
        reasons = {m: f"{m!r} is admissible when {sib} is one of {list(allowed)!r}; the unit has no {sib}"
                      + (f" ({doc})" if doc else "") for m, (sib, allowed, doc) in gone.items()}
        base = v.domain if isinstance(v.domain, Enum) else Enum((False, True))
        domain = base.without({m: why for m, why in reasons.items() if base.contains(m)})
        index_domains = None
        if v.index_domains:
            index_domains = {ix: (d.without({m: why for m, why in reasons.items() if d.contains(m)})
                                  if any(d.contains(m) for m in reasons) else d)
                             for ix, d in v.index_domains.items()}
        out[i] = replace(v, domain=domain, index_domains=index_domains, member_when=kept or None)
        if report is not None:
            for m, why in reasons.items():
                report.add(Row(v.name, m, "behavior", why, (), ""))
            report.conditions = [c for c in report.conditions if not (c[0] == v.name and c[1] in gone)]
            if domain.default() != base.default():
                report.defaults.append((v.name, (), base.default(), domain.default()))
    return out


def check_options(spec: dict) -> list:
    """The option rules a spec breaks, each in the YAML's terms."""
    c = Contract(spec)
    out = []
    for r in OPTION_RULES:
        if spec.get(r.option) != r.value:
            continue
        p = _failing(r.requires, c)
        if p is not None:
            out.append(_reason(f"{r.option}: {r.value}", p, c))
    return out


def outside_reason(domain, value) -> str:
    """`: <reason>` where a domain check removed the value, else ''."""
    why = domain.exclusion_reason(value) if hasattr(domain, "exclusion_reason") else None
    return f": {why}" if why else ""


# ---- the declaration side: conformance's rule-defect note -----------------------------------------------

def declared_rule_members(vars_: dict) -> list:
    """The declared VAR values a behavior, selector or interface rule or a
    conditional family governs, as `name=value (rule)` strings: what a
    conformance failure of such a declaration names as a candidate rule
    defect (plan pitfall 1). Syntactic: the family of a choice comes from
    the block where it declares one, else the rule is matched with the
    family wild."""
    out = []
    conditional = set(_conditional_family_names())
    for name, value in vars_.items():
        if not str(name).startswith("core."):
            continue
        parts = str(name).split(".")
        if parts[-1] == "family":
            if str(value) in conditional:
                out.append(f"{name}={value} (conditional family)")
            for r in RULES:
                if r.kind not in ("deferred", "nested") and not r.retired and r.choice == "*" \
                        and fnmatch.fnmatchcase(str(value), r.family):
                    out.append(f"{name}={value} ({r.key})")
            continue
        choice = parts[-1]
        fam = vars_.get(".".join(parts[:-1] + ["family"]), "*")
        for r in RULES:
            if r.kind in ("deferred", "nested") or r.retired or (r.choice == "*" and r.member == "*"):
                continue
            if fnmatch.fnmatchcase(f"{fam}|{choice}|{_fmt(value)}", r.key) or \
                    (fam == "*" and fnmatch.fnmatchcase(f"{r.family}|{choice}|{_fmt(value)}", r.key)):
                out.append(f"{name}={value} ({r.key})")
    return sorted(set(out))


def _conditional_family_names() -> list:
    return sorted({f.name for _path, f in _every_family() if f.behavior == "conditional"})


# ---- the lint ----------------------------------------------------------------------------------------------

def space_roots() -> list:
    """(slot path, space factory) for every space the library defines,
    the ALU's core partitioning included."""
    from chialu.spaces import (adder_spaces, approx_spaces, checker_spaces, decimal_spaces, div_spaces,
                               dsp_posit_spaces, fma_dot_spaces, fp_spaces, misc_spaces, mul_spaces,
                               redundant_spaces, sfu_spaces, shift_simd_spaces)
    return [
        ("logic", misc_spaces.logic_space), ("rounder", misc_spaces.rounder_space), ("unpacker", misc_spaces.unpacker_space),
        ("adder", adder_spaces.cpa_space), ("incrementer", adder_spaces.incrementer_space),
        ("comparator", adder_spaces.comparator_space),
        ("multiplier", lambda: mul_spaces.mul_space(16)), ("divider", div_spaces.div_space),
        ("divider.seed", div_spaces.seed_table_space), ("divider.final_round", div_spaces.mult_final_round_space),
        ("fp_adder", fp_spaces.fp_add_space), ("fp_multiplier", lambda: fp_spaces.fp_mul_space(11)),
        ("fp_divider", fp_spaces.fp_div_space), ("fp_comparator", fp_spaces.fp_cmp_space),
        ("converter", fp_spaces.fp_cvt_space), ("fp_fma", lambda: fp_spaces.fp_fma_space(11)),
        ("dot", lambda: fma_dot_spaces.dot_acc_space(8)),
        ("shifter", shift_simd_spaces.shifter_space), ("bitcount", shift_simd_spaces.bitcount_space),
        ("subword", shift_simd_spaces.subword_space),
        ("checker", checker_spaces.checker_space), ("checker.comparator", checker_spaces.two_rail_space),
        ("sfu", sfu_spaces.sfu_approx_space), ("sfu.poly", sfu_spaces.poly_datapath_space),
        ("sfu.segment", sfu_spaces.segment_space), ("sfu.range", sfu_spaces.range_reduction_space),
        ("adder", decimal_spaces.decimal_adder_space), ("multiplier", decimal_spaces.decimal_mul_space),
        ("divider", decimal_spaces.decimal_div_space),
        ("representation", redundant_spaces.signed_digit_space), ("channels", redundant_spaces.rns_space),
        ("adder", approx_spaces.approx_adder_space), ("multiplier", lambda: approx_spaces.approx_mul_space(16)),
        ("divider", approx_spaces.approx_div_space),
        ("posit_unit", dsp_posit_spaces.posit_unit_space),
        ("core", _core_space),
    ]


def _core_space():
    from adir.spaces import Space
    from chialu.modules.alu import core_families
    return Space(core_families({}), free_form_allowed=False)


def _every_family() -> list:
    """(slot path, Family) over every space and its component slots."""
    out = []
    seen = set()

    def walk(space, path):
        for f in space.families:
            key = (path, f.name)
            if key in seen:
                continue
            seen.add(key)
            out.append((path, f))
            for slot, sub in f.components.items():
                walk(sub, f"{path}.{slot}")
    for path, factory in space_roots():
        walk(factory(), path)
    return out


def lint() -> dict:
    """Unregistered families, stale rules, unknown predicates and missing
    evidence over every space: the gate is 0 unregistered, 0 stale."""
    fams = _every_family()
    unregistered = [(p, f.name) for p, f in fams if not f.behavior]
    bad_conditional = [(p, f.name) for p, f in fams if f.behavior == "conditional" and not (f.requires and f.evidence)]
    unknown = sorted({n for _p, f in fams for n in f.requires if n not in PREDICATES}
                     | {n for r in RULES for n in list(r.requires) + list(r.under) if n not in PREDICATES}
                     | {n for r in OPTION_RULES for n in r.requires if n not in PREDICATES})
    stale, retired_stale = [], []
    for r in RULES:
        hit = False
        for p, f in fams:
            if not (fnmatch.fnmatchcase(p, r.slot) and fnmatch.fnmatchcase(f.name, r.family)):
                continue
            if r.retired:
                hit = True
                break
            if r.choice == "*":
                hit = True
                break
            for choice, dom in f.design_choices.items():
                if not fnmatch.fnmatchcase(choice, r.choice):
                    continue
                if r.member == "*" or not isinstance(dom, (Enum, Bool)):
                    hit = True
                    break
                members = dom.members() if isinstance(dom, Bool) else list(dom.members_)
                if any(fnmatch.fnmatchcase(_fmt(m), r.member) for m in members):
                    hit = True
                    break
            if hit:
                break
        if not hit:
            (retired_stale if r.retired else stale).append(r.key)
    no_evidence = [r.key for r in RULES if not r.evidence and not r.retired]
    known = [r for r in RULES if all(n in PREDICATES for n in list(r.requires) + list(r.under))]
    # a deferred rule names a predicate nothing evaluates; every other rule's predicates are evaluable over the
    # contract or lowered from a sibling; a nested rule is a choice-level rule on a bare sibling choice
    deferred_bad = [r.key for r in known if r.kind == "deferred" and all(PREDICATES[n].evaluable for n in r.requires)]
    not_evaluable = [r.key for r in known if r.kind != "deferred" and not r.retired
                     and any(not PREDICATES[n].evaluable for n in r.requires)]
    under_bad = [r.key for r in known if any(PREDICATES[n].holds is None for n in r.under)]
    nested_bad = [r.key for r in known if r.kind == "nested"
                  and (r.member != "*" or r.choice == "*"
                       or not any(PREDICATES[n].sibling and "." not in PREDICATES[n].sibling[0] for n in r.requires))]
    sibling_unresolved = _unresolved_siblings(known, fams)
    counts = {}
    distinct = {}
    for _p, f in fams:
        distinct.setdefault(f.name, f.behavior or "unregistered")
    for b in distinct.values():
        counts[b] = counts.get(b, 0) + 1
    ok = not (unregistered or stale or retired_stale or unknown or bad_conditional or no_evidence or deferred_bad
              or not_evaluable or under_bad or nested_bad or sibling_unresolved)
    return {"families": len(distinct), "nodes": len(fams), "counts": counts, "unregistered": unregistered, "stale": stale,
            "retired_stale": retired_stale, "unknown_predicates": unknown, "bad_conditional": bad_conditional,
            "no_evidence": no_evidence, "deferred_evaluable": deferred_bad, "not_evaluable": not_evaluable,
            "under_not_over_contract": under_bad, "nested_bad": nested_bad, "sibling_unresolved": sibling_unresolved,
            "rules": len(RULES), "retired": sum(1 for r in RULES if r.retired),
            "deferred": sum(1 for r in RULES if r.kind == "deferred"),
            "conditioned": sum(1 for r in RULES if r.kind != "deferred" and any(PREDICATES[n].sibling for n in r.requires
                                                                                if n in PREDICATES)),
            "ok": ok}


def _unresolved_siblings(rules: list, fams: list) -> list:
    """(rule key, sibling path) for every sibling predicate whose path
    names no choice the spaces declare: a `<slot>.<choice>` path needs a
    root slot of that name whose families declare the choice (`family`
    is every slot's), and a bare path needs the rule's own family to
    declare the choice."""
    roots = {p: factory for p, factory in space_roots()}
    out = []
    for r in rules:
        for n in r.requires:
            p = PREDICATES[n]
            if not p.sibling:
                continue
            path = p.sibling[0]
            if "." in path:
                slot, choice = path.split(".", 1)
                space = roots.get(slot)
                found = space is not None and (choice == "family"
                                               or any(choice in f.design_choices for f in space().families))
            else:
                found = any(fnmatch.fnmatchcase(sp, r.slot) and fnmatch.fnmatchcase(f.name, r.family)
                            and path in f.design_choices for sp, f in fams)
            if not found:
                out.append((r.key, path))
    return out


def _print_lint(r: dict) -> int:
    print(f"[behavior_rules] {r['families']} families: " + ", ".join(f"{n} {k}" for k, n in sorted(r["counts"].items()))
          + f"; {r['rules']} rules ({r['retired']} retired, {r['conditioned']} on a sibling, {r['deferred']} deferred); "
          f"{len(r['unregistered'])} unregistered, {len(r['stale']) + len(r['retired_stale'])} stale")
    for k in r["not_evaluable"]:
        print(f"  RULE WITH A PREDICATE NOTHING EVALUATES (make it deferred): {k}")
    for k in r["under_not_over_contract"]:
        print(f"  RULE WHOSE `under` NAMES A PREDICATE NOT OVER THE CONTRACT: {k}")
    for k in r["nested_bad"]:
        print(f"  NESTED RULE NOT OF THE FORM family|choice|* ON A BARE SIBLING CHOICE: {k}")
    for k, path in r["sibling_unresolved"]:
        print(f"  SIBLING PATH NAMES NO CHOICE OF THE SPACES: {k}: {path}")
    for p, n in r["unregistered"]:
        print(f"  UNREGISTERED: {p}: {n}")
    for k in r["stale"]:
        print(f"  STALE RULE: {k}")
    for k in r["retired_stale"]:
        print(f"  STALE RETIRED RULE (its family left the space): {k}")
    for n in r["unknown_predicates"]:
        print(f"  UNKNOWN PREDICATE: {n}")
    for p, n in r["bad_conditional"]:
        print(f"  CONDITIONAL WITHOUT REQUIRES OR EVIDENCE: {p}: {n}")
    for k in r["no_evidence"]:
        print(f"  RULE WITHOUT EVIDENCE: {k}")
    for k in r["deferred_evaluable"]:
        print(f"  DEFERRED RULE WHOSE PREDICATES ARE EVALUABLE: {k}")
    return 0 if r["ok"] else 1


def _print_table():
    for p, f in _every_family():
        extra = ""
        if f.behavior == "conditional":
            extra = f"  requires {', '.join(f.requires)}  [{f.evidence}]"
        print(f"{p:28s} {f.name:40s} {f.behavior or 'UNREGISTERED':12s}{extra}")


def _print_rules():
    for r in RULES:
        req = ", ".join(r.requires) if r.requires else ("(retired: " + r.reason + ")" if r.retired else "(numeric: fixed-only)")
        if r.under:
            req += " under " + ", ".join(r.under)
        print(f"{r.kind:9s} {r.slot:12s} {r.key:64s} {req}")
    for r in OPTION_RULES:
        print(f"option    {r.option + ': ' + str(r.value):77s} {', '.join(r.requires)}")


def _print_report(path: str) -> int:
    from adir.instance import load
    inst = load(path)
    rep = (inst.elaboration.info or {}).get("behavior_report") or {}
    for r in rep.get("removed", []):
        where = f" [{', '.join(r['indexes'])}]" if r["indexes"] else ""
        print(f"{r['kind']:12s} {r['variable']}{where}: {r['member']}: {r['reason']}")
    for d in rep.get("defaults_changed", []):
        print(f"default      {d['variable']}: {d['from']!r} -> {d['to']!r}")
    for d in rep.get("deferred", []):
        print(f"deferred     {d['variable']}: {d['rule']} ({d['evidence']})")
    for d in rep.get("disagreements", []):
        print(f"disagreement {d['variable']}: {d['member']}: admitted by {d['admitting']}, excluded by {d['excluding']}")
    for d in rep.get("conditioned", []):
        print(f"condition    {d['variable']}: {d['member']} while {d['sibling']} in {d['allowed']}: {d['reason']}")
    for d in rep.get("nested", []):
        print(f"nested       {d['variable']}: under {d['sibling']} in {d['allowed']}: {d['reason']}")
    for d in rep.get("not_lowered", []):
        print(f"not lowered  {d['variable']}: {d['rule']}: {d['why']}")
    print(f"[behavior_rules] {len(rep.get('removed', []))} removed, {len(rep.get('defaults_changed', []))} defaults changed, "
          f"{len(rep.get('conditioned', []))} member conditions, {len(rep.get('nested', []))} nested choices, "
          f"{len(rep.get('deferred', []))} deferred rules, {len(rep.get('disagreements', []))} disagreements, "
          f"{len(rep.get('not_lowered', []))} not lowered")
    return 0


def _print_defects(path: str) -> int:
    """The archive records whose conformance failed on a declaration the
    rules admitted a conditional member of."""
    import json
    n = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            outputs = rec.get("outputs") or rec.get("metrics") or {}
            conf = outputs.get("conformance") if isinstance(outputs.get("conformance"), dict) else \
                {k[len("conformance."):]: v for k, v in outputs.items() if str(k).startswith("conformance.")}
            if conf and conf.get("rule_defect_candidate"):
                n += 1
                print(f"{rec.get('candidate_id', '?')}: {conf.get('rule_members')}: {str(conf.get('detail', ''))[:160]}")
    print(f"[behavior_rules] {n} conformance failure(s) on declarations the rules admitted")
    return 0


def main(argv=None) -> int:
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "lint"
    if cmd == "lint":
        return _print_lint(lint())
    if cmd == "table":
        _print_table()
        return 0
    if cmd == "rules":
        _print_rules()
        return 0
    if cmd == "report" and len(argv) > 1:
        return _print_report(argv[1])
    if cmd == "defects" and len(argv) > 1:
        return _print_defects(argv[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
