---
family: classic_fma
pin: {negation_handling: end_around_carry}
---
# end_around_carry

Effective subtraction runs in one's complement: the aligned addend is
inverted where the signs differ, merged with the carry-save product
in the last 3:2 row, and the 161-bit sum is resolved by one adder
whose carry-out wraps around as an end-around carry to correct the
one's-complement result, while the LZA reads the same adder operands
to predict the normalization shift. Implementations split the carry
chain into a 106-bit adder and a 53-bit incrementer selected by the
lower carry.

This is the RS/6000 lineage's choice and the default of the POWER
units, since one adder serves both signs and the wrap-around costs a
carry recirculation rather than a second datapath: the POWER6 unit
resolves a 120-bit end-around-carry adder across cycles 3 to 5 of its
seven-cycle pipeline, selecting 32-bit conditional sums by the
recirculated carry, and Lang and Bruguera estimate the 106-bit prefix
adder with end-around-carry logic at 46 of the 175 tinv4 critical
path. The carry path is the timing-critical wire, so it loses to
dual_adder where a second wide adder is affordable, which is how the
z990 dataflow removes the recirculation, and to complement_recode
where a single-path two's-complement formulation is preferred over
sign-magnitude handling. In the ADIR grammar it is
`family: classic_fma` with `pin: {negation_handling: end_around_carry}`.

The wrap-around survives being split across passes and across
precisions. The dual-pass PowerPC 603e latches the low 26 bits of the
161-bit sum in its first add cycle and increments them in the second,
which is where the end-around carry is applied and where the
sign-magnitude result is produced. The CELL SPE units form the sum or
the absolute difference by the same concept at 11 FO4 per stage, the
single-precision one splitting its 73-bit adder into a 25-bit
incrementer, a main adder generating S and S + 1, and sticky logic.

The library realizes this choice as a pin of the generated classic_fma module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

montoye_1990 -> R. K. Montoye, E. Hokenek, S. L. Runyon, "Design of the IBM RISC System/6000 Floating-Point Execution Unit", IBM Journal of Research and Development, 1990
lang_2004 -> T. Lang, J. D. Bruguera, "Floating-Point Multiply-Add-Fused with Reduced Latency", IEEE Transactions on Computers, vol. 53, pp. 988-1003, 2004
trong_2007 -> S. D. Trong, M. Schmookler, E. M. Schwarz, M. Kroener, "P6 Binary Floating-Point Unit", 18th IEEE Symposium on Computer Arithmetic, 2007
yu_2006 -> X. Y. Yu, Y.-H. Chan, M. Kelly, E. Schwarz, B. Curran, B. Fleischer, "A 5GHz+ 128-bit Binary Floating-Point Adder for the POWER6 Processor", 32nd European Solid-State Circuits Conference (ESSCIRC), 2006
jessani_1998 -> R. M. Jessani, M. Putrino, "Comparison of Single- and Dual-Pass Multiply-Add Fused Floating-Point Units", IEEE Transactions on Computers, vol. 47, no. 9, 1998
mueller_2005 -> S. M. Mueller et al., "The Vector Floating-Point Unit in a Synergistic Processor Element of a CELL Processor", ARITH-17, pp. 59-67, 2005
oh_2006 -> H.-J. Oh et al., "A Fully Pipelined Single-Precision Floating-Point Unit in the Synergistic Processor Element of a CELL Processor", IEEE Journal of Solid-State Circuits, vol. 41, no. 4, 2006
