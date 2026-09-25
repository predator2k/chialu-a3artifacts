---
family: self_checking_datapath
pin: {encoding: parity_plus_dual_rail_carry}
---
# parity_plus_dual_rail_carry

The adder or ALU carries its carries in double-rail code and its data
in parity: a check-carry slice recomputes each carry, a two-rail
checker compares the normal and check carries, and the output parity
is predicted from the operand parities, the carry-in and the carry
parity, which the checker itself produces because its structure
corresponds to a parity tree. A single fault in a carry, check-carry
or bit-slice module then yields a non-codeword at the output without
duplicating the datapath.

The encoding is the pick where buses and register files already use
parity. The check-carry slices use ripple logic fed from the preceding normal
carry, so lookahead or skip logic is not duplicated and fast adders
get the lowest relative overhead: 12% for a 64-bit carry-lookahead
adder and 39% for a 16-bit ALU against 100% for duplication. The
scheme is fault secure for single logic faults in the enumerated
modules and self-testing for single stuck-at faults when the blocks
have no redundant faults; a static implementation needs current
monitoring to be self-testing for stuck-on faults. Global ALU control
lines need parity coding and their own checker, ALUs cost more than
adders because logic operations add parity prediction, and in a
Booth multiplier the cells stay fault secure only while every signal
has odd sum-path parity. In the ADIR grammar it is
`family: self_checking_datapath` with
`pin: {encoding: parity_plus_dual_rail_carry}`.

The generated checker has no realization for this family (an exception, `alu_checker.EXCEPTIONS`): the core would emit the dual-rail carries.

## references

nicolaidis_2003 -> M. Nicolaidis, "Carry Checking/Parity Prediction Adders and ALUs", IEEE Transactions on VLSI Systems, vol. 11, no. 1, pp. 121-128, 2003
nicolaidis_1993 -> M. Nicolaidis, "Efficient Implementations of Self-Checking Adders and ALUs", Proc. FTCS-23, pp. 586-595, 1993
nicolaidis_duarte_1999 -> M. Nicolaidis, R. O. Duarte, "Fault-Secure Parity Prediction Booth Multipliers", IEEE Design & Test of Computers, vol. 16, no. 3, pp. 90-101, 1999
