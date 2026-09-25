"""The HintedPrefetcher template: what a candidate may declare.

The hardware is the paper's -- an L1D ensemble whose members are fixed,
a hint table in memory, a buffer caching it on chip. What the search
decides is the program that fills the table, plus the four hardware
parameters below. The model hyper-parameters of the original design are
gone: there is no model.
"""
from __future__ import annotations

from adir import Enum, IntRange, Template, Variable

FIXED = ("fixed",)
SEARCHED = ("fixed", "search")

MEMBERS = ("none", "next_line", "ip_stride", "streamer", "ampm", "sandbox", "sms")

HintedPrefetcher = Template(
    name="pfllm.HintedPrefetcher",
    doc="An L1D prefetcher ensemble steered by a per-load-PC hint table that a "
        "program, written by the search, derives from the binary's disassembly.",
    variables=[
        Variable("cache_level", Enum(("L1D", "L2C")), FIXED,
                 doc="the ensemble sits at L1D, as in the paper"),
        Variable("api", Enum(("champsim_modules",)), FIXED,
                 doc="ChampSim's module interface: prefetcher_cache_operate / _fill"),
        Variable("isa", Enum(("x86_64",)), FIXED,
                 doc="a 48-bit virtual PC indexes the hint table"),
        Variable("hint.bits", IntRange(4, 16), FIXED,
                 doc="bits per hint: 4 selection + 2 degree + 2 filter"),
        Variable("hint.degree_levels", IntRange(1, 3), FIXED,
                 doc="1, 2, 3 map to the first quartile, the median and the third "
                     "quartile of the selected member's own native degree range"),
        Variable("hint.fields", Enum(("SDF", "SD", "S")), SEARCHED,
                 doc="which hint fields the orchestrator applies: selection, "
                     "selection+degree, or all three"),
        Variable("hint.default", Enum(("none", "next_line", "ip_stride", "streamer")), SEARCHED,
                 doc="the reserved entry: the policy used while a buffer miss is served"),
        Variable("ensemble", Enum(("full", "reduced")), SEARCHED,
                 doc="full: every member; reduced: the four the generator selects most often"),
        Variable("phb.entries", Enum((256, 128, 512)), SEARCHED,
                 doc="entries in the on-chip hint buffer"),
    ],
    comment_syntax={"python": "#"},
)
