# parity_prediction_multiplier

Concurrent error detection for a multiplier by parity prediction: the
product parity is predicted as Pout = Ppp XOR PC, the XOR of the
partial-product parity and the parity of the internal carries of the
reduction network, and compared with the parity of the product. The
adder cells are restructured with redundant carries and odd fan-out sum
paths so that any single fault in an AND gate, a Booth decoder, a
selector or an adder cell produces an odd-multiplicity output error or
an invalid double-rail checker output, and a two-rail checker tree
covers the duplicated decoders and the carry-lookahead final adder.

The recoding choice sets what has to be protected. Without recoding the
AND-generated partial products enter a Braun array or a Wallace network
whose cells use redundant carries, and the cellular proof of fault
secureness follows the cells. With radix-4 Booth recoding one decoder
fault can corrupt many partial products, so the decoder cells are
duplicated and checked, the sign-extension region needs modified
fan-outs and duplicated XOR logic, and the reduced-cost form derives
the decoded-line parities from the double-rail checker instead of
separate row-parity circuits. The check depth in every reported design
is a single final comparison; per-stage checks are the split the
family's mutations offer. The final adder matters to the proof: a
ripple adder keeps the cellular argument, a carry-lookahead adder needs
redundant carries and its own double-rail checker. The cell style
trades area against parity delay, since a cell that shares the
propagate signal is smaller but lengthens the worst-case parity path.

The fault contract is single-fault secureness, with the two-rail
checker self-testing when every cell sees all four code inputs in
normal operation; primary-input faults need input checking where a zero
partial-product parity masks them, and false-alarm behaviour and
quantitative coverage are not reported. The cost is substantial: with
shared-propagate cells the area overhead of a Braun or Wallace array is
about 47 percent in 1.0 um CMOS, and for Booth/Wallace with a
carry-lookahead adder it falls from about 48 percent at 8x8 to 34
percent at 64x64 while delay overhead shrinks with width. Against the
residue checker, which is the neighbour, parity prediction is cheaper
below about 16x16 with a carry-lookahead final adder; a Kogge-Stone
final adder forces residue onto modulus 2^12 - 1 and moves the
crossover to 32x32. Regular arrays keep linear delay and Wallace trees
logarithmic delay under the restructuring. The datapath is
feed-forward.

The generated checker (`chialu/targets/rtl/alu_checker.py`) realizes this family: the parity of the partial-product rows (an AND array, or radix-4 Booth rows under `recoding: booth2`) and of the carry vectors of the checker's own row-by-row reduction, compared with the product's parity for mul_wide and mul; check_depth per_csa_stage and fault_secure_structuring need the datapath's internal carries and cells, which the seam does not carry, so the check stays final_only over the replica.

## references

nicolaidis_1997 -> M. Nicolaidis, R. O. Duarte, S. Manich, J. Figueras, "Fault-Secure Parity Prediction Arithmetic Operators", IEEE Design & Test of Computers, vol. 14, pp. 60-71, 1997
nicolaidis_duarte_1999 -> M. Nicolaidis, R. O. Duarte, "Fault-Secure Parity Prediction Booth Multipliers", IEEE Design & Test of Computers, vol. 16, no. 3, pp. 90-101, 1999
