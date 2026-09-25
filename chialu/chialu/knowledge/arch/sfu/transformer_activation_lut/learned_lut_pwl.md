---
family: transformer_activation_lut
pin: {method: learned_lut_pwl}
---
# learned_lut_pwl

The function is distilled into an N-entry piecewise-linear table: a
one-hidden-layer ReLU network with N − 1 neurons is trained offline
against the target, and its weights and biases define N − 1 sorted
breakpoints and N interval functions s_i x + t_i. At inference a
comparator selects the interval, the LUT supplies s_i and t_i, and
one multiplier and one adder form the result, so GELU, EXP, DIV and
1/SQRT share one datapath and differ only in table contents.

Against integer_polynomial, the table is the general and the cheap
option: 16 entries suffice in the evaluated models, every function
takes two cycles, and in 7 nm the INT32 table runs at under half the
area and a small fraction of the power of the I-BERT unit, with FP16
parameters cheaper still. Its accuracy contract is statistical rather
than analytic, known only through operation-wise L1 error and task
metrics, so calibration = learned_from_data, a short regression on
unlabeled activations while the Transformer stays frozen, recovers
most of the lost GLUE score. Learned breakpoints matter most for
softmax and layer-norm inputs with a large dynamic range, and small
1/SQRT inputs need a power-of-two prescale into the trained range. In
the ADIR grammar it is `family: transformer_activation_lut` with
`pin: {method: learned_lut_pwl}`.

The library's module for transformer_activation_lut realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

yu_2022 -> J. Yu, J. Park, S. Park, M. Kim, S. Lee, D. H. Lee, J. Choi, "NN-LUT: Neural Approximation of Non-Linear Operations for Efficient Transformer Inference", ACM/IEEE Design Automation Conference (DAC), pp. 577-582, 2022
kim_2021 -> S. Kim, A. Gholami, Z. Yao, M. W. Mahoney, K. Keutzer, "I-BERT: Integer-only BERT Quantization", International Conference on Machine Learning (ICML), PMLR 139, pp. 5506-5518, 2021
