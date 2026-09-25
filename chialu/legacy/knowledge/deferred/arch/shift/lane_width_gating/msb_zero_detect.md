---
family: lane_width_gating
pin: {detection: msb_zero_detect}
---
# msb_zero_detect

Result-producing hardware detects leading zeros, or leading ones for
negative two's-complement values, on every result and stores a
narrow-width tag with the operand in the reorder buffer. A 16-bit tag
gates the high 48 input-latch bits of the 64-bit unit and selects
zeros onto the high result bits; a second threshold recognizes values
that fit in 33 bits. Loads are tagged on arrival so that cache-sourced
operands are recognized as well.

Both operands must fit the selected width before the upper bits are
gated, and the same tags let the issue logic pack compatible narrow
operations instead of gating, though one implementation performs only
one of the two at a time. On a SimpleScalar Alpha model whose baseline
already has opcode-based clock gating, operand-based 16-bit and 33-bit
gating cuts integer-unit power by 54.1% on SPECint95 and 57.9% on
MediaBench, about 5 to 6% of processor power, against 4.2 mW for the
48-bit zero detect and 3.2 mW for the result muxes; omitting load
detection misses 13.1% of the SPECint95 opportunities (brooks_1999).
It is the pick when operand widths vary at runtime and no compiler or
ISA help exists; significance_tags carries the width through storage
instead, and static_mode applies when precision is set per mode rather
than per value.

## references

brooks_1999 -> D. Brooks, M. Martonosi, "Dynamically Exploiting Narrow Width Operands to Improve Processor Power and Performance", Proc. HPCA-5, pp. 13-22, 1999
