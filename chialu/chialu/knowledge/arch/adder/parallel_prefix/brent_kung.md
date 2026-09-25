---
family: parallel_prefix
pin: {topology: brent_kung}
---
# brent_kung

The regular-layout prefix tree: a binary reduction tree combines (g,p)
pairs pairwise up to the group term for the whole word, and an inverted
tree fans the group terms back down so every carry is formed, with each
operator output driving at most two successors. Depth is 2 log2(n) - 2
operator levels and size is 2n - log2(n) - 2 operators, O(n) area at
bounded fanout, which is the linear-area, logarithmic-delay point of the
family.

Brent-Kung is the pick when area, wire regularity or bounded fanout
outweigh the extra levels: at 32 bits it has depth 8 and 57 black nodes
where Sklansky has depth 5 and 80, and in a 0.6 um standard-cell
comparison it is the smallest of the three fixed trees while Kogge-Stone
is about twice its area. Its size sits on the depth-size frontier, since
a prefix graph must satisfy depth plus size >= 2n - 2 and the compressed
unrolled Brent-Kung construction reaches 2n - 2 - log2(n) nodes. The
regular structure supports medium-grained pipelining and a width-w
segment-pipelined form, and it serves as the final adder of fixed-width
multipliers and as the base of a speculative-completion asynchronous
adder. Han-Carlson trades some of its area back for fewer levels by
embedding a Kogge-Stone graph between Brent-Kung graphs.

## references

brent_kung1982 -> R. P. Brent, H. T. Kung, "A Regular Layout for Parallel Adders", IEEE Transactions on Computers, vol. C-31, no. 3, pp. 260-264, 1982.
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
snir1986 -> M. Snir, "Depth-Size Trade-Offs for Parallel Prefix Computation", Journal of Algorithms, vol. 7, no. 2, pp. 185-201, 1986.
han_carlson1987 -> T. Han, D. A. Carlson, "Fast Area-Efficient VLSI Adders", 8th IEEE Symposium on Computer Arithmetic (ARITH-8), pp. 49-56, 1987.
nowick1996 -> S. M. Nowick, "Design of a Low-Latency Asynchronous Adder Using Speculative Completion", IEE Proceedings - Computers and Digital Techniques, vol. 143, no. 5, pp. 301-307, 1996.
