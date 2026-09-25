---
family: barrel_mux_tree
pin: {stage_order: small_shift_first}
---
# small_shift_first

The mux stages are ordered by increasing displacement: the first stage
shifts by 1, then 2, 4, 8 and so on to the largest power of two, each
stage controlled by the shift-amount bit of that weight. The CDC 6600
network, the TSPC pipelined shifter with its 0/1, 0/2, 0/4 and 0/8
stages and the parameterized posit shifters take this order, and a
full-function rotator folds its one-bit preshift into the first
rotation stage.

Placing the short displacements first lets a full-function rotator
absorb its one-bit preshift into the first stage and complement the
amount for left shifts without an adder (huntzicker_2008), and it lets
the six-cycle TSPC pipeline put one stage on each of the 1, 2, 4 and 8
steps with a new instruction every clock (pereira_1995). The CDC 6600
executes every shift in one minor cycle in this order (thornton_1970),
and the posit generators keep it so that S = log2(N) stages follow
directly from the word width (jaiswal_2018). Two fused multiply-add
aligners keep the order with radix-4 partial-decode stages, 0/1/2/3,
then 0/4/8/12, then the coarse multiples of 16, and collect the sticky
bits at the end (jessani_1996, mueller_2005). The order is the pick
when the first stage must carry a preshift or the design is generated
from a parameter; large_shift_first is the sibling where the coarse
displacement is resolved by a wide first-stage multiplexor while
sticky bits are collected at the end.

## references

huntzicker_2008 -> S. Huntzicker, M. Dayringer, J. Soprano, A. Weerasinghe, D. M. Harris, D. Patil, "Energy-Delay Tradeoffs in 32-bit Static Shifter Designs", Proc. IEEE ICCD, 2008
pereira_1995 -> R. Pereira, J. A. Michell, J. M. Solana, "Fully Pipelined TSPC Barrel Shifter for High-Speed Applications", IEEE Journal of Solid-State Circuits, vol. 30, no. 6, pp. 686-690, 1995
thornton_1970 -> J. E. Thornton, "Design of a Computer: The Control Data 6600", Scott, Foresman and Co., 1970
jaiswal_2018 -> M. K. Jaiswal, H. K.-H. So, "Universal Number Posit Arithmetic Generator on FPGA", Design, Automation and Test in Europe (DATE), 2018
jessani_1996 -> R. M. Jessani, C. H. Olson, "The Floating-Point Unit of the PowerPC 603e Microprocessor", IBM Journal of Research and Development, vol. 40, no. 5, 1996
mueller_2005 -> S. M. Mueller et al., "The Vector Floating-Point Unit in a Synergistic Processor Element of a CELL Processor", ARITH-17, pp. 59-67, 2005
