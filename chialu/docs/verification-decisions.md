# Verification decisions

This records choices that affect generation, golden verification and the remaining acceptance work.

## SFU accuracy

* The selected rule uses the supplied precision target, or 1 ULP by default, for implementation and unresolved numerical-parameter search. A fixed numerical algorithm reports its error range without applying that budget. Exact arithmetic choices may remain searchable without changing the numerical algorithm.
* The reason is the user's stated priority between a chosen approximation and a precision target. RTL must still implement its algorithm. A missing independent algorithm contract prevents conformance from passing even when a numerical range has been measured.
* The alternatives were one budget gate for every fixed approximation, or treating sampled maxima as complete error bounds. Both conflict with the requested acceptance.

## Digit-recurrence normalization

* `additive` stores a zero-centered delta and computes its digit product plus a separate digit bias. `multiplicative` retains the one-centered state. Every additive state and its selector are evaluated in the new coordinate system.
* The reason is a terminology gap: the cited algorithm names normalization by operation, while this project's schema declares both choices for each operation. Merely relabeling the old exponential residual subtraction would not implement another physical datapath.
* The alternatives were removing existing operation/pin combinations or changing to a different exponential-factor algorithm. The selected contract and its precise limits are documented in [additive.md](../chialu/knowledge/arch/sfu/digit_recurrence_exp_log/additive.md). Coordinate equivalence applies only to exact child arithmetic; it does not establish coverage for approximate children.

## Value-table controls

* Direct and compressed tables store deterministic rounding results and stochastic transition thresholds. Runtime logic consumes the complete random word and applies DAZ, FTZ and flags.
* The reason is that the old selected table path returned only RNE values. Thresholds represent the stochastic decision without a table containing every possible random word.
* The alternatives were enumerating up to 2^32 random words per operand, or retaining the old RNE table and relaxing numerical verification. Neither provides the required implementation.

## Reference corrections

* Independently demonstrated reference errors are corrected and receive directed regressions. Examples include signed exponent-only rounding, invalid-result propagation, scale overflow and small transcendental corrections lost before directed rounding.
* The reason is the user's authorization to repair proven reference errors. A defective reference cannot certify correct RTL.
* The alternative was preserving each defect as a verification gap under the original frozen-reference rule. The user explicitly permits corrections instead.

## Exponent-only special values

* M = 0 with both NaN and infinity is rejected. NaN-only, infinity-only and finite-only exponent formats remain available with or without a sign bit.
* The reason is that the declared encoding has no distinct NaN and infinity patterns when the mantissa is absent.
* The alternative was assigning one pattern to two meanings or inventing another encoding. Either changes the declared format.

## Infinity-only finite neighbours

* Infinity-only formats with mantissa bits retain finite values above the reserved infinity encoding. Rounding crosses that hole using the actual finite neighbours, including their three-unit gap for stochastic rounding. Nearest-even ties use the finer common binary quantum; for `fps1e2m1I`, 4.5 rounds to 6 and 3.5 rounds to 3.
* The reason is the declared encoding: its positive finite values are 0, 0.5, 1, 1.5, 2, 3 and 6. Treating the reserved encoding as an overflow threshold incorrectly rounds finite intermediate values to infinity or the maximum.
* The alternatives were removing the finite encodings above infinity or preserving the incorrect contiguous-code quantizer. Both conflict with the existing format. Fused multiplier injection retains the unrounded product when its tentative result hits this hole so the selected rounder can make the correct neighbour decision.

## CORDIC double rotation

* The conventional-CPA residual now constructs both rotations, including the cancelling pair selected for a zero digit.
* The reason is that `double_rotation` already used the squared gain factor, while this residual branch performed only one rotation. A directed whole-seed check improves from 5 ULP to 0 ULP after the correction.
* The alternative was changing the gain factor to match one rotation. That would leave the requested double rotation unimplemented.

## ADIR dependency

* The four-line template-default extension is committed on `chialu-verification-defaults`, starting from the version already used by chiALU.
* The reason is that the verified SFU binding path depends on this extension. The submodule commit must be published before chiALU points to it.
* The alternative was upgrading to the newer ADIR main branch. That would add unrelated changes to the verified source snapshot.

## Carry-save exit aliases

* The per-mode adder and the representation's assimilator name one physical carry-save exit. Their family and active pins are resolved within the intersection of the original user-bound domains. An explicit conflict or empty intersection is an error.
* The current assimilator interface is global, so different fixed per-mode exits cannot share that binding. The selected implementation requires a common family and pins across those modes.
* The alternatives were silently selecting one alias, narrowing the stored search domains, or adding an indexed representation interface. The first two would lose user intent; the last remains an interface extension rather than an implicit fallback.

## Diminished-one cyclic carry

* The cyclic diminished-one adder uses the requested generate/propagate topology followed by an inverted carry row. The selected incrementer handles the external carry-in, including the all-propagate zero-code boundary.
* The reason is that the old cyclic graph did not feed either output; separate wide add/subtract logic computed the answer. Functional agreement alone did not establish the requested recirculation.
* The alternatives were deleting the unused graph and renaming that implementation, or implementing a wrap at every prefix level. The selected extra-row construction is also part of the documented cyclic-prefix contract and retains the requested topology.

## Approximate adder geometry and correction

* The lower region must leave an upper region, and the complete speculation window must fit within the lower region. Oversized choices are illegal geometries and fail without clipping.
* The correction selector is active only for the documented speculative-carry repair. An explicit correction binding for another lower scheme fails as inactive. The current interface selects the correction circuit at generation time; it exposes no runtime correction-enable port.
* The alternatives were silently retaining ignored selectors, applying an unspecified repair algorithm to other schemes, or adding a new runtime interface. The selected rule follows the existing algorithm and port contract. Independent native algorithm verification and whole-ALU composition remain separate scopes.

## Wide multiplier compensation

* Compensation means and fitted residual sums use exact integers and fractions until their final nearest-integer rounding. The independent multiplier contract is unchanged.
* For a 53-bit significand with two extra columns, the exact scaled mean is `12.5 + 2^-53` and rounds to 13. Binary floating accumulation lost the positive term and produced 12. A normal FP64 operand pair distinguishes the resulting RTL outputs.
* The alternatives were adding a fixed amount of floating precision or redefining the algorithm around the inaccurate calibration. Exact arithmetic follows the stated mean/intercept contract for every width.

## Native algorithm and numerical gates

* Native verification checks the algorithm words separately from the mathematical reference and its budget. A faithful implementation can still fail its requested numerical budget.
* All scale, minimum and slack constants in the numerical bench have explicit widths large enough to contain their values. The old unsized `2^32` scale became zero during conversion and prevented measurement.
* The alternatives were relaxing the budget or accepting only the algorithm comparison. Neither establishes the intended numerical criterion. Legacy grid rows with documented illegal geometry are reported separately; inactive default aliases are projected without changing the synthesis point generator.

## RNS chunk geometry

* Each selected `chunk_bits` value retains at least one complete input chunk. A final short chunk retains its nominal size and reports its actual port width.
* A modular MAC requires a second actual chunk so residue feedback exists. A final ROM after canonical chunk tables also requires a second chunk. Segmented conversion requires four chunks so two actual segment additions feed the final combination.
* These are target geometry requirements. The declared Range remains 1 through 64. The alternative was clipping large chunks or accepting a parameter whose selected stage disappears.
* Activity evidence distinguishes physical chunks from chunks whose entire input affects the residue. A power-of-two channel can discard high bits; an odd channel supplies full-bit coverage. The smallest component sweeps also require enough width for actual reduction and a nontrivial MAC radix modulo the chosen modulus.

## Complex BKM contract

* The first complex path evaluates a quarter angle inside the E-mode convergence rectangle and reconstructs the requested angle with two complex squarings. Both pair outputs feed the sine/cosine quadrant selection.
* Signed real correction digits cancel the magnitude growth of imaginary steps. Nonnegative digits are incompatible with this scale-free unit-circle contract. Higher radices and the other selectors remain declared implementation gaps.
* The alternatives were counting a real exp/log path with permanently zero imaginary state as complex coverage, or adding an artificial phase perturbation. Neither establishes the selected complex construction.

## Large combinational simulation

* An optional procedural simulator handles large acyclic circuits whose intermediate transitions overwhelm Verilator. It consumes the original the yosys frontend/Yosys elaborated network and retains the independent expected words.
* A separate parser matches every emitted operator, bit connection, signed width, input/output binding and evaluation dependency with that network. Unsupported cells and unrecognized source statements are errors. Official Yosys-cell simulation and mutation regressions validate the accepted grammar. The seed's original physical hierarchy requires its own audit.
* The frontend remains a compiler assumption. No SAT or formal run is part of this path. A passing path requires the independent correspondence certificate, complete matching output words and the original hierarchy audit.
* The alternatives are longer original-path timeouts or replacing the selected CPA with another fixture. Timeout retries remain separately recorded; a different CPA proves a different target.
* Complete word-address case ROMs avoid an expensive generic barrel expansion of packed table bit slices. The identity between these encodings holds for every complete table, and full-address simulations cover the wide residue banks. Yosys maps the memories and parallel muxes before the checker reads the final cell graph.
* Long-lived workers record source observations at import and loaded-code fingerprints. Earlier reports sometimes hashed newer disk files after importing older code. Fresh certificates recheck the unchanged network, source and result artifacts with a frozen checker; the old reports are retained.

## RNS representation contracts

* Raw-binary RNS consumers retain a selected EAC module and decode its modular outputs. Generic-p decoding combines input quotient/remainder information with the selected native remainder and carry. Native EAC characterization keeps its modular contract and now accepts the complete binary input domain.
* The reason is that a native modular sum is not an ordinary binary CPA result. Selecting that family without a representation adapter previously changed surrounding arithmetic.
* The alternatives were silently replacing EAC with another CPA, or restricting its native operands to canonical residues. The selected adapter preserves the physical choice and its full input interface. Both native outputs have fault-propagation tests.
* ROM reverse conversion uses complete banks of at most eight address bits and selected modular additions. CRT-II has two actual nonempty subgroups, including three channels. The alternative of substituting arithmetic products or CRT-I would ignore the selected implementation or algorithm.
* Approximate modular addition normalizes the selected child's actual output over its complete word domain. An exact recomputation would hide the requested approximation. This local contract does not establish a whole approximate RNS algorithm or its numerical budget.

## RNS comparison correction

* Mixed-radix and diagonal approximate selections use coarse keys followed by exact tie correction. Fractional estimation uses its documented nearby-result correction. Targets must exercise both paths; the smallest default widths are six, six and seven respectively.
* The reason is to make the exactness selection change an observable construction without changing the comparator's exact output contract. Independent probes check the internal keys and both decision paths.
* The alternatives were ignoring the selector or counting an always-active correction at a smaller width as coarse-estimate coverage. Both would overstate parameter coverage.

## RTL module identity

* Extended adders use complete SHA256 architecture tags. Module collection accepts repeated definitions only when their SystemVerilog tokens agree, and rejects conflicting definitions instead of keeping the first one.
* The reason is six actual short-hash collisions in the complete generic-p Range. Separate simulations passed each design but did not establish that both could coexist in one target.
* The alternatives were separating the colliding targets forever or adding suffixes without updating references. Full tags and strict conflict rejection preserve joint construction and make any later collision explicit.

## Fresh simulation artifacts

* Each Verilator compilation starts after removal of the previous compiled artifact. A zero exit code must also have a fresh nonempty artifact and no compilation-error diagnostic. Simulation exits must succeed before a printed PASS is accepted.
* The reason is an observed 1,024-error compile returning zero. Running a surviving old artifact could otherwise certify the previous circuit against a new source description.
* The alternative of trusting only the exit status is insufficient. Failed reports and old evidence remain preserved; missing historical compiler logs are reported as missing rather than invented.

## Simulator selection

* `chialu.verify.simulate` runs every bench of the flow under Verilator or Verilator. The default is `auto`, which picks Verilator when the design reaches `AUTO_BYTES` (64 KB) or the estimated event work (vectors plus fault rows, times design bytes) reaches `AUTO_WORK` (2e9), and Verilator otherwise; `CHIALU_SIM` names one simulator for a whole run.
* Each candidate compiles one testbench (`tb_gen.emit_tb_universal`) that serves the conformance run, the seam fault masks and the grouped internal-fault plan through plusargs. The build is cached under `~/.cache/chialu/sim_build` by the content key of (simulator, design, checker, bench), so the compile is paid once per design rather than once per campaign. The clocked SFU benches and the table-driven slots keep the per-campaign bench.
* The reason is the measured cost split. On the 20-core host Verilator's verilate-plus-C++ compile takes 3.5 s for an 18 KB behavioral design, 30 s for the 190 KB fp16x4 library seed, 97 s for the 469 KB fp64 library seed and 124 s for the 243 KB fp80 library seed, against Verilator compiles under 0.3 s for the behavioral seeds. Every behavioral case below work 1.5e9 finishes under Verilator in less time than Verilator's compile alone, while the behavioral mixed seven-mode unit (93552 vectors, 584 KB) takes 247.9 s under Verilator against 11.9 s under Verilator. The library-realized seeds behave differently: every matrix seed of 64 KB and more took 20 s to 3446 s under Verilator, the fp64 seed timed out after 1800 s of simulation and the fp80 and fp16x4 seeds after 1800 s of compilation (a 215 MB the model), while the same three seeds pass under Verilator in 0.03 s to 0.5 s of simulation.
* The alternatives were Verilator for every candidate, which adds about 4 s per node to the small cases that make up most of the matrix and gives up Verilator's four-state view of an undriven net on every design, or Verilator alone, which lets the large seeds dominate a sweep's wall time or time out. A checked candidate whose conformance and fault nodes both pick Verilator pays two builds, because the conformance node does not receive the checker; that cost is accepted.
* Verilator runs the `#1`-delay benches under `--timing`, which needs a C++ compiler with coroutines (GCC 10 or later; on the RHEL 8 host `source /opt/rh/gcc-toolset-11/enable`) and `libatomic`. Without a usable `verilator`, `auto` falls back to Verilator.
* Verilator builds run without an object cache unless `CHIALU_OBJCACHE` names one, and then with `include_file_mtime,include_file_ctime` added to `CCACHE_SLOPPINESS`. The reason is that ccache 3.7 leaves a precompiled header out of an object's hash when the header is younger than the second ccache started in, and verilated.mk includes a header it made milliseconds earlier, so a design's runtime objects came from another design's build (models dead at start or silent at 0 s). The alternative of a cache keyed on the whole model directory buys under a second per new design, since the flow's own build cache already serves a repeated design. A model that exits 0 without a bench line counts as dead and reruns under Verilator.

## What the search starts from and what the prompt varies

* The search run's seeds are the baseline (the score reference of `ratio_to_seed`) and the plans the numeric stage's front adds; the three other hand plans (`packed_banks`, `per_position`, `dedicated_speed` in `chialu/plans.py`) are reference designs of the evaluation's tables, measured beside the results, and no longer seeds. The reason is that a hand plan is one point of the space the enumeration and the numeric search now cover, so it earns its place by measurement rather than by construction; the baseline stays because the score is relative to it.
* The prompt samples two knobs per round, the operator (structural, local, free) and the ambition (conservative, moderate, aggressive); the evaluation's feedback is always shown whole (`feedback_depth: full`, the long texts as files under `feedback/` in the call directory) and the knowledge base as its card list (`knowledge_depth: index`), which the agent reads with its file tools. The reason is that how much of the feedback or the knowledge the agent sees is not a design decision worth sampling; the alternatives sampled before (a 400-character summary, the bare knowledge path) only withheld information.
* The tactic sources are `critical_path` (the parent's reported path as a target) and `moves` (a move card); `unexplored_values` is gone, since the structural operator's own section proposes untried declaration values.
* Under the structural operator the agent edits VAR lines alone: the template re-renders a region whose declaration changed from its library, and a region whose text the agent also edited keeps the agent's text (`replan`), so the prompt says to leave the text alone unless the agent wants its own realization.

## One carry-propagate adder for the integer adders and the float significand add

* A unit that serves integer and float modes can share one adder between the integer adders' bank and the float adder's significand add: the plan groups the binary integer adders with the float adder of a single-lane float mode under `partitioned_carry_chain`, the seed widens the lane-partitioned adder to the significand width plus its carry-out bit (rounded to the finest lane; fp16 with a 16-bit bus gives 32 bits), gives the float mode a full-width lane of its own, muxes the operands by mode (the integer operands in the low bits, the significands at bit 0, their carry-out the sum's bit iw), and the float adder family takes the adder through ports (`fp.py add_sv`, `external`: the family must be single-path with the operands swapped before one shifter and two's complement subtraction, so that one adder serves add and subtract). `sharing_schemes` enumerates it as the `intfp` axis and the estimate prices the group as the bank's row at the shared width plus each float adder's row less its own significand adder's.
* Measured on mixed_cvt_alu (fp16, int16, 2 x int8, fxs1i7f8; default families, all integer adders banked): without the float adder 7358.6 um2 at 7739 ps, with it 7665.6 um2 at 8845 ps, both bit-exact on 12,868 vectors. On this unit the mux and the wider bank cost more than the 27-bit significand adder saves, so the option stays a point the numeric stage prices and the gates measure rather than a default; where the integer bank is wide and the float format narrow the balance differs.
* The alternative of sharing the whole float adder with the integer adder (one datapath for both) is not a realizable family of the library; the significand adder is the part the two have in common.

## Sharing schemes by enumeration, micro-architecture by the database search

* The chain's first two decisions are now separate and ordered: a sharing scheme first, the families and choices under it second. `chialu.plans.sharing_schemes` enumerates every sharing plan the seed realizes (the five group kinds of `validate_partition`: binary adders under the lane-partitioned carry chain, binary multipliers under the twin-precision matrix, integer gate rows, rounders or unpackers across float formats, an adder with its lane's comparator or its lane's gates under `alu_pg_fused`, and the subword family), per kind as none, all, per mode or per lane (`natural`, 184 schemes on int_subword_alu, 4 on fp_alu_cmp) or as every set partition (`all`, 7650). The pipeline prices each scheme with the estimate node at the instance's default families, keeps the non-dominated schemes spread along the front (`--schemes`, 6 by default), runs the numeric search under each (the estimate node takes the scheme as `plan_json` and prices a group as one unit at the bus width, its delay in every mode it serves), and `front_seeds` merges the schemes' archives into one front whose plans carry the scheme's groups and the point's families.
* The reason is that the estimate counted one unit per structure and never saw a shared datapath, so the numeric stage could not rank sharing and the discover role's plans and the numeric front reached the seeds as parallel inputs; the seed realizes a closed, small set of group kinds, so the schemes are enumerable, and the model is not needed to find them.
* The discover role is removed from the chain: the run files name no discover role and the pipeline has no discover stage, since the enumeration covers the closed set of sharing schemes the seed realizes (the exhaustive check over the ALU targets is in the worklog). ADIR keeps its generic discover capability (`search.seeds.discover`, with the sharing-only mode added on the way) for other domains.
* The tactic is a target rather than a recipe: `target` offers the critical path (the units that own its longest segments, to shorten) or the logic off it (the largest units the path does not cross, to shrink without lengthening the path), both read from the parent's synthesis report, and the composer's UCB picks one per round. The former `moves` source handed the agent rewrite recipes, which is knowledge the agent reads from the move cards under the local operator, and `critical_path` alone had no counterpart for area; the operator says what kind of change, the target where.
* The alternative of sharing as a template variable (a `core.sharing.*` axis the numeric backend mutates beside the families) would let one NSGA-II run cover schemes and families together; it needs the seed generator to build its partition from a declaration rather than from a plan, which the replan path does not do today, so the enumeration with one numeric run per kept scheme is the form for the demo.

## Synthesis reports for the coding agent

* `chialu.eda.synth_ppa` returns, beside its scored numbers, four texts from `chialu.synthreport`: `summary` (one row per unit instance of the flattened design with area, share, cells, the cells ABC merged with another unit, and the latest arrival at the unit's input and output ports), `critical_path` (one line: the latest endpoint and the path as `owner(cells, ps)` per segment), `paths` (the 20 latest endpoints, the first three cell by cell with edge, cell type, owner, net, fanout, load and slew) and `area_by_hierarchy` (the instance tree and the member-to-module-to-instance table). The run files name them under `feedback:`; the composer shows what fits its cap inline and writes the rest to `feedback/<key>.txt` in the call directory, which the agent reads with its file tools; the card `knowledge/flow/synthesis_reports.md` says how to read them; the `critical_path` tactic quotes the line.
* The reason is that the agent had only the two numbers and the seed's own text; where the delay goes (which unit, which decode net with a fanout of 29 and a slew of 479 ps, which chain) was not visible, and the earlier tactic read `synth_ppa.detail`, which is empty on success.
* ABC's mapping drops every hierarchical name, so the reports come from a second ABC run on the same pre-mapping netlist with `keep` on the unit instances' port nets (344 nets on int_subword_alu, 284 on fp_alu_cmp); its area and delay stand within a few per cent of the metric (+0.1 % and +1.9 %, +3.2 % and +0.8 %) and every text's header states both. The timing is a static analysis under ABC's `stime` model that reproduces ABC's `Delay =` to the last digit on the flow's own netlist. The cost is 5.3 s on int_subword_alu and 7.5 s on fp_alu_cmp per candidate (`CHIALU_SYNTH_REPORT=0` turns it off).
* The alternatives were `keep` on every hierarchical net, which names the nets inside a unit but moves fp_alu_cmp's area by 37 % and its delay by 23 %; a per-unit mapping (`synth_unit`'s view), whose total stands at 1.6 to 8 times the flat design because ABC merges the units' duplicated logic only when it sees the whole; an on-demand path query tool through CHIA's tool servers, which nothing in the backends wires today and which a precomputed per-unit path file covers; and OpenSTA, which the host does not have.

## Reading the SystemVerilog without the yosys frontend (explored, not yet adopted)

* The flow reads SystemVerilog directly at both ends. Verilator builds every measured design from the raw members with identical conformance and seam-fault dumps (int_subword_alu, fp_alu_cmp, block_alu, approx_alu) in the same compile time, and yosys reads all members in one `read_slang` command in 0.24 s and 3.55 s (yosys 0.68+36, the slang frontend the host's oss-cad-suite ships). Nothing converts.
* The slang frontend changes the measurements: whole-ALU area moves under 1 % (int_subword_alu 5544.5 to 5508.9 um2, fp_alu_cmp 6838.6 to 6814.9), delay by 3 % and 0.7 %, cell counts by 5 % and 28 %, and single units by up to 8 % area and 13 % delay, since slang's word-level netlist differs from what yosys builds from the yosys frontend's output. The 4742-row database, the calibration ratios and the seed baselines are consistent only within one frontend.
* The decision is deferred until after the demo's runs: the switch (files to Verilator, `read_slang` for lint, synthesis and the database, a version salt on the build cache, checked candidates to Verilator or the yosys frontend kept as an Verilator-only lowering) and the database rebuild go together in one change, so every number in the archives stays comparable. Fourteen scripts outside the nodes still call the yosys frontend (the matrix, the selftests, the formal and equivalence checks); a flow-only switch leaves the yosys frontend installed for them.
* The alternative of rewriting the generator so yosys's own frontend reads the seeds (qualified `pkg::f()` calls, no `return`) does not cover a candidate the model writes.

## Estimate calibration

* The numeric stage's estimate (`chialu.eda.estimate`) multiplies its area and delay sums by `area_scale` and `delay_scale`, which the pipeline's `calibrate` stage fits on the baseline seed: the search run's synthesis of the baseline over the numeric run's estimate of the same declaration, written into `<name>.numeric.cal.yaml`.
* The reason is that the raw sums stand off the unit's synthesis in different directions per target (int_subword_alu delay x1.68, area x0.94; fp_alu_cmp delay x0.85, area x0.60), so a constant cannot serve, and the constraint `estimate.delay_ps <= vars.clock_ps` ranked the float baseline infeasible although it meets its target. The rows are modules synthesized alone at their own timing target, and the delay sum has no term for the unit's decode, operand select and result mux.
* The alternatives were an additive delay offset (one measured point fits one parameter either way; the ratio keeps the constraint's form and the front's ordering) and per-kind context factors from the tier-2 measurements, which need more measured units than the demo has. The residual error of the scaled estimate on the other plan seeds is reported as a table of its own.

## Modular adders inside binary structures

* A structure that sums binary quantities through an adder slot (a count tree's final adder, a block adder, an exponent adder) takes the slot's family through `binary_cpa.adder_module`, the decode wrapper that restores the binary sum and carry of a modular family (`end_around_carry` sums modulo 2^W - 1 or 2^W + 1), never the family's native module from `FAM.adder_module`.
* The reason is fp_alu_cmp's front_1 seed: `count.py` took the native module for a popcount tree's final adder, the leading-zero count of a zero-operand fadd came out 19 for 15, and the rounder mis-shifted; the space selftest had reported such points as `no_golden` rather than checking them.
* The alternative of removing the modular families from every binary slot's domain loses the end-around-carry adder where it is a legitimate choice (the exponent adders and the decode wrapper carry it correctly); the wrapper is the rule, and the remaining raw calls listed in the worklog are to be checked against their slots' domains.

## Exact spaces and algorithm-level families

* An exact unit's slot spaces hold no family with `algorithm_level` set (`chialu.modules.alu.exact_only`, applied at every depth of `core_slots`); the approximate unit's spaces keep them.
* The reason is that these families change the computed function (the truncated and the logarithmic multiplier, the approximate-compressor multiplier, the approximate adder), and the numeric search over the declared space reached them on both demo targets, which cost every repaired front seed its bit-exact gate.
* The alternative of removing them from the exact spaces' lists breaks the approximate spaces, which build on those lists; the alternative of a rejection at render time leaves the numeric search ranking points the seed never realizes.

## Prompt ambition and conduct

* Every ALU run file samples an `ambition` prompt variant per round (conservative, moderate, aggressive) beside the operator, the focus and the feedback depth, under the composer's UCB; the composer's system text carries a Conduct section: a round returns a changed candidate, an analysis of metrics, seeds or history is not evidence that the design is at its limit, a failed expectation names its assumption and changes a different thing.
* The reason is the user's rule of 2026-09-16: one prompt at one level of ambition either stalls on small edits or wastes rounds on redesigns, and an agent that declares the optimum ends a search early and biases the method's comparison.
* The alternative of three separate run files per ambition was not taken: the sampler credits each level by its children's improvement, which one run measures.

## Front plans from numeric points

* `chialu.front_seeds` renders every front point through `plan_seed` and repairs a plan the seed refuses by dropping the declarations the rejection names (inactive choices, values outside an enum or range, a family the mode cannot take, a nested family rejected at its width, a fused family that needs a group), then by reducing the plan to families at every depth, then to the structures' own families; a plan that fails there is dropped with its reason.
* The reason is that the numeric space admits values the seed's realization refuses at the unit's widths and formats, since the estimate reads the database rows without rendering; a front point is still worth a seed at the level it renders, and the record keeps what was dropped.
* The alternative is a realizability node in the numeric graph that renders each candidate (about 3 s per declaration on fp_alu_cmp, so about 10 min over a 200-iteration run) and marks an unrenderable point infeasible, which would keep the front on realizable points; it is the next step once the demo runs.

## Checker phase

* The user resumed `docs/checker-spec-plan.md` on 2026-09-15; its four stages are realized (the plan's "Realization" section names the modules). The `check_en` + `checker.*` spelling stays as the one-rule form, so every existing run file and matrix case loads unchanged.
* `direct_compare` is a family of the comparator space rather than a value `feasible_families` adds by hand: the space is the authority the variables, the database and the coverage tool read.
* The checker enters the synthesis database over one fixed op set (`CHAR_OPS`: the add class and `mul_wide`, one integer mode), so rows compare on the same work; the alternative of a row per run-file op set does not fit a database.
* A search-chosen checker family reaches the fault gate through the node `chialu.eda.checker_gen` reading `decl.check`, as ADIR's design (3.7) states for a generator that depends on a searched variable; the alternative of a candidate-dependent fixed artifact does not exist in ADIR.
* The internal fault sites are the nets a unit's modules declare with a literal width, corrupted one bit at a time while a vector is applied; a masked corruption is not a fault. The alternative of a text rewrite that inserts XOR taps into a candidate's modules is fragile against a candidate that rewrites its module headers.
* An ADIR template default written as a pattern (`check.*`) is inert when it names no variable of the instance (`third_party/adir/adir/instance.py`); without that rule the one-rule spelling would fail with an unknown variable.

## Synthesis of a kept hierarchy

* `synth_ppa`, `synth_unit` and `yosys_stat` drop the `keep_hierarchy` attribute before `synth -flatten` (`chialu/eda.py:HIERARCHY_RESET`); the attribute serves the simulation-side elaboration checks.
* The reason is that every design with a ripple-carry adder failed synthesis with "synthesis left a module hierarchy (flatten failed)" since the attribute landed on the ripple chunk, which made such candidates infeasible and the ripple rows of the database unbuildable.
* The alternative of removing the attribute from `adder.sv` would lose the per-chunk hierarchy the correspondence checks read.

## Files rather than inline text, and the call directory as the agent's only view

The composer writes every long section of a solution prompt as a file
of the call directory and inlines an index of those files. The prompt
keeps what the agent needs to act without reading: the task, the
metrics, constraints and goal, the conduct, the declaration block's
form, the parent's score line, the program file's name with its mutable
regions, the region in focus, the operator, the ambition, the tactic and
the response form. The files under `context/` are `unit.md`,
`decisions.md`, `seeds.md` (static per target), `parent.md`, one file
per PromptSource (`chialu_interface.md`, `chialu_families.md`,
`chialu_timing.md`, `chialu_structures.md`) and one `<candidate>.md`
beside each context program's `.sv`; every feedback artifact is a file
under `feedback/` (`feedback_depth: files`, the run files' value); the
knowledge base is a copy under `knowledge/`, named with one line on its
layout rather than a card list (`knowledge_depth: path`): the agent lists
the directory when it wants a card. The index gives each file's path
relative to the directory, its size and one line on what it holds.

Nothing in the directory is a link. The program, the members, the
context programs and the knowledge base are copies, so every path the
agent can read is the call's own file, and the copies are byte-identical
to the run's files, so a SEARCH block matched against the copy applies
to the program the evaluator holds. opencode runs with the directory as
its working directory and `external_directory: deny`, so a read outside
is refused with the rule quoted (two such attempts were refused in the
smoke sessions, one on the run directory and one on the directory of
the other calls); `edit`, `bash` and `webfetch` are denied, and
`doom_loop` is denied so a tool call repeated three times with the same
input fails at once rather than waiting for an answer.

The system text's order is fixed: "Your role" first (the run file's
`role.file`, `targets/prompts/role.md`: a senior arithmetic designer who
reads synthesis and timing reports and changes one thing per round),
"Conduct" second, "Task" third, then the files index, the metrics and
goal, the block's form and the knowledge line. There is no title: the
template's name told the model nothing, and a prefix that changes
between runs defeats the prompt cache, whereas this text is the same
bytes in every call of a run. The task is not written by hand per
target: `chialu/task.py` renders it from the bound unit (the modes and
their format kinds, the ops, the structure kinds of the manifest, the
clock and the library, the goal and the score rule, the gates, the
checker or the error budget, format notes for float, posit, block,
decimal and conversions, and what a round does), so a user's new target
gets its statement from its run file alone; the per-target `.md` files
are gone.

**Why:** the user's rule of 2026-09-16 is that whatever need not be
inline is handed to the coding agent as a file path, and that the agent
sees its own copy of the files alone. The role, the order and the generated task follow the user's
requests of the same day. Before the change the prompt
carried 60,000 characters, of which the families menu and the library
timing table were 22,500 and the synthesis feedback 11,200, every round,
while the agent read the files it wanted anyway.

## The realization switch

`realization` is a fixed option of chialu.ALU with the values `library`
(the default) and `behavioral`. Under `library` the seed realizes a
declared family from the family library, as every run so far has. Under
`behavioral` the family library's module factories answer None for the
duration of the render (`chialu.targets.rtl.families.library_realization`),
`has_module` answers False, and every structure renders as the behavioral
text it has where the library holds no module; the families menu of the
prompt then carries no `[library]` mark. The lane-partitioned adder and
the twin-precision matrix are library constructions with no behavioral
form, so a run under `behavioral` fixes `core.subword.family` to
`replicated_lanes` and uses plans without shared adders or multipliers;
the generator refuses otherwise with a message that names the choice.

**Why:** the evaluation plan's first ablation removes the library from
the loop while every other mechanism stays, and the measure is how far
the model gets when the declaration no longer brings a realization with
it. The switch is a variable rather than an environment flag so the run
file records it and the contract's hash changes with it.

## The invalid flag follows IEEE 754

A signalling NaN operand raises the invalid flag; a quiet NaN operand
propagates to the canonical (or propagated) NaN without a flag. The rule
holds for the arithmetic ops, for `fmin` and `fmax` under both
`minmax_nan` values, for `fcmp` (a quiet comparison), for a float-to-float
conversion, for block elements and for the dot unit's products and
addend; a NaN converted to an integer, a posit `nar` and the invalid
operations (inf - inf, 0 x inf, 0 / 0, inf / inf, sqrt of a negative)
keep the flag as before. The reference (`alu_ref._is_snan`, `dot_ref`)
and the generated RTL (`alu_mode.is_snan` over the operand pattern's
quiet bit, in `alu_float`, `alu_block` and `dot_seed`) changed together.

**Why:** the reference used to raise invalid on any NaN operand. IEEE
754, SoftFloat/TestFloat, FPnew and HardFloat raise it on a signalling
NaN alone, and the evaluation's conformance runs showed the size of the
difference (chialu-a3eval, docs/plan.md: 4,212 of FPnew's 34,261 flag
mismatches, 1,253 of 2,447 per TestFloat case). The user chose the IEEE
rule for chiALU on 2026-09-17.

## The mapper is ABC's classic `map -D`

`chialu.eda.DEFAULT_SCRIPTS` map with `+strash; dc2; [dch -f;] map -D
<clock>; topo; stime` (a second rewriting round under `high`), so a
design gives a different (area, delay) point at each clock target;
`CHIALU_ABC_FLOW=nf` selects the earlier `&nf -D` scripts, which ignore
their target in this ABC build (identical mappings at D = 1 and
D = 1,000,000). The ABC script is part of the synthesis database's tool
hash, so rows measured under `&nf` show as measured under other tools
until the database is rebuilt under the classic mapper.

**Why:** the evaluation needs area at each clock target, and the user
decided on 2026-09-17 that a mapper is what the target should bind. The
two mappers give different points for the same design (int_subword_alu's
baseline: `&nf` 5544.5 um2 / 1949 ps against `map -D 4000` 5632.0 /
2154), so the database and the calibrations must follow the switch.

## The review is a coding agent with a call directory

The review node takes `only: candidate.touched`, the members whose text
differs from the parent's before any replan (ADIR computes them in the
evaluator entry), and judges those modules alone; a unit the library
re-rendered after a VAR change realizes its declaration by construction
and is not read. A candidate that changed VAR lines alone gets no review
call; a seed gets none either.

The call itself has the shape of a solution call. The node writes a
directory holding `program.sv` (the whole candidate), `members/` where
the candidate is a family, `modules/<name>.sv` for each module under
review, and a copy of the knowledge base under `knowledge/`; the agent
runs with that directory as its working directory and its own file
tools, and the prompt is an index of those files, one line per item with
the module, the declared family and the card's path. No RTL and no card
text is inlined, so the prompt's length does not grow with the design: on
int_subword_alu's `front_2`, six items give a 1,380-character prompt
beside a 1,267-character system text, where the earlier form inlined up
to 20,000 characters of module text per item. The agent follows an
instantiation by searching `program.sv` itself.

A run file names the agent, the model and (for opencode) the provider:
the node is `chialu.review.opencode`, `.claude` or `.codex`, each taking
that agent's worker credential, and `model`, `provider`, `timeout_s` and
`only` are its inputs. Editing, the shell, the web and every path
outside the call directory are denied, as for a solution call.

**Why:** the review's model calls cost 1,054 s of a 1,073 s evaluation on
fp_alu_cmp (eleven units, one call each) and rejected a bit-exact
candidate on one verdict that contradicted the same module's verdict in
another mode, with the reviewer noting that the text it was given had
been cut. Both faults come from the same place: a prompt that carried a
capped, hand-ordered slice of the RTL. An agent that reads the files
decides what to read, and the cap disappears.
