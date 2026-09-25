---
family: generalized_signed_digit
pin: {addition_scheme: carry_free}
---
# carry_free

Totally parallel addition: each position selects its outgoing
transfer from its own position sum, so the interim digit and the
transfer from the position below combine into the result digit with
no further transfer, and every result digit depends on two adjacent
operand positions only. The radix-2 form with {-1, 0, 1} first picks
an intermediate carry and sum whose signs are kept from clashing
with the lower carry, so each output depends on six local digits
and the depth is still constant.

Carry-free selection exists only with enough redundancy, radix above
2 and redundancy index at least 3 (or 2 with no digit bound equal to
1), which is the price against two_stage_limited_carry, which works
for every digit set at one more stage. Where it applies it gives the
shortest cell: the general redundant cell is 42 transistors and 5
gate delays, the redundant-plus-binary cell 22 and 3, and a
three-level redundant-binary tree sums a 16-bit product in 18 gates.
It is the pick for multiplier trees, online residual updates and
signed-digit DNN datapaths that stay redundant between operations.

The library's signed-digit adder realizes this scheme when the digit set allows it (2 alpha >= r + 2); with the minimal set the two-stage rule applies and the module header says so (`chialu/targets/rtl/families/redundant.py`).

## references

avizienis_1961 -> Avizienis, "Signed-Digit Number Representations for Fast Parallel Arithmetic", IRE Transactions on Electronic Computers, 1961
parhami_1990 -> Parhami, "Generalized Signed-Digit Number Systems: A Unifying Framework for Redundant Number Representations", IEEE Transactions on Computers, 1990
takagi_1985 -> Takagi, Yasuura, Yajima, "High-Speed VLSI Multiplication Algorithm with a Redundant Binary Addition Tree", IEEE Transactions on Computers, 1985
kuninobu_1987 -> Kuninobu, Nishiyama, Edamatsu, Taniguchi, Takagi, "Design of High Speed MOS Multiplier and Divider Using Redundant Binary Representation", 8th IEEE Symposium on Computer Arithmetic, 1987
harata_1987 -> Harata, Nakamura, Nagase, Takigawa, Takagi, "A High-Speed Multiplier Using a Redundant Binary Adder Tree", IEEE Journal of Solid-State Circuits, 1987
