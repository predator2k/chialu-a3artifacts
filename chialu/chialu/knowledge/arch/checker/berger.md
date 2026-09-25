# berger

Separable unordered code: the check symbol is the binary count of zeros
in the information word (B0), or the complemented count of ones (B1),
which costs ceil(log2(k+1)) check bits and detects every single error
and every unidirectional multi-bit error, because a unidirectional
error moves the count in a direction the symbol cannot follow. The
checker regenerates the check field from the information bits with a
counting tree and compares it with the stored field in a self-checking
two-rail tree. For an ALU the result symbol is instead predicted from
the operand symbols, the carry vector and the operation (S_c = X_c +
Y_c - C_c - c_in + c_out for addition), so the check runs concurrently.

The check_field choice trades check bits for the error length covered.
The full-log field is the least redundant unordered code that detects
all unidirectional errors; the modulo-reduced field encodes the zero
count modulo t+1 in ceil(log2(t+1)) bits and covers unidirectional
errors of length t, or encodes the distance from the minimum valid zero
count, which drops the worked four-output PLA from 3 check bits to 2 at
the cost of one extra product term. The regenerating counter is the
checker's area: a full-adder count tree spends the sum of (2^a - 1)
modules over the check bits (4 modules at 7 information bits, 11 at
15), and the union-of-m-out-of-n construction uses fewer gates and
levels but its fan-in grows with information length and it requires B1
encoding.

The family fits units whose single faults produce unidirectional
errors: a PLA's stuck-at, bridging and contact faults yield either a
detectable unidirectional non-codeword or the correct word. A raw ALU
does not err unidirectionally under every fault, so a Berger-checked
ALU needs the check-prediction organization that forces the analysed
faults onto non-codewords; that construction gave an 8-bit processor a
12-bit internal bus against 16 bits for a two-rail duplicate. The
granularity choice places the checker at the endpoint in every design
on file; per-stage placement is untested. The checker's own faults are
exposed only when normal operation supplies enough distinct valid
codewords, and the residue mutation is the route when arithmetic rather
than logic dominates the unit.

The generated checker (`chialu/targets/rtl/alu_checker.py`) realizes this family: the ones count of the sum predicted from the addends' counts, the carry-in and the carry vector of the replica chain, compared with the count of the result.

## design choices

### construction

| member | what it selects |
| --- | --- |
| `berger` | the check symbol is the full zero count of the result, which detects any unidirectional error. |
| `bose_lin_method2` | the check symbol is that count modulo 2^r, which costs r bits and detects a unidirectional error of at most 2^r - 1 bits. |

## references

lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
lo_1992 -> J.-C. Lo, S. Thanawastien, T. R. N. Rao, M. Nicolaidis, "An SFS Berger Check Prediction ALU and Its Application to Self-Checking Processor Designs", IEEE Transactions on Computer-Aided Design, vol. 11, no. 4, pp. 525-540, 1992
