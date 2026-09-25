---
family: commercial_decimal_fpu
pin: {implementation: millicode_with_assists}
---
# millicode_with_assists

Decimal floating-point executed as millicode sequences over the
fixed-point unit's packed-decimal hardware: dedicated milli-ops move
floating-point register values, decode and encode the DPD fields, and
run register-based BCD add, subtract, multiply and divide; format
extraction, alignment, addition, rounding and repacking are steps of
a routine rather than pipeline stages. The S/390 G5 form is the same
pattern one level down: a divide assist yields one quotient digit
per millicode iteration.

The z9 took this route because the decimal standard was unfinished
during processor development, and the millicode favours reuse and
future flexibility over fixed hardware latency. A long-format add
costs about 100 to 150 cycles, a multiply 150 to 200 and a divide 350
to 400, which is about ten times faster than pure software and, by
the designers' projection, another factor of ten slower than full
hardware; equal-exponent add and subtract take a fast path. It is the
pick only while the hardware DFU is unavailable or the instruction
set is still moving.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

duale_2007 -> Duale, Decker, Zipperer, Aharoni, Bohizic, "Decimal Floating-Point in z9: An Implementation and Testing Perspective", IBM Journal of Research and Development, 2007
slegel_1999 -> T. J. Slegel et al., "IBM's S/390 G5 Microprocessor Design", IEEE Micro, vol. 19, no. 2, pp. 12-23, 1999
wang_2009 -> Wang, Schulte, Thompson, Jairam, "Hardware Designs for Decimal Floating-Point Addition and Related Operations", IEEE Transactions on Computers, 2009
