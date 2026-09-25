---
family: iterative_decimal_multiplication
pin: {multiple_set: easy_2x_4x_5x}
---
# easy_2x_4x_5x

The Erle-Schulte reduced multiple set: dedicated logic generates 2A,
4A and 5A from the multiplicand, 2A in 3 gate delays and all three
ready in 6, and each BCD multiplier digit selects two of {A, 2A, 4A,
5A} whose sum is the digit times the multiplicand. A decimal 3:2
counter merges the two selected multiples into a redundant partial
product, and a decimal 4:2 compressor accumulates it with the
carry-save intermediate product, retiring one product digit per
iteration, LSD first.

The set is the pick for a high-frequency iterative multiplier: no
multiples are stored, and removing the first 3:2 counter from the
feedback path lets the two carry-save stages pipeline without doubling
the iteration count, which gives n+4 latency and an n+1 initiation
interval for n digits. The
decimal64 unit of Erle, Hickmann and Schulte reaches 25 cycles normal
latency in 0.11 um; Kenney's overloaded-decimal accumulator keeps the
same multiple selection but admits intermediate digits 0 through 15,
buying 14% clock frequency for 77% more area from the clean-up blocks
at 34 digits. The POWER6 DFU uses the same easy multiples serially,
19+N cycles for decimal64. Against full_1x_to_9x
it trades stored odd multiples for a second selected term per digit;
against double_quintuple_only it adds 4x so every digit needs two
terms rather than an add or subtract sequence. In the ADIR grammar it
is `family: iterative_decimal_multiplication` with
`pin: {multiple_set: easy_2x_4x_5x}`.

## references

erle_2003 -> Erle, Schulte, "Decimal Multiplication Via Carry-Save Addition", IEEE ASAP, 2003
erle_2009 -> Erle, Hickmann, Schulte, "Decimal Floating-Point Multiplication", IEEE Transactions on Computers, 2009
kenney_2004 -> Kenney, Schulte, Erle, "A High-Frequency Decimal Multiplier", IEEE International Conference on Computer Design (ICCD), 2004
