# parity_prediction_adder

Concurrent error detection for an adder by predicted parity: the
result parity is the XOR of the two operand parities, the carry-in,
and the parity of the carry vector, so a parity-encoded datapath only
has to generate the carry parity. If that parity comes from the
adder's own carries, a fault confined to carry generation moves
predicted and actual parity together and is never detected, and one
carry fault that flips an even number of sum bits escapes parity.
The family builds an independent carry replica (ripple, grouped
lookahead, or a dual-rail pair per carry), compares it with the main
carries in a two-rail checker, and takes the carry parity from the
checked pair.

The carry scheme sets the fault contract. Parity derived from the
adder's own carries is nearly useless for conventional addition,
because one component malfunction can corrupt any number of sum
digits from zero to n+1 and carry generation is never independently
checked. Unchecked duplicate carries give finite detection latency,
with a stuck-at carry fault detected with probability above one half
per cycle under uniform inputs, but they are not fault secure against
even-multiplicity output errors. Checking the normal/replica carry
pairs with a double-rail checker makes the adder fault secure for a
single logic fault, and the checker's outputs supply the carry parity
for free. Cost depends on the base adder: for a ripple adder the
checked scheme costs slightly more than plain parity prediction
(asymptotically about 18 percent versus 11 percent over the unchecked
adder, static CMOS), while for a lookahead adder it costs less (about
16 percent versus 32 percent), because plain prediction duplicates the
fast carry network and is not fault secure there anyway, since the
lookahead block is not a network of full and half adders. A replica
cell may share its propagate signal with the main cell only when any
fault that reaches both carries also reaches the sum.

Parity groups exist because a single XOR tree over the whole width
arrives later than the sum; a grouped predictor built from
generate/transmit and half-sum signals keeps detection inside one
adder cycle, and a half-sum check over the inputs completes coverage
of single-gate failures. The family wins where operands already carry
parity and results must go straight to a cache or register file with
parity attached; the prediction circuit is on the order of a third of
the adder, and parity catches every odd-multiplicity flip and every
single flip within a protected byte. Parity is also cheaper than
residue at the data-flow level once three or more data-transfer checks
share the code. Residue replaces it when the storage code is flexible,
which is the upgrade path the family names. Execution is feed-forward.

The generated checker (`chialu/targets/rtl/alu_checker.py`) realizes this family: the parity of the addends, the carry-in and the carry vector of the checker's own replica chain (duplicate_carry), compared with the result's parity.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
garner_1966 -> H. L. Garner, "Error Codes for Arithmetic Operations", IEEE Transactions on Electronic Computers, vol. EC-15, pp. 763-770, 1966
langdon_tang_1970 -> G. G. Langdon, C. K. Tang, "Concurrent Error Detection for Group Look-ahead Binary Adders", IBM Journal of Research and Development, vol. 14, no. 5, pp. 563-573, 1970
nicolaidis_1993 -> M. Nicolaidis, "Efficient Implementations of Self-Checking Adders and ALUs", Proc. FTCS-23, pp. 586-595, 1993
nicolaidis_1997 -> M. Nicolaidis, R. O. Duarte, S. Manich, J. Figueras, "Fault-Secure Parity Prediction Arithmetic Operators", IEEE Design & Test of Computers, vol. 14, pp. 60-71, 1997
nicolaidis_2003 -> M. Nicolaidis, "Carry Checking/Parity Prediction Adders and ALUs", IEEE Transactions on VLSI Systems, vol. 11, no. 1, pp. 121-128, 2003
lipetz_schwarz_2011 -> D. Lipetz, E. Schwarz, "Self Checking in Current Floating-Point Units", Proc. 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 73-76, 2011
