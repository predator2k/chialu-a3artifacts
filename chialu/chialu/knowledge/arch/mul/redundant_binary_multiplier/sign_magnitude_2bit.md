---
family: redundant_binary_multiplier
pin: {rb_encoding: sign_magnitude_2bit}
---
# sign_magnitude_2bit

Each redundant digit as a sign bit and a magnitude bit: the digit set
{-1, 0, 1} is coded with one bit saying nonzero and one saying
negative, the radix-4 Booth recoder's adjacent even and odd terms are
paired and the two binary multiples subtracted to form one
signed-digit partial product, so an n-bit multiplier reduces about n/4
rows through log2(n) - 2 levels of two-input redundant adders before a
carry-lookahead converter.

It is the pick when the partial-product count is the lever: the
paired-Booth formation gives n/4 rows, and the 64x64 design lands at
34 gates on the critical path and 90,000 transistors, 90 percent and
75 percent of a Booth-plus-Wallace multiplier, with a regular tree
layout. Against plus_minus_pair it trades the free negation of the
two-wire code for simplified redundant adder cells organized around
the sign and magnitude fields; both double the wiring of a
conventional tree, and the comparison in the evidence is limited to
the paper's own 64-bit circuits.

## references

kuninobu_1987 -> Kuninobu, Nishiyama, Edamatsu, Taniguchi, Takagi, "Design of High Speed MOS Multiplier and Divider Using Redundant Binary Representation", 8th IEEE Symposium on Computer Arithmetic, 1987
