---
family: parity_prediction_adder
pin: {carry_scheme: carry_dependent_sum}
---
# carry_dependent_sum

Parity prediction from the adder's own carries: the result parity is
the digitwise modulo-b sum P(s) = P(n1) XOR P(n2) XOR P(c), where c is
the carry vector that the main adder itself produces, so no second
carry network exists and the check covers only the digitwise sum
stage. The scheme is the minimal form of the family and the one every
checked variant is measured against.

Carry generation is never independently checked, so a single
component malfunction can corrupt any number of sum digits from zero
through n+1, and the burst nature of the errors tends to make the
check useless for conventional addition. Because predicted and actual
parity change together, every fault confined to carry-generation
logic has infinite detection latency. It is cheaper than the
duplicate-carry and dual-rail schemes by the replica and the
comparator, and it still detects any odd number of output flips, so
it is the pick only where the datapath is already parity encoded and
the fault model excludes the carry logic; otherwise the family
upgrades to duplicate or dual-rail carries.

The generated checker's replica chain supplies the carries (duplicate_carry); carry_scheme is not a pin it reads.

## references

garner_1966 -> H. L. Garner, "Error Codes for Arithmetic Operations", IEEE Transactions on Electronic Computers, vol. EC-15, pp. 763-770, 1966
langdon_tang_1970 -> G. G. Langdon, C. K. Tang, "Concurrent Error Detection for Group Look-ahead Binary Adders", IBM Journal of Research and Development, vol. 14, no. 5, pp. 563-573, 1970
nicolaidis_2003 -> M. Nicolaidis, "Carry Checking/Parity Prediction Adders and ALUs", IEEE Transactions on VLSI Systems, vol. 11, no. 1, pp. 121-128, 2003
