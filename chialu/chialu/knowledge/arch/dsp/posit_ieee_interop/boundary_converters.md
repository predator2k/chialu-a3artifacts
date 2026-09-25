---
family: posit_ieee_interop
pin: {interop_style: boundary_converters}
---
# boundary_converters

Posits are a storage format decoded at the memory boundary into a
wider IEEE format for computation and encoded back on the way out:
Posit8 and Posit16 map exactly into FP32 and Posit32 into FP64.
FP-to-posit prenormalizes subnormal FP inputs, derives regime and
exponent from the unbiased FP exponent and shifts a built
regime/exponent/mantissa word; posit-to-FP detects the regime run with
an LOD/LZD, removes it with a dynamic shift and builds the biased
exponent.

Converters are the pick when the established IEEE arithmetic and
libraries must stay and only memory density is wanted: on a Kintex-7
the Posit16-to-FP32 and FP32-to-Posit16 converters take 90 and 63
LUTs against 367 for an FP32 adder and 798 for a divider, and the
Virtex-6 generator does either direction in one cycle, so converter
cost amortizes over whole FP pipelines. The contract is weaker than
native posit arithmetic: exact input conversion does not give
standard posit results because the conversion back after IEEE
computation can double round, FP subnormals collapse to the smallest
posit and posits never decode as FP subnormals. Clarinet places the
converters as FCVT instructions between separate float and posit
register files, at 2N conversions for an N-iteration legacy loop. A
unified dual-format datapath removes the double rounding, and an ISA
that replaces float removes the conversions.

The library realizes this variant as one dedicated converter module per lane and target (`posit.cvt_sv`): a decoded posit value into a float target through the float rounder datapath, into a posit target through the posit encoder, and a float lane's decoded value into the posit format through the posit encoder, in the directions `conversion_direction` names.

## references

dedinechin_2019b -> F. de Dinechin, L. Forget, J.-M. Muller, Y. Uguen, "Posits: The Good, the Bad and the Ugly", Conference for Next Generation Arithmetic (CoNGA), 2019
jaiswal_2018 -> M. K. Jaiswal, H. K.-H. So, "Universal Number Posit Arithmetic Generator on FPGA", Design, Automation and Test in Europe (DATE), 2018
crespo_2022 -> L. Crespo, P. Tomás, N. Roma, N. Neves, "Unified Posit/IEEE-754 Vector MAC Unit for Transprecision Computing", IEEE Transactions on Circuits and Systems II: Express Briefs, 2022
