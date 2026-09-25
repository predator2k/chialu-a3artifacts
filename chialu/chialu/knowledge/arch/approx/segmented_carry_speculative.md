# segmented_carry_speculative

Addition split into parallel sub-adders whose carry-ins are guessed
rather than propagated: each k-bit sub-adder takes its carry from a
short window of preceding operand bits (a constant, a
propagate/generate window, a carry-select pair resolved by a block
propagate, or a cut-back gate that substitutes a fixed guess when a
long propagate run is detected), so the critical path spans one or two
blocks instead of the full width. A wrong guess needs a propagate chain
longer than the window, whose probability falls exponentially with
window length for random operands; the correction stage repairs the
sign, shrinks the error magnitude in place, or rebuilds the exact sum
in an extra cycle.

The sub_adder_width and prediction_window choices set the same
accuracy/delay slope from two sides: larger blocks and longer windows
raise the carry-correctness probability and lengthen the block path,
smaller ones raise speed and error rate. A 16-bit adder with 4-bit
blocks reaches a 0.18% error rate and 2.4x the speed of ripple carry in
90 nm, while 2-bit blocks push the error rate above 11%. Overlapping
windows (GeAr's R committed bits out of L = R + P) reproduce the ACA
and ETAII points as special cases, and the window a wide adder needs
for a 99.99% pass rate grows only logarithmically, from 17 bits at 64
bits to 23 at 2048.

The carry_in_scheme choice trades prediction quality for hardware: a
fixed carry is cheapest and suits high error tolerance, propagate
windows cost a small predictor, carry-select speculation duplicates
carry paths for the best accuracy at more power and area, and carry
cut-back cuts from the MSB side with a propagate monitor and a single
guess direction so errors never accumulate in one direction. Savings
depend on the timing target: the cut-back adder saves 44% of energy at
0.8 GHz but 14% at 3.3 GHz in a 65 nm library at 2% maximum relative
error. The correction choice sets the error contract. No correction
leaves single-sided errors with large bias; the error-reduction stage
forces all-propagate blocks to one and lowers the worst-case magnitude
from 2^(n-k) to 2^(n-3k), or bounds the maximal relative error to
1/2^k; sign repair guarantees the two's-complement sign; the extra
cycle detects the all-ones/carry condition and increments, which turns
the adder into an exact variable-latency one at about 28% detection
area.

The family is feed-forward and single-cycle in its approximate mode and
stalls only in the extra-cycle variants. Its error is data dependent
and deterministic, is specified as an error rate plus MRED/NMED under
uniform inputs, and is accepted by image, DSP, machine-learning and neuromorphic
consumers. It also
serves as the final CPA of approximate multipliers and as the base
adder of the speculative variable-latency family.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/approx.py`: sub-adders of the `sub_adder` family with the carry into each from a `prediction_window` of the bits below (a zero, the window's carry, a carry-select of both candidates, or the cut-back that keeps the true carry unless the window propagates), and a correction that repairs a missed carry on the top block or every block; the extra cycle is a combinational stage here); the ArithmeticError gate governs.

## design choices

### correction

| member | what it selects |
| --- | --- |
| `none` | the speculated carries stand, so a mispredicted segment leaves its error in the result. |
| `sign_repair` | a repair stage corrects the sign of a mispredicted segment. |
| `error_reduction_stage` | a reduction stage subtracts the mispredicted segment's contribution. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the adder is sub-adders whose carry-in is speculated over a window | - | `sub-adders .* carry-in by \w+ over a \d+-bit window` |

## references

verma2008 -> A. K. Verma, P. Brisk, P. Ienne, "Variable Latency Speculative Addition: A New Paradigm for Arithmetic Circuit Design", Design, Automation and Test in Europe (DATE), 2008
ebrahimi2020 -> F. Ebrahimi-Azandaryani, O. Akbari, M. Kamal, A. Afzali-Kusha, M. Pedram, "Block-Based Carry Speculative Approximate Adder for Energy-Efficient Applications", IEEE Transactions on Circuits and Systems II, vol. 67, no. 1, pp. 137-141, 2020
kahng_kang2012 -> A. B. Kahng, S. Kang, "Accuracy-Configurable Adder for Approximate Arithmetic Designs", 49th Design Automation Conference (DAC), pp. 820-825, 2012
kim2013 -> Y. Kim, Y. Zhang, P. Li, "An Energy Efficient Approximate Adder with Carry Skip for Error Resilient Neuromorphic VLSI Systems", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 130-137, 2013
shafique2015 -> M. Shafique, W. Ahmad, R. Hafiz, J. Henkel, "A Low Latency Generic Accuracy Configurable Adder", 52nd Design Automation Conference (DAC), 2015
hu_qian2015 -> J. Hu, W. Qian, "A New Approximate Adder with Low Relative Error and Correct Sign Calculation", Design, Automation and Test in Europe (DATE), pp. 1449-1454, 2015
camus2016 -> V. Camus, J. Schlachter, C. Enz, "A Low-Power Carry Cut-Back Approximate Adder with Fixed-Point Implementation and Floating-Point Precision", 53rd Design Automation Conference (DAC), 2016
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
