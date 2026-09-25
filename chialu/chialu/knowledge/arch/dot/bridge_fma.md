# bridge_fma

A fused multiply-add composed from separate full-rate multiplier and
adder pipelines: the multiplier array produces the unrounded product
(sum and carry vectors, or a sign, 11-bit exponent and 105-bit
fraction for binary64), a bridge or an internal bus hands it to the
adder, which supplies the pre-aligned addend and the shared
add/round stage, and one final rounding closes the fused operation.
The bridge hardware performs the classic-FMA alignment, combination
and normalization steps and is clock-gated outside FMA instructions,
while standalone adds and multiplies keep executing in parallel at
their own latencies.

The composition style sets the contract and the schedule. Bridge
reuse keeps standalone adds and multiplies 30 to 70 percent faster
and 50 to 70 percent lower in peak power than routing them through a
classic FMA, at about 40 percent more area than the add-plus-multiply
block and about 20 percent more FMA latency and power than a classic
FMA (1454 against 1224 ps in 65 nm SOI); the ARM form defers the
augend until the add pipeline begins, so dependent FMAs issue at add
latency and n products take a(n-1)+m+1 cycles rather than fn, which
wins when the add latency is below the fused latency (a four-term
dot product in 17 against 28 cycles, and 2n+1 against 4n cycles with
2-cycle multiply and 2-cycle add pipelines). Cascading a rounded
multiply into the adder over an internal bus avoids external routing
delay but rounds the product first, so it drops the single-rounding
contract and its accumulated error can exceed a dedicated MAC's. The
extra bridge stages are the hand-off cycles between the pipelines.

The slots fill as in a classic FMA: full alignment of a 161-bit
addend, a leading-zero anticipator or a count after the add,
injection or compound-adder rounding, and a Booth-recoded tree
multiplier. The family wins as a retrofit onto existing add and
multiply units and wherever standalone throughput and dependent-FMA
issue rate matter more than fused latency; it loses to the
monolithic FMA when the fused operation dominates, since the bridge
FMA has about 65 percent higher peak power than the add-plus-multiply
block and lower FMA performance than the classic unit. The ARM
implementation is IEEE 754-2008 compliant with subnormals at full
speed.

The cascade's narrow datapath and short dependent path are what it
sells. Aligning after the multiply keeps the aligner, adder and
normalizer at about 48 bits for single precision against about 72 for
the fused datapath, and the aligner swaps its two inputs by which
significand carries the smaller exponent. At the same 3.2 GFlops
single-precision point in 90 nm the cascade and the fused unit reach
the same area efficiency of 0.036 mm2/GFlops and the same power
efficiency of 0.046 W/GFlops, and the cascade gets there at 12 cycles
against the fused unit's 10. The forwarding path for a dependent
accumulate is shorter than the path through the multiplier, so a dot
product can finish sooner on the cascade despite the longer
single-operation latency. A 45 nm generator study puts the cascade on
the latency frontier for that reason, at pipeline depths of 5 to 12
and 16, with about half of those designs replicating the multiplier as
a multi-cycle block, and it clocks only one of the addition's close and
far paths. The cascade's accumulation latency is about half its
multiply-add latency, where a fused unit's two latencies are equal.

Rounding the product before the addition is what makes the
intermediate result and the exceptions ordinary. The SPARC64 unfused
multiply-add rounds twice, in the unit's active IEEE-754 mode, which
makes the intermediate IEEE-754 compliant and the exceptions precise,
and it suppresses the addition when the multiply raises an exception.
That instruction takes 7 cycles at one per cycle in 0.15 um, reserves
half a cycle of every latency for result distribution, and blocks any
add, subtract, conversion, compare or move from that adder in the
cycle the bridged add runs. Under the definition that calls a MAF IEEE
compatible when it delivers the result of a sequential FMPY followed
by an FADD, the unoverlapped chained organization is the compatible
one. Its fused latency is the sum of the multiply and add latencies,
its stand-alone addition latency is the plain one, and its area is the
smallest of the organizations compared, because the adder and the
multiplier are optimized separately without the extra loading a fused
unit puts on them.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: the library's fp significand multiplier and fp adder composed: the exact product crosses the bridge as an X of twice the significand width into an adder generated for that width (`bridge_reuse`), or the product is rounded to d by the library rounder first (`cascade_mul_then_add`, `cascade_product_rounding`), which is the sequential contract; `monolithic_fused` is the classic_fma datapath). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## in the ALU's fp_fma slot

The ALU class offers the family on its `fp_fma` slot (fp_spaces.fp_fma_space) beside classic_fma, reduced_latency_fma and multipath_fma, one structure per float mode and lane: the bridge serves the mode's fadd and fsub as 1 * a + b, its fmul as a * b + 0 and its fused multiply-add ops (fmadd, fmsub, fnmsub, fnmadd) as a * b + c through one datapath under the op code `fop`, as every fused family of the slot does (families/fp.py `fma_sv` wraps dot.py's `_bridge_sv`). The family's multiplier and adder are its own slots (`multiplier`, and `align`, `lza`, `cpa`, `norm_shifter` for the adder, mapped onto the library's fp multiplier and single-path fp adder), so the mode's fp_adder and fp_multiplier slots stay closed under it, exactly as under the other fused families: nothing is declared twice, and the standalone add and multiply of the paper's bridge, which keep their own rate beside the fused op, are not what the ALU's family buys. What it buys is the composition from the library's own multiplier and adder, whose exact 2 SW-bit product crosses the bridge into an adder generated for that width. The specials follow the engine's order for each op as under classic_fma.

Three rules hold, each registered in `chialu/behavior_rules.py` (`docs/behav_checker_plan.md`), the seed's raise with the rule's text staying the last defense:

* `composition_style: cascade_mul_then_add` rounds the product before the add under its own fixed `cascade_product_rounding`, which is neither the one rounding the mode's fadd, fsub and fmul promise nor the mode's `rounding` that the ALU's `fma_contract: sequential` rounds the product under; the sequential contract's fused ops go through `separate_multiplier_and_adder`. The registry removes the member from the ALU's slot under every contract (`fma_contract_cascade_product_rounding`), and `cascade_product_rounding` is a decision under the cascade alone (a nested choice).
* `composition_style: bridge_reuse` needs the exact X: the bridge carries the 2 SW-bit product into the adder, and the guard-round-sticky X (the unit option `x_form: guard_round_sticky`) is narrower than the product. The registry removes the member under that option (`x_form_exact`).
* under `bridge_reuse` the choice `subnormal_representation` is inactive: the multiplier reads the stored significands and the adder normalizes both addends at its entry (the product fills its field, the addend the format's); the variant sweep rejects an explicit value as inactive (`alu_contracts`), and the registry records the inactivity as a deferred rule, since it holds under two siblings' values (the family and its `composition_style`) on a choice four families share. Under `monolithic_fused` the choice is classic_fma's.

The family itself is conditional on the unit's `fma_contract` as every fused family is: a mode with a fused op under `fma_contract: sequential` loses it (one rounding of the exact product plus addend is not the product rounded first).

Under `bridge_reuse` the adder returns the other operand as it came when one operand is zero, so the family promises nothing about its results' form and the mode's rounder keeps its normalizer (families/fp.py `fma_normalization`); `monolithic_fused` is classic_fma's text and carries classic_fma's promise.

### composition_style (the ALU's fp_fma slot)

| member | what it selects |
| --- | --- |
| `bridge_reuse` | the library's fp multiplier (`multiplier` slot) and single-path fp adder (`align`, `lza`, `cpa`, `norm_shifter` slots) composed, the exact product across the bridge as an X of twice the significand width, one rounding in the mode's rounder. |
| `cascade_mul_then_add` | the product rounded to the mode's format by the library rounder before the add (`cascade_product_rounding`): refused in the ALU, since the mode's fp ops promise one rounding. |
| `monolithic_fused` | classic_fma's datapath under the family's pins. |

### subnormal_representation (the ALU's fp_fma slot)

| member | what it selects |
| --- | --- |
| `as_stored` | under `monolithic_fused`, classic_fma's: a subnormal operand enters with its leading zeros and the one normalize after the sum absorbs them; inactive under `bridge_reuse`. |
| `pseudo_normalized_wide_exponent` | under `monolithic_fused`, each operand normalized at entry (the stochastic mode's need); inactive under `bridge_reuse`, whose adder normalizes both addends at its entry regardless. |

### negation_handling (the ALU's fp_fma slot)

| member | what it selects |
| --- | --- |
| `end_around_carry` | the adder's ones' complement difference with the end-around carry added back (under `bridge_reuse` the adder's unswapped datapath alone, which `lza.string_form: dual_pos_neg_strings` selects; the swapped datapath's difference is non-negative and takes none); classic_fma's window sum under `monolithic_fused`. |
| `dual_adder` | two adders (X - Y and Y - X) selected by the first one's carry, on the same datapaths. |
| `complement_recode` | one two's complement adder, the negative difference complemented after the fact, on the same datapaths. |

### sharing (the ALU's fp_fma slot)

| member | what it selects |
| --- | --- |
| `dedicated_per_mode` | one bridge per float mode and lane. |
| `shared_across_formats` | one physical bridge per lane at the widest geometry for every float mode that selects it, the operands muxed by the mode. |

## design choices

### cascade_product_rounding

| member | what it selects |
| --- | --- |
| `rne` | the cascaded product is rounded to nearest, ties to even, before it enters the next stage. |
| `truncate` | the cascaded product is truncated instead, which drops the rounding adder at the cost of a biased error. |

## references

quinnell_2008 -> E. Quinnell, E. E. Swartzlander, C. Lemonds, "Bridge Floating-Point Fused Multiply-Add Design", IEEE Transactions on VLSI Systems, vol. 16, no. 12, pp. 1726-1730, 2008
quinnell_2007 -> E. Quinnell, E. E. Swartzlander, C. Lemonds, "Floating-Point Fused Multiply-Add Architectures", 41st Asilomar Conference on Signals, Systems and Computers, 2007
lutz_2011 -> D. R. Lutz, "Fused Multiply-Add Microarchitecture Comprising Separate Early-Normalizing Multiply and Add Pipelines", Proc. 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 123-128, 2011.
lutz_2019 -> D. R. Lutz, "ARM Floating Point 2019: Latency, Area, Power", 26th IEEE Symposium on Computer Arithmetic, 2019
chong_2009 -> Y. J. Chong, S. Parameswaran, "Flexible Multi-Mode Embedded Floating-Point Unit for Field Programmable Gate Arrays", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2009
galal_2011 -> S. Galal, M. Horowitz, "Energy-Efficient Floating-Point Unit Design", IEEE Transactions on Computers, vol. 60, no. 7, 2011
galal_2013 -> S. Galal, O. Shacham, J. S. Brunhaver, J. Pu, A. Vassiliev, M. Horowitz, "FPU Generator for Design Space Exploration", ARITH-21, 2013
naini_2001 -> A. Naini, A. Dhablania, W. James, D. Das Sarma, "1-GHz HAL SPARC64 Dual Floating Point Unit with RAS Features", ARITH-15, 2001
quach_1991 -> N. Quach, M. Flynn, "Suggestions for Implementing a Fast IEEE Multiply-Add-Fused Instruction", Stanford CSL-TR-91-483, 1991
