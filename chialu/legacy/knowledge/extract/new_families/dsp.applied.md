# dsp plan: applied

Plan: `chialu/knowledge/extract/new_families/dsp.md`, plus the two
`hard_fp_dsp` lines under `## deferred (other file)` in
`new_families/dot.applied.md`. File edited: `chialu/spaces/dsp_posit_spaces.py`
only (rev 7 to rev 8). Rulings applied without re-opening: the FPGA-mapping
ruling in the module docstring (operand packing stays prose under
`dsp48_style_slice`, the `pasca_2023` adder extraction stays rejected, no
block-footprint choice), no FPU-level, core-level or pulse-counting family, no
ALU-level line on an adder family. `ho_2009` stays at
`composition=subblock_bus_array`. No retired handle appears in the plan;
`langhammer_2015` (the FPGA 2015 bundle paper) and `langhammer_2015b` (the
ARITH 2015 paper) are both already in `hard_fp_dsp.papers`, and no `papers=`
tuple of an existing family needed a new handle.

## applied

New values (3 lines, 2 families; every cited handle was already in the
family's `papers=`):

* `hard_fp_dsp += choice subnormal_support: {flush_to_zero, dedicated_per_unit, shared_adder_handler}` [langhammer_2015]; mutation `share_adder_as_subnormal_handler` added.
* `hard_fp_dsp += choice chain_topology: {linear_accumulate, recursive_tree}` [langhammer_2015b] (dot deferred line). The dedicated inter-block connections and the block's multiplier/adder role modes are block architecture beside `dsp48_style_slice.cascade_paths`, so the FPGA-mapping ruling admits it; `accumulate_chain=True` is the linear case and `accumulate_chain=False` leaves the choice moot. Mutation `compose_recursive_tree_over_chain` added.
* `posit_adder_multiplier += choice operator_set: {add_mul, add_mul_div}` with slot `sig_div: div_space()` [jaiswal_2019]; mutation `add_divider_behind_shared_decode` added. `div_space` is imported at top level from `chialu.spaces.div_spaces`; `div_spaces` imports only `arith_spaces` and `sfu_spaces`, neither of which imports `dsp_posit_spaces`, and both import orders succeed. The slot's `newton_raphson.iterations` is `IntRange(1, 3)`; the proposal's seed-only lower bound of 0 and its es of 6 stay outside the family, as the plan states.

New family (1, from 4 proposals):

* `embedded_fpu_block` inserted after `multiprecision_block_proposal` in `dsp_block_space()`, snippet as in the plan: choices `precision`, `composition`, `integer_component_access`, `io_registers`, `feedback_registers`; slots `multiplier: mul_space(53)`, `adder: cpa_space()`, `shifter: shifter_space()`; six mutations; `papers=` beauchamp_2006, beauchamp_2008, chong_2009, ho_2009, all in `PAPER_DB`; feed-forward by default. `shifter_space` joins the `arith_spaces` import line.
* Docs: `chialu/knowledge/arch/dsp/embedded_fpu_block.md` (first paragraph 692 characters, 344 words after it, four references copied from the bundle), `chialu/knowledge/extract/gaps/embedded_fpu_block.md` = none.

Variant docs written (6), each with front matter `family:` + `pin:`, a first
paragraph under 500 characters, 87 to 116 words after it, and citations copied
verbatim from `run/extract/reduce/newfam_dsp.md` (`langhammer_2015b` from
`run/extract/reduce/newfam_dot.md`, which carries the evidence for the chain
line):
* `chialu/knowledge/arch/dsp/embedded_fpu_block/multiply_add_block.md` (beauchamp_2006, beauchamp_2008)
* `chialu/knowledge/arch/dsp/embedded_fpu_block/linked_multiplier_adder.md` (chong_2009)
* `chialu/knowledge/arch/dsp/embedded_fpu_block/subblock_bus_array.md` (ho_2009)
* `chialu/knowledge/arch/dsp/hard_fp_dsp/shared_adder_handler.md` (langhammer_2015)
* `chialu/knowledge/arch/dsp/hard_fp_dsp/recursive_tree.md` (langhammer_2015b)
* `chialu/knowledge/arch/dsp/posit_adder_multiplier/add_mul_div.md` (jaiswal_2019)

Every bare variant name resolves uniquely in `variant_table()`.

## skipped

* `hard_fp_dsp += choice chain_routing: {dedicated_chain, balanced_soft_routing}` [langhammer_2015b] (dot deferred line) — `balanced_soft_routing` is soft-fabric routing with balanced logic-register depths around unchanged blocks, which the FPGA-mapping ruling excludes, and `dedicated_chain` is `accumulate_chain=True`; the family doc already carries the soft-register case as prose.
* Absorbed (4) and rejected (1) entries of the plan — nothing to do in this file.
* `block_height_clbs`, `placement_style`, `runtime_reconfiguration`, `parameterization_time`, `granularity_mix` — not proposed by the plan (footprint, floorplan, single-valued, or host-FPGA properties); the scope ruling rules out a block-footprint choice.
* Widening `posit_adder_multiplier.es_bits` past 3 or `newton_raphson.iterations` below 1 — the plan notes the mismatch and proposes no widening.
* The `posit_divider` family alternative in `posit_unit_space()` — the plan chose the choice by the prefer-new-values rule.
* New values on `hard_fp_dsp` (`fp_format += fp64, fp64_or_dual_fp32`, `integer_component_access`, `composition`) as the alternative to the family — the plan chose the family.
* No variant doc for `subnormal_support=flush_to_zero` (the shipped contract, a baseline) or `dedicated_per_unit` (a cost point rather than a named structure), for `chain_topology=linear_accumulate` (the existing `accumulate_chain=True` structure), for `operator_set=add_mul` (the existing family), for the `precision` values (mode settings; the dual-mode 53x53 tree is the `booth_recoded_parallel/prevention_constant` variant in mul), or for the Bool choices.
* Existing family docs `hard_fp_dsp.md` and `posit_adder_multiplier.md` were not edited; `hard_fp_dsp.md` already names the shared subnormal handler and the recursive reduction tree in prose, and `posit_adder_multiplier.md` does not mention the divider.

## deferred (other file)

none — every plan line and both dot-deferred lines target `dsp_posit_spaces.py`.

## checks

* `python3 -c "from chialu.papers import _all_spaces; s=_all_spaces(); print(len(s))"` prints 36.
* `python3 -m chialu.archdocs`: `[archdocs] 232 docs for 232 families; 0 undocumented; 428 variant docs`, exit 0, no ORPHAN / BAD REF / BAD VARIANT lines. `--strict` lists no family of this plan.
* `python3 -m chialu.extract vocab > /dev/null` exits 0.
* `kb_section_alu16()` renders.
* Every handle in every `papers=` tuple of `dsp_block_space()` and `posit_unit_space()` exists in `PAPER_DB`.
* `import chialu.spaces.div_spaces, chialu.spaces.dsp_posit_spaces` and the reverse order both succeed.

applied 3 new-value lines (2 families) + 1 family (4 proposals) + 1 family doc + 6 variant docs, skipped 8 items, deferred 0 lines
