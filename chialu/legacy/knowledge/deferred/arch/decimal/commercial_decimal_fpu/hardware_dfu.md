---
family: commercial_decimal_fpu
pin: {implementation: hardware_dfu}
---
# hardware_dfu

A dedicated decimal execution unit: a 144-bit (36-digit) BCD
coefficient dataflow with DPD/BCD codecs, a two-cycle rotator, a
two-stage adder built from 4-digit conditional adders that splits
into two 18-digit halves, a 2X/5X multiples generator, a prescale
table and quotient correction. Iterative multiplication and
prescaled digit-recurrence division reuse the adder. The unit first
shipped in POWER6, was carried into the z10, and became the
four-stage z196 accelerator.

The hardware unit is the pick once decimal workloads matter: the z196
adds decimal64 in 6 cycles against 12 to 28 on the z10 and 154 in
software, and divides in 16 to 140 cycles against 627 to 940, for
1.43 mm2 in 45 nm. Its costs are that area, a separate unit with
communication delay to the core (z10) or register-file sharing with
the binary FPU (POWER6), and the residue-3 and parity checking the
dataflow needs. Later cores keep the structure and change its
packaging: the POWER8 DFU is fully pipelined at 13 cycles dependent
latency, and the z13 places one DFU in each of two vector units.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

schwarz_2009 -> Schwarz, Kapernick, Cowlishaw, "Decimal Floating-Point Support on the IBM System z10 Processor", IBM Journal of Research and Development, 2009
carlough_2011 -> Carlough, Collura, Mueller, Kroener, "The IBM zEnterprise-196 Decimal Floating-Point Accelerator", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), 2011
schwarz_2007 -> Schwarz, Carlough, "Power6 Decimal Divide", IEEE ASAP, 2007
wang_2009 -> Wang, Schulte, Thompson, Jairam, "Hardware Designs for Decimal Floating-Point Addition and Related Operations", IEEE Transactions on Computers, 2009
sinharoy_2015 -> B. Sinharoy, et al., "IBM POWER8 Processor Core Microarchitecture", IBM Journal of Research and Development, vol. 59, no. 1, pp. 2:1-2:21, 2015.
