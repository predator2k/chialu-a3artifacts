# online_arithmetic_unit

An operator that consumes operand digits most-significant-first and
commits result digit j after operand digit j + delta: it stores the
operand prefixes and a redundant residual, each cycle forms the new
residual from the shifted old one and the digit multiples (for
multiplication w[j] = r(w[j-1] - d[j-1]) + X[j] y[j] + Y[j-1] x[j]),
selects one result digit from a few leading residual digits, by
selection constants or by rounding a truncated estimate, and keeps
the remainder. Redundant digits make the selection irrevocable and
the step carry-free, so step time is independent of word length, an
n-digit result takes n + delta + 1 cycles, and a dependent operator
starts after delta digits.

radix trades cycles against cell size: a higher radix cuts the step
count but grows the selector, the multiple generation and the adder,
and selection constants become impractical above radix 4, where
rounding the residual estimate is the simpler rule as long as the
recurrence preserves the bounds; the digit-pipelined system settled
on base 4. online_delay is what the digit_set buys: with maximal
redundancy addition at radix above 2, multiplication and radix-4-plus
square root run at delay 1 with three-digit residual estimates, while
radix-2 addition needs 2, radix-2 multiplication 3, division 3 to 4,
and online CORDIC sine/cosine 5 after averaging two branching modules
(6 with one), which also tightens the error bound from 2^-n+3 to
2^-n+2; online division needs an intermediate set. residual_form is
carry-save or signed-digit: a preliminary comparison found no clear
difference, the rotation-factor unit used carry-save throughout with
two- or three-bit estimates, and the digit-pipelined and
large-number units kept signed digits.

The family is fixed-iteration and pays off in networks of dependent
operators: overlapped and pipelined online networks run 2 to 16
times faster than conventional arithmetic networks at typical
precision, dependent CORDIC and rotation steps overlap, logarithm,
multiplication and exponential evaluation overlap in the powering
unit, and a DNN layer can consume digits before the producing layer
terminates, for up to 16 times the throughput of the following
layer. Step time is about ten gate delays at radix 2. It loses on
isolated operations and comparisons, where conversion and serial
flow dominate, and a bounded-size online operator can compute only
functions that are affine with rational coefficients on each
interval, so multiplication, division and square root of
arbitrary-length operands need storage that grows with the word.
Inputs with k significant digits give at least k - delta significant
output digits, a symmetric digit set avoids truncation bias, and
on-the-fly conversion or rounding turns the digit stream
conventional without a carry-propagate pass.

The family's defining structure streams one result digit per cycle after the on-line delay, so the library has no combinational module for it; a core that declares it stays behavioral and the family is listed as an exception (`redundant.EXCEPTIONS`).

## references

ercegovac_2004 -> M. D. Ercegovac and T. Lang, "Digital Arithmetic", Morgan Kaufmann, 2004
ercegovac_1984 -> Ercegovac, "On-Line Arithmetic: An Overview", SPIE Real-Time Signal Processing VII, 1984
trivedi_1977 -> Trivedi, Ercegovac, "On-Line Algorithms for Division and Multiplication", IEEE Transactions on Computers, 1977
ercegovac_1977 -> Ercegovac, "A General Hardware-Oriented Method for Evaluation of Functions and Computations in a Digital Computer", IEEE Transactions on Computers, 1977
oklobdzija_1982 -> Oklobdzija, Ercegovac, "An On-Line Square Root Algorithm", IEEE Transactions on Computers, 1982
irwin_owens_1987 -> Irwin, Owens, "Digit-Pipelined Arithmetic as Illustrated by the Paste-Up System: A Tutorial", IEEE Computer, 1987
ercegovac_lang_1988 -> Ercegovac, Lang, "On-Line Scheme for Computing Rotation Factors", Journal of Parallel and Distributed Computing, 1988
muller_1994 -> Muller, "Some Characterizations of Functions Computable in On-Line Arithmetic", IEEE Transactions on Computers, 1994
