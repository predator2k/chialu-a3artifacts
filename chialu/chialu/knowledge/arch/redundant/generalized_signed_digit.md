# generalized_signed_digit

A radix-r digit takes values from a redundant set, symmetric {-a..a}
or asymmetric {-alpha..beta} with alpha + beta + 1 > r, so a number
has several representations and addition needs no carry chain: each
position forms p(i) = x(i) + y(i), selects a transfer t(i+1) and an
interim digit w(i) = p(i) - r t(i+1), and the result digit s(i) =
w(i) + t(i) needs no further transfer. With enough redundancy the
transfer is selected from the position alone and carries move one
place; otherwise a binary range estimate of the lower neighbour
restricts the transfer and bounds propagation to two stages,
as for radix 2 with {-1, 0, 1} in two full-adder levels. Addition
time is independent of word length.

radix and redundancy set the digit set and the cell. Raising the
radix cuts the relative storage overhead but grows the digit adder,
about 12 half-adder equivalents for a radix-4 stage, 2.5 to 3 times
a conventional one, with 3 storage bits per digit against 2; base 4
was chosen in the digit-pipelined system because base 8 needs more
logic and interconnect and a radix-2 most-significant-first adder
cannot reach latency one. Maximal redundancy (a = r - 1) gives
one-digit online delay, fewer residual digits for selection and
accepts conventional operands without conversion; minimal
redundancy (a = r/2) keeps recoding simple and avoids pseudonormal
cases, which is why the radix-16 division picks it, and online
division needs an intermediate set. Carry-free addition exists
exactly when r > 2 and the redundancy index alpha + beta + 1 - r is
at least 3, or at least 2 with neither bound equal to 1; the
two-stage limited-carry scheme applies to every set.

digit_encoding fixes the cell: a sign-magnitude or two's-complement
code, a positive/negative bit pair whose swap negates a digit and
lets subtractors reuse adder gates, or a one-hot 1-out-of-3 code
that detects every unidirectional error cheaply; the general
redundant cell costs about 42 transistors and 5 gate delays and the
redundant-plus-binary cell half that. final_conversion is the
family's tax: a carry-propagate adder takes time proportional to log
n and adds 8 gates to the 18-gate intrinsic path of a 16-bit
redundant-binary multiplier tree, whereas on-the-fly conversion
absorbs most-significant-first digits by conditional concatenation
at two logic levels per digit with no carry propagation. The family
wins where conversion is amortized over long operation sequences or
long operands, in multiplier trees, in online most-significant-first
units, which require a redundant representation, and in residue
checkers; sign, zero and overflow tests need separate scans, since
zero is unique only when the largest digit magnitude is below r.
Arithmetic is exact and feed-forward.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/redundant.py`: the adder of a `redundant_internal` core under this representation: radix 2^k digits in [-alpha, alpha] by `radix` and `redundancy`, the Booth-like entry recoding by the transfer t = [d >= r - alpha], the one-stage carry-free rule where 2 alpha >= r + 2 or the two-stage limited-carry rule whose transfer thresholds follow the sign set of the position below (`addition_scheme`), the digits stored in the `digit_encoding` between the stages, and the exit conversion through the lane's cpa family or on the fly (`final_conversion`); the negation, overflow and zero-scan choices concern a datapath that keeps the redundant form across ops, and the module header says the lane presents the complemented operand with a carry-in and reads its flags off the converted sum). `python3 -m chialu.targets.rtl.families.redundant --width 32 --slot representation --kind adder --family generalized_signed_digit --pins k=v,...` emits it for a rewrite.

## design choices

### digit_encoding

| member | what it selects |
| --- | --- |
| `sign_magnitude` | a sign bit beside the magnitude, so a digit costs k + 1 bits. |
| `twos_complement` | the digit as a two's complement word, so the digit add is a binary add. |
| `borrow_save` | the digit as a positive and a negative bit vector whose difference is its value, at 2k bits. |
| `one_hot` | one wire per digit value, at 2 alpha + 1 bits, which turns the digit decode into a select. |

### redundancy

| member | what it selects |
| --- | --- |
| `minimal` | alpha = r / 2, the smallest digit set that keeps the carry bounded. |
| `intermediate` | alpha = r / 2 + 1, which radix 2 and radix 4 do not have because no digit set lies between minimal and maximal. |
| `maximal` | alpha = r - 1, the largest digit set, which absorbs the carry in one position at the widest digit encoding. |

## references

avizienis_1961 -> Avizienis, "Signed-Digit Number Representations for Fast Parallel Arithmetic", IRE Transactions on Electronic Computers, 1961
parhami_1990 -> Parhami, "Generalized Signed-Digit Number Systems: A Unifying Framework for Redundant Number Representations", IEEE Transactions on Computers, 1990
parhami_1993 -> Parhami, "On the Implementation of Arithmetic Support Functions for Generalized Signed-Digit Number Systems", IEEE Transactions on Computers, 1993
ercegovac_2004 -> M. D. Ercegovac and T. Lang, "Digital Arithmetic", Morgan Kaufmann, 2004
takagi_1985 -> Takagi, Yasuura, Yajima, "High-Speed VLSI Multiplication Algorithm with a Redundant Binary Addition Tree", IEEE Transactions on Computers, 1985
ercegovac_1987 -> Ercegovac, Lang, "On-the-Fly Conversion of Redundant into Conventional Representations", IEEE Transactions on Computers, 1987
irwin_owens_1987 -> Irwin, Owens, "Digit-Pipelined Arithmetic as Illustrated by the Paste-Up System: A Tutorial", IEEE Computer, 1987
kuninobu_1987 -> Kuninobu, Nishiyama, Edamatsu, Taniguchi, Takagi, "Design of High Speed MOS Multiplier and Divider Using Redundant Binary Representation", 8th IEEE Symposium on Computer Arithmetic, 1987
