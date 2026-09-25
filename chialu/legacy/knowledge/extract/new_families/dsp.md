# new-family review: dsp

Source bundle: `run/extract/reduce/newfam_dsp.md` (11 proposals). Registry read:
`chialu/spaces/dsp_posit_spaces.py` (both spaces, the ASIC scope ruling in the module
docstring) plus the family lists of `fma_dot_spaces.py`, `fp_spaces.py`,
`mul_spaces.py`, `adder_spaces.py`, and the `newton_raphson` entry of `div_spaces.py`
for the posit-divider slot. Family docs read: `arch/dsp/dsp48_style_slice.md`,
`arch/dsp/hard_fp_dsp.md`, `arch/dsp/posit_adder_multiplier.md`,
`arch/dot/bridge_fma.md` and its `cascade_mul_then_add` variant. No note was needed;
every proposal block carried enough mechanism to classify.

Handle notes for the human:
* `langhammer_2015` (bundle, FPGA 2015) and `langhammer_2015b` (ARITH 2015) are both
  already family papers of `hard_fp_dsp`; the bundle handle is kept below.
* `pasca_2023`, `sommer_2022`, `nguyen_2017`, `lee_2019` and `jaiswal_2019` are already
  cited by `dsp_posit_spaces.py` (the first under `hard_fp_dsp`, the next three under
  `dsp48_style_slice`, the last under `posit_adder_multiplier`).
* `chong_2009` is cited by no space file, but three docs in other domains already use
  it: `arch/dot/bridge_fma.md` (the `cascade_mul_then_add` variant is Chong's
  multiplier-to-adder link), `arch/mul/booth_recoded_parallel/prevention_constant.md`
  (the dual-mode 53x53 tree) and `arch/fp/single_path.md`. `beauchamp_2008` is cited
  by `arch/shift/fpga_mapped.md` and `arch/adder/fpga_carry_chain.md`.
  `beauchamp_2006` and `ho_2009` appear nowhere in the registry today.

Scope notes that decide the buckets:
* The module docstring rules FPGA mapping techniques out of scope and keeps the DSP
  block's own internal ALU architecture in scope. Operand packing into an unchanged
  hard block (four proposals) is mapping; the `dsp48_style_slice` doc already carries
  it as prose ("Virtual packing is the other route to multi-lane use"), so those four
  are absorbed rather than rejected, and no `virtual_packing` choice is proposed.
* The shared subnormal handler is the block's own internal organization, so it becomes
  a choice on `hard_fp_dsp` even though the doc prose already mentions its cost.
* The fp16-adder extraction leaves the block unchanged and remaps exponents in LUTs
  around it, so the scope ruling rejects it.

## absorbed

* dsp_accumulator_addition_packing -> dsp48_style_slice (family prose; hardware analogue `simd_partition`) — the doc already states that the same ports pack five 9-bit additions per block, and the guard-bit and mixed 9/10-bit packing of one 48-bit accumulator addition is use of the unpartitioned ALU rather than a change to it; `simd_partition=dual_half|quad_quarter` is the in-scope hardware form of independent lanes [sommer_2022].
* dsp_multiplier_packing -> dsp48_style_slice (family prose, "virtual packing") — the INT-N packing of offset operands into the one hard multiplier is the packing the doc describes; the overpacking and MR-overpacking modes (negative padding, MSB-restoring correction in 4 to 17 LUTs) extend that prose but stay usage of an unchanged block, which the scope ruling keeps out of the choice set [sommer_2022].
* shared_operand_dsp_mac_packing -> dsp48_style_slice (family prose, "virtual packing") — the doc already gives this mechanism with its numbers: two n-bit products sharing one unsigned operand packed with n separating bits and a guard bit, corrections accumulated outside the block and applied once, 0.5 DSP per 8-bit MAC at 11 LUTs and 12 FFs [nguyen_2017].
* shared_operand_packed_dsp_mac -> dsp48_style_slice (family prose, "virtual packing") — the journal form of the same Double MAC mechanism; the signed-lower-lane correction and the output-channel or spatial lane pairing are the same virtual-lane packing, and `lee_2019` is already a family paper [lee_2019].

## new values

* hard_fp_dsp += choice subnormal_support: {flush_to_zero, dedicated_per_unit, shared_adder_handler} — the block's treatment of subnormal results: flush (the shipped Arria 10 contract), dedicated normalization and rounding in both multiplier and adder (about 4% more DSP area, longer final stage), or the subnormal-capable adder reconfigured per block to accept the multiplier's pre-rounding mantissa, low product bits and modified exponent and to run its shifters, LZC, guard/round/sticky update and rounding on them (about 1%), during which the adder is unavailable for add/accumulate/multiply-add/recursive modes; supported cases are normal-times-normal and normal-times-subnormal underflow. The doc prose already carries the costs; the choice makes them a searchable axis [langhammer_2015]  (from shared_subnormal_handler)
* posit_adder_multiplier += choice operator_set: {add_mul, add_mul_div} — PACoGen's divider reuses the family's decoder and encoder: variable-position field extraction, a significand quotient from a parameterized Newton-Raphson reciprocal, regime/exponent subtraction, normalization, posit reconstruction and RNE at encode. Add a slot `sig_div: div_space()` filled by `newton_raphson` (its `iterations` choice covers the proposal's 1..3; the proposal's lower bound of 0, seed only, is outside the registry's `IntRange(1, 3)`); posit(32,6) at 2 iterations is 12 pipeline stages on a Virtex-7. The proposal's es of 6 also exceeds the family's `es_bits: IntRange(0, 3)`. The alternative is a `posit_divider` family in `posit_unit_space()` mirroring fp's `sig_div_then_round`; by the prefer-new-values rule the choice is proposed, and the deciding question is whether the significand divider deserves its own decode/encode context [jaiswal_2019]  (from posit_divider)

## new families

One family from 4 proposals, placed in `dsp_block_space()` after
`multiprecision_block_proposal`. The alternative is new values on `hard_fp_dsp`
(`fp_format += fp64, fp64_or_dual_fp32`; `+= choice integer_component_access: Bool`;
`+= choice composition`), and the deciding question is whether `hard_fp_dsp` keeps its
identity as the FP overlay on a fixed-point DSP block (Arria 10 line). The registry
already separates the academic `multiprecision_block_proposal` line from the shipped
blocks, and the four proposals are the analogous academic embedded-FPU line of 2006 to
2009, so a family is proposed.

### embedded_fpu_block

Merged from: embedded_fpga_fpu_block (beauchamp_2006), embedded_floating_point_tile
(beauchamp_2008), flexible_embedded_fpu_block (chong_2009),
floating_point_coarse_grained_fpga (ho_2009). The two Beauchamp proposals are the
conference and journal forms of one work. All four place a standalone hard FP block in
dedicated columns of an island-style FPGA and differ in how the block is composed
inside.

* domain: dsp (`dsp_block_space()`)
* doc: "academic embedded-FPU proposals (Beauchamp/Chong/Ho line): a hard fp64 multiply-add block in fabric columns, with dual-fp32, integer-component and subblock-bus variants"
* execution_style: feed_forward (omitted in the snippet, as `dsp_posit_spaces.py` does)
* mechanism: A coarse-grained FP block sits in columns among CLBs and RAMs, horizontal routing crosses it and vertical routing stays at its edge. The Beauchamp block computes fp64 multiply, add or (A*B)+C with optional input/output registers. The Chong block pairs a dual-precision multiplier (53x53 or two 24x24) with a dual-precision adder over a configurable link and exposes multiplier, adder, 64-bit right shifter and 54-bit left shifter for integer use through configuration multiplexers. The Ho unit holds registered FP multiplier and adder/subtractor subblocks plus wordblocks, joined by unidirectional left-to-right bus multiplexers with feedback registers for accumulation; subblock count, type, placement, buses and feedback registers are design-time parameters, and configuration bits select the datapath at runtime.
* choices (each with the proposals that give evidence):
  * `precision: {fp32, fp64, fp64_or_dual_fp32}` [ho_2009 single/double; beauchamp_2006 fp64; beauchamp_2008 fp64 or configurable 2xfp32; chong_2009 one fp64 or two fp32]
  * `composition: {multiply_add_block, linked_multiplier_adder, subblock_bus_array}` [beauchamp_2006, beauchamp_2008 (one block: multiply, add or multiply-add); chong_2009 (multiplier and adder with a configurable link, `multiplier_adder_link`); ho_2009 (several subblocks on a bus, multiplier subblocks placed before adder subblocks)]
  * `integer_component_access: Bool` [chong_2009: none, or multiplier/adder/shifters exposed; dedicated shifter ports allow concurrent shifter and adder use]
  * `io_registers: Bool` [beauchamp_2008 optional input/output registers; beauchamp_2006 output registration; chong_2009 optional I/O registers; ho_2009 registered subblock outputs]
  * `feedback_registers: Bool` [ho_2009 present, for accumulation and right-to-left dependencies; absent in the other three]
* choices deliberately not proposed: `block_height_clbs` (beauchamp: 4 to 160 CLBs, 32 chosen) and `placement_style: column_based` describe the block's footprint and floorplan in the fabric rather than its datapath; `runtime_reconfiguration` and `parameterization_time` (ho) are single-valued; `granularity_mix` (ho) is the host FPGA rather than the block. Add `block_height_clbs: EnumChoice((4, 8, 16, 32, 64, 96, 128, 160))` if the registry wants the footprint as an axis.
* slots: `multiplier: mul_space(53)` (the fp64 significand tree; Chong's dual-mode 53x53 tree is the `booth_recoded_parallel` prevention-constant variant), `adder: cpa_space()`, `shifter: shifter_space()` (the integer-exposed shifters of Chong; `shifter_space` comes from `chialu.spaces.arith_spaces` and needs adding to the import line). The `linked_multiplier_adder` composition is `bridge_fma.composition_style=cascade_mul_then_add` seen from the block level.
* mutations: add_dual_fp32_mode, expose_integer_components, link_multiplier_to_adder, compose_subblocks_on_bus, add_feedback_registers, register_block_boundaries
* handles: beauchamp_2006, beauchamp_2008, chong_2009, ho_2009
* evidence strength: 4 papers (3 distinct works; Beauchamp 2006/2008 are one work), all conference or journal, no textbook or thesis block. Results are VPR-modeled or 0.13 um synthesis: 55% average area reduction and 40.7% speed increase against embedded multipliers over five fp64 benchmarks (beauchamp_2006), 5.2x fp64 area and 5.8x delay improvement (chong_2009), 25x average area reduction over Virtex II (ho_2009).

```python
        Architecture(
            "embedded_fpu_block",
            papers=("beauchamp_2006", "beauchamp_2008", "chong_2009",
                    "ho_2009"),
            design_choices={
                "precision": EnumChoice(("fp32", "fp64",
                                         "fp64_or_dual_fp32")),
                "composition": EnumChoice(("multiply_add_block",
                                           "linked_multiplier_adder",
                                           "subblock_bus_array")),
                "integer_component_access": BoolChoice(),
                "io_registers": BoolChoice(),
                "feedback_registers": BoolChoice()},
            components={"multiplier": mul_space(53),
                        "adder": cpa_space(),
                        "shifter": shifter_space()},
            mutations=("add_dual_fp32_mode", "expose_integer_components",
                       "link_multiplier_to_adder",
                       "compose_subblocks_on_bus",
                       "add_feedback_registers",
                       "register_block_boundaries"),
            doc="academic embedded-FPU proposals (Beauchamp/Chong/Ho "
                "line): a hard fp64 multiply-add block in fabric "
                "columns, with dual-fp32, integer-component and "
                "subblock-bus variants"),
```

## rejected

* embedded_dsp_fp_adder_extraction — an FPGA mapping technique the scope ruling excludes: the hard block is unchanged, and an fp16 add is realized by driving the block's existing low-precision sum-of-products mode (a*1+b*1+(-0)) or its fp32 add mode with LUT exponent remapping around it; `hard_fp_dsp` already cites `pasca_2023` and its `fp_format=fp16_fp32` is the block mode the extraction uses [pasca_2023].

absorbed 4, new values 2, new families 1 (from 4 proposals), rejected 1
