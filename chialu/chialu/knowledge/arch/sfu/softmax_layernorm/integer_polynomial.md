---
family: softmax_layernorm
pin: {exp_evaluation: integer_polynomial}
---
# integer_polynomial

The exponential as a low-degree integer polynomial after a base-2 or ln
2 range reduction: the input, made non-positive by maximum subtraction,
is split as x = (-ln 2) z + p with p in (-ln 2, 0], exp(p) is a
quadratic with integer-scaled coefficients, 0.3585 (p + 1.353)^2 +
0.344, and the 2^-z factor is a right shift. The alternative on file
evaluates 2^f for f in [-0.5, 0.5] with a fourth-order minimax
polynomial whose four constants sit in registers and reuse one
multiplier and one adder.

The integer polynomial is the pick when the whole softmax must stay in
integer arithmetic, as in integer-only BERT inference, or when a lookup
table is unwanted: the quadratic's largest gap from exp on the reduced
interval is 1.9 x 10^-3, below the 3.9 x 10^-3 unit-interval
quantization error of INT8, and the register-resident fourth-order form
keeps outputs within 0.001 without a large truth table. The cost is a
multiplier per evaluation, or several cycles when one multiplier and
adder are shared, and a range reducer that the max subtraction must feed
with non-positive inputs. It sits between the LUT/PWL sibling, which
spends memory, and the shift-add base-2 sibling, which spends accuracy
for 4-bit exponent codes.

The library's module for softmax_layernorm realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

kim_2021 -> S. Kim, A. Gholami, Z. Yao, M. W. Mahoney, K. Keutzer, "I-BERT: Integer-only BERT Quantization", International Conference on Machine Learning (ICML), PMLR 139, pp. 5506-5518, 2021
hussain_2021 -> M. A. Hussain, T.-H. Tsai, "An Efficient and Fast Softmax Hardware Architecture (EFSHA) for Deep Neural Networks", IEEE International Conference on Artificial Intelligence Circuits and Systems (AICAS), pp. 1-4, 2021
