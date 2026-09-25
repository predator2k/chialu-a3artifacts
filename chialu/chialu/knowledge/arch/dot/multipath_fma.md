# multipath_fma

A fused multiply-add whose datapath forks after the multiplier tree into mutually exclusive paths, chosen early from the exponent difference d = Ex + Ey - Ez and in some designs from the effective operation sign, so each path carries only the alignment, normalization, and rounding work its case needs and the inactive path is clock- or power-gated. A far path handles large exponent differences, anchored on the addend or on the product; a close path handles effective subtraction at near-equal exponents, where the addend shifts by at most a few bits, can enter the multiplier's compression tree, and a leading-zero anticipator drives normalization. The paths rejoin in one shared add/round stage.

path_count trades area for latency and power. Two paths, a near path for d in {-2, -1, 0, 1} and a far path for everything else, give 72 critical-path logic levels against 84 for the Power6 FMA and 76 for Lang's, at about 8% more area than Power6 and 12% less than Lang in a normalized block estimate. Three paths, an addend-anchored far path, a product-anchored far path, and a subtraction-only close path, cut latency by 11.7% and maximum power by 14.8% below a classic FMA in AMD 65-nm SOI standard cells at 38.6% more area. Five logical cases can share two physical major paths, with the close-subtraction case alone getting small alignment, unconditional operand negation, integrated addition, rounding, and leading-zero counting, and combined normalization and post-normalization. path_select_criterion decides whether the close path is entered on exponent difference alone or only for effective subtraction, which confines cancellation handling to the one path that needs it. Because the near path is the short chain, it is also what add_accumulate_forwarding_path exploits: a case-dependent latency lets a variable-latency unit expose the result earlier and shortens the loop-carried accumulate dependence.

The slots specialize per path. align is bounded on the close path and full on the far path, lza serves the close path while the far path needs no leading-zero count beyond one position, and the multiplier can use radix-8 Booth for the far cases and radix-4 for the close case. One completion rounder serves both paths, as injection rounding or compound-adder selection. The family keeps the 1/2-ulp contract and all four IEEE rounding modes; subnormal handling is not established in the split-path design, whose inputs are normalized. It wins where latency and power dominate and area is available, and loses to the classic single datapath on area; the three-path design also does not provide a full-performance floating-point add without further work.

Five cases can also run at different latencies rather than at one. The far-out case, where the addend is so much larger than the product that their fractions do not overlap, finishes in one third of the slow near path's latency, so a variable-latency unit built this way suits an out-of-order processor while a fixed-latency variant with two parallel datapaths suits an in-order one. Two parallel datapaths mean two full-size multipliers and adders, which raise single-precision FPU area by about 50 percent and more at double precision, and add 5 FO4 for distributing the operands to both paths and collecting their results. That overhead was judged unacceptable for a unit replicated across a multi-core chip, where a single datapath reaches about the same latency in logic levels once its exponent-rounding and result-selection optimizations are applied. All four rounding modes run at the same latency on both paths.

Splitting on the exponent difference need not split at a difference of 1. SNAP divides six exponent cases at a difference of 2, because summing the carry-save product's two vectors may overflow, and shares one rounding mask between the paths, which is a string of ones followed by a string of zeros whose transition point gives the carry point and whose weight supplies the rounding constant. SNAP has the lowest fused latency of the four organizations compared, for a small increase in stand-alone addition latency over the unoverlapped chained unit and in area over the partially overlapped one, paid in wire and design complexity. A quadruple-precision two-path implementation fixes the close path's negation without an end-around carry. The addend is aligned by a 3-bit shifter, inverted, and summed with the multiplier result in a 117-bit 3:2 CSA whose empty slot carries the two's complement +1, while a row of half adders carries the same +1 on the far path. Its close path is entered for effective subtraction at an exponent difference of -1, 0 or 1, and at -2 when the multiplication overflows. Its far path performs the full-length alignment with one shifter shared between the product and the addend and normalizes in the second stage, and both paths extend into the third stage rather than splitting only the second. Post-layout in 65 nm that unit measures 149,343 um2 at 427 MHz and 618.47 pJ per operation for one double-precision or two single-precision instructions.

An accumulate loop splits the same way. A four-path single-precision multiply-accumulator selects from 3-bit exponent comparisons. One path shifts the smaller mantissa right by 32 bits and adds, when the exponents are equal or differ by one. One path bypasses the adder and selects the larger number, when they differ by more than one. One path handles more than 31 leading zeros or ones in the accumulated result through a second 4-2 adder, and takes priority over the bypass. One path selects the incoming mantissa when the feedback mantissa is zero, which is needed because the feedback exponent may then be non-zero and would shift the incoming mantissa wrongly. That organization holds the accumulation critical path to 9 FO4 in 90 nm. The leading-zero path is what keeps a non-commutative input stream correct, and its second 4-2 adder can be removed where the additions commute.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: the classic window computed along `path_count` paths (the close path with the anticipator for a possible cancellation, the far path without one, the far case split by which operand shifts, the close case split by the effective operation, a zero-operand bypass) and selected by `path_select_criterion` (the exponent difference, a cancellation estimate from the operands' leading positions, or both)). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

In the combinational generator, two or three paths reserve the close
path for effective subtraction. Four paths add a separate close-addition
datapath, selected when the product and addend leading-position estimates
differ by at most one. Five paths additionally bypass zero operands.
`path_select_criterion` controls the close-subtraction decision; the
close-addition path uses exponent proximity because addition has no
cancellation to estimate. Its normalization uses the selected
`norm_shifter` component. The path-activity regression checks the actual
result mux and independently verifies the fused result and flags.

## design choices

### path_select_criterion

| member | what it selects |
| --- | --- |
| `exponent_difference` | the path is chosen from the exponent difference. |
| `cancellation_estimate` | the path is chosen from an estimate of the cancellation. |
| `both` | both criteria select together. |

### subnormal_representation (the ALU's fp_fma slot)

| member | what it selects |
| --- | --- |
| `as_stored` | a subnormal operand enters with its leading zeros; the exponent alignment places it in the window and the one normalize after the sum absorbs the zeros (FPnew's `is_subnormal` exponent adjustment, no normalizer at entry); the IEEE modes. |
| `pseudo_normalized_wide_exponent` | each operand normalized at entry by a leading-zero count and a shift, its exponent lowered (the dot class's contract, which the stochastic mode's exact comparison of the dropped bits needs). |

### negation_handling (the ALU's fp_fma slot)

| member | what it selects |
| --- | --- |
| `end_around_carry` | the ones' complement window sum with the end-around carry added back through an incrementer. |
| `dual_adder` | two window adders (X + Y or X - Y, and Y - X) selected by the first one's carry. |
| `complement_recode` | one two's complement adder, the negative sum complemented after the fact. |

### sharing (the ALU's fp_fma slot)

| member | what it selects |
| --- | --- |
| `dedicated_per_mode` | one fused datapath per float mode and lane. |
| `shared_across_formats` | one physical datapath per lane at the widest geometry for every float mode that selects it, the operands muxed by the mode. |

## references

seidel_2003 -> P.-M. Seidel, "Multiple Path IEEE Floating-Point Fused Multiply-Add", IEEE MWSCAS, 2003
quinnell_2007 -> E. Quinnell, E. E. Swartzlander, C. Lemonds, "Floating-Point Fused Multiply-Add Architectures", 41st Asilomar Conference on Signals, Systems and Computers, 2007
srinivasan_2013 -> S. Srinivasan, K. Bhudiya, R. Ramanarayanan, P. S. Babu, T. Jacob, S. Mathew, R. Krishnamurthy, V. Erraguntla, "Split-Path Fused Floating Point Multiply Accumulate (FPMAC)", ARITH-21, pp. 17-24, 2013
mueller_2005 -> S. M. Mueller et al., "The Vector Floating-Point Unit in a Synergistic Processor Element of a CELL Processor", ARITH-17, pp. 59-67, 2005
manolopoulos_2016 -> K. Manolopoulos, D. Reisis, V. A. Chouliaras, "An Efficient Multiple Precision Floating-Point Multiply-Add Fused Unit", Microelectronics Journal, vol. 49, 2016
quach_1991 -> N. Quach, M. Flynn, "Suggestions for Implementing a Fast IEEE Multiply-Add-Fused Instruction", Stanford CSL-TR-91-483, 1991
vangal_2006 -> S. Vangal, Y. Hoskote, N. Borkar, A. Alvandpour, "A 6.2-GFlops Floating-Point Multiply-Accumulator With Conditional Normalization", IEEE Journal of Solid-State Circuits, vol. 41, no. 10, 2006
