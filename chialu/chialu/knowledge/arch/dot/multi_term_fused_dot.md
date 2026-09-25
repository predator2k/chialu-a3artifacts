# multi_term_fused_dot

N significand products are formed without rounding or normalization,
aligned to a common exponent, reduced together in carry-save form,
assimilated by one internal adder, and normalized and rounded once, so
an N-term dot product carries a single rounding error rather than one
per multiply and one per add. The alignment strategy fixes the error
contract, because the bits a product loses when it is shifted into the
common window are the only bits the contract must account for: a window
spanning the exponent range keeps every bit, a bounded window truncates
the smallest products behind guard bits.

The N=4 reference aligns the four sum/carry product pairs to the
largest product exponent without sorting, since the six exponent-sum
differences select the largest exponent and the four shifts directly;
duplicated 4:2 CSA trees form opposite-sign candidate pairs and a
significand comparison selects the positive one; a four-input LZA
predicts the normalization shift before the main addition, so early
normalization halves the width of the final adder and fixes the
rounding positions, and a compound adder computes sum and sum+1 while
rounding proceeds in parallel. Sorting the products by exponent through
pairwise comparisons and a crossbar is the alternative, and movable
realignment lines that select fixed regions inside the internal adder
keep that adder from spanning the exponent range while avoiding
excessive shifting; without a sticky bit before the internal addition
the correctly rounded contract reaches 0.5 ulp for round to nearest and
1 ulp for round toward zero. On an FPGA the fused squared-sum datapath
with 3 internal guard bits is last-bit accurate, and exact products
shifted into a fixed-point accumulator give the truncated-with-guard
contract with an error bounded by the window's least significant bit.

The family wins over a network of discrete multipliers and adders on
every axis, about 40 percent less area, latency and power for four
terms in 45 nm, and over a single long adder spanning the exponent
range at small N, while the long adder takes over as N grows because
the realignment shifters and comparison logic scale with the term
count. Its average error is a third of the operator network's. The
guard bits per level and the normalization deferral set how much of
that accuracy survives a bounded window, and the multiplier, reduction
and CPA slots are open. The datapath is feed-forward with a latency set
by the pipeline target.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: the unrounded products aligned by `alignment_strategy` (a per-level tree, the single wide window of the frame, a coarse and a fine shift stage, a max-exponent tree with right shifts to it, the pairwise exponent differences reused for the shifts, or an odd-even sorting network on the exponents with the shifts along the realignment lines), the sign handling by two's complement or by positive and negative reductions with the pair selected, the smallest product bypassed around the reduction when a cancellation is detected, the products normalized before the add on request, the `reduction` tree and the `lza` normalization; `correctly_rounded` keeps the exact frame, `faithful` and `truncated_with_guard` generate the window of `guard_bits_per_level` and the module comment names the contract). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## design choices

### alignment_strategy

| member | what it selects |
| --- | --- |
| `per_level` | a tree whose nodes align their two inputs to the larger exponent and add. |
| `single_wide_window` | one window wide enough for every term, which is the seed's exact frame. |
| `two_stage_coarse_fine` | a coarse shift then a fine one. |
| `max_exponent_tree` | a window anchored at the largest exponent, found by a tree. |
| `pairwise_difference_reuse` | the pairwise exponent differences computed once and reused across the terms. |
| `exponent_sorted_realignment_lines` | a sorting network over the exponents feeding realignment lines, with the first nonzero cluster selected after one add. |

### cancellation_handling

| member | what it selects |
| --- | --- |
| `none` | no term is bypassed. |
| `detect_and_bypass_smallest_operand` | the smallest operand is detected and bypassed, which keeps a cancelling pair from setting the window. |

### normalization_deferral

| member | what it selects |
| --- | --- |
| `per_term` | each product is normalized before it is aligned. |
| `final_only` | normalization waits for the sum, so the products enter the window as they are. |

### sign_handling

| member | what it selects |
| --- | --- |
| `post_add_complement` | the terms enter in two's complement and the sum is complemented after the add. |
| `dual_reduction_positive_pair_select` | the positive and negative terms are reduced separately and the pair is selected. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the realignment lines are sized to the exponent range, so the adder does not rise to the exact frame | alignment_strategy=exponent_sorted_realignment_lines | `realignment lines: \d+ lines of \d+ bits` |
| the products enter unrounded and one normalization closes the sum | - | `unrounded products aligned by` |

## references

sohn_2016 -> J. Sohn, E. E. Swartzlander, "A Fused Floating-Point Four-Term Dot Product Unit", IEEE TCAS-I, vol. 63, no. 3, pp. 370-378, 2016
tao_2013 -> T. Yao, D. Gao, X. Fan, J. Nurmi, "Correctly Rounded Architectures for Floating-Point Multi-Operand Addition and Dot-Product Computation", IEEE ASAP, pp. 346-355, 2013
dedinechin_2011 -> F. de Dinechin, B. Pasca, "Designing Custom Arithmetic Data Paths with FloPoCo", IEEE Design and Test of Computers, vol. 28, no. 4, 2011
dedinechin_2008 -> F. de Dinechin, B. Pasca, O. Cret, R. Tudoran, "An FPGA-Specific Approach to Floating-Point Accumulation and Sum-of-Products", IEEE FPT, pp. 33-40, 2008
