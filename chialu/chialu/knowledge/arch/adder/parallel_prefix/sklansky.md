---
family: parallel_prefix
pin: {topology: sklansky}
---
# sklansky

The minimum-depth divide-and-conquer prefix tree: log2(n) levels, each
of which combines a group generate/propagate with the carry of the
adjacent lower half-word, so one node per level drives up to n/2
successors while the interconnect stays within log2(n) wire tracks.
Depth is minimal and the size is O(n log n) gates, but the fanout of the
highest-distribution nodes is unbounded and grows with the word length.

Sklansky is the fastest cell-based starting architecture and the largest
of the fixed prefix graphs: at 32 bits it has depth 5 and 80 black nodes
against 8 and 57 for Brent-Kung, and in a 0.6 um standard-cell library
it is the fastest topology at large widths while Kogge-Stone pays
large-area routing delay for its bounded fanout. The high-fanout nodes
are taken off the critical path by one buffer level, and the
antisymmetric halves of the graph fold onto each other to fill the node
locations that the unfolded layout leaves empty, which suits macro-cells
better than bus-oriented datapaths. Sklansky also supports fine-grained
pipelining and partitioning for dual-size adders. It loses to Brent-Kung
when area or a regular constant-track layout matters more than the extra
levels, and to Kogge-Stone when the fanout cannot be buffered cheaply.

## references

zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
zimmermann1999 -> R. Zimmermann, "Efficient VLSI Implementation of Modulo (2^n +/- 1) Addition and Multiplication", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999
harris2003 -> D. Harris, "A Taxonomy of Parallel Prefix Networks", 37th Asilomar Conference on Signals, Systems and Computers, 2003.
