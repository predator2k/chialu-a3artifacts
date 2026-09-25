---
family: sequential_shift_add
pin: {accumulator_form: carry_propagate}
---
# carry_propagate

The partial product lives in one register, and each step's conditional
addition of the selected multiplicand multiple resolves its carries
before the shift, one carry-propagate addition and one one-place shift
per multiplier digit, so after n steps the register holds the
assimilated product and no final addition follows. Shifting the
accumulated sum rather than the multiplicand keeps the adder at
multiplicand width plus one, and the vacated low accumulator orders
hold the multiplier digits.

It is the form the textbook and early-machine designs use: the
Mead-Conway program that shifts X and Z and adds Y under the removed
most-significant bit for 16 iterations on a dynamic Manchester chain,
Richards' shifting accumulator, Booth's and Tocher's circulating
registers, and MacSorley's variable-shift multiplier on a group-5
carry-lookahead adder. The loop delay is a full carry propagation per
step, so speed is bought with a faster step adder or with recoding
rather than with the accumulator: zero-chain skipping halves the
average step count to about n/2, and minimal signed-digit recoding
removes about a third of the additions for long operands. It is the
pick for minimum area at one or two bits per cycle; the carry_save
sibling takes the carry chain out of the loop once several multiples
are added per pass and pays one assimilating addition at the end.

## references

mead_conway1980 -> C. Mead, L. Conway, "Introduction to VLSI Systems", Addison-Wesley, 1980.
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
booth1951 -> A. D. Booth, "A Signed Binary Multiplication Technique", Quarterly Journal of Mechanics and Applied Mathematics, vol. 4, no. 2, pp. 236-240, 1951
tocher_1958 -> Tocher, "Techniques of Multiplication and Division for Automatic Binary Computers", Quarterly Journal of Mechanics and Applied Mathematics, 1958
macsorley1961 -> O. L. MacSorley, "High-Speed Arithmetic in Binary Computers", Proceedings of the IRE, vol. 49, no. 1, pp. 67-91, 1961
