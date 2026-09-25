---
family: parallel_prefix
pin: {topology: han_carlson}
---
# han_carlson

The hybrid prefix tree: a Kogge-Stone graph is embedded between
Brent-Kung graphs, so the tree merges carries only on the even bit
positions, transmits the odd-bit generate/propagate pairs through the
levels with alternate-bit interstage wiring, and forms the missing odd
carries in one extra level that folds into the sum XORs. Fanout stays at
two, the extra depth k sets how much of the graph is Kogge-Stone, and
the layout area is O(n log n) against O(n^2) for a full Kogge-Stone.

Han-Carlson is the pick when Kogge-Stone wiring is the constraint but
Brent-Kung is too slow: at 16 bits with k = 1 it has 5 prefix levels
against 7 for Brent-Kung, the layout folds to half its area for n <= 64,
and its alternating positive/negative cells need no inverter stages. In
a 130 nm dual-VT ALU the single-ended Han-Carlson tree uses 50% fewer
carry-merge gates, 50% less interstage routing and 40% less active
leakage energy than a differential domino Kogge-Stone, at 5 GHz. In
energy-delay comparisons the extra stage saves energy once the delay
target is relaxed, while minimum-depth Kogge-Stone wins at the highest
performance. Under frequency over-scaling the odd bits fail together and
produce clustered high-magnitude errors, which is a caveat for
speculative timing.

## references

han_carlson1987 -> T. Han, D. A. Carlson, "Fast Area-Efficient VLSI Adders", 8th IEEE Symposium on Computer Arithmetic (ARITH-8), pp. 49-56, 1987.
vangal_2002 -> S. Vangal, et al., "5-GHz 32-bit Integer Execution Core in 130-nm Dual-VT CMOS", IEEE Journal of Solid-State Circuits, vol. 37, no. 11, pp. 1421-1432, 2002.
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
zeydel2010 -> B. R. Zeydel, D. Baran, V. G. Oklobdzija, "Energy-Efficient Design Methodologies: High-Performance VLSI Adders", IEEE Journal of Solid-State Circuits, vol. 45, no. 6, pp. 1220-1233, 2010.
venkatesan2011 -> R. Venkatesan, A. Agarwal, K. Roy, A. Raghunathan, "MACACO: Modeling and Analysis of Circuits for Approximate Computing", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 667-673, 2011
