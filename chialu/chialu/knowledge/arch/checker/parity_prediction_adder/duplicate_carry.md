---
family: parity_prediction_adder
pin: {carry_scheme: duplicate_carry}
---
# duplicate_carry

Parity prediction with an independently generated carry replica: each
cell or lookahead group produces its normal carry and a separately
formed check carry, the predicted result parity takes its
carry term from the replica, and the two carry sets are compared so a
fault in carry generation moves only one of predicted and actual
parity. The replica may be a ripple chain under a lookahead main
adder, duplicate group carries, or a compact cell that shares the
propagate signal with the main cell.

Unchecked duplicate carries give finite detection latency, with a
stuck-at carry fault detected with probability above one half per
cycle under uniform inputs, but stay non-fault-secure against an even
number of output errors; checking the normal/check pairs in a
double-rail checker makes the adder fault secure for a single logic
fault and yields the carry parity for free. The scheme costs about 21
percent over a conventional 16-bit carry-lookahead adder and keeps
detection inside one adder cycle when parity is predicted per group
from generate/transmit signals. It is the pick where operand parity
already exists and the base adder is ripple or grouped lookahead; the
textbook caveat is that complete checking needs enough logic that
full adder duplication with bit-by-bit comparison is probably as
attractive.

The generated checker realizes this variant: the checker's own replica chain supplies the carry vector.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
langdon_tang_1970 -> G. G. Langdon, C. K. Tang, "Concurrent Error Detection for Group Look-ahead Binary Adders", IBM Journal of Research and Development, vol. 14, no. 5, pp. 563-573, 1970
nicolaidis_1997 -> M. Nicolaidis, R. O. Duarte, S. Manich, J. Figueras, "Fault-Secure Parity Prediction Arithmetic Operators", IEEE Design & Test of Computers, vol. 14, pp. 60-71, 1997
nicolaidis_2003 -> M. Nicolaidis, "Carry Checking/Parity Prediction Adders and ALUs", IEEE Transactions on VLSI Systems, vol. 11, no. 1, pp. 121-128, 2003
