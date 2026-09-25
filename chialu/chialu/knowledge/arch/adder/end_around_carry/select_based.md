---
family: end_around_carry
pin: {recirculation: select_based}
---
# select_based

Two tentative results are formed and the end-around carry chooses
between them instead of re-entering a carry chain: one path computes
the plain sum and the other the sum plus the wrapped increment, and a
carry-out derived from the low-order bits selects the high-order bits
of one candidate. The carry that decides the selection can come from
a short m-bit addition of the overflow bits, so no full-length
end-around addition is performed.

The form wins where the wrapped addition would otherwise sit on a
byte-organized or pipelined critical path: in low-cost residue
checking an m-bit addition replaces the full-length modulo 2^(k+1)-1
pass, and in the POWER6 128-bit floating-point adder four 32-bit
groups with wrapped group-carry equations compute conditional sums in
one cycle and a transmission-gate multiplexer stage selects them at
the start of the next, with the carry blocks placed so wire delays
stay balanced. It pays for that with duplicated sum logic and a wide
select fanout, which is where cyclic_prefix_level, with one prefix
core and no candidates, is the cheaper pick.

## references

avizienis_1985 -> A. Avizienis, "Arithmetic Algorithms for Operands Encoded in Two-Dimensional Low-Cost Arithmetic Error Codes", Proc. ARITH-7, pp. 285-292, 1985
yu_2006 -> X. Y. Yu, Y.-H. Chan, M. Kelly, E. Schwarz, B. Curran, B. Fleischer, "A 5GHz+ 128-bit Binary Floating-Point Adder for the POWER6 Processor", 32nd European Solid-State Circuits Conference (ESSCIRC), 2006
