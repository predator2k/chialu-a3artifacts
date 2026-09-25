# uniform

One adder family across the full width of the final carry-propagate addition: the two rows leaving the reduction tree enter a single adder chosen from the adder slot (ripple, lookahead, conditional-sum, prefix, ...) with no regard to when each column's bits arrive. It is the simplest cpa and the one a shared or synthesized datapath usually gets.

The cost is arrival skew: the tree delivers low-order bits early and high-order bits late, so a uniformly fast adder wastes its speed on the early region and a uniformly slow one adds delay where it can least afford it, and joint tree/adder optimization showed that hybrid segmentation beats any uniform adder on a tree profile. uniform still wins in three settings: when the adder is shared with another unit (the S/390 G5 combined its Booth tree's two 120-bit rows in the carry-propagate adder used by floating-point addition), when the profile is flat because the tree is pipelined or is a regular carry-save array with a final row adder, and when a single conditional-sum or prefix adder from the library keeps synthesis and verification simple. A 54x54 design that combined the two 108-bit rows in one conditional carry-selection adder is the uniform end of the same production line.

Where the adder sits on the critical path of a custom tree, hybrid_arrival_driven is the pick.

## references

noll_1991 -> Noll, "Carry-Save Architectures for High-Speed Digital Signal Processing", Journal of VLSI Signal Processing, 1991
oklobdzija1995 -> V. G. Oklobdzija, D. Villeger, "Improving Multiplier Design by Using Improved Column Compression Tree and Optimized Final Adder in CMOS Technology", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 3, 1995
ohkubo1995 -> N. Ohkubo, M. Suzuki, T. Shinbo, T. Yamanaka, A. Shimizu, K. Sasaki, Y. Nakagome, "A 4.4-ns CMOS 54x54-b Multiplier Using Pass-Transistor Multiplexer", IEEE Journal of Solid-State Circuits, vol. 30, 1995
schwarz_1999 -> E. M. Schwarz and C. A. Krygowski, "The S/390 G5 Floating-Point Unit", IBM Journal of Research and Development, 1999
yehjen2000 -> W.-C. Yeh, C.-W. Jen, "High-Speed Booth Encoded Parallel Multiplier Design", IEEE Transactions on Computers, vol. 49, no. 7, pp. 692-701, 2000
