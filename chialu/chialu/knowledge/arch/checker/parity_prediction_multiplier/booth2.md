---
family: parity_prediction_multiplier
pin: {recoding: booth2}
---
# booth2

Parity prediction over a radix-4 Booth multiplier: output parity is
predicted as Ppp XOR PC from the partial-product parity and the
internal-carry parity, the Booth decoder cells are duplicated and fed
to double-rail checker trees because one decoder fault corrupts many
partial products, and modified sum-path fan-outs plus duplicated XOR
logic make the Wallace reduction an odd-fan-out network so faults in
the sign-extension region stay parity-visible.

The Booth form pays for decoder duplication and the sign-extension
restructuring, but the reduced-cost construction reuses the checker
outputs to derive the decoded-line parities and drops the separate
row-parity circuits. It is the pick when the multiplier is Booth
recoded anyway and the width is moderate: with a Wallace tree and a
carry-lookahead final adder the area overhead falls from about 48
percent at 8x8 to 34 percent at 64x64 in 1.0 um CMOS, and it stays
cheaper than residue checking below about 16x16, or 32x32 when a
Kogge-Stone final adder forces the residue modulus to 2^12 - 1. The
contract is single-fault secureness over decoders, predictor, selectors
and the modified adder network, with a self-testing two-rail checker.

The generated checker realizes this variant (`checker.recoding: booth2`): radix-4 Booth rows from the overlapping triplets of the multiplier.

## references

nicolaidis_duarte_1999 -> M. Nicolaidis, R. O. Duarte, "Fault-Secure Parity Prediction Booth Multipliers", IEEE Design & Test of Computers, vol. 16, no. 3, pp. 90-101, 1999
