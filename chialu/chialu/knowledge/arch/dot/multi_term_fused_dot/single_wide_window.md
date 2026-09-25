---
family: multi_term_fused_dot
pin: {alignment_strategy: single_wide_window}
---
# single_wide_window

Every product is shifted once into one common window and the whole
reduction happens inside it: the largest product exponent, or a
fixed-point range chosen for the application, sets the window, each
product is aligned to it by its own shifter, and the aligned terms
enter one carry-save reduction and one internal adder with a single
normalization and rounding at the end. No per-level alignment exists,
so the only precision loss is the bits shifted out of the window.

This is the alignment every reported fused dot unit uses, from the
four-term unit that aligns sum/carry pairs to the largest exponent
without sorting to the realignment-line design and the FPGA
accumulators. It is the pick when the term count is small enough for 2N
shifters and a window-wide adder to fit, since the window holds every
bit needed for a correctly rounded or last-bit accurate result and a
comparison-selected sign resolution keeps the adder at half width. It
loses ground as N grows, where a long adder spanning the exponent range
or a bounded window with guard bits caps the shifter and adder cost at
the price of a truncation contract.

The library realizes this choice as a pin of the generated multi_term_fused_dot module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

sohn_2016 -> J. Sohn, E. E. Swartzlander, "A Fused Floating-Point Four-Term Dot Product Unit", IEEE TCAS-I, vol. 63, no. 3, pp. 370-378, 2016
tao_2013 -> T. Yao, D. Gao, X. Fan, J. Nurmi, "Correctly Rounded Architectures for Floating-Point Multi-Operand Addition and Dot-Product Computation", IEEE ASAP, pp. 346-355, 2013
dedinechin_2008 -> F. de Dinechin, B. Pasca, O. Cret, R. Tudoran, "An FPGA-Specific Approach to Floating-Point Accumulation and Sum-of-Products", IEEE FPT, pp. 33-40, 2008
