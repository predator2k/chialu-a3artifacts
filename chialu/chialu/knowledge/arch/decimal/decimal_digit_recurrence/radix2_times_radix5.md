---
family: decimal_digit_recurrence
pin: {digit_split: radix2_times_radix5}
---
# radix2_times_radix5

The split-digit recurrence: each radix-10 quotient digit is written
q = 5 qH + qL with qH in {-1, 0, 1} and qL in {-2, -1, 0, 1, 2}, and
the iteration runs two steps, v = 10 w - qH (5d) and then
w = v - qL d, so only the divisor, its double and its quintuple are
ever added or subtracted. Robertson forms 2d and 5d on demand through
one permuted excess-three circuit; the BCD unit precomputes 5dBCD and
2dBCD and their negatives and adds them with BCD-aware carry-save
adders.

It is the pick when stored multiples and a wide selection table are
too expensive: the multiple store shrinks to d, the first step is
skipped when qH is zero, and the average falls to 2.33 operations per
digit. The cost is two dependent add/subtract passes per digit, so
the cycle per digit is longer than the single pass of a prescaled
-5..5 recurrence, and the most significant slice needs its own
radix-2 selection logic. Unsplit sets win when a full set of
multiples or a prescaler is affordable and the digit loop must be one
adder pass.

## references

robertson_1958 -> Robertson, "A New Class of Digital Division Methods", IRE Transactions on Electronic Computers, 1958
lang_2007b -> Lang, Nannarelli, "Combined Radix-10 and Radix-16 Division Unit", 41st Asilomar Conference on Signals, Systems and Computers, 2007
