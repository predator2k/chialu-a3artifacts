---
family: rns_montgomery_crypto
pin: {base_extension: mixed_radix}
---
# mixed_radix

Base extension through mixed-radix digits: B, N and R sit in a
primary and an auxiliary RNS base while A supplies mixed-radix
digits, each digit determines q_i so the intermediate value divides
exactly by m_i, the division removes one primary-base residue while
the auxiliary residues preserve the result, and a second application
with the bases permuted recovers AB mod N. The RNS-to-MRS conversion
overlaps with the modular operations on a nearest-neighbour ring of
processors.

The mixed-radix extension is the pick for a systolic ring: n
processors give O(n) time with a latency of 4n-1 cycles and an
initiation interval of 3n, p processors with p dividing n keep
utilization between 62.5 and 100 percent, and the survey names it as
the extension behind RNS Montgomery multipliers for RSA and
elliptic-curve point multiplication, which reach less than half the
area of earlier designs. Its costs are the triangular conversion
task when A arrives in RNS, the second pass with permuted bases, and
moduli of 9 to 10 bits in the order of 80 channels; the Cox-Rower
approximate extension is the sibling for wide channels with one
Rower each.

The kernel is not an ALU op; the family is an exception (`redundant.EXCEPTIONS`).

## references

bajard_1998 -> Bajard, Didier, Kornerup, "An RNS Montgomery Modular Multiplication Algorithm", IEEE Transactions on Computers, 1998
chang_2015 -> Chang, Molahosseini, Zarandi, Tay, "Residue Number Systems: A New Paradigm to Datapath Optimization for Low-Power and High-Performance Digital Signal Processing Applications", IEEE Circuits and Systems Magazine, 2015
