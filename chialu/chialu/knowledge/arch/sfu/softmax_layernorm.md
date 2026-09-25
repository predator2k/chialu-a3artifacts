# softmax_layernorm

Softmax and layernorm as one unit: softmax subtracts (or tracks online)
the vector maximum so every exponential argument is nonpositive,
evaluates the exponential per element, reduces the exponentials into
one denominator, and normalizes each element through a true divider, a
shared reciprocal multiply, or a subtraction in the log domain
(exp(x_i - max - ln sum)); layernorm shares the reduction tree and the
normalization stage to form mean, variance and inverse standard
deviation before the affine transform. passes_over_vector counts the
data-dependent sweeps; online softmax fuses the maximum pass into the
sum pass by shift-renormalizing the running sum whenever a larger
maximum appears.

The exp_evaluation choice fixes precision against datapath. A
piecewise-linear power-of-two with an integer-ceiling maximum makes
every renormalization a shift and brings the unnormalized unit to 0.25x
the area and 0.10x the energy of a 16-bit floating-point softmax in 7
nm; base-2 shift-add with 4-bit log2 codes for the exponentials shrinks
the intermediate buffers from 16 bits to 4 and beats that design on
area and energy efficiency at 28 nm. Substituting 2^x for e^x on
integer inputs turns each input into a floating-point exponent, so the
reduction is a tree of adds on mantissa 1.0 and the outputs still sum
to one. An integer quadratic after subtracting the maximum and
factoring out powers of two holds the exponential within 1.9e-3, inside
the INT8 quantization step, and a fixed-point minimax polynomial with a
shift-subtract divider gives an exact-looking S15.16 softmax at the
cost of multi-cycle modules. Grouped lookup tables with a valid window
that drops inputs more than 8 below the maximum keep three decimal
digits with a bypass for a lone valid input.

The normalization_division choice trades one shared block against N
per-element ones: N dividers become one reciprocal shared by every
output, or one LOG unit plus 2N subtractors whose log input is bounded
to [0, N] by the maximum subtraction; a consumer that only ranks
categories can skip the final exponential. Maximum subtraction is what
bounds the exponential inputs and the log arguments, and quantizing
after it keeps the largest inputs distinguishable. Layernorm adds an
integer square-root recurrence (at most four iterations for INT32) or a
compressed 4-bit statistic path with 0.2% error on E(x^2), and its pass
count is the latency lever: pairwise variance drops a 512-element
vector from three passes and 52 cycles to two passes and 38 cycles on a
ZCU102 for about 3x the registers and O(log n) intermediate memory.

The contract is empirical task accuracy rather than an error bound,
with worst drops under about 1% on GLUE/SQuAD/ImageNet across the
designs on file and no fault model. Execution is feed-forward,
pipelined to match the MAC throughput that feeds it.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: the lanes as fixed-point values, the maximum subtracted (`max_subtraction`), the exponential core by `exp_evaluation`, a reduction tree, and the normalization by a true divider (the library's restoring array), a reciprocal multiply or the log-domain subtraction; layernorm as the exact mean and variance, the reciprocal square root core and one multiply per lane). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family softmax_layernorm --pins k=v,...` emits the module with its modeled error for a rewrite.

## design choices

### exp_evaluation

| member | what it selects |
| --- | --- |
| `lut_pwl` | the exponential comes from a piecewise-linear table. |
| `base2_shift_add` | it comes from a base-two shift-add form. |
| `approximate_substitute` | a cheaper function stands in for the exponential. |
| `integer_polynomial` | an integer polynomial evaluates it. |
| `group_lookup_table` | one table serves a group of inputs at once. |

### lut_group_gating

| member | what it selects |
| --- | --- |
| `fixed` | the group's table entries are always read. |
| `input_proximity` | the entries are read only where the inputs fall near them. |

## references

yuan_2016 -> B. Yuan, "Efficient Hardware Architecture of Softmax Layer in Deep Neural Network", IEEE International System-on-Chip Conference (SOCC), pp. 323-326, 2016
du_2019 -> G. Du, C. Tian, Z. Li, D. Zhang, Y. Yin, Y. Ouyang, "Efficient Softmax Hardware Architecture for Deep Neural Networks", ACM Great Lakes Symposium on VLSI (GLSVLSI), pp. 75-80, 2019
stevens_2021 -> J. R. Stevens, R. Venkatesan, S. Dai, B. Khailany, A. Raghunathan, "Softermax: Hardware/Software Co-Design of an Efficient Softmax for Transformers", ACM/IEEE Design Automation Conference (DAC), pp. 469-474, 2021
kim_2021 -> S. Kim, A. Gholami, Z. Yao, M. W. Mahoney, K. Keutzer, "I-BERT: Integer-only BERT Quantization", International Conference on Machine Learning (ICML), PMLR 139, pp. 5506-5518, 2021
cardarilli_2021 -> G. C. Cardarilli, L. Di Nunzio, R. Fazzolari, D. Giardino, A. Nannarelli, M. Re, S. Spano, "A Pseudo-Softmax Function for Hardware-Based High Speed Image Classification", Scientific Reports, vol. 11, 2021
hussain_2021 -> M. A. Hussain, T.-H. Tsai, "An Efficient and Fast Softmax Hardware Architecture (EFSHA) for Deep Neural Networks", IEEE International Conference on Artificial Intelligence Circuits and Systems (AICAS), pp. 1-4, 2021
wang_2023 -> W. Wang, S. Zhou, W. Sun, P. Sun, Y. Liu, "SOLE: Hardware-Software Co-Design of Softmax and LayerNorm for Efficient Transformer Inference", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 1-9, 2023
koca_2025 -> N. A. Koca, A. T. Do, C. H. Chang, "Accuracy-Preserving Layer Normalization Approximations for Efficient Transformer Hardware Accelerators", IEEE International Symposium on Circuits and Systems (ISCAS), pp. 1-5, 2025
