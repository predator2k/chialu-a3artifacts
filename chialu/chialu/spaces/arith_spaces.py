"""Shared arithmetic architecture spaces (design rev 4, §9.5, §11).

The reusable card sub-libraries units compose: carry-propagate adders,
adder trees, multipliers. Each factory returns a fresh Space;
families open component slots recursively (a Wallace multiplier opens a
`cpa` slot; a shift-add multiplier opens an `adder_tree` slot whose
csa_tree family opens a `final_cpa` slot). The full reachable tree is
disclosed to the agent even when the instantiation controls nothing —
the agent cannot explore what it was never told exists.
"""

from adir import Enum, Range
from adir.spaces import Family, Space


def cpa_space() -> Space:
    """Delegates to the survey-complete adder knowledge base
    (adder_spaces.py; lazy import breaks the module cycle)."""
    from chialu.spaces.adder_spaces import cpa_space as _as
    return _as()


def adder_tree_space() -> Space:
    """Multi-operand accumulation; csa_tree keeps carries redundant and
    opens a final_cpa slot — recursion into cpa_space."""
    return Space(families=[
        Family("linear_chain", behavior="neutral", doc="operands added in sequence"),
        Family("binary_tree", behavior="neutral",
                     components={"cpa": cpa_space()},
                     doc="balanced tree of two-input adders"),
        Family("csa_tree", behavior="neutral",
                     design_choices={
                         "compressor": Enum(("3:2", "4:2", "7:3"))},
                     components={"final_cpa": cpa_space()},
                     doc="carry-save reduction; one CPA at the root"),
    ])


def div_space(width: int = 24) -> Space:
    """Delegates to the survey-complete divider knowledge base
    (div_spaces.py; lazy import breaks the module cycle)."""
    from chialu.spaces.div_spaces import div_space as _ds
    return _ds(width)


def shifter_space() -> Space:
    """Delegates to the survey-complete shifter knowledge base
    (shift_simd_spaces.py; lazy import breaks the module cycle)."""
    from chialu.spaces.shift_simd_spaces import shifter_space as _ss
    return _ss()


def mul_space(width: int) -> Space:
    """Delegates to the survey-complete multiplier knowledge base
    (mul_spaces.py; lazy import breaks the module cycle)."""
    from chialu.spaces.mul_spaces import mul_space as _ms
    return _ms(width)


def component_mul_space(width: int) -> Space:
    """The multiplier families a component slot can bind: mul_space without
    twin_precision_subword, which packs the unit's lanes into one matrix
    and has no module of its own."""
    return Space([f for f in mul_space(width).families if f.name != "twin_precision_subword"], free_form_allowed=False)
