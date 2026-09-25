---
family: softmax_layernorm
pin: {normalization_division: reciprocal_multiply}
---
# reciprocal_multiply

Normalization by one reciprocal and N multiplications: the denominator,
the sum of exponentials or the standard deviation, is reduced once, its
reciprocal is approximated once by a small piecewise-linear block, and
every output is its numerator times that shared value. The reciprocal is
computed on a normalized mantissa or a fixed-point sum, so its block is
narrow, and in the online form the stored numerators are
shift-renormalized against the running maximum before the multiply.

Reciprocal-multiply is the pick when many outputs share one denominator,
which is every softmax vector and every LayerNorm row: the divider
disappears and the per-element cost is one multiplier. In TSMC 7 nm the
Softermax normalization unit with a Q(1,7) piecewise-linear reciprocal
is 0.65x the area and 0.39x the energy of a 16-bit floating-point
library softmax, at a worst task-accuracy drop under 0.5% after
Softermax-aware fine-tuning; the pseudo-softmax unit shares one
reciprocal mantissa across all outputs and runs unpipelined at 310 MHz
in 90 nm for ten inputs; the 16-bit fixed-point LayerNorm on a ZCU102
takes 2945 LUTs, 98 DSPs and 52 cycles per 512-element vector against
91651 LUTs and 153 cycles for the fp32 baseline, with an average BERT
accuracy drop of 0.06%. It loses to log-domain subtraction when even the
multipliers are too costly.

The library's module for softmax_layernorm realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

stevens_2021 -> J. R. Stevens, R. Venkatesan, S. Dai, B. Khailany, A. Raghunathan, "Softermax: Hardware/Software Co-Design of an Efficient Softmax for Transformers", ACM/IEEE Design Automation Conference (DAC), pp. 469-474, 2021
cardarilli_2021 -> G. C. Cardarilli, L. Di Nunzio, R. Fazzolari, D. Giardino, A. Nannarelli, M. Re, S. Spano, "A Pseudo-Softmax Function for Hardware-Based High Speed Image Classification", Scientific Reports, vol. 11, 2021
koca_2025 -> N. A. Koca, A. T. Do, C. H. Chang, "Accuracy-Preserving Layer Normalization Approximations for Efficient Transformer Hardware Accelerators", IEEE International Symposium on Circuits and Systems (ISCAS), pp. 1-5, 2025
