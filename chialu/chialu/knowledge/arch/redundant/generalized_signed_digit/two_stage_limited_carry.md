---
family: generalized_signed_digit
pin: {addition_scheme: two_stage_limited_carry}
---
# two_stage_limited_carry

Limited-carry addition for digit sets too small for carry-free
selection: a binary range estimate of the lower neighbour's position
sum, low or high, restricts the transfer before a second selection
stage, so each result digit depends on the two lower operand
positions and propagation stops after two stages. The original modified
form, two transfers and three steps, admits
radix 2 with {-1, 0, 1}; the radix-2 online adder is two full-adder
levels at online delay 2, against 1 above radix 2.

The scheme applies to every generalized signed-digit system, so it
is the pick whenever the digit set is minimal: radix-2 signed
digits, the minimally redundant radix-16 set of the signed-digit
divider, whose maximal set would bring pseudonormal cases and harder
recoding, the base-4 digit-pipelined adder whose restricted interim
sets make its second addition carry-free at four gate delays word
parallel, and the decimal [-8, 8] adders that take four operands per
level. Its cost over carry_free is the extra stage and the longer
transfer path; the smaller digit set repays it in storage bits and
simpler multiple selection.

The library's signed-digit adder realizes this scheme as the transfer rule whose thresholds (alpha, -alpha - 1 or alpha + 1, -alpha) follow whether the position below can send a negative transfer (`chialu/targets/rtl/families/redundant.py`).

## references

parhami_1990 -> Parhami, "Generalized Signed-Digit Number Systems: A Unifying Framework for Redundant Number Representations", IEEE Transactions on Computers, 1990
avizienis_1961 -> Avizienis, "Signed-Digit Number Representations for Fast Parallel Arithmetic", IRE Transactions on Electronic Computers, 1961
ercegovac_2004 -> M. D. Ercegovac and T. Lang, "Digital Arithmetic", Morgan Kaufmann, 2004
irwin_owens_1987 -> Irwin, Owens, "Digit-Pipelined Arithmetic as Illustrated by the Paste-Up System: A Tutorial", IEEE Computer, 1987
tung_1968 -> Tung, "A Division Algorithm for Signed-Digit Arithmetic", IEEE Transactions on Computers, 1968
