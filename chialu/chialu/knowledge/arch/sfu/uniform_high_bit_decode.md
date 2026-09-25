# uniform_high_bit_decode

Range reduction by the leading input bits: the k most significant
bits of the argument form the index i, the argument is written as
x = 2^-k i + y with y in [0, 2^-k), and i selects one of 2^k
coefficient sets or table entries directly, so the segmentation
costs no range-reduction hardware at all. The same decoding addresses
the regular grids of table-driven methods, such as k/64 and i/256
breakpoints, and the fixed-width input subwords that bipartite tables
pair as addresses, where two k-bit fields address each table for an
input of n = 3k bits.

The single tunable is k. Raising it multiplies the storage by two per
bit while lowering the local polynomial degree and the width of the
reduced argument that the evaluator multiplies, so the choice moves
between storage and arithmetic, and on an FPGA it also decides when
the coefficient store crosses a block-RAM or DSP threshold; reported
designs use 64 to 8192 subintervals. Because the decoding is direct,
it applies only to regularly spaced partitions; a scheme that
perturbs the nominal grid points to gain accuracy must store the
perturbed breakpoints as corrections, and a function whose curvature
varies strongly across the interval would prefer a nonuniform or
logarithmic segmentation that the leading bits cannot express.

The family is feed-forward and is the default front end of piecewise
polynomial and table-plus-polynomial evaluators: it wins whenever
the function is smooth enough that equal-width segments give a
near-uniform error budget, and it loses storage to nonuniform
segmentation where the error is concentrated in a small part of the
range.

The library realizes this segmenter inside the segmented-polynomial engine (`chialu/targets/rtl/families/sfu.py`: the segment index from the top bits of the argument, the rest as the local variable).

## references

pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
