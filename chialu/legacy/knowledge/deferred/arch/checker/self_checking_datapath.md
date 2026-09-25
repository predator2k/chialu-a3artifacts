# self_checking_datapath

Concurrent error detection without duplication: the functional unit
maps input code words to output code words and a checker validates the
output code, so a non-code output signals a fault in the unit or in the
checker. In the binary form the adder/ALU carries its carries in double
rail (a normal carry and a check carry per slice), a two-rail tree
compares the pair, and the output parity is predicted from the operand
parities, the carry-in and the carry parity. The two-rail checker has
the structure of a parity tree, so it emits the carry-parity signals
and no separate parity generator or double-rail-to-parity translator
is needed; buses and register files around the unit stay parity coded.

The encoding choice sets how much of the datapath is doubled. Checking
only the carries is the cheapest form; adding parity prediction covers
the sum outputs as well; a fully two-rail unit doubles every signal.
The overhead lever is the check-carry network: each check-carry slice
uses ripple logic but takes its carry input from the preceding normal
carry, so a carry-lookahead, skip or conditional-sum block is never
duplicated and no linear delay is added. That gives about 12% overhead
for a 64-bit carry-lookahead adder against 100% for duplication, and
about 39% for a 16-bit carry-lookahead ALU, because logic operations
need extra parity-prediction logic and global control lines need
parity coding. Partial duplication shares one signal among normal
carry, check carry and sum so that a common-mode carry error becomes
parity-visible.

The fault contract is the totally-self-checking one: fault-secure
(never an incorrect code word) for single logic faults in the
enumerated carry and bit-slice modules, and self-testing (every assumed
fault yields a non-code output for some code input) when the optimized
blocks carry no redundant faults. Static CMOS reaches that contract for
stuck-at and stuck-open faults; stuck-on faults are only fault-secure
without current monitoring, while DCVS or domino logic is strongly
fault-secure for all three. In multiplier arrays the same carry-checked
cells are fault-secure only when every signal has odd sum-path parity,
so even fan-outs in the Booth sign-extension region need a duplicated
XOR.

The family sits between parity prediction (the relax mutation, which
drops the checked carries and loses fault security on the carry chain)
and residue checking, which multipliers prefer. Berger check prediction
is the other codeword-emitting form: the ALU and logic units are
separated, the zeros of the internal carries are counted, and the extra
hardware falls from about 92% at 8 bits toward 29% at 64 bits. The
biquinary adder with one-hot quinary lines and a carry/no-carry pair is
the decimal ancestor of the idea.

The family's defining structure lies outside the checker seam (the core itself would emit codewords, dual-rail carries or m-out-of-n and Berger outputs, which the interface does not carry), so the generator has no realization for it: the checker variable does not offer it and the family is listed as an exception (`alu_checker.EXCEPTIONS`).

## references

lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
nicolaidis_2003 -> M. Nicolaidis, "Carry Checking/Parity Prediction Adders and ALUs", IEEE Transactions on VLSI Systems, vol. 11, no. 1, pp. 121-128, 2003
nicolaidis_1993 -> M. Nicolaidis, "Efficient Implementations of Self-Checking Adders and ALUs", Proc. FTCS-23, pp. 586-595, 1993
nicolaidis_duarte_1999 -> M. Nicolaidis, R. O. Duarte, "Fault-Secure Parity Prediction Booth Multipliers", IEEE Design & Test of Computers, vol. 16, no. 3, pp. 90-101, 1999
lo_1992 -> J.-C. Lo, S. Thanawastien, T. R. N. Rao, M. Nicolaidis, "An SFS Berger Check Prediction ALU and Its Application to Self-Checking Processor Designs", IEEE Transactions on Computer-Aided Design, vol. 11, no. 4, pp. 525-540, 1992
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
