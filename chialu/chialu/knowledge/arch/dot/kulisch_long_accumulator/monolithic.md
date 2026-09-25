---
family: kulisch_long_accumulator
pin: {organization: monolithic}
---
# monolithic

One full-width register and one full-width adder: every exact product
is shifted by its exponent into the register and added with the carry
resolved immediately across the whole width, so the accumulator holds a
standard binary number at every cycle and no exit conversion beyond the
final rounding is needed. The shifter and the adder both span the
accumulator width, and the encoding is either two's complement or sign
magnitude with conditional negation of the product or accumulator.

This is the pick when the width is small enough for the wide adder to
close the cycle: the binary16 case, whose products span 80 bits, is
smaller than an fp32 FMA in 28 nm and accumulates one product per
cycle, and an application-specific accumulator of 100 to 200 bits on an
FPGA fits the same form. At binary64 width the full register and adder
are far more resources than any segmented sibling with a longer per-sum
latency, so the segmented and banked organizations take over once the
format's exponent range is the sizing constraint rather than the
application.

The library realizes this choice as a pin of the generated kulisch_long_accumulator module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
brunie_2017 -> N. Brunie, "Modified Fused Multiply and Add for Exact Low Precision Product Accumulation", ARITH-24, pp. 106-113, 2017
uguen_2017 -> Y. Uguen, F. de Dinechin, "Design-Space Exploration for the Kulisch Accumulator", HAL preprint hal-01488916, 2017
