---
family: rns_reverse_converter
pin: {algorithm: mixed_radix}
---
# mixed_radix

The residues are first converted to mixed-radix digits and each
digit's weighted binary contribution, read from a ROM, is summed. The
classical digit chain is strictly sequential; the fully parallel form
lets each residue address tables that yield the nonzero mixed-radix
digits of its orthogonal projection, and the triangular digit array is
summed by column modulo p_k in balanced adder trees, so lookup and
column summation form two pipelined stages.

It is the pick when the digits are useful in themselves, for sign
detection, magnitude comparison, overflow detection and scaling, and
when the parallel two-stage form fits: for up to 15 moduli it converts
in two clock cycles instead of n-1, 50 ns against 350 ns with ECL
adders and RAM, at n(n+1)/2 tables of half the classical size plus n
comparator/subtractors. At limited width the whole conversion collapses
into one table, as for 8-bit conversion over moduli 15 and 17 in a 4K
ROM. The CRT is the sibling when a direct modulo-M sum is cheaper than
the digit chain.

The library realizes this algorithm as the chain of modular subtract-and-multiply steps that yields the mixed-radix digits, then their weighted sum (`chialu/targets/rtl/families/redundant.py`).

## references

huang_1983 -> Huang, "A Fully Parallel Mixed-Radix Conversion Algorithm for Residue Number Applications", IEEE Transactions on Computers, 1983
jullien_1978 -> Jullien, "Residue Number Scaling and Other Operations Using ROM Arrays", IEEE Transactions on Computers, 1978
chang_2015 -> Chang, Molahosseini, Zarandi, Tay, "Residue Number Systems: A New Paradigm to Datapath Optimization for Low-Power and High-Performance Digital Signal Processing Applications", IEEE Circuits and Systems Magazine, 2015
