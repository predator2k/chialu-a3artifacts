# approximate_compressor_tree

Partial-product reduction by inexact 4:2 compressors: the exact
compressor's truth table is simplified (carry set equal to cin, cout
omitted, the all-ones case mapped to 11 rather than 100, XOR-heavy
sum logic replaced by AND/OR terms), so each cell is smaller and
shorter than the exact one at a per-cell error rate between 1/256
and 62.5 percent, and a Dadda-like tree built from these cells in the
n least-significant columns, with exact compressors above them,
reduces the matrix to two rows for an exact carry-propagate adder.
The errors are deterministic arithmetic errors that a recovery module
can accumulate with OR gates or adders and that a dual-quality cell
can switch off at run time.

The approximate column count sets the frontier: approximating the
whole matrix cuts delay by up to about 50 percent and power by about
80 percent for 16x16 in TSMC 28 nm at an NMED near 1e-2, while
bounding the region to the low columns keeps NMED near 1.5e-5 at
about 39 percent power saving and leaves exact compressors on the
critical path, which removes the delay gain. Signed matrices keep
the most-significant columns exact, because complemented partial
products raise the input-one probability there. The compressor
choice sets the per-cell error rate, the error polarity and the
input symmetry: the Momeni designs are cheapest at the highest cell
error rate and emit a nonzero output for all-zero inputs, the Yang
cells err on 1/256 to 1/16 of patterns, the encoded and
propagate/generate-altered cells lower the error probability by
making faulty rows unreachable, the unbiased cells discard the
lowest-probability terms of a carry-free j-input compressor, and the
dual-quality cells add a supplementary exact part. Non-symmetric
cells need probability-aware pin assignment.

Error recovery trades logic for accuracy: OR-based and configurable
accumulation of error bits restores part of the result, and the
Lin correction detects the single erroneous base-block pattern with
an AND gate and repairs two product bits. Dual-quality operation
costs a supplementary part that is power-gated in approximate mode,
a 22 to 26 ps mode transition during which outputs are invalid, and
a small exact-mode overhead from tristate isolation.

The accuracy contract is statistical: error rates approach 100
percent under full-matrix approximation, and the compressor
approximation beats truncation schemes on NMED and MRED at more
power and area. The family wins for error-tolerant multimedia and
signal processing where the low columns can be cheap, composes with
approximate Booth encoding except at sign-extension bits, and its
cpa slot stays exact in most designs (Kogge-Stone, ripple carry or a
speculative adder used only at the final sum).

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/approx.py`: the inexact 4:2 cell styles over the low `approximate_columns` (the design-1 rule, the OR rule, the unbiased rule; the module comment names which rule realizes the named cell), the dropped carries OR-ed back or a compensation constant); the ArithmeticError gate governs.

## design choices

### error_recovery

| member | what it selects |
| --- | --- |
| `none` | the compressors' errors stand. |
| `or_based` | the cells' error signals of the top approximate columns are ORed into the column above. |
| `compensation_module` | a constant is added at the approximate columns' top, which centres the error. |

## references

momeni2015 -> A. Momeni, J. Han, P. Montuschi, F. Lombardi, "Design and Analysis of Approximate Compressors for Multiplication", IEEE Transactions on Computers, vol. 64, no. 4, pp. 984-994, 2015
strollo2020 -> A. G. M. Strollo, E. Napoli, D. De Caro, N. Petra, G. Di Meo, "Comparison and Extension of Approximate 4-2 Compressors for Low-Power Approximate Multipliers", IEEE Transactions on Circuits and Systems I, vol. 67, no. 9, pp. 3021-3034, 2020
jiang2017 -> H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
esposito2018 -> D. Esposito, A. G. M. Strollo, E. Napoli, D. De Caro, N. Petra, "Approximate Multipliers Based on New Approximate Compressors", IEEE Transactions on Circuits and Systems I, vol. 65, no. 12, pp. 4169-4182, 2018
akbari2017 -> O. Akbari, M. Kamal, A. Afzali-Kusha, M. Pedram, "Dual-Quality 4:2 Compressors for Utilizing in Dynamic Accuracy Configurable Multipliers", IEEE Transactions on VLSI Systems, vol. 25, no. 4, pp. 1352-1361, 2017
ansari2018 -> M. S. Ansari, H. Jiang, B. F. Cockburn, J. Han, "Low-Power Approximate Multipliers Using Encoded Partial Products and Approximate Compressors", IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 8, no. 3, pp. 404-416, 2018
venkatachalam2017 -> S. Venkatachalam, S.-B. Ko, "Design of Power and Area Efficient Approximate Multipliers", IEEE Transactions on VLSI Systems, vol. 25, no. 5, pp. 1782-1786, 2017
yang2015 -> Z. Yang, J. Han, F. Lombardi, "Approximate Compressors for Error-Resilient Multiplier Design", IEEE International Symposium on Defect and Fault Tolerance in VLSI and Nanotechnology Systems (DFTS), pp. 183-186, 2015
