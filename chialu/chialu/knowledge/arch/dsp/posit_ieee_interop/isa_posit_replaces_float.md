---
family: posit_ieee_interop
pin: {interop_style: isa_posit_replaces_float}
---
# isa_posit_replaces_float

Fixed-size posits stand in for IEEE floats in the instruction set
itself: PERI's tightly coupled integration replaces the IEEE-754 FPU
while keeping the RISC-V "F" encodings and the 32-register state, so
the existing float instructions execute posit arithmetic. Gustafson's
proposal is the same substitution at the format level, a drop-in
replacement that keeps rounding after inexact operations while
changing encoding, exception handling, tapered precision and the
fused-operation requirements.

Replacement is the pick when the software stack should change as
little as possible and IEEE and posit never need to coexist: the "F"
replacement needs fewer compiler changes than a custom posit
extension, and Gustafson argues for 32-bit posits substituting for
fp64 with a projected 2 to 4 times calculation speed from the smaller
operands, without an implementation measurement. Bitwise-identical
results across systems then depend on mandated correct rounding and
no covert extra precision. The cost is exclusivity: simultaneous
IEEE-754 use is excluded, so PERI also offers a RoCC accelerator with
its own posit register file and custom opcodes that coexists with the
IEEE FPU at the same execution-cycle count but needs new compiler
instructions. Boundary converters keep the IEEE core and pay
conversions; the unified datapath keeps both formats in one core.

Under this variant the seed instantiates the library's decoder and encoder of the posit mode; the conversions, where the mode set still has float modes, stay on the lane's shared X datapath.

## references

gustafson_2017 -> J. L. Gustafson, I. T. Yonemoto, "Beating Floating Point at its Own Game: Posit Arithmetic", Supercomputing Frontiers and Innovations, vol. 4, no. 2, pp. 71-86, 2017
tiwari_2021 -> S. Tiwari, N. Gala, C. Rebeiro, V. Kamakoti, "PERI: A Configurable Posit Enabled RISC-V Core", ACM Transactions on Architecture and Code Optimization, 2021
