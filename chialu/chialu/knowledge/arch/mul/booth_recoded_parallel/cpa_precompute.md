---
family: booth_recoded_parallel
pin: {hard_multiple_gen: cpa_precompute}
---
# cpa_precompute

The hard multiples that radix-8 and radix-16 recoding need are formed
once by a full-width carry-propagate addition before partial-product
generation, and the Booth multiplexers select among wired shifts of M
and the precomputed multiples. Conventional Booth 3 uses one such
adder for 3M; Booth 4 needs 3M, 5M and 7M, with 6M a shifted 3M; a
pipelined array places the 3x generation in its own stage ahead of the
array, and a radix-16 design precomputes 3Y, 5Y and 7Y in three carry-
select adders.

The precompute puts a full-width carry-propagate addition and long
carry wires before partial-product generation, although it can
sometimes overlap multiply setup, and Booth 4 is not competitive
through 64 bits because the hard-multiple adders and larger
multiplexers offset the reduced row count; in a 0.6 um BiCMOS ECL
comparison the fastest Booth 3 ran at 3.0 ns and 11.0 mm2 against 2.6
ns and 15.4 mm2 for Booth 2 (bewick1994). Shipping designs take the
scheme when a pipeline stage is free for it: a 0.75 um FPU generates
3x in cycle 4 ahead of a two-cycle radix-8 array (dobberpuhl_1992),
and the S/390 G5 forms 3X in its first stage before a 19-to-2 counter
tree (schwarz_1999). Radix-16 with precomputed odd multiples halves
the CSA rows and beats 3-bit recoding from 16x16 to 64x64 in 0.9 um
CMOS (samgupta1990). partially_redundant is the pick
when the setup adder must leave the critical path.

## references

bewick1994 -> G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
dobberpuhl_1992 -> D. W. Dobberpuhl, et al., "A 200-MHz 64-b Dual-Issue CMOS Microprocessor", IEEE Journal of Solid-State Circuits, vol. 27, no. 11, pp. 1555-1567, 1992.
schwarz_1999 -> E. M. Schwarz and C. A. Krygowski, "The S/390 G5 Floating-Point Unit", IBM Journal of Research and Development, 1999
samgupta1990 -> H. Sam, A. Gupta, "A Generalized Multibit Recoding of Two's Complement Binary Numbers and Its Proof with Application in Multiplier Implementations", IEEE Transactions on Computers, vol. 39, no. 8, pp. 1006-1015, 1990
