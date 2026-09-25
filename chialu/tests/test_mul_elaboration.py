"""The multiplier generators' text elaborates under the synthesis frontend.

The family selftest simulates under Verilator, which is more lenient than yosys-slang, the frontend
synthesis reads the same text with: it accepts an identifier used before its declaration, which
slang rejects. So a family can pass its selftest and still never synthesize -- recursive_karatsuba
did, at every width and both splits, and all 245 of its database rows failed. The selftest also
never crossed `staggered_tiling` with a narrow `adder_width`, which is the only place a tile is one
bit wide. Each case here is read by `read_slang` alone (no mapping), which takes seconds.
"""
from __future__ import annotations

import shutil
import subprocess

import pytest

from chialu.targets.rtl.families import library_closure, mul

CASES = [
    # a helper adder is placed ahead of the split declarations it reads (mul.karatsuba_sv)
    *[(f"karatsuba_{split}_w{w}", w, True, "recursive_karatsuba",
       {"recursion_depth": 1, "split_kind": split})
      for split in ("two_way", "three_way") for w in (8, 16, 32)],
    ("karatsuba_d2_w16", 16, True, "recursive_karatsuba", {"recursion_depth": 2}),
    # a one-bit tile's sum is declared as a scalar and then indexed (mul.tiled_cpa_reduction_tree):
    # the stagger offset is adder_width // 2, one bit when adder_width is 2 or 3
    *[(f"tiled_staggered_aw{aw}_w{w}", w, s, "booth_recoded_parallel",
       {"reduction.family": "tiled_cpa_reduction_tree", "reduction.adder_width": str(aw),
        "reduction.carry_assimilation": "staggered_tiling"})
      for aw in (2, 3) for w, s in ((16, False), (16, True), (8, True))],
]


@pytest.mark.skipif(shutil.which("yosys") is None, reason="yosys (with the slang frontend) not on PATH")
@pytest.mark.parametrize("name,width,signed,family,pins", CASES, ids=[c[0] for c in CASES])
def test_elaborates_under_slang(name, width, signed, family, pins, tmp_path):
    top, text, _ = mul.mul_sv(width, signed, family, pins)
    src = tmp_path / f"{name}.sv"
    src.write_text(library_closure(text) + "\n" + text)
    r = subprocess.run(["yosys", "-p", f"read_slang --top {top} {src}"],
                       capture_output=True, text=True, timeout=300)
    errors = [l for l in (r.stdout + r.stderr).splitlines() if ": error:" in l]
    assert r.returncode == 0 and not errors, "\n".join(errors[:6]) or r.stderr[-800:]
