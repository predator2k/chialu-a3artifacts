---
family: decimal_encoding_codec
pin: {significand_encoding: bid}
---
# bid

Binary integer decimal: the decimal significand is stored as one binary
integer rather than as DPD declets, so no digit-level codec exists and
every decimal operation is carried out in the binary integer domain with
binary multiplication, division and shifting, tables, and a corrective
rounding step. The encoding is the 754-2008 alternative to DPD and is
the natural target for a software library on a binary processor.

BID is the pick when decimal arithmetic runs in software on a binary
integer datapath: the library on file computes decimal64 and decimal128
with correctly rounded results in all rounding modes and correct IEEE
status flags, and on an EM64t Xeon 5100 a decimal64 addition takes 133
cycles maximum and 71 median against 684 and 486 for the decNumber
package. The measurements are preliminary, from a pre-beta library with
few optimizations, on corner and ordinary cases rather than a decimal
workload. Against DPD the trade is that no unpack is needed before
binary arithmetic, but a binary integer has none of the digit boundaries
that DPD keeps for decimal shifting, rounding and character conversion,
so the hardware decimal units on file all choose DPD with BCD inside.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

cornea_2009 -> Cornea, Harrison, Anderson, Tang, Schneider, Gvozdev, "A Software Implementation of the IEEE 754R Decimal Floating-Point Arithmetic Using the Binary Encoding Format", IEEE Transactions on Computers, 2009
cowlishaw_2002 -> Cowlishaw, "Densely Packed Decimal Encoding", IEE Proceedings - Computers and Digital Techniques, 2002
