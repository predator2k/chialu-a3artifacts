# sequential_shift_add

Multiplication by one adder row reused across the multiplier digits:
each step senses one multiplier digit or recoded digit group,
conditionally adds or subtracts the selected multiplicand multiple to
the partial product, and shifts the partial product one place right
per digit, p[k+1] = (p[k] + y[n-k] x) / 2, so after n steps the
accumulator and the vacated multiplier register hold the
double-length product. Shifting the accumulated sum rather than the
multiplicand keeps the adder at multiplicand width plus one, and the
multiplier digits can occupy the low accumulator orders. One step
per cycle makes it the minimum-area baseline that array and tree
multipliers unroll.

Bits per cycle is bought with multiple generation. One digit per step
is the n-cycle baseline; modified Booth recoding reads overlapping
three-bit windows into 0, +-X, or +-2X and halves the iteration
count with a two-place shift; three-bit groups need a stored 6X
multiple alongside 1X, 2X, 4X, and 8X; four bits per pass come from
adding two recoded multiples through a four-input two-output adder.
That last step is where the accumulator form changes: a carry-save
partial product in two registers removes the carry propagation from
the loop and needs one final assimilating addition, which is the
form that cascaded carry-save rows then unroll. String skipping
crosses runs of equal multiplier bits with a variable shift, about
three bit positions per addition with an unbounded shifter and 2.9
with a limit of six, and halves the average step count to about n/2,
at the price of a data-dependent cycle count and a shifter; uniform
grouping gives a predictable count and suits cascaded adders.
Signed-digit recoding of the multiplier, whether Booth's
adjacent-bit transitions or a minimal {-1, 0, 1} form, removes about
a third of the additions for long operands and handles every sign
combination; two's-complement operands can instead negate both
operands with a least-significant-digit-first complement and insert
the partial-product sign digit each step, and a signed-digit
accumulator makes each step one carry-free addition.

The family wins on area, and it loses on latency to every parallel
family because it spends N clocks on N partial products; the loop's
maximum rate usually exceeds the system clock, so minimum delay needs
a multiplied or self-generated clock, and in register-heavy
technologies the iteration registers themselves argue against it. The
operation-count argument assumes shift and complementation time are
negligible against an addition. Execution is fixed iteration (or
data-dependent with skipping) and exact.

The family's defining structure is sequential (one adder row reused over the cycles), so the library has no combinational module for it; a seed that declares it stays behavioral and the family is listed as an exception (`mul_ext.SEQUENTIAL_MUL`).

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
bewick1994 -> G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
goldschmidt_1964 -> Goldschmidt, "Applications of Division by Convergence", MS thesis, MIT, 1964
booth1951 -> A. D. Booth, "A Signed Binary Multiplication Technique", Quarterly Journal of Mechanics and Applied Mathematics, vol. 4, no. 2, pp. 236-240, 1951
robertson1955 -> J. E. Robertson, "Two's Complement Multiplication in Binary Parallel Digital Computers", IRE Transactions on Electronic Computers, 1955
tocher_1958 -> Tocher, "Techniques of Multiplication and Division for Automatic Binary Computers", Quarterly Journal of Mechanics and Applied Mathematics, 1958
macsorley1961 -> O. L. MacSorley, "High-Speed Arithmetic in Binary Computers", Proceedings of the IRE, vol. 49, no. 1, pp. 67-91, 1961
avizienis_1961 -> Avizienis, "Signed-Digit Number Representations for Fast Parallel Arithmetic", IRE Transactions on Electronic Computers, 1961
