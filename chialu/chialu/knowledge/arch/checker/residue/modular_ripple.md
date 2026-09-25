---
family: residue
pin: {generator_style: modular_ripple}
---
# modular_ripple

A residue generator as a chain of modular end-around-carry additions:
the information word is partitioned into r-bit groups and the groups
are added modulo 2^r - 1 with end-around-carry adders, so the check
bits are the digit sum with carries returned to the low end. The
decimal ancestor is casting out 9's, whose digit sum yields the
remainder modulo 9; binary data grouped into 3-bit digits gives the
modulo-7 check, and 4-bit bytes give the STAR computer's byte-serial
modulo-15 bus checker.

The ripple generator is the low-cost residue code in its simplest
hardware, one r-bit end-around-carry adder that consumes the word
group by group, so it suits byte-serial transmission and a checker
shared by a bus; the STAR machine checked every 28-bit operand and
address with a 4-bit check byte this way, concurrently with word
transmission. Its cost is latency proportional to the number of
groups, which the carry-save tree removes for wide parallel operands,
and a zero residue needs an explicit all-ones representation. It is
the pick when the datapath is narrow or serial, when the modulus is
2^r - 1 with r matching the byte width, or when the generator must
sit on a bus rather than beside a wide adder.

The generated checker's residue generator folds the k-bit chunks of the word and subtracts M once (`residue.py`); generator_style is not a pin it reads.

## references

lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
avizienis_gilley_1971 -> A. Avizienis, G. C. Gilley, F. P. Mathur, D. A. Rennels, J. A. Rohr, D. K. Rubin, "The STAR (Self-Testing And Repairing) Computer: An Investigation of the Theory and Practice of Fault-Tolerant Computer Design", IEEE Transactions on Computers, vol. C-20, no. 11, 1971
