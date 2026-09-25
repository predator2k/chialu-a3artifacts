# lza

Leading-zero/one anticipation: the normalization shift of an effective subtraction is predicted from the adder inputs while the carries propagate, by forming per-bit generate/propagate/zero tokens, combining them into an indicator string whose first set bit marks the leading digit, and encoding that string with the encoder slot; the prediction is exact or one position too large, because unmonitored low-order bits can carry into the position. The count completes in about log(n) time beside the adder, so normalization needs no post-add count.

correction_scheme handles the one-bit error: post_norm_fine_shift is a one-bit shift after normalization, compensation_in_rounding leaves the value one position short for the rounder's own normalization to absorb; a concurrent correction tree that yields the exact position in parallel with the anticipation, and an exact true count compared at the LSB, are circuit-level forms of the first. string_form and split_string_select set whether one indicator serves both signs (single_indicator, the Schmookler-Nowka string) or separate positive and negative strings are formed (dual_pos_neg_strings, over the two orders of the unswapped operands) and chosen by the true sign or by the higher leading one of the two counts (maximum_count, the smaller zero count, since either string may over-anticipate by one). indicator_restriction simplifies the logic when the result is known positive (positive_result_only: the swapped datapath's difference, or the string of each order), where the first function is a generate and the following zero positions give the count. zero_result_detect finds an all-zero difference from the normalized result (indicator_or) or from the operands' equality (operand_function_or). The anticipator reads the adder's operands; a carry-save pair (an FMA anticipates over the product and aligned addend, a packet-forwarding adder over a partially compressed borrow-save sum) and four inputs (a fused dot product) are the fused units' forms, and emitting the shift MSB first or as one-hot controls so shifting starts before encoding ends is a shifter-control encoding the library's binary count does not use. The four-bit initial groups of the origin design reflect an anticipation cell more complex than a carry cell; a pseudo-LZA or a plain LZC costs less area and power.

The correction can be detected before the normalizer runs. The CELL single-precision unit forms generate, propagate and kill per bit on the merging 3:2 counter's output and detects an edge from the current bit's and the two preceding bits' tokens, with the sign bit extended; the first stage emits the edge vector and the second counts its leading zeros. That unit also emits a mask vector carrying a single one at the shift position, which is ANDed with the adder output into a zero checker, so the one-too-large case is resolved from the mask rather than from the normalizer output's most significant bit, and the result multiplexer selects bits 0 to 23 or bits 1 to 24 of the normalized fraction. The estimate itself comes from the edge-vector count when the result comes only from the compound adder, and from the aligner's shift amount when the incrementer also contributes.

Bounding the shift for a denormalized result is an anticipator modification rather than a normalizer option, because the normalizer must not shift past the radix point of a denormal result. The maximum shift a denormal admits, indexed against the difference of the product exponent and Emin, is compared with the anticipated shift and the lesser selected; two units produce the two shift amounts in parallel, one supporting the normalized dataflow with limited shifts and a slow one supporting the maximum shift amounts; or the comparison and the selection of the lesser collapse into one equation. The remaining forms inject the bound into the anticipator itself. Forcing the LZA bit at the most significant bit position of a denormal to one decodes the maximum shift in parallel. ORing a monotonic denormal mask U into the monotonic LZA vector V before encoding gives M = V + U and Shift = LZD(M), which is the Power3 form, and ORing the denormal vector into both the carry and the sum inputs of the anticipator is the PowerPC A50 form.

An LZA is mandatory wherever normalization must overlap the add (every MAF and close path); lzc_after_add is the pick when the result arrives early enough anyway or when energy matters more than latency.

## design choices

### indicator_restriction

| member | what it selects |
| --- | --- |
| `general` | the indicator string covers both signs of the result. |
| `positive_result_only` | the string assumes a non-negative difference, which the swapped datapath guarantees. |

### split_string_select

| member | what it selects |
| --- | --- |
| `true_sign` | the positive and negative strings are selected by the true sign of the difference. |
| `maximum_count` | the two strings are selected by the larger leading-zero count, which needs no sign. |

## references

hokenek_cook_1990 -> E. Hokenek, R. K. Montoye, P. W. Cook, "Second-Generation RISC Floating Point with Multiply-Add Fused", IEEE Journal of Solid-State Circuits, vol. 25, no. 5, pp. 1207-1213, 1990
hokenek_1990 -> E. Hokenek and R. K. Montoye, "Leading-Zero Anticipator (LZA) in the IBM RISC System/6000 Floating-Point Execution Unit", IBM Journal of Research and Development, 1990
suzuki_1996 -> H. Suzuki, H. Morinaka, H. Makino, Y. Nakase, K. Mashiko, T. Sumi, "Leading-Zero Anticipatory Logic for High-Speed Floating Point Addition", IEEE Journal of Solid-State Circuits, 1996
bruguera_1999 -> J. D. Bruguera and T. Lang, "Leading-One Prediction with Concurrent Position Correction", IEEE Transactions on Computers, 1999
schmookler_2001 -> M. S. Schmookler, K. J. Nowka, "Leading Zero Anticipation and Detection — A Comparison of Methods", Proc. ARITH-15, pp. 7-12, 2001
lang_2004 -> T. Lang, J. D. Bruguera, "Floating-Point Multiply-Add-Fused with Reduced Latency", IEEE Transactions on Computers, vol. 53, pp. 988-1003, 2004
sohn_2016 -> J. Sohn, E. E. Swartzlander, "A Fused Floating-Point Four-Term Dot Product Unit", IEEE TCAS-I, vol. 63, no. 3, pp. 370-378, 2016
dimitrakopoulos_2008 -> G. Dimitrakopoulos, K. Galanopoulos, C. Mavrokefalidis, D. Nikolos, "Low-Power Leading-Zero Counting and Anticipation Logic for High-Speed Floating Point Units", IEEE Transactions on VLSI Systems, 2008
oh_2006 -> H.-J. Oh et al., "A Fully Pipelined Single-Precision Floating-Point Unit in the Synergistic Processor Element of a CELL Processor", IEEE Journal of Solid-State Circuits, vol. 41, no. 4, 2006
schwarz_2003 -> E. M. Schwarz, M. Schmookler, S. D. Trong, "Hardware Implementations of Denormalized Numbers", 16th IEEE Symposium on Computer Arithmetic, 2003
