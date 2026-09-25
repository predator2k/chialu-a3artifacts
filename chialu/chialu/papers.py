"""chiALU paper database.

The registry of record for MICROARCHITECTURES is the spaces layer
(family x choices x slots) plus one description md per family under
knowledge/arch/ (chialu.archdocs). This module keeps the two paper-
level artifacts that survive that design:

* Bibliography: parsed from the `## bibliography` sections of the
  legacy/knowledge/bib/*.md, one per domain, the single authoritative
  place a citation lives (entries tagged [unverified] carry
  verified=False). Handles also key the collected PDFs in
  legacy/knowledge/pdf/.
* Presets: a SMALL curated table of famous named designs (the RS/6000
  LZA, the TPU-v1 MAC, ...), each a family with pinned choices,
  invokable from a run file as `<path>: {preset: <handle>}` at the slot
  the design belongs to. Everything else is expressed directly as family
  and choice variables.
"""
from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass

from adir import Preset

KB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "legacy", "knowledge", "bib")


@dataclass(frozen=True)
class PaperRef:
    handle: str
    ref: str            # Authors, "Title", Venue, Year
    note: str = ""
    verified: bool = True


@dataclass(frozen=True)
class PaperVariant:
    """One paper's exact architecture: a family with pinned choices, and
    pinned choices of the component slots it opens."""
    handle: str
    paper: str          # PaperRef handle
    spec: dict          # {family, pin: {choice: value}, components: {slot: {...}}}
    note: str = ""

    def bindings(self, prefix: str = "") -> dict:
        """The fixed bindings the variant pins, relative to a slot."""
        return _flatten(self.spec, prefix)


def _flatten(spec: dict, prefix: str) -> dict:
    out = {}
    p = f"{prefix}." if prefix else ""
    if "family" in spec:
        out[f"{p}family"] = spec["family"]
    for k, v in (spec.get("pin") or {}).items():
        out[f"{p}{k}"] = v
    for slot, sub in (spec.get("components") or {}).items():
        out.update(_flatten(sub or {}, f"{p}{slot}"))
    return out


class PaperDB:
    def __init__(self):
        self.papers: dict[str, PaperRef] = {}
        self.variants: dict[str, PaperVariant] = {}

    def add(self, *items):
        for it in items:
            if isinstance(it, PaperRef):
                self.papers[it.handle] = it
            elif isinstance(it, PaperVariant):
                self.variants[it.handle] = it
            else:
                raise TypeError(f"not a paper object: {it!r}")
        return self

    def variant(self, handle: str) -> PaperVariant:
        if handle not in self.variants:
            raise KeyError(f"unknown paper variant {handle!r} (has: {sorted(self.variants)})")
        return self.variants[handle]

    def presets(self) -> dict:
        """`adir.Preset` objects, one per variant, applicable at any slot
        path (the family and choice names decide whether they fit)."""
        return {h: Preset("", v.bindings(), doc=v.note) for h, v in self.variants.items()}


# Hand-verified seed refs for families whose kb report has not landed
# yet; a kb bibliography entry with the same handle overrides.
_SEED_REFS = (
    PaperRef("sklansky1960",
             'J. Sklansky, "Conditional-Sum Addition Logic", '
             'IRE Trans. Electronic Computers, 1960'),
    PaperRef("kogge_stone1973",
             'P. M. Kogge and H. S. Stone, "A Parallel Algorithm for the '
             'Efficient Solution of a General Class of Recurrence '
             'Equations", IEEE Trans. Computers, 1973'),
    PaperRef("brent_kung1982",
             'R. P. Brent and H. T. Kung, "A Regular Layout for Parallel '
             'Adders", IEEE Trans. Computers, 1982'),
    PaperRef("han_carlson1987",
             'T. Han and D. A. Carlson, "Fast Area-Efficient VLSI '
             'Adders", IEEE Symp. Computer Arithmetic, 1987'),
    PaperRef("booth1951",
             'A. D. Booth, "A Signed Binary Multiplication Technique", '
             'Quart. J. Mech. Appl. Math., 1951'),
    PaperRef("macsorley1961",
             'O. L. MacSorley, "High-Speed Arithmetic in Binary '
             'Computers", Proc. IRE, 1961'),
    PaperRef("wallace1964",
             'C. S. Wallace, "A Suggestion for a Fast Multiplier", '
             'IEEE Trans. Electronic Computers, 1964'),
    PaperRef("dadda1965",
             'L. Dadda, "Some Schemes for Parallel Multipliers", '
             'Alta Frequenza, 1965'),
)

_PRESETS = (
    PaperVariant("kogge_stone1973_prefix", paper="kogge_stone1973",
                 spec={"family": "parallel_prefix",
                       "pin": {"topology": "kogge_stone", "valency": 2,
                               "fanout_cap": 2}},
                 note="minimum depth, unit fanout, maximal wiring"),
    PaperVariant("brent_kung1982_prefix", paper="brent_kung1982",
                 spec={"family": "parallel_prefix",
                       "pin": {"topology": "brent_kung",
                               "wire_track_budget": 1}},
                 note="regular layout, constant wire tracks, +log depth"),
    PaperVariant("wallace1964_tree", paper="wallace1964",
                 spec={"family": "csa_reduction_tree",
                       "pin": {"geometry": "wallace",
                               "counter_kind": "3_2"}},
                 note="reduce every column as early as possible; use at "
                      "a reduction slot"),
    PaperVariant("dadda1965_tree", paper="dadda1965",
                 spec={"family": "csa_reduction_tree",
                       "pin": {"geometry": "dadda",
                               "counter_kind": "3_2"}},
                 note="reduce as late as possible, fewest counters; use "
                      "at a reduction slot"),
    PaperVariant("rs6000_lza", paper="hokenek_1990",
                 spec={"family": "lza",
                       "pin": {"correction_scheme": "post_norm_fine_shift",
                               "operand_source": "carry_save_pair"}},
                 note="the RS/6000 MAF anticipator; fine shift absorbs "
                      "the 1-bit error"),
    PaperVariant("even_seidel_injection", paper="even_2000",
                 spec={"family": "injection"},
                 note="rounding by injection"),
    PaperVariant("amd_k7_goldschmidt", paper="oberman_1999",
                 spec={"family": "goldschmidt",
                       "components": {"final_round":
                                      {"family":
                                       "back_multiply_remainder"}}},
                 note="K7 div/sqrt on the shared FP multiplier, "
                      "back-multiply rounding, ACL2-proved"),
    PaperVariant("bruguera_2020_radix64", paper="bruguera_2020",
                 spec={"family": "digit_recurrence_sqrt_combined",
                       "pin": {"radix": 64, "shared_with_division": True,
                               "speculation_between_subiterations": True}},
                 note="radix-64 as three overlapped radix-4 iterations"),
    PaperVariant("rs6000_maf", paper="montoye_1990",
                 spec={"family": "classic_fma",
                       "pin": {"subsume_fp_add": True}},
                 note="first production fused MAF; FP add as a*1+c"),
    PaperVariant("sohn_2016_dot4", paper="sohn_2016",
                 spec={"family": "multi_term_fused_dot",
                       "pin": {"alignment_strategy": "single_wide_window",
                               "normalization_deferral": "final_only"}},
                 note="fp32 four-term fused dot, one rounding: the "
                      "N=4 reference AI units descend from"),
    PaperVariant("tpu_v1_mac", paper="jouppi_2017",
                 spec={"family": "integer_mac",
                       "pin": {"array_style": "systolic_array",
                               "accumulator_width_bits": 32}},
                 note="256x256 int8 systolic MAC, accumulators sized so "
                      "element sums never round"),
    PaperVariant("ocp_mx32", paper="ocp_mx_2023",
                 spec={"family": "mx_microscaling_dot",
                       "pin": {"block_size_k": 32,
                               "scale_encoding": "e8m0"}},
                 note="the standardized MX point"),
    PaperVariant("ibm_fpu_residue15", paper="lipetz_schwarz_2011",
                 spec={"family": "residue",
                       "pin": {"modulus": 15,
                               "generator_style": "csa_tree"}},
                 note="Power6/7, z10/z196 production FPU checking: "
                      "residue beats duplication and parity on size"),
    PaperVariant("tmr_voted", paper="lyons_vanderkulk_1962",
                 spec={"family": "duplication",
                       "pin": {"replication": 3}},
                 note="voted triple-modular redundancy"),
    PaperVariant("nvidia_sfu_interpolator", paper="oberman_2005",
                 spec={"family": "gpu_multifunction_interpolator",
                       "pin": {"interpolation_degree": 2,
                               "attribute_interpolation_reuse": True}},
                 note="the NVIDIA SFU: quadratic interpolation, "
                      "per-function ROMs, shared with attribute "
                      "interpolation"),
)

def load_kb_bibliography(db: PaperDB, kb_dir: str = KB_DIR) -> int:
    """Parse `handle -> ref` lines from every report's bibliography."""
    n = 0
    for path in sorted(glob.glob(os.path.join(kb_dir, "*.md"))):
        in_bib = False
        with open(path) as f:
            for line in f:
                if line.startswith("## bibliography"):
                    in_bib = True
                    continue
                if in_bib and line.startswith("## "):
                    in_bib = False
                if not in_bib:
                    continue
                m = re.match(r"(?:\*\s*)?([a-z0-9_]+)\s*->\s*(.+)",
                             line.strip())
                if m:
                    ref = m.group(2)
                    verified = "[unverified]" not in ref
                    db.add(PaperRef(m.group(1),
                                    ref.replace("[unverified]", "").strip(),
                                    verified=verified))
                    n += 1
    return n



def _all_spaces() -> list:
    """Every architecture space the library defines (component slots are
    reached recursively by the walker)."""
    from chialu.spaces import (adder_spaces, approx_spaces, checker_spaces, decimal_spaces,
                               div_spaces, dsp_posit_spaces, fma_dot_spaces, fp_spaces,
                               misc_spaces, mul_spaces, redundant_spaces, sfu_spaces,
                               shift_simd_spaces)
    return [
        misc_spaces.logic_space(), misc_spaces.rounder_space(), misc_spaces.unpacker_space(),
        adder_spaces.cpa_space(), adder_spaces.incrementer_space(),
        adder_spaces.comparator_space(),
        mul_spaces.mul_space(16), div_spaces.div_space(),
        div_spaces.seed_table_space(), div_spaces.mult_final_round_space(),
        fp_spaces.fp_add_space(), fp_spaces.fp_mul_space(11),
        fp_spaces.fp_div_space(), fp_spaces.fp_cmp_space(),
        fp_spaces.fp_cvt_space(),
        fma_dot_spaces.dot_acc_space(8),
        # after the dot space: the ALU's fp_fma slot reuses the FMA lineage's family names with its own choices,
        # and the family table keeps the first definition of a name (the dot's, whose variant cards pin its choices)
        fp_spaces.fp_fma_space(11),
        shift_simd_spaces.shifter_space(), shift_simd_spaces.bitcount_space(),
        shift_simd_spaces.subword_space(),
        checker_spaces.checker_space(), checker_spaces.two_rail_space(),
        sfu_spaces.sfu_approx_space(), sfu_spaces.poly_datapath_space(),
        sfu_spaces.segment_space(), sfu_spaces.range_reduction_space(),
        decimal_spaces.decimal_adder_space(), decimal_spaces.decimal_mul_space(),
        decimal_spaces.decimal_div_space(),
        redundant_spaces.signed_digit_space(),
        redundant_spaces.rns_space(),
        approx_spaces.approx_adder_space(), approx_spaces.approx_mul_space(16),
        approx_spaces.approx_div_space(),
        dsp_posit_spaces.posit_unit_space(),
    ]


def build_paper_db() -> PaperDB:
    db = PaperDB()
    db.add(*_SEED_REFS)
    load_kb_bibliography(db)
    db.add(*_PRESETS)
    return db


PAPER_DB = build_paper_db()
PRESETS = PAPER_DB.presets()
