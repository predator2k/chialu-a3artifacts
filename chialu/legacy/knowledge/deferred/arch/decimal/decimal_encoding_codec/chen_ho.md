---
family: decimal_encoding_codec
pin: {significand_encoding: chen_ho}
---
# chen_ho

The Chen-Ho compression: each BCD digit is split into a magnitude
indicator, which says whether the digit is 8 or 9, and detail bits, and
a Huffman-coded indicator field plus a variable-length detail field
combine into a fixed-length codeword, 7 bits for two digits or 10 bits
for three. Encoding and decoding are tests of the indicator bits
followed by permutations, deletions, insertions and fixed fill bits, so
no arithmetic is involved.

Chen-Ho is the storage-side pick that DPD later refined: three-digit
blocks compress 12 BCD bits into 10, within 0.34% of the asymptotic
limit, and save 20% of storage at the arithmetic-unit/memory interface
while the arithmetic unit keeps expanded BCD. In 80% of two-digit cases
the codeword is the BCD pattern with a redundant zero removed, and 64%
of three-digit cases are formed by deletion alone; the two-digit mapping
preserves the parity of the digits, the three-digit one does not
uniformly. Against DPD, which uses the same three-digits-in-ten-bits
density, Chen-Ho leaves only values 0 through 7 unchanged where DPD
keeps 0 through 79 identical to BCD, and it fits 69 digits in 230 of 237
available bits where DPD fits 71, so the 754-2008 hardware encoding is
DPD.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

chen_ho_1975 -> Chen, Ho, "Storage-Efficient Representation of Decimal Data", Communications of the ACM, 1975
cowlishaw_2002 -> Cowlishaw, "Densely Packed Decimal Encoding", IEE Proceedings - Computers and Digital Techniques, 2002
