---
family: softmax_layernorm
pin: {exp_evaluation: lut_pwl}
---
# lut_pwl

The exponential from a table or piecewise-linear block: the Power of Two
subunit of Softermax evaluates a base-2 exponential of a low-precision
fixed-point input, Q(6,2) after subtraction of the running integer
maximum, and delivers a Q(1,15) unnormalized value that a reduction
subunit accumulates, while a separate piecewise-linear reciprocal serves
the normalization. The exponent is a lookup or a few line segments, so
no multiplier or polynomial sits on the exponential path.

LUT/PWL exponentials are the pick when the input is already quantized to
a few bits and the datapath is co-designed with training: in TSMC 7 nm
the unnormed Softermax unit is 0.25x the area and 0.10x the energy of a
16-bit floating-point library softmax, the full processing element 0.90x
and 0.43x, with a worst task-accuracy drop under 0.5% on BERT after
Softermax-aware fine-tuning, which replaces rather than adds a training
phase. The table costs grow with input precision, and a grouped-table
design on file enables zero to three table groups by how close the
inputs are, with probability errors from 0.0043 down to 0.0000 as groups
are added. It loses to the integer polynomial when a multiplier is
cheaper than the table and to the shift-add base-2 form when 4-bit
exponent codes are acceptable.

The library's module for softmax_layernorm realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

stevens_2021 -> J. R. Stevens, R. Venkatesan, S. Dai, B. Khailany, A. Raghunathan, "Softermax: Hardware/Software Co-Design of an Efficient Softmax for Transformers", ACM/IEEE Design Automation Conference (DAC), pp. 469-474, 2021
du_2019 -> G. Du, C. Tian, Z. Li, D. Zhang, Y. Yin, Y. Ouyang, "Efficient Softmax Hardware Architecture for Deep Neural Networks", ACM Great Lakes Symposium on VLSI (GLSVLSI), pp. 75-80, 2019
