---
family: parity_prediction_adder
pin: {carry_scheme: dual_rail_carry}
---
# dual_rail_carry

Carries represented as double-rail pairs while the sums stay
single-rail: a double-rail checker verifies the carry pairs and its
outputs supply the carry parity for PS = PA XOR PB XOR PC, so carry
checking rather than double-rail checking of the sum outputs delivers
fault security. Under a lookahead main adder the normal carries come
from the lookahead block, redundant check carries ripple
independently, and the lowest erroneous lookahead carry is compared
against its unaffected check carry.

The scheme gives strongly fault-secure and totally self-checking
behaviour under the stated technology-dependent fault guarantees,
where conventional parity prediction detects single output errors but
fails when one carry fault produces several. For a ripple adder it
costs slightly more than plain parity prediction, about 18 percent
versus 11 percent asymptotically in static CMOS with the checker
excluded; for a carry-lookahead adder it costs less, about 16 percent
versus 32 percent, because plain prediction duplicates the fast carry
network and is not fault secure there anyway. It is the pick when the
base adder is lookahead or when fault security rather than finite
latency is the contract; the duplicate-carry scheme with checked
pairs reaches the same contract with partial sharing of the sum path.

The generated checker's replica chain supplies the carries (duplicate_carry); carry_scheme is not a pin it reads.

## references

nicolaidis_1993 -> M. Nicolaidis, "Efficient Implementations of Self-Checking Adders and ALUs", Proc. FTCS-23, pp. 586-595, 1993
nicolaidis_2003 -> M. Nicolaidis, "Carry Checking/Parity Prediction Adders and ALUs", IEEE Transactions on VLSI Systems, vol. 11, no. 1, pp. 121-128, 2003
