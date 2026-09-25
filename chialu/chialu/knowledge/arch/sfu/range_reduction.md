# range_reduction

Maps an argument x into the approximation interval: additive reduction computes x* = x - kC, multiplicative x* = x / C^k, exact for a radix-power C. cody_waite splits C into two or three exactly representable terms, so x - kC1 is exact for small k and later terms recover the cancelled bits. payne_hanek multiplies the significand by only the exponent-selected middle bits of 4/pi, at argument-independent cost. modular_mrr replaces each power of two by a small residue modulo C, sums the residues the input bits select in a tree, then a short table-driven second reduction. table_augmented uses a tabulated reciprocal or a high-radix digit split. Continued fractions of C fix the guard precision.

method is chosen by argument size. Cody-Waite is the cheap form but is restricted to small arguments when last-bit accuracy is required for every input, because kC1 stops being exact once k grows; add_split_constant_term extends the range by one more subtraction, and a library can add further pieces only for the rare cancellation-heavy arguments. Payne-Hanek covers the whole floating-point range at nearly argument-independent speed, with the window width set by the worst-case loss; the VAX octant implementation stores a reciprocal of about 32,000 bits and bounds sine and cosine to slightly more than 3/4 ulp with 6 guard bits. Between the two, a high-radix table split of the rounded integer into eight 7-bit parts with 24 Kbytes of tables runs 4 to 5 times faster than a Payne-Hanek routine over [8, 2^63), at the price of the table size. Modular reduction is the hardwired form: the first reduction is a cellular array or a Wallace tree with logarithmic latency, shares hardware with a multiplier, and Booth recoding halves its terms, but an iterative modular reduction pipelines poorly.

reduction_type follows the function. Logarithm and exponential reduce multiplicatively through the exponent field, and the exponential's integer estimate E of X/log 2 may be grossly approximate as long as Y stays in [-1/2, 1/2), because normalization absorbs the offset; guaranteeing Y >= 0 costs more hardware. A tabulated reciprocal makes z = y*r_i - 1 exact and small, and fuse_reduction_into_first_table_index folds the second reduction into the table address. Function-specific identities preserve exact rounding for reciprocal, square root, 2^x, and log2, but not for trigonometric functions, whose reduction error is what worst_case_bound_proven guards: the guard precision is about 29.2 bits for binary32 and 60.9 bits for binary64 with C = pi/2, and the reduced argument usually needs a wider format or a double-word. Near a multiple of C a naive subtraction keeps only a couple of significant digits.

The library realizes this component family inside every function module (`chialu/targets/rtl/families/sfu.py`: for sin and cos the `method` (Cody-Waite split constants with `split_constant_terms`, Payne-Hanek windows of 2/pi by exponent, the modular or table-augmented sum of 2^i (2/pi) mod 4 over the integer bits), `path_structure` dual_close_far adding the close path x h(x) at the first quadrant; the other functions reduce by their identities: the exponent split of 2^x, the exponent extraction of the logarithm, the parity of the exponent for the roots, the symmetry folding of the activations).

## design choices

### argument_scaling

| member | what it selects |
| --- | --- |
| `radian` | the argument is in radians, so the constant split is of pi. |
| `pi_scaled` | the argument is already scaled by pi, which removes that constant. |

### path_structure

| member | what it selects |
| --- | --- |
| `single` | one reduction path serves every argument. |
| `dual_close_far` | a close and a far path, chosen by the argument's magnitude. |

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
payne_1983 -> M. H. Payne, R. N. Hanek, "Radian Reduction for Trigonometric Functions", ACM SIGNUM Newsletter, vol. 18, no. 1, pp. 19-24, 1983
daumas_1995 -> M. Daumas, C. Mazenc, X. Merrheim, J.-M. Muller, "Modular Range Reduction: A New Algorithm for Fast and Accurate Computation of the Elementary Functions", Journal of Universal Computer Science, vol. 1, no. 3, pp. 162-175, 1995
brisebarre_2005 -> N. Brisebarre, D. Defour, P. Kornerup, J.-M. Muller, N. Revol, "A New Range-Reduction Algorithm", IEEE Transactions on Computers, vol. 54, no. 3, pp. 331-339, 2005
gal_1991 -> S. Gal, B. Bachelis, "An Accurate Elementary Mathematical Library for the IEEE Floating Point Standard", ACM Transactions on Mathematical Software, vol. 17, no. 1, pp. 26-45, 1991
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
detrey_2007b -> J. Detrey, F. de Dinechin, "Floating-Point Trigonometric Functions for FPGAs", International Conference on Field Programmable Logic and Applications (FPL), pp. 29-34, 2007
