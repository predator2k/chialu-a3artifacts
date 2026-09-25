# sigmoid_tanh_pwl

Sigmoid or tanh evaluated on a folded input: the sign selects y or 1 - y, so only the positive half-axis is stored, and that half is split into a few segments whose straight-line or quadratic pieces have slopes fixed to powers of two, so each segment is a shift, a mux, and an add with no multiplier; beyond a saturation point the output is forced to 0 or 1. Variants replace the shift/add evaluation with direct Boolean mappings from input bits and range flags to output bits, or evaluate at the encoding level, where posit8 flips the first bit and shifts right by two. The error is absolute, at most a few percent, and is absorbed by training or tolerated at inference. Feed-forward, one cycle.

approximation trades error against gates. Integer-grid pieces with power-of-two ordinates and PLAN's four magnitude ranges with slopes 0.25, 0.125, 0.03125, and 0 are the cheapest; on an APEX-II part PLAN reaches 0.59% average and 1.89% maximum absolute error in 39 logic elements at 75.8 MHz, where the A-law line sits at 2.47% and 4.90% in 36. Piecewise quadratic pieces that reach saturation with zero derivative at a power-of-two threshold cost one multiplication, one shift, and one add, and a two-segment quadratic generator cuts the maximum error to 2.2e-2 against 1.6e-1 for the earlier quadratic. Bit-level mapping minimizes each output bit as a sum of products after truncating input and output, with worst-case error 2^-(z+1) for a z-bit output, and reaches 0.17% average error in 45 logic elements. Probability-weighted PWL places segments where a layer's neuron values concentrate, with three selectable functions per layer; twelve segments give 0.0125 maximum absolute error over [-5, 5] in 140 LUTs and no DSP on Artix-7, and MNIST accuracy of 97.46% against 97.37% with the exact sigmoid. segments and the segmenter slot move along the same curve: more nonuniform segments cut error until the recursive interpolator saturates at 17 segments, and its q + 1 cycles per evaluation cost throughput.

symmetry_folding halves the stored range for a z-bit adder/subtractor or two's complement on the input; mapping the whole input range instead removes that arithmetic but doubles the mapped inputs. training_absorbs_error is what makes the contract tolerable: a continuous approximation with a derivative supports generalized-delta-rule learning, a gradient slightly below the sigmoid's slows convergence, a derivative floor keeps neurons active, and a modified derivative restores generalization from 63.8% to the sigmoid's 85.4%. At inference with weights trained on the exact function, recognition accuracy does not track approximation error monotonically. The family wins wherever an activation must be multiplier-free and single-cycle against a library exp plus divide of over a hundred cycles, and loses where an error contract in ulps is required, which none of these designs reports.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: the sigmoid or the tanh over a folded (`symmetry_folding`) bounded argument by `segments` pieces in the `approximation` (linear, quadratic, a bit-level table, power-of-two slopes, quantile-placed pieces, or a step staircase); the error is reported as measured). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family sigmoid_tanh_pwl --pins k=v,...` emits the module with its modeled error for a rewrite.

## design choices

### approximation

| member | what it selects |
| --- | --- |
| `pwl_segments` | piecewise-linear segments. |
| `piecewise_quadratic` | piecewise-quadratic segments. |
| `bit_level_mapping` | a bit-level mapping of the input to the output. |
| `shift_add_powers_of_two` | shift-add terms in place of the multiplies. |
| `probability_weighted_pwl` | segments weighted by the input distribution. |
| `step_sum` | a sum of step functions. |

## references

alippi_1991 -> C. Alippi, G. Storti-Gajani, "Simple Approximation of Sigmoidal Functions: Realistic Design of Digital Neural Networks Capable of Learning", IEEE International Symposium on Circuits and Systems (ISCAS), pp. 1505-1508, 1991
amin_1997 -> H. Amin, K. M. Curtis, B. R. Hayes-Gill, "Piecewise Linear Approximation Applied to Nonlinear Function of a Neural Network", IEE Proceedings - Circuits, Devices and Systems, vol. 144, no. 6, pp. 313-317, 1997
kwan_1992 -> H. K. Kwan, "Simple Sigmoid-Like Activation Function Suitable for Digital Hardware Implementation", Electronics Letters, vol. 28, pp. 1379-1380, 1992
zhang_1996 -> M. Zhang, S. Vassiliadis, J. G. Delgado-Frias, "Sigmoid Generators for Neural Computing Using Piecewise Approximations", IEEE Transactions on Computers, vol. 45, no. 9, pp. 1045-1049, 1996
tommiska_2003 -> M. T. Tommiska, "Efficient Digital Implementation of the Sigmoid Function for Reprogrammable Logic", IEE Proceedings - Computers and Digital Techniques, vol. 150, no. 6, pp. 403-411, 2003
wei_2020 -> L. Wei, J. Cai, V. Nguyen, J. Chu, K. Wen, "P-SFA: Probability Based Sigmoid Function Approximation for Low-Complexity Hardware Implementation", Microprocessors and Microsystems, vol. 76, art. 103105, 2020
gustafson_2017 -> J. L. Gustafson, I. T. Yonemoto, "Beating Floating Point at its Own Game: Posit Arithmetic", Supercomputing Frontiers and Innovations, vol. 4, no. 2, pp. 71-86, 2017
