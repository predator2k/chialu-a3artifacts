# Work plan

This plan lists the work the discussions of 2026-09-12 decided, in the
order it should be done, with the decision each item rests on. Each
item carries its state; item 1 was done on 2026-09-12 and the others
are listed and not started. The evaluation (`docs/evaluation-plan.md`)
is on hold until items 2 to 5 are done.

## 1. Scope and hiding

State: done on 2026-09-12 (`docs/deferred-families.md` records the
result).

The scope is single-cycle combinational units in this version
(README, `docs/formats-and-options.md` section 1). The 21 families whose
structure needs cycles, or which are methods or kernels, are deferred
(`docs/deferred-families.md`). The same rule is extended to:

1. **The choice-level sequential options**: `trap_to_software` (fp
   subnormal slot), `shared_multiplier` (SFU evaluator),
   `microcoded_fpu_sequence` (SFU sharing), `folded_sequential` (cordic
   topology), `msdf_online_serial` (transformer_activation_lut method),
   `sequential_reuse` (add_table_add table_access),
   `bit_serial_composable` (integer_mac array_style),
   `compensated_two_sum` and `ordered_fp_loop_lookahead`
   (streaming_accurate_accumulator approach). Each value leaves its enum
   (or its sub-slot space), its variant card moves under
   `legacy/knowledge/deferred/`, and `docs/deferred-families.md` records
   it.
2. **The three groups no unit opens or that are exceptions at the core
   level**: the on-line families (`online_space`: online_arithmetic_unit,
   online_pipeline_composition, redundant_cordic, bit_serial_dnn_datapath)
   with the core families `online_msdf_core` and `merged_mul_div`;
   `dsp_block_space` (6 families); `decimal_misc_space` (9 families).
   Their spaces, cards and variant cards move to legacy the same way;
   `chialu/papers.py` and `chialu/extract.py` drop them from
   `_all_spaces()`.

## 2. The coverage check of the generators against the spaces

State: the tool exists (`chialu/targets/rtl/families/coverage.py`,
added 2026-09-12); it is the done criterion of item 3 and runs clean on
the kinds item 3 has covered so far.

The two hand audits of `docs/slot-audit.md` are replaced by a tool that
answers the same questions mechanically and runs as a selftest:
`python3 -m chialu.targets.rtl.families.coverage`. It walks every space
a template opens, including the sub-slot spaces, and reports per family,
slot and choice:

* **Family coverage**: every family has a module (`has_module`, extended
  to the sub-slot kinds: lzc, align, norm, rounding, subnormal,
  seed_table, qds, final_round, segment, evaluator, ...) or a documented
  exception with its reason.
* **Slot coverage**: for every declared slot, the consuming generator
  reads `<slot>.family` and can instantiate every member of the slot's
  domain; a slot no generator reads, a domain the helper rejects in part,
  and a slot whose space is not the space the generator consumes are
  each reported.
* **Undeclared pins**: every pin a generator reads is declared by the
  space, so the planner can bind it and the database can characterize
  it. The check records pin reads by handing the generator a pins
  dictionary that logs every key it looks up.
* **Choice sensitivity**: every enum member of every design choice is
  read by the generator and changes the module text, or is documented as
  a no-op with a reason; a value that falls through silently to another
  (booth radix 16, the reduction geometries, the 5:2 and 7:3 counters,
  the msdf comparator structures, `coefficient_adapted` outside degrees
  3 to 4, `fma_based`) is reported.
* **Component realization**: inside every generated module, a component
  of a library kind is a library instance chosen by a slot pin; a
  hard-coded family and behavioral text for a library kind are reported
  (the classes B and C of the audit), and a simulation-only fallback is
  admitted only where it does not change the synthesized structure.
* **Module naming**: two pin sets that render different texts never
  share a module name (the `dedupe_modules` collision of the fp add and
  mul names).
* **Family distinctness** (not implemented, found on 2026-09-13): two
  families of a kind never render the same body at the same geometry,
  or the pair is allowlisted with its reason. A scan of every kind at
  16 bits, comparing the texts with the comments removed, found seven
  groups. The adder's 18 families, the multiplier's 17 and every other
  kind's are distinct.

  The scan takes each family's first registered point. The SFU's 22
  families and every other kind's are distinct.

  | Kind | The families that render one body | What it means |
  | --- | --- | --- |
  | rounder | dedicated_per_op, shared_per_lane, shared_across_formats | the family is where the rounder sits in the unit, not what the module contains, so one module text serves all three; the seed's instantiation count differs |
  | unpacker | per_unit_unpack, shared_per_lane, shared_across_formats | the same placement question |
  | logic | lane_replicated_gates, wide_gate_row | a bitwise row over one lane is a wide row |
  | dot | pairwise_tree, integer_mac, kulisch_long_accumulator, bf16_fma_datapath, fp8_training_datapath | the geometry's frame is already a long exact accumulator, so the families coincide there |
  | divider | srt_radix2, digit_recurrence_sqrt_combined | the combined recurrence's module for the divider kind is its divide half, which at radix 2 is the SRT radix-2 divider; its square-root half is the fp_sqrt kind's, and the sharing is the unit's, which asks for both operations |
  | fp_divider | sig_div_then_round, sig_sqrt_then_round | a defect, fixed: `fp_div_space` carries both families and the fp_divider realizer builds a divider whatever family it is handed, so the square-root family entered as a divider's measurement under its own name; each kind now takes the families it realizes |
  | posit_unit | posit_adder_multiplier, posit_ieee_interop | the interop family's converters are the seed's, which the coverage allowlist already records for its `interop_style` and `conversion_direction` choices; the unit module is the decoder and encoder either way |

  The scan also found that no SFU point could be generated at all, which
  is fixed: the SFU's points now come from the characterization table,
  since its generator needs the function and the format, and the space
  carries neither. A dense build would have written a failed row for
  every one of them.

  Two were defects and are fixed: `low_power_gated` rendered
  `single_path`'s text at its `datapath_partitions` default of one,
  which is no gating, so the generator's default is two; and
  `kulisch_long_accumulator`'s header named a 512-bit word it did not
  build.
* **Menu honesty**: the `[library]` mark, `has_module` and the existence
  of a module agree for every family.

The tool prints a table with a verdict per row and file:line evidence,
and fails when any row is neither clean nor covered by an allowlist
entry that names its reason. The allowlist starts empty apart from the
documented exceptions.

## 3. Fixing every gap of the two audits

State: open again for the dot and the SFU kinds (2026-09-14). A
whole-repository sweep finished for the first time on 2026-09-13, once
the tool could bound a family's sweep, and it found that the dot kind is
not clean: three dot families alone report 115 findings (54 choice, 42
component, 19 slot), and 15 more dot families and 21 SFU families take
longer than four minutes each, so no earlier run had ever swept them.
The claim below that every kind is clean rests on the per-kind runs that
did finish, which are every kind except dot, sfu, divider and
fp_divider. `block_fp_accumulation` is the clearest case: `block_size`,
`exponent_sharing_granularity`, `inter_block_accumulate` and every pin
of its `lza` slot leave the module's text unchanged at the block
geometry the sweep probes.

State of the rest: done (2026-09-13). Every other kind reports zero
findings under the coverage check of item 2; the work ran generator by generator, each kind
clean before the next. Done: the leaf kinds (the shifters, the bit
counters, the comparator, the logic row), the adder kind (the
carry-propagate adders) and the dot kind (the accumulators and the FMA
lineage, with item 4's structures) and the multiplier kind (its batch
merged on 2026-09-12 evening; `docs/deferred-families.md` records the
choices and slots removed and the ones realized per batch). In
merged: the float kinds (the float fork's batch, 2026-09-12 night) and
the special functions (the `Net` primitives bound to library families).
Done as well: the approximate, decimal, subword, posit, redundant, RNS,
checker and divider families (2026-09-12 night and 2026-09-13). Every
kind now reports zero coverage findings, so item 3's criterion is met;
what remains under it is the periodic re-run of the check as the
generators change.

Every finding of `docs/slot-audit.md` is fixed, not the first five
alone; the coverage check of item 2 is the done criterion. By class:

* **Inlined components of a library kind (class C-no-slot)**: the dot
  accumulators' normalization shifter, leading-zero counter, alignment
  shifter, frame moves and kulisch segment chain; the dividers' operand
  scaling, quotient de-scaling, iteration adders, SRT assimilation and
  restoring square root; the decimal Newton shifts and digit normalize;
  the fp rounder's masks and shifts, the align sticky mask, the fused
  multiplier's injection adders; the posit regime word and the PLAM
  adder; Karatsuba's adders; Mitchell's normalize and log adder; the RNS
  channel multiplier and Booth row sum; the checkers' residue and AN
  arithmetic; and the SFU's `Net` primitives (every multiply, add,
  variable shift and leading-zero count), which get a slot binding so a
  declared multiplier, adder, shifter or counter family renders through
  the library. Each becomes a slot-chosen library instance, or is listed
  in the allowlist with its reason.
* **Hard-coded families (class B)**: the unpacker's and rounder's
  counters, shifters and incrementers, the `compound_flagged_prefix` of
  the compound adders, the posit constants `LZC_FAMILY` and
  `SHIFTER_FAMILY`, the dividers' `lzd_cell_tree`, the cascade rounders,
  `prefix_and_incrementer` everywhere: each gets a declared slot, or the
  space records that the family fixes it.
* **Ignored slots (about 25 sites)** and **undeclared pins (11)**: each
  slot is read or removed from the space; each undeclared pin is declared
  (the signed-digit `cpa`, `norm.lzc`, `lod`, `cross`, `exact`,
  `segment`, the decimal dividers' `multiplier`, softmax's `divider`,
  the fp unpacker's and rounder's kinds).
* **Mistyped and narrowed domains**: `direct_polynomial.approximator`,
  `dynamic_segment.core_multiplier`, the `cpa` pin path of the approximate
  multipliers, `reduction.family`, `block_adder_space` at seven sites,
  `lzc_space` against `lzd_cell_tree`, the `converter` kind's family, the
  posit unit's two slots, the kulisch width range, the checker comparator
  domain and the comparator slot of every checker family, the residue
  `generator_style`, the dot checker's comparator.
* **Choice-level fallthroughs** are realized or documented (item 2's
  choice sensitivity lists them).
* **Module names** carry every pin that affects the text.
* **The `[library]` mark** follows the existence of a module
  (`alu_pg_fused`).

## 4. The dot accumulators

State: done (2026-09-13). The fp_alu profile of the last bullet closed
it.

* The accumulator families read their `align`, `lza` and `norm_shifter`
  slots (the alignment shifter, the anticipator or counter of the final
  normalization, the normalize shifter), the tensor-core and fp8
  datapaths their `round` slot, and `SHIFTER_LIBRARY_MAX` rose from 128
  to 320 bits, so the fp16 x fp32 frame and every bounded window render
  the library shifter. The `_cpa_of` default is the sklansky prefix
  adder until item 5's database answers "the fastest adder at this
  width"; the choice then moves to a query.
* The bounded alignment (`bounded_align` of the dot's alignment space,
  `families/dot.py` `BandGeom`): the products in their exponent band,
  the addend in a near window around it (a sticky and a borrow below it,
  by `sticky_method` and the `tzc` slot) or in a far word (the products'
  sum as a sticky and a borrow), a zero products' sum bypassed to the
  addend; exact to the X's last bit (the card `arch/fp/bounded_align.md`
  gives the argument). On fp16 x fp32 with four products the near
  window is 193 bits against the 281-bit frame.
* `exponent_sorted_realignment_lines` under the correctly-rounded
  contract builds the lines its card describes: T lines of
  Wt + L + XW - 2 bits, a realignment line opened by a gap of
  Wt + L + XW - 1, the first nonzero cluster selected after the one add
  (its card gives the construction and the widths per geometry).
* The kulisch width range is 64 to 4288 bits in steps of 32.
* Two latent defects found by the new directed vectors are fixed: a
  product normalized before the alignment (multi_term_fused_dot's
  per-term deferral) can have its lsb below the frame, so its alignment
  shifts right as well; the FMA lineage normalizes its multiplier
  operands at entry, since a subnormal operand's product put the X's low
  bits below the window's guard bits. The X conversion of a windowed sum
  uses the floor convention (a negative floor with a nonzero fraction
  has its one's complement as magnitude), which the earlier code got
  wrong by one lsb.
* The fp_alu seed's 6.8 ns is profiled by cut synthesis per stage
  (`chialu/profile.py`, 2026-09-13 on nangate45 at the run file's 20 ns
  target, medium effort). The seed maps to 6843 ps and 7953 um2. The
  delay is the behavioral float structures of the fp16 lane, not the
  mode decode or the flag logic:

  | stage | the cut's wire | delay ps | the stage adds |
  | --- | --- | --- | --- |
  | unpack | `xa_m0_m0_m0_l0_unpacker` | 168 | 168 |
  | significand add | `x_m0_m0_m0_l0_fp_adder` | 4187 | 4009 |
  | round | `y_m0_m0_l0_rounder` | 7774 | 3646 |
  | mode and op select | `y` | 7003 | the mux costs nothing measurable |
  | the flag path | `flags` | 6777 | -212 |

  Each structure alone, against the library's own fp16 rows: the seed's
  fp adder is 6860 ps against 2590 ps for two_path, its rounder 4147 ps
  against 3869 ps for dedicated_per_op, its multiplier 3336 ps against
  844 ps for sig_mul_then_round, its unpacker 345 ps against 198 ps for
  per_unit_unpack. The seed's add and round chain is 7.8 ns where the
  library's complete fp adder is 2.6 ns, so realizing the declared
  families is the whole of the difference and the decode around them is
  under 0.3 ns. A cut maps on its own, so the deepest cut (7774 ps)
  stands above the whole top (6843 ps); the cuts order the stages rather
  than decompose the top exactly.

## 5. The synthesis database

State: the tool is written and its consumers read it (2026-09-13,
`chialu/synthdb.py`). No rows stand. The first dense build of nangate45
reached 10,638 rows and was discarded because a row named its top family
alone: the pins carried the family's own choices and nothing about the
slots, so an fp adder's 84 rows all measured a ripple-carry significand
adder without saying so, and of 9,403 distinct rows 6,581 named no
sub-structure. The row was redesigned around the complete structure and
the rebuild was discarded in turn (2026-09-14): the RTL those rows
measured is verified only where a hand-written selftest case covers it,
which is 724 cases against 5,057 enumerated points at width 16, so an
area and a delay may belong to a circuit that computes the wrong
function. `docs/verification-golden-plan.md` is the work that has to
land before a build is worth running. In place: the
row's key and its provenance (the generator's hash, the liberty's hash
and a hash of the yosys and the yosys frontend versions, which a rebuild under other
tools supersedes), the per-kind width range, the run files' own
structure widths (`build --seeds`, cached in
`chialu/synth/seed_widths.json`, with the float formats they build
beside them), the build's resumption on a detached
host process, and the consumers, which are the timing prompt,
`chialu.prune` per width and `chialu.prune --best` as the evaluation's
no-model reference.

The complete structure in the row (2026-09-14):

* `pins` binds `<slot>.family` for every slot the family opens, and for
  every slot the family bound there opens, so the row names the
  significand adder, the alignment shifter, the leading-zero path and
  the exponent adder an fp adder was measured with.
* `slots` lists those paths, and `synthdb prune` drops a row whose pins
  leave one unnamed.
* The points move one slot at a time off a baseline that binds each slot
  to its space's first family. The cross product of fp_adder's slots is
  about 43,000 points per family per width, which no database holds, and
  one-at-a-time answers which sub-structure a top family is best served
  by. A sub-structure's interactions with its own sub-structures are
  measured under that sub-structure's own kind.
* `synthdb slots` reports what each slot buys: how many of its members
  map to a netlist of their own, and the delay from the fastest member
  to the slowest. A slot whose members all map to one netlist is one the
  generator does not read.
* The point count goes from 11,145 to 28,098 over 27 kinds.

What is left is the data itself, which waits on
`docs/verification-golden-plan.md`. A probe of the dense build on the
EDA host (20 cores, 25 GB) put the cost at 3,800 rows in ten minutes
under sixteen jobs, with 8.7 GB free at the worst sample and the largest
mapper at 0.8 GB.

The database is redesigned and gets a user-facing build script. The
current file is a JSONL list, so the redesign concerns the row, the
coverage, the queries, the PDK set and the file layout.

What is wrong today:

* The width grid is 8, 16, 32 and 64 bits, unrelated to the widths the
  seeds build (a 281-bit accumulator frame, a 22-bit product, a 9-bit
  shift amount), so the rows cannot explain a seed's delay.
* Every row is repeated at four clock targets although the mapping
  result does not depend on the target.
* The composite kinds are characterized as whole modules; their
  components have no rows, and several component kinds the generators
  use (incrementer, lzc, the sticky mask) are not kinds of the database.
* Rows are keyed by hand-named variants chosen in `characterize.py`
  rather than by the pins.
* There is no provenance, so a stale row is indistinguishable from a
  current one.
* Only three PDK descriptors exist under `pdk/`, and the build accepts
  only their names.
* The query is "the fastest variant per family at the run's clock".

The redesign:

* **Row**: one row per (pdk, effort, kind, family, the full pin
  dictionary, the width parameters as a dictionary), carrying area,
  delay, cell count, the module name, the generator's content hash, the
  liberty file's hash, a hash of the yosys and the yosys frontend versions the
  measurement passed through, the date and the status. The clock target leaves
  the key unless a flow that depends on it is adopted.
* **Coverage**: every realized family and every component kind the
  generators instantiate; widths on a dense grid (the powers of two from
  4 to 512 and the intermediate points 12, 24, 48, 96, 192, 384) plus
  the exact widths harvested from the seeds' manifests; every PDK the
  user builds.
* **PDKs**: any liberty set. `synthdb build` takes a descriptor name
  under `pdk/`, a descriptor file anywhere, or `--liberty a.lib[,b.lib]
  --name <pdk>` with the ABC scripts defaulting to the shipped ones; the
  descriptor's fields stay name, liberty paths or URLs, ABC scripts,
  area unit and corner; the database directory is named by the
  descriptor and records the liberty hash.
* **The build script**: `python3 -m chialu.synthdb build --pdk ...
  [--kinds ...] [--families ...] [--widths ...] [--effort ...] [--jobs N]
  [--host <eda host>]`, incremental by content hash, resumable, parallel,
  with `status`, `verify` (re-synthesize a sample and compare), `query`
  and `merge` (union of two databases, newest provenance wins)
  subcommands. Each generator registers its own characterization points
  (family, pins, widths) instead of the hand table in `characterize.py`.
* **File layout**: `chialu/synth/<pdk>/<kind>.jsonl`, split further into
  `<kind>/<family>.jsonl` when a file would exceed 10 MB, with a
  `manifest.json` per PDK (descriptor hash, liberty hash, generator
  hashes, row counts per file). GitHub warns at 50 MB and refuses 100 MB
  per file; the cap keeps every file diffable in plain text and the
  repository off Git LFS. Today's 4648 rows are 369 bytes each (1.7 MB);
  a dense grid over all component kinds is of the order of 10^5 rows per
  PDK, which the per-kind split holds at a few MB per file.
* **Query**: exact lookup; nearest width with interpolation on the kind's
  own law (linear in the width for the ripple class, logarithmic for the
  prefix class, per-kind laws stated in the kind's descriptor); fastest
  and smallest per family at a width; a decomposition query that sums a
  composite module's components for a given geometry, so the timing
  prompt can show where a seed's delay goes.
* **Consumers**: the timing prompt source shows per-component estimates
  and a composite's decomposition; `chialu.prune` works per width; the
  evaluation's tier 2 gains a "database-best" seed as the no-model
  reference.

## 6. The knowledge base

State: done (2026-09-13). `python3 -m chialu.archdocs` runs the three
checks and exits nonzero on a finding: every enum member is named by its
family card or carries a variant card (469 by a card, 288 by a variant
card, 60 numeric, none undescribed), the 18 card claims seeded over 17
families are met by their modules' headers, and the 228 gap reviews are
triaged (`--gaps`), with `docs/knowledge-gaps.md` recording the decision
per state. What remains under it is the 327 structural gap proposals
that need a person's reading against the standing rule, which that
document lists per family.

* A lint requiring every enum member to be named in its family card (a
  per-choice table in the card is the simplest form), with the 597
  undescribed members as its first work list; the members the notes pin
  but the variant rule filtered out are written from the reduce bundles.
* A check of a card's structural claims against the module header of
  the family's realization, so a realization that drops a technique's
  point (the realignment lines raised to the exact frame) is caught.
* The pending gap reviews under `legacy/knowledge/extract/gaps/` are
  triaged for the realized families and applied or closed with a note.

## 7. The approximate ALU's accuracy control

State: done on 2026-09-13, apart from three families named at the end.
`accuracy_ctl` (static | runtime) and `accuracy_modes` (2 to 8) are
declared under `accuracy: approximate`; runtime gives the unit an
`accuracy_mode_sel` input of ceil(log2(accuracy_modes)) bits, which the
seed carries to every lane module, and `error_budget` binds one budget
per mode in mode order with mode 0 the coarsest. `accuracy_configurable`
muxes each block boundary's carry-in or each low block's sum against the
static point, and `dynamic_segment` masks the operand windows by the
mode; the static text is unchanged for both, so no database row moves.
The judge scores each mode's vectors against that mode's budget, the
checker holds `check_err` low outside the exact modes, and a checked
approximate unit is an error at load unless one mode is exact
(`docs/formats-and-options.md` sections 3.3 and 3.4). Measured over 4000
vectors per mode: 3372, 2937, 2000 and 0 wrong results under the
correction-stage grain, and 4000, 3987, 3785 and 0 under the truncation
grain. The families selftest passes 1907 of 1907, the ALU matrix 76 of
76, and two new smoke cases cover the runtime modes and the checked
runtime modes.

Not realized: the dual-quality cells of `approximate_compressor_tree`,
whose exact 4:2 compressor carries a third output the inexact rule does
not, so a mode mux needs the shared reduction restructured and the two
enum members that rev 8 removed restored; the same shape applies to
`pp_perforation`'s accuracy modes and `approximate_functional`'s quality
scaling.

The runtime quality controls of the approximate families (dual-quality
cells, runtime width scaling, the accuracy-configurable adder's modes)
are realized at a static operating point named in the module comment,
because the unit interface carries no port for them. The decision is: a
run that asks for runtime configurability gets a port. The work is an
option (`accuracy_ctl: runtime`, next to the existing SPRS controls
`rounding`, `daz_in`, `ftz_out`, `check_en`) that adds an input port to
the ALU selecting the operating mode, a reference in `chialu/verify`
that takes the mode as a control and applies the per-mode error budget,
a checker contract per mode, and the generator's realization of the
mode switch instead of the static point.

## 8. Future work

State: done on 2026-09-13. `docs/future-work.md` records both subjects,
and the later-version section of `docs/deferred-families.md` points at
it.

Two subjects are recorded as later versions rather than deferred items:

* **Registered and multi-cycle units**: a latency or valid protocol
  variable on the templates, registers in the seed, the fixed-latency
  and iterative testbench protocols (present in `chialu/verify/tb_gen.py`,
  set by no template), a timing metric of cycle time times cycles or of
  throughput, the pipelined configurations of the baselines in the
  evaluation, and the return of the sequential families and choices of
  item 1.
* **Decimal floating point**: the families of `decimal_misc_space`
  (bid_fp_addition, decimal_fp_addition, decimal_fp_multiplication,
  decimal_fma, decimal_encoding_codec, binary_decimal_conversion,
  redundant_decimal_conversion, decimal_cordic_transcendental,
  commercial_decimal_fpu) need a unit template with decimal
  floating-point modes (formats, the cohort and preferred-exponent rules
  of IEEE 754-2019 clause 5, the DPD and BID encodings) in the verify
  layer and the seed before any of them has a place to be realized.

## 9. The evaluation

On hold. `docs/evaluation-plan.md` stays as written; its prerequisites
(the two code switches, the TestFloat harness, the comparison run files,
the baseline wrappers, the numerical-behavior model of each baseline)
are not started until items 2 to 5 are done, since the units it would
compare are the ones those items change.
