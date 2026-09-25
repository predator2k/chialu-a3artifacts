---
family: approximate_compressor_tree
pin: {compressor: ansari_encoded}
---
# ansari_encoded

An approximate 4:2 compressor fed by encoded partial products:
symmetric products pp_ij and pp_ji become a propagate P = pp_ij +
pp_ji and a generate G = pp_ij * pp_ji, which makes several faulty
truth-table rows unreachable and cuts the faulty carry/sum cases from
5/7 to 2/4, while the cell itself omits Cout and replaces XOR-heavy
logic with AND/OR equations. M1 keeps the terminal carry c4 with an
exact full adder and M2 omits it to break the longest carry path.

The encoded cell is the pick when error probability must fall
without a wider exact region: M16-2 has the lowest PDP of the
compared unsigned 16-bit designs, and M16-5 has 44 percent smaller
PDP than the configurable-recovery multiplier at the same MRED and
59 percent smaller than the exact Wallace multiplier in ST 28 nm at
an MRED of 0.0013. The recursion decides the accuracy through which
subproducts stay exact, and omitting c4 buys latency for accuracy.
The propagate/generate-altered cells are the sibling when the OR
grouping of generate terms is preferred to compressing them.

## references

ansari2018 -> M. S. Ansari, H. Jiang, B. F. Cockburn, J. Han, "Low-Power Approximate Multipliers Using Encoded Partial Products and Approximate Compressors", IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 8, no. 3, pp. 404-416, 2018
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
