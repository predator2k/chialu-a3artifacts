---
family: sparse_prefix_hybrid
pin: {tree_topology: han_carlson}
---
# han_carlson

The carry network is a Han-Carlson prefix tree. The one block that
pins it, Oklobdzija's energy-delay comparison of high-performance VLSI
adders, classes Han-Carlson together with Intel's quaternary tree as a
sparse design and places both against Kogge-Stone (KS4-IBM) in the
energy-delay space at 32 b and 64 b, with the carry network realised
in static, domino or compound-domino CMOS.

Han-Carlson is the pick for the energy side of the curve: HC and the
quaternary tree consume less energy than KS4-IBM at lower-performance
targets, while Kogge-Stone holds the high-performance end. The 32-b
comparison reproduces the energy-delay trade-off observed in optimised
H-SPICE simulations, scaled from 130 nm to 100 nm with 50% energy and
30% delay scaling, and supports the quaternary tree as an
energy-reducing option without sacrificed performance; at 64 b the
quaternary tree carries one more stage than Kogge-Stone, which reduces
its benefit. In the ADIR grammar it is `family: sparse_prefix_hybrid`
with `pin: {tree_topology: han_carlson}`.

## references

oklobdzija2005 -> V. G. Oklobdzija, B. R. Zeydel, H. Q. Dao, S. Mathew, R. Krishnamurthy, "Comparison of High-Performance VLSI Adders in the Energy-Delay Space", IEEE Transactions on VLSI Systems, 2005.
