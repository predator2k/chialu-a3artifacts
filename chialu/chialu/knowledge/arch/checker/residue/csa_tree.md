---
family: residue
pin: {generator_style: csa_tree}
---
# csa_tree

A residue generator as a carry-save tree with end-around carry: the
input bits are partitioned into sets of equal weight modulo the
modulus, a carry-save network reduces the sets while every carry
leaving the highest position returns to weight 1, a short cyclic
adder leaves a few bits, and a converter produces the residue.
For a modulus 2^a - 1 the tree uses n - a full adders, the same count
as a conventional tree, at lower delay, and 4:2 compressors sum
hexadecimal digits for modulo 15.

The CSA tree is the generator for wide parallel operands, where it
beats the conventional tree of modular adders on delay at the same
full-adder count, and it serves both residue prediction for addition
and the modular partial-product tree of a multiply-add predictor; the
textbook form is the same tree of modulo-(2^b - 1) adders over b-bit
groups. Its efficiency grows with the ratio of word length to the
period of powers of two modulo the modulus and drops when that ratio
is below about 3, so it fits 2^a - 1 moduli best. Among the modulus-3
circuits measured in 45 nm, a serial loop is smallest but slowest and
a one-hot pass-gate multiplexor tree is the compact fast form; the
compressor tree is the standard for modulus 15 and for the
mixed-width predictors of a GPU pipeline.

The generated checker's residue generator folds the k-bit chunks of the word and subtracts M once (`residue.py`), a tree of folds; generator_style is not a pin it reads.

## references

lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
lipetz_schwarz_2011 -> D. Lipetz, E. Schwarz, "Self Checking in Current Floating-Point Units", Proc. 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 73-76, 2011
sullivan_2018 -> M. B. Sullivan, S. K. S. Hari, B. Zimmer, T. Tsai, S. W. Keckler, "SwapCodes: Error Codes for Hardware-Software Cooperative GPU Pipeline Error Detection", Proc. MICRO-51, pp. 762-774, 2018
