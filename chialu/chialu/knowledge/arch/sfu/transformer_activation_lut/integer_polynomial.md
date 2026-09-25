---
family: transformer_activation_lut
pin: {method: integer_polynomial}
---
# integer_polynomial

The nonlinearity is replaced by a low-degree polynomial evaluated in
integer arithmetic only: i-GELU substitutes the clipped odd quadratic
L(x) = sgn(x)[a(clip(|x|, max = −b) + b)^2 + 1], with a = −0.2888 and
b = −1.769, for erf, and Algorithm 2 evaluates the polynomial and the
GELU scaling on INT32 with precomputed static scales, so inference
contains no floating-point operation and the output requantizes to
INT8.

Against learned_lut_pwl, the polynomial needs no table, comparator or
training run, since its coefficients come from an interpolation-point
search, and its error is analytic: at most 0.018 from exact GELU on
[-4, 4], with INT8 I-BERT scoring at or slightly above the FP32
RoBERTa baselines on GLUE. It loses on hardware, since each function
needs a dedicated unit of three to five cycles, and in 7 nm the
I-BERT unit costs about 2.6x the area and 4x the delay of the INT32
NN-LUT datapath at far higher power. Degree stays low to bound cost
and integer-overflow risk, and the cheaper h-GELU costs up to 1.1
points of downstream accuracy. In the ADIR grammar it is
`family: transformer_activation_lut` with
`pin: {method: integer_polynomial}`.

The library's module for transformer_activation_lut realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

kim_2021 -> S. Kim, A. Gholami, Z. Yao, M. W. Mahoney, K. Keutzer, "I-BERT: Integer-only BERT Quantization", International Conference on Machine Learning (ICML), PMLR 139, pp. 5506-5518, 2021
yu_2022 -> J. Yu, J. Park, S. Park, M. Kim, S. Lee, D. H. Lee, J. Choi, "NN-LUT: Neural Approximation of Non-Linear Operations for Efficient Transformer Inference", ACM/IEEE Design Automation Conference (DAC), pp. 577-582, 2022
taghavizade_2024 -> A. Taghavizade, D. Rahmati, S. Gorgin, J.-A. Lee, "GELU-MSDF: A Hardware Accelerator for Transformer's GELU Activation Function Using Most Significant Digit First Computation", IEEE International System-on-Chip Conference (SOCC), pp. 1-6, 2024
