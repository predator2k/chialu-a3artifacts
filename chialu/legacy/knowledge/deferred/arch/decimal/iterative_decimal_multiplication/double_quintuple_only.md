---
family: iterative_decimal_multiplication
pin: {multiple_set: double_quintuple_only}
---
# double_quintuple_only

A doubler/quintupler is the only multiple generator: it produces the
1x, 2x, 5x and 10x easy multiples of the multiplicand, and every other
digit multiple is formed by addition or subtraction of those. One
multiplier digit is processed at a time. The z10 pairs partial
products in 16-digit mode, alternating pair formation with running-sum
accumulation on two 18-digit adders, and in 34-digit mode uses one
36-digit adder on alternate cycles, one partial product every other
cycle.

The set is the pick where the decimal adder already exists and area
for stored or generated 4x multiples does not: the z196 accelerator
forms the same 1x/2x/5x/10x multiples of the normalized larger operand
on the fly and accumulates them through its split adder, with
multiplication-only logic at 10% of the accelerator footprint;
parallel summation was rejected for area and cycle-time reasons
despite a projected 4 to 10 times latency reduction. Latency is data
dependent, 16 to 55 cycles for double-word and 17 to 104 for quadword
operands on the z10. Against easy_2x_4x_5x it drops the 4x multiple
and the carry-save accumulator, so a digit that is not an easy
multiple costs an additional add or subtract rather than a second
selected term. In the ADIR grammar it is
`family: iterative_decimal_multiplication` with
`pin: {multiple_set: double_quintuple_only}`.

## references

schwarz_2009 -> Schwarz, Kapernick, Cowlishaw, "Decimal Floating-Point Support on the IBM System z10 Processor", IBM Journal of Research and Development, 2009
carlough_2011 -> Carlough, Collura, Mueller, Kroener, "The IBM zEnterprise-196 Decimal Floating-Point Accelerator", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), 2011
