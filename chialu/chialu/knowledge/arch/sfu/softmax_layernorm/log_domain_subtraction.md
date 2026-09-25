---
family: softmax_layernorm
pin: {normalization_division: log_domain_subtraction}
---
# log_domain_subtraction

Normalization in the log domain: the unit takes the logarithm of the sum
once and subtracts it from each shifted input, ln p_i = (x_i - x_max) -
ln sum exp(x_k - x_max), so N dividers become one logarithm unit and 2N
subtractors. A final exponential converts back to probabilities, or is
omitted when only the ranking is consumed; a shift-based form keeps the
exponent outputs as log2 codes and divides by a leading-one detect, a
subtraction and a shift.

Log-domain subtraction is the pick when the divider is the dominant cost
or when outputs feed a ranking rather than a probability: the shared LOG
unit works on an input bounded to [0, N] after max subtraction and needs
fewer quantization bits than a divider, at the price of a sorting block,
a LOG unit and 2N subtractors and a critical path of one log and two
subtractions in place of one division. With the final exponential kept,
the 65 nm ESHA design runs at 500 MHz in 0.64 mm2 and 0.82 mW with
probability errors of a few 10^-3 and MNIST accuracy 99.01% against
99.25% in software; with 4-bit log2 exponent codes and a Mitchell-style
shift divider the 28 nm SOLE softmax unit is 3.04x more energy-efficient
than Softermax at a worst accuracy drop under 0.9% against FP32.

The library's module for softmax_layernorm realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

yuan_2016 -> B. Yuan, "Efficient Hardware Architecture of Softmax Layer in Deep Neural Network", IEEE International System-on-Chip Conference (SOCC), pp. 323-326, 2016
du_2019 -> G. Du, C. Tian, Z. Li, D. Zhang, Y. Yin, Y. Ouyang, "Efficient Softmax Hardware Architecture for Deep Neural Networks", ACM Great Lakes Symposium on VLSI (GLSVLSI), pp. 75-80, 2019
wang_2023 -> W. Wang, S. Zhou, W. Sun, P. Sun, Y. Liu, "SOLE: Hardware-Software Co-Design of Softmax and LayerNorm for Efficient Transformer Inference", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 1-9, 2023
