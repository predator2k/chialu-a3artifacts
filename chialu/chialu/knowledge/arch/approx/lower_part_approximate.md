# lower_part_approximate

A k-bit addition split into an exact upper module of m bits and an
approximate lower module of n bits: the upper part is any precise
adder, and the lower cells are replaced by something cheaper than a
full adder. The lower-part OR adder (LOA) forms each lower sum bit as
the OR of the operand bits and feeds the upper adder an AND of the two
most significant lower input bits as carry-in; the cell variants
instead keep a ripple of transistor-reduced mirror adders (AMA),
XOR/XNOR pass-transistor cells (AXA), inexact cells with an exact sum
or an exact carry (InXA), or reverse-carry cells whose carry runs from
the joining point down toward the LSB, and truncation drops the lower
bits altogether.

The accuracy contract is a deterministic functional error confined to
the lower bits: the worst case is 2^(m-1) for m approximate bits, the
error rate is high, growing as 1 - (3/4)^m for the OR cell, the
relative error is small, and the mean is near zero or slightly
negative for the OR cell, while set-to-one or truncated lower parts
are biased. Error masking keeps a lower-bit error from entering the
upper part, so only the most significant approximate bit raises the
mean error distance. The lower width is the main knob: each further
approximate bit saves 21 to 31 gates and 0.16 to 0.55 ns against a
precise ripple adder in 0.13-µm CMOS, but the error probability rises
from about 40 percent at 2 bits to about 90 percent at 8, the MSE
grows exponentially, and JPEG DCT quality degrades appreciably beyond 9 approximate bits.

The lower cell trades power against error shape. The OR cell costs
about 0.2 of a full-adder cell's power per lower bit where the mirror
variants cost 0.8 to 0.95, and it has the best power-saving to error
ratio of the compared designs; the mirror cells cut a 40.66 µm² cell
to 13.5 to 29 µm² in IBM 90 nm and keep a carry path so their error
can be shaped per application; the XOR/XNOR cells reach 6 to 8
transistors but lose full swing; the inexact cells with an exact carry
stop error propagation between cells; the reverse-carry cells give the
smallest hybrid delay and energy-delay product because an unfinished
carry loses weight as it moves toward the LSB. The carry-to-upper
choice sets whether the boundary receives a speculative AND, the
lower cell's own carry, or nothing.

The family wins in error-tolerant DSP such as image, DCT, FIR and
SAD arithmetic and in accumulation where a low average bias matters,
and it beats truncation on quality at a similar power saving. It
loses when the application is sensitive to error frequency regardless
of magnitude, when biased errors cascade through matrix computations,
and in general-purpose processors where arithmetic is a small share
of energy.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/approx.py`: an exact upper adder of the `upper_adder` family and the low `lower_width` bits by the cell style (forced constants, OR gates, the AXA xnor-sum / first-operand carry, the AMA majority carry with the complemented sum, the InXA exact sum with the first-operand carry, or the reversed carry chain), the carry into the upper part none, the top AND, or a window's carry); the ArithmeticError gate governs.

## design choices

### carry_to_upper

| member | what it selects |
| --- | --- |
| `none` | the upper adder's carry-in is tied to zero, so the low part never propagates into the exact part. |
| `msb_and` | the carry-in is the AND of the two most significant low bits, which is the cheapest estimate of the low part's carry-out. |
| `window_speculation` | the carry-in is the carry-out of an exact add over the top `window` bits of the low part. |

### lower_cell

| member | what it selects |
| --- | --- |
| `truncate_constant` | the low sum bits are held at one, which is the constant closest to the mean of a truncated part. |
| `or_gate` | each low sum bit is the OR of the operand bits (the LOA cell). |
| `xor_xnor_axa` | the AXA cell: the low sum bit is the XNOR of the operand bits. |
| `approx_mirror_ama` | the AMA mirror-adder cell, whose transistor-level simplification the RTL renders as its logic function. |
| `inexact_cell_inxa` | the InXA cell family, whose sum and carry expressions drop terms of the exact cell. |
| `reverse_carry_rcpa` | the low part keeps an exact chain whose carries run from the most significant low bit down, so the error is bounded by the chain's direction rather than by a dropped carry. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the upper part stays exact and the substituted cells sit in the low part | - | `the upper \d+ bits exact .* the low \d+ bits by` |

## references

mahdiani2010 -> H. R. Mahdiani, A. Ahmadi, S. M. Fakhraie, C. Lucas, "Bio-Inspired Imprecise Computational Blocks for Efficient VLSI Implementation of Soft-Computing Applications", IEEE Transactions on Circuits and Systems I, vol. 57, no. 4, pp. 850-862, 2010
gupta2013 -> V. Gupta, D. Mohapatra, A. Raghunathan, K. Roy, "Low-Power Digital Signal Processing Using Approximate Adders", IEEE Transactions on Computer-Aided Design, vol. 32, no. 1, pp. 124-137, 2013
liang2013 -> J. Liang, J. Han, F. Lombardi, "New Metrics for the Reliability of Approximate and Probabilistic Adders", IEEE Transactions on Computers, vol. 62, no. 9, pp. 1760-1771, 2013
jiang2017 -> H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
yang2013 -> Z. Yang, A. Jain, J. Liang, J. Han, F. Lombardi, "Approximate XOR/XNOR-Based Adders for Inexact Computing", 13th IEEE International Conference on Nanotechnology (IEEE-NANO), pp. 690-693, 2013
almurib2016 -> H. A. F. Almurib, T. N. Kumar, F. Lombardi, "Inexact Designs for Approximate Low Power Addition by Cell Replacement", Design, Automation and Test in Europe (DATE), pp. 660-665, 2016
pashaeifar2018 -> M. Pashaeifar, M. Kamal, A. Afzali-Kusha, M. Pedram, "Approximate Reverse Carry Propagate Adder for Energy-Efficient DSP Applications", IEEE Transactions on VLSI Systems, vol. 26, no. 11, pp. 2530-2541, 2018
