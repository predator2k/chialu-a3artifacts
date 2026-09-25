---
family: pp_perforation
pin: {cell: exact_and}
---
# exact_and

Row perforation proper: the partial products stay exact AND terms or
modified-Booth digits, and the approximation is the omission of whole
rows, k successive partial products from row j, so the reduction tree
loses n full adders per row and an operand-count level, and the error
equals the multiplicand times the omitted k-bit field of the
multiplier. The broken-array form applies the same idea cellwise,
removing carry-save cells above a horizontal break and right of a
vertical break.

It is the pick when delay and energy must fall together, since omitted
rows shorten the accumulation tree where truncation does not, giving
up to 50 percent power, 45 percent area and 35 percent delay reduction
at 16 bits under NMED below 10^-3 in 65 nm, with larger widths saving
more for the same error; the operand-swap corrections cut the error
further except for squaring. Against kulkarni_2x2_inaccurate it has an
error rate close to 100 percent but a small, bounded and
distribution-predictable error. Against the broken array it keeps the
tree, so PPAM has the shortest delay at large error while BAM has the
lowest power at medium accuracy; the modified-Booth form pairs
perforation with multiplicand rounding for extra energy at a slight
error cost.

## references

zervakis2016 -> G. Zervakis, K. Tsoumanis, S. Xydis, D. Soudris, K. Pekmestzi, "Design-Efficient Approximate Multiplication Circuits Through Partial Product Perforation", IEEE Transactions on VLSI Systems, vol. 24, no. 10, pp. 3105-3117, 2016
mahdiani2010 -> H. R. Mahdiani, A. Ahmadi, S. M. Fakhraie, C. Lucas, "Bio-Inspired Imprecise Computational Blocks for Efficient VLSI Implementation of Soft-Computing Applications", IEEE Transactions on Circuits and Systems I, vol. 57, no. 4, pp. 850-862, 2010
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
leon2018b -> V. Leon, G. Zervakis, S. Xydis, D. Soudris, K. Pekmestzi, "Walking Through the Energy-Error Pareto Frontier of Approximate Multipliers", IEEE Micro, vol. 38, no. 4, pp. 40-49, 2018
