# pwl_residual_lut

Residual coding of a function: the output is a cheap piecewise-linear
estimate p_linear(x) minus a correction E_LUT(x) read from a table
addressed by a few residual bits of the argument, so f = p_linear -
E_LUT. Because the linear estimate is already close, the table stores
only the error, whose word width is far narrower than f itself, and
residual_bits sets how many argument bits address it, so depth and
width shrink together. The canonical instance is Mitchell's logarithm:
a leading-one detector gives the integer part, the mantissa itself is
the linear estimate of log2(1 + f) with a peak error of 0.086, and the
correction is a per-region constant, a PWL term, or a small table.

Residual bits trade the error table against the error left over. Few
bits leave the peak error of the bare line; more bits cut it toward
the table's own quantization while the table depth doubles per bit,
and the survey's crossover between more table and more arithmetic
moves with precision and with fabric (ASIC ROM against FPGA BRAM and
DSP blocks). At the low end the correction collapses to a constant per
region or to ROM-free shift-add terms over a handful of regions, which
reaches an error around 0.9% without any table; at the high end, once
the correction table carries enough bits, the structure is a table of
initial values plus offset tables, which is the bipartite corner.

The segmenter sets where the linear pieces break. Uniform high-bit
decode is free but spends segments evenly; nonuniform, hierarchical,
and power-of-two segmentation follow local curvature and replace the
address slice with an index decoder, cutting segment counts by orders
of magnitude for functions with concentrated nonlinearity.

The family is feed-forward and its accuracy contract is a bounded
absolute error rather than faithful rounding. It wins in LNS datapaths,
Mitchell-style multipliers, and NN accelerator front-ends, where the
application tolerates the residual error and area matters more than
ulps; it loses to table-plus-polynomial and piecewise-polynomial units
whenever the contract is faithful or exact.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: an 8-segment linear part and a residual table over `residual_bits` more argument bits). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family pwl_residual_lut --pins k=v,...` emits the module with its modeled error for a rewrite.

## references

mitchell1962 -> J. N. Mitchell, "Computer Multiplication and Division Using Binary Logarithms", IRE Transactions on Electronic Computers, vol. EC-11, no. 4, pp. 512-517, 1962
combet1965 -> M. Combet, H. Van Zonneveld, L. Verbeek, "Computation of the Base Two Logarithm of Binary Numbers", IEEE Transactions on Electronic Computers, vol. EC-14, no. 6, pp. 863-867, 1965
juang_2009 -> T.-B. Juang, S.-H. Chen, H.-J. Cheng, "A Lower Error and ROM-Free Logarithmic Converter for Digital Signal Processing Applications", IEEE Transactions on Circuits and Systems II, vol. 56, no. 12, pp. 931-935, 2009
coleman_2000 -> J. N. Coleman, E. I. Chester, C. I. Softley, J. Kadlec, "Arithmetic on the European Logarithmic Microprocessor", IEEE Transactions on Computers, vol. 49, no. 7, pp. 702-715, 2000
lee_2003 -> D.-U. Lee, W. Luk, J. Villasenor, P. Y. K. Cheung, "Non-Uniform Segmentation for Hardware Function Evaluation", Field-Programmable Logic and Applications (FPL), LNCS 2778, pp. 796-807, 2003
