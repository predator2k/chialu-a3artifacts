# behavioral_star

The multiplier written as the HDL operator: the datapath states p = a * b and leaves partial-product generation, the reduction tree, and the final adder to logic synthesis, which infers an implementation from its cell library. In the exact-dot-product accelerator the front end expresses exponent addition, mantissa multiplication, and shifting as Chisel operators that map to the equivalent Verilog operators, and inserted output registers are retimed across the three modules to pipeline the datapath, so the pipeline latency is a parameter rather than a structure. The family is feed-forward and has no structural choices of its own.

What the family trades is control for effort. The space lists no choices and no slots, so a search over this family is a search over the synthesis constraints and the retiming budget rather than over recoding radix, reduction geometry, or final adder; the inferred topology is left open by the one instantiating design and no multiplier-only area or delay result is reported for it. The designer fixes only the operand widths, which in the accelerator are fp32 or fp64 mantissas, and the front-end pipeline latency, which the retimer distributes across the exponent, mantissa, and shift modules.

The family fits where the multiplier is not the critical block and where the surrounding datapath sets the numerical contract. In the exact-dot-product front end the mantissa product is retained without rounding before accumulation, so the operator need only be exact at full product width, which any synthesized multiplier is. It loses wherever the reduction geometry, the final adder's arrival profile, or an approximate or truncated contract must be chosen deliberately, because none of those is expressible from the operator.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/mul_ext.py`: `p = a * b`, the structure left to synthesis (the default of every multiplier component slot: an undeclared iteration or segment multiplier is this)).

## references

koenig_2017 -> J. Koenig, D. Biancolin, J. Bachrach, K. Asanovic, "A Hardware Accelerator for Computing an Exact Dot Product", ARITH-24, pp. 114-121, 2017
