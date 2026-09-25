---
family: mixed_precision_cascade_fma
pin: {error_term_normalization: on_demand_copy}
---
# on_demand_copy

A p-bit residual register captures the low product or sum bits that the
datapath already forms for the sticky computation, and a separate
instruction normalizes that residual through the adder's leading-zero
counter and shifter, accounting for whether the rounding chose the
truncated significand or its successor. The two-term expansion (2Sum or
2Mult) is delivered in two instructions with no second datapath: the
first returns the rounded result, the second copies and normalizes the
error term.

The residual register is the low-cost route to error-free
transformations: the textbook prices it at under 10 percent area over a
classical binary32 GPU floating-point unit, against a dedicated 2Sum
operator whose own error-term leading-zero count and shifter make it 50
percent larger than a standard adder at identical delay on an FPGA. It
wins when 2Sum and 2Mult are occasional, since the error term is
produced only on demand and the main pipeline is unchanged, and the
dedicated operator wins when every operation must return both terms at
full rate. The error_term_ops choice states whether additions,
multiplications or both fill the register. The compensated two-sum
accumulator consumes the term, and the classic FMA is the alternative
host if the expansion output is not tied to mixed precision.

The library realizes this choice as a pin of the generated mixed_precision_cascade_fma module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
