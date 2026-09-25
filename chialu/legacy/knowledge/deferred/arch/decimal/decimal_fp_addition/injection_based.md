---
family: decimal_fp_addition
pin: {rounding: injection_based}
---
# injection_based

Injection-based rounding: a value that depends on the rounding mode
and the sign is injected into the round and sticky digit positions
before the significand addition, so most rounding becomes truncation
of the sum. When the corrected result has a nonzero most-significant
digit, a second injection-correction value is applied through flag
vectors derived from the prefix network rather than through another
carry-propagate addition, and the same flags support overflow
detection.

Wang's decimal64 adder with injection rounding runs 21 percent faster
and 1.6 percent smaller than the Thompson adder that corrects and
rounds after addition, and the trailing-nine flags cost 13.7 percent
more Kogge-Stone network area. z196 injects into the guard/sticky
locations of a pipelined end-around-carry AREN and selects the
injection at digit p or p+1 once the most-significant result digit
resolves carry-out or cancellation, delivering the rounded output in a
third AREN cycle. Injection is cleared for effective subtraction when
RSA is zero, and no underflow logic is needed because addition and
subtraction cannot produce a result that is both subnormal and
inexact. z10 instead adds 1 at the least-significant digit after the
sum, which can extend execution. Injection is the pick when one adder
pass with fixed latency is wanted and the carry network can carry the
flags; the lsd_increment_table sibling is pinned by no block.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

wang_2009 -> Wang, Schulte, Thompson, Jairam, "Hardware Designs for Decimal Floating-Point Addition and Related Operations", IEEE Transactions on Computers, 2009
carlough_2011 -> Carlough, Collura, Mueller, Kroener, "The IBM zEnterprise-196 Decimal Floating-Point Accelerator", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), 2011
schwarz_2009 -> Schwarz, Kapernick, Cowlishaw, "Decimal Floating-Point Support on the IBM System z10 Processor", IBM Journal of Research and Development, 2009
