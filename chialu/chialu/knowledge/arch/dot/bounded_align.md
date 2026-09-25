# bounded_align

The alignment choice of the dot accumulators' `align` slot (`fma_dot_spaces.dot_align_space`): the products stay in their exponent band and the addend joins through a near window or a far word, exactly (the construction below). The floating-point adder's own bounded alignment left its `align` slot on 2026-09-12, since the engine keeps the whole window there (`docs/deferred-families.md`); the paragraphs that follow keep the family's literature.

Alignment right-shift clamped to significand+guard positions: the shift amount saturates at the bound, and an operand shifted past it collapses into the sticky bit, so the shifter is a fixed log-depth mux tree independent of the exponent range and the sticky is a function of the shift amount and low operand bits computed in parallel with the shift. The clamp is what keeps a far-path or accumulator input shifter minimal.

bound sets the clamp and with it the datapath width; mux_radix and the shifter slot fix the tree; swap_before_shift decides whether the smaller operand is selected before or after the shifter; sticky_method chooses an OR tree over the shifted-out bits, a mask precomputed from the amount, or a trailing-zero count compare that never examines the discarded bits. Bounded alignment is the close-path and accumulator idiom: a close path needs at most a one- or two-bit pre-alignment so its result arrives early enough for post-add counting, an exact fixed-point accumulator shifts every product bit into a window whose LSB bounds the error, and the 1959 Stretch adder bounded its repeated shifting so that 80 per cent of numbers finished within six shifting cycles. In an FMA the aligner keeps two positions beyond the product LSB for the rare denormal subtraction case.

Choose it over full_align when the path organization already excludes large exponent differences or when precision beyond the bound is sticky by contract; full_align is required on a single path that must handle every difference.

In the dot accumulators (`chialu/targets/rtl/families/dot.py`, `BandGeom`) the choice bounds the alignment of a floating-point accumulate with an addend: the products stay in their exponent band (the frame without the addend's range), the products' sum meets the addend in a near window of max(Sc, XW) + `bound` guard positions below the band and XW + Sc above it (an addend below the window is a sticky by the `sticky_method`, through the shifter's own collection, a thermometer mask or the `tzc` slot's trailing-zero count against the shift; a negative truncated addend borrows one lsb through the adder's carry-in, so the window sum is the floor of the exact sum), and an addend whose lsb is at or above the band's top plus XW + 1 + `bound` - Sc takes the far word: its magnitude less one lsb with ones below when the products' sum has the other sign, the sticky set. A zero products' sum bypasses to the addend. The result is exact to the X's last bit: a nonzero products' sum is at least one band lsb, so an addend entirely below the window leaves the leading one at or above the band's lsb minus one with XW + 1 window bits under it, and a far addend exceeds the products' sum by more than the far word's lsb. On fp16 x fp32 with four products the near window is 193 bits against the 281-bit frame; on a mode whose addend range lies inside the products' band the window clips to the frame.

## design choices

### sticky_method

| member | what it selects |
| --- | --- |
| `or_tree_shifted_out` | the sticky comes from the alignment shifter's own collection of the bits it drops. |
| `precomputed_mask` | a thermometer mask of the dropped positions is ORed against the addend. |
| `trailing_zero_compare` | the addend's trailing-zero count, from the trailing-zero slot, is compared against the shift amount. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the addend enters a near window around the products' band, or a far word | kind=dot;family=pairwise_tree;align.family=bounded_align | `the bounded alignment` |

## references

seidel_2004 -> P.-M. Seidel and G. Even, "Delay-Optimized Implementation of IEEE Floating-Point Addition", IEEE Transactions on Computers, 2004
bloch_1959 -> E. Bloch, "The Engineering Design of the Stretch Computer", Proc. Eastern Joint Computer Conference, pp. 48-58, 1959.
seidel_2003 -> P.-M. Seidel, "Multiple Path IEEE Floating-Point Fused Multiply-Add", IEEE MWSCAS, 2003
dedinechin_2008 -> F. de Dinechin, B. Pasca, O. Cret, R. Tudoran, "An FPGA-Specific Approach to Floating-Point Accumulation and Sum-of-Products", IEEE FPT, pp. 33-40, 2008
pillai_1997 -> R. V. K. Pillai, D. Al-Khalili, A. J. Al-Khalili, "A Low Power Approach to Floating Point Adder Design", IEEE International Conference on Computer Design (ICCD), 1997
santoro_1989 -> M. R. Santoro, G. Bewick, M. A. Horowitz, "Rounding Algorithms for IEEE Multipliers", 9th IEEE Symposium on Computer Arithmetic, 1989
