# pp_perforation

Parallel multiplication with partial-product rows left out: the
multiplier omits k successive partial products from row j, so each
omitted row removes n full adders and can remove a tree level, and
the error is the multiplicand times the omitted k-bit field of the
multiplier, bounded and predictable from j, k and the operand PDFs.
The broken-array form removes carry-save cells above a horizontal
break and right of a vertical break instead. The cell choice replaces
the exact AND partial products with a 2x2 underdesigned block that
returns 7 for 3x3 and is correct on the other fifteen inputs, tiled
over 2-bit operand groups and summed by an accurate adder network.

perforated_rows and the first omitted row set the error: under
uniform inputs NMED grows with 2^j (2^k - 1), the optimal pair depends
on the error constraint and the operand distribution (correlated audio
favours a later first row than uniform data), and signed operands keep
the last partial product. Perforation shortens the accumulation tree
where truncation alone does not touch the critical path, which gives
up to 50 percent power, 45 percent area and 35 percent delay
reduction at 16 bits under NMED below 10^-3 in 65 nm, with larger
widths saving more for the same error. The broken array trades the
other way: the horizontal break is the coarse and the vertical break
the fine control, the result never exceeds the exact product, and the
array keeps its slower structure, so PPAM has the shortest delay at
large error while BAM has the lowest power at medium accuracy. The
modified-Booth form perforates the least-significant Booth digits and
rounds the multiplicand at a chosen bit for extra energy at a slight
error increase.

The underdesigned cell moves the trade to the error rate: the cell
errs on one input in sixteen with a maximum error of 22.22 percent,
the multiplier-level error probability grows with width, and the
accurate accumulation keeps the overhead high, so NMED and MRED are
large for the error rate; mixing exact and inexact cells tunes the
curve, and inaccurate partial products beat inaccurate adders in the
tree. The correction choice ranges from operand swapping after
comparing the perforated fields or the whole operands, which lowers
the mean error but cannot help squaring, to a decoder plus residual
adder that recovers the exact product for about a tenth more area at
16 bits in 45 nm.

The accuracy contract is statistical: most configurations have an
error rate close to 100 percent, the error is bounded and its
distribution follows from j, k and the operand PDFs, and no runtime
checker exists. The family suits error-resilient DSP, statistics and
learning kernels, and its error stays below the exponent when it
replaces a floating-point mantissa multiplier.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/approx.py`: the low `perforated_rows` partial-product rows skipped, compensated by a constant, the skipped rows' top bits (error correction vector) or their expected value given the multiplier bit); the ArithmeticError gate governs.

## design choices

### carry_prediction

| member | what it selects |
| --- | --- |
| `two_or_more_threshold` | a carry is predicted where two or more of the omitted bits are set. |
| `simplified_or` | a carry is predicted by an OR over the omitted bits. |

### correction

| member | what it selects |
| --- | --- |
| `none` | the omitted rows are simply absent. |
| `constant` | a constant compensates the omitted rows' mean. |
| `error_correction_vector` | a vector computed from the operands compensates the omission. |
| `probabilistic_compensation` | the compensation follows the omitted rows' probability rather than a fixed constant. |

## references

zervakis2016 -> G. Zervakis, K. Tsoumanis, S. Xydis, D. Soudris, K. Pekmestzi, "Design-Efficient Approximate Multiplication Circuits Through Partial Product Perforation", IEEE Transactions on VLSI Systems, vol. 24, no. 10, pp. 3105-3117, 2016
kulkarni2011 -> P. Kulkarni, P. Gupta, M. Ercegovac, "Trading Accuracy for Power with an Underdesigned Multiplier Architecture", 24th International Conference on VLSI Design, pp. 346-351, 2011
mahdiani2010 -> H. R. Mahdiani, A. Ahmadi, S. M. Fakhraie, C. Lucas, "Bio-Inspired Imprecise Computational Blocks for Efficient VLSI Implementation of Soft-Computing Applications", IEEE Transactions on Circuits and Systems I, vol. 57, no. 4, pp. 850-862, 2010
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
jiang2017 -> H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
leon2018b -> V. Leon, G. Zervakis, S. Xydis, D. Soudris, K. Pekmestzi, "Walking Through the Energy-Error Pareto Frontier of Approximate Multipliers", IEEE Micro, vol. 38, no. 4, pp. 40-49, 2018
mazahir2017b -> S. Mazahir, O. Hasan, R. Hafiz, M. Shafique, "Probabilistic Error Analysis of Approximate Recursive Multipliers", IEEE Transactions on Computers, vol. 66, no. 11, pp. 1982-1990, 2017
