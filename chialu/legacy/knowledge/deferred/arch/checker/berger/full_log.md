---
family: berger
pin: {check_field: full_log}
---
# full_log

The conventional Berger code: the check field is the full binary count
of zeros in the k information bits under B0 encoding, or the
complemented count of ones under B1 encoding, in c = ceil(log2(k+1))
check bits. A Type I checker regenerates the complement of the check
field from the information bits and compares it with the stored field
in a totally self-checking two-rail checker; a Berger check prediction
ALU instead predicts the result symbol from the operand symbols and the
carry vector.

The full count detects single and arbitrary unidirectional multibit
errors and is the least-redundant unordered code that does so, whereas
the modulo_reduced field detects unidirectional errors only up to
length t in ceil(log2(t+1)) check bits (lala_2001). A maximal-length
code with c check bits needs a full-adder count generator of sum over
a from 1 to c-1 of (2^a - 1) modules, which is 4 modules at 7
information bits and 11 at 15. The full field is the pick when
unidirectional errors of any length must be caught, as in an ALU whose
organization forces the analyzed faults to produce noncodewords; Berger
coding alone does not detect multiple non-unidirectional ALU-output
errors, so the carry-aware prediction equations are required (lo_1992).

The generated checker realizes this variant: a full count compare.

## references

lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
lo_1992 -> J.-C. Lo, S. Thanawastien, T. R. N. Rao, M. Nicolaidis, "An SFS Berger Check Prediction ALU and Its Application to Self-Checking Processor Designs", IEEE Transactions on Computer-Aided Design, vol. 11, no. 4, pp. 525-540, 1992
