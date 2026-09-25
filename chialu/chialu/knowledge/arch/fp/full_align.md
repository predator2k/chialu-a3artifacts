# full_align

Alignment right-shift across the full exponent difference: after the exponent compare the smaller significand is swapped into the shifter and moved by the whole difference, the shifted-out bits are gathered into guard, round and sticky, and the wider operand stays fixed. It is the shifter of a single-path adder, of the far path of a two-path adder, and of the addend of an FMA, where the addend aligns across a 3m+2 window in parallel with the multiply.

The shifter slot fixes the tree (and its stage radix, which trades levels against fan-in per level), funnel or masked implementation; a pass-transistor shifter took less area than a binary-weighted mux tree. The fp add family's operand_order selects the smaller operand ahead of one shifter (swap_before_shift) or duplicates the shifter and computes both exponent differences in parallel (shift_each_operand: each operand shifted by its own amount, the difference taken both ways and the non-negative one selected), which shortens the far path at the cost of a second shifter and a second subtractor. sticky_method chooses an OR tree over the shifted-out bits, a mask from the shift amount, or a trailing-zero count compare that never examines the discarded bits; sticky runs in parallel with the shift and never extends its delay. In an FMA aligning only the addend keeps the product sum and carry off the shifter, the 161-bit aligner and adder form a wire-dominated critical path, and bits shifted far below the product affect only the final rounding. Under a short cycle the align and sticky split across stage boundaries.

full_align is the library's aligner: the engine's X keeps every bit of the alignment window and its stochastic rounding compares the dropped bits exactly, so a shift bounded below the window (Seidel's bounded alignment, exact only for rounding at the format's precision under the IEEE modes) changes the packed result. A close path's shift is limited by the family's path threshold rather than by the aligner.

## design choices

### sticky_method

| member | what it selects |
| --- | --- |
| `or_tree_shifted_out` | the sticky comes from the alignment shifter's own collection of the bits it drops. |
| `precomputed_mask` | a thermometer mask of the dropped positions is ORed against the operand. |
| `trailing_zero_compare` | the operand's trailing-zero count, from the trailing-zero slot, is compared against the shift amount. |

## references

ercegovac_2004 -> M. D. Ercegovac and T. Lang, "Digital Arithmetic", Morgan Kaufmann, 2004
nielsen_2000 -> A. M. Nielsen, D. W. Matula, C. N. Lyu, G. Even, "An IEEE Compliant Floating-Point Adder that Conforms with the Pipelined Packet-Forwarding Paradigm", IEEE Transactions on Computers, 2000
beaumont_smith1999 -> A. Beaumont-Smith, N. Burgess, S. Lefrere, C.-C. Lim, "Reduced Latency IEEE Floating-Point Standard Adder Architectures", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999.
quinnell_2007 -> E. Quinnell, E. E. Swartzlander, C. Lemonds, "Floating-Point Fused Multiply-Add Architectures", 41st Asilomar Conference on Signals, Systems and Computers, 2007
schwarz_2005 -> E. M. Schwarz, M. Schmookler, S. D. Trong, "FPU Implementations with Denormalized Numbers", IEEE Transactions on Computers, 2005
oberman_1996 -> S. F. Oberman and M. J. Flynn, "A Variable Latency Pipelined Floating-Point Adder", Euro-Par'96 Parallel Processing (LNCS 1124), Springer, 1996
montoye_1990 -> R. K. Montoye, E. Hokenek, S. L. Runyon, "Design of the IBM RISC System/6000 Floating-Point Execution Unit", IBM Journal of Research and Development, 1990
santoro_1989 -> M. R. Santoro, G. Bewick, M. A. Horowitz, "Rounding Algorithms for IEEE Multipliers", 9th IEEE Symposium on Computer Arithmetic, 1989
