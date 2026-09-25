---
family: decimal_encoding_codec
pin: {significand_encoding: dpd}
---
# dpd

Densely packed decimal: each BCD digit is classed as small (0 to 7) or
large (8 or 9), and an equivalent Huffman code maps three digits, 12 BCD
bits, into a 10-bit declet whose indicator bits name one of the eight
large/small combinations. One- and two-digit encodings are the rightmost
4 and 7 bits of the same mapping, so a field expands by zero padding,
and compression and expansion are fixed bit mappings that a lookup table
or a few levels of Boolean gates implement.

DPD is the pick for hardware decimal units and for interchange with
BCD-oriented databases: the encoding keeps decimal digit boundaries, is
17% more compact than BCD so a 128-bit register holds 33 digits with
sign and a four-digit exponent, and uses 1,000 of 1,024 declet values,
above 97.6% efficiency against 62.5% for BCD. Every hardware unit on
file expands DPD to BCD before arithmetic and compresses the result
back: POWER6 does so in three logic-gate levels with two expanders and
one compressor, z9 does it in one-cycle milli-ops, and the conversion
logic around a lookup table costs roughly two gate delays. The cost is
that floating-point operations spend codec cycles that packed-BCD
fixed-point operations avoid, which an unpacked internal register format
removes at 18 extra bits per decimal64 value.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

cowlishaw_2002 -> Cowlishaw, "Densely Packed Decimal Encoding", IEE Proceedings - Computers and Digital Techniques, 2002
eisen_2007 -> Eisen, Ward, Tast, Mading, Leenstra, Mueller, Granito, Prasad, Whitcomb, Mansfield, "IBM POWER6 accelerators: VMX and DFU", IBM Journal of Research and Development, 2007
duale_2007 -> Duale, Decker, Zipperer, Aharoni, Bohizic, "Decimal Floating-Point in z9: An Implementation and Testing Perspective", IBM Journal of Research and Development, 2007
schwarz_2009 -> Schwarz, Kapernick, Cowlishaw, "Decimal Floating-Point Support on the IBM System z10 Processor", IBM Journal of Research and Development, 2009
wang_2009 -> Wang, Schulte, Thompson, Jairam, "Hardware Designs for Decimal Floating-Point Addition and Related Operations", IEEE Transactions on Computers, 2009
