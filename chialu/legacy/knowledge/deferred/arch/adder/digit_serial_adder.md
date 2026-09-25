# digit_serial_adder

One k-bit carry-propagate adder reused over the word, least-significant
digit first: each cycle takes one radix-2^k digit from each operand,
adds it in the k-bit CPA of the digit_adder slot, and stores the carry
or borrow in a flip-flop, latch or unit delay so that it enters the
next digit's addition; an n-bit sum takes n/k + 1 cycles of
t_CPA(k) + t_FF. At k = 1 the structure is the simple series adder:
one full adder whose carry output returns to its carry input through a
unit delay, seven two-input gates and 4n gate delays. Subtraction
complements the y digit and presets the carry to 1, or re-transmits the
end-around carry in a second pass.

The digit width trades cycles against hardware. The cost is one k-bit
CPA, k XOR gates, one flip-flop and one k-bit output register, and the
total time is n/k + 1 cycles, so widening the digit removes cycles and
grows the digit adder toward a parallel CPA, while k = 1 keeps one
single-order unit in place of one device per order. The digit adder
slot admits the leaf chains and a prefix block, but the interdigit
transmission and storage timing fixes the throughput, so a faster carry
generator inside the digit does not speed the addition. The carry state
choice names that store: a clocked flip-flop or latch, or the unit
delay through which the series adder feeds its carry back.

The subtraction choice selects the complement policy. Two's-complement
subtraction complements the y digit at the k XOR gates and initializes
the carry flip-flop to 1 in the same pass; ones'-complement subtraction
costs a second pass through the adder to re-transmit the end-around
carry.

The execution style is fixed-iteration: n/k + 1 cycles per addition,
one carry computed at a time, which minimizes hardware and makes the
carry-to-carry delay the speed limit. The family is the area floor of
the adder axis and loses to every parallel family on latency; the 4n
gate delays of the bit-serial adder compare with an average of 4 + n to
4 + n + 2 log2 n gate delays for the carry-completion adder of the same
evaluation. A slot admits the family only where its initiation-interval
contract accepts an iterative adder. Unrolling the digit loop yields a
parallel ripple chain of the same cells.

The family's defining structure is sequential (one digit adder reused over the cycles), so the library has no combinational module for it; a seed that declares it stays behavioral and the family is listed as an exception (`adder_ext.SEQUENTIAL_ADD`).

## references

ercegovac_2004 -> M. D. Ercegovac and T. Lang, "Digital Arithmetic", Morgan Kaufmann, 2004
sklansky1960b -> J. Sklansky, "An Evaluation of Several Two-Summand Binary Adders", IRE Transactions on Electronic Computers, vol. EC-9, no. 2, pp. 213-226, 1960.
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
