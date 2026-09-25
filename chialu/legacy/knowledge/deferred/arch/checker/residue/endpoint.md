---
family: residue
pin: {granularity: endpoint}
---
# endpoint

One separate mod-m mirror over the whole operation: operand residues,
preprovided by a residue-encoded dataflow or generated beside the
unit, pass through a residue adder or multiplier, a generator
recomputes the residue of the produced result, and a two-rail
comparator tests the two at the output. The check is independent of
the internal adder or multiplier design, and every separate checking
code is a residue code or isomorphic to one.

Endpoint checking aliases whenever the error value is a multiple of
m: modulus 3 leaves about 2/3 coverage of random multiple-bit
failures, 9 gives 8/9 and 15 gives 14/15, while every single-bit flip
is caught. Cost turns on where the operand residues come from: with
both residues generated locally a mod-3 adder check costs more than
parity and even duplication in 1970 circuit counts, whereas
preprovided residues make one generator plus one checker the cheapest
data-flow strategy. Over a Booth/Wallace multiplier in 1.0-micron
CMOS the base-3 check costs about 37 percent at 16 by 16 and 11.5
percent at 64 by 64. Group look-ahead adders need a supplementary
duplicate group-carry check for error values divisible by m, and
per-stage checking takes over when rounding, rotation and shifted-out
digits must be covered inside the operation.

The generated checker checks at the endpoint (the module's outputs); granularity is not a pin it reads.

## references

lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
garner_1966 -> H. L. Garner, "Error Codes for Arithmetic Operations", IEEE Transactions on Electronic Computers, vol. EC-15, pp. 763-770, 1966
langdon_tang_1970 -> G. G. Langdon, C. K. Tang, "Concurrent Error Detection for Group Look-ahead Binary Adders", IBM Journal of Research and Development, vol. 14, no. 5, pp. 563-573, 1970
lipetz_schwarz_2011 -> D. Lipetz, E. Schwarz, "Self Checking in Current Floating-Point Units", Proc. 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 73-76, 2011
nicolaidis_duarte_1999 -> M. Nicolaidis, R. O. Duarte, "Fault-Secure Parity Prediction Booth Multipliers", IEEE Design & Test of Computers, vol. 16, no. 3, pp. 90-101, 1999
