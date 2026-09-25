# dedicated_magnitude_comparator

A magnitude comparison unit separate from the arithmetic datapath: for
each operand format a dedicated unit takes the two operands and
determines the greater-than, less-than and equal condition codes
directly, so a compare instruction does not pass through the adder. For
recording arithmetic instructions the same unit determines the relation
of the result to zero in parallel with the fixed-point unit producing
that result, so the condition codes and the result arrive together.

The family is feed-forward and single-cycle: the 64-bit compare unit of
the 1.0 GHz PowerPC integer processor, built in 0.25 um CMOS dynamic
logic, resolves explicit compare operations in one cycle. Its inputs
are the two operands, or the arithmetic result and zero for a recording
operation, and its outputs are the three condition codes, so explicit
compares and recording operations share one comparator. Its value is
latency on control-dependent code, because comparison runs beside
rather than after the arithmetic, and a dependent conditional branch
resolves without waiting for the arithmetic result. The trade is area
for that latency: the unit duplicates magnitude logic that an
adder-based comparison would share with the arithmetic, and it is
replicated per format. The space records no further design choices for
the family, so the tunables are the operand width and whether the
parallel condition-code generation for recording operations is present.
No error checking is reported for the unit.

## the library's module

The seed instantiates the library's generated float module for this family
(`chialu/targets/rtl/families/fp.py`, value-exact against the engine: the exponents compared, then the significands).
The component family (comparator, one instance over the exponents and one over the significands) selects its sub-structures
from the library.

## references

silberman_1998 -> J. Silberman, et al., "A 1.0-GHz Single-Issue 64-Bit PowerPC Integer Processor Using Dynamic Logic", IEEE Journal of Solid-State Circuits, vol. 33, no. 11, pp. 1600-1608, 1998.
