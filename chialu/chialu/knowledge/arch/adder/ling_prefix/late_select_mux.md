---
family: ling_prefix
pin: {sum_recovery: late_select_mux}
---
# late_select_mux

Sum recovery by selection: conditional sums are precomputed for both
values of the incoming pseudo-carry, and when H arrives a multiplexer
picks the right one, so the AND of H with the propagate that turns
the pseudo-carry into a true carry never sits on the critical path.
In the two-bit form the sum cell uses H_{i-1} to choose between d_i
and d_i XOR p_{i-1}; the original adder expresses the same selection
with the Sklansky conditional-sum method.

This is the recovery every reported high-speed Ling adder uses, from
the 1981 three-level 32-bit design through the HP 64-bit dynamic
adder to the 90-nm and 65-nm energy-delay studies, because the
carry-tree gain is only kept if the recovery is hidden. Its cost is
the sum-precompute logic, whose complexity grows faster than the
carry tree's as sparseness increases, so at long delay and minimum
size the conventional equations use less energy; an XOR correction
of a preliminary sum is the lighter alternative when the sum stage is
not critical.

## references

ling1981 -> H. Ling, "High-Speed Binary Adder", IBM Journal of Research and Development, vol. 25, no. 2-3, pp. 156-166, 1981.
jackson_talwar2004 -> R. Jackson, S. Talwar, "High Speed Binary Addition", 38th Asilomar Conference on Signals, Systems and Computers, 2004.
dimitrakopoulos2005 -> G. Dimitrakopoulos, D. Nikolos, "High-Speed Parallel-Prefix VLSI Ling Adders", IEEE Transactions on Computers, 2005.
zlatanovici2009 -> R. Zlatanovici, S. Kao, B. Nikolic, "Energy-Delay Optimization of 64-Bit Carry-Lookahead Adders With a 240 ps 90 nm CMOS Design Example", IEEE Journal of Solid-State Circuits, 2009.
zeydel2010 -> B. R. Zeydel, D. Baran, V. G. Oklobdzija, "Energy-Efficient Design Methodologies: High-Performance VLSI Adders", IEEE Journal of Solid-State Circuits, vol. 45, no. 6, pp. 1220-1233, 2010.
