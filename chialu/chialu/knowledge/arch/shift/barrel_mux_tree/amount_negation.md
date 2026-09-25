---
family: barrel_mux_tree
pin: {direction_handling: amount_negation}
---
# amount_negation

One rotator serves both directions: a left shift by N becomes a right
rotation by W-N, the amount being the radix complement of the count or
its one's complement followed by a one-position preshift folded into
the first stage, and masking turns the rotation into a logical or
arithmetic shift by inserting zeros or the sign. The datapath is a
single staged mux array; only the amount logic and the mask generator
know the direction.

The one's-complement form with a one-bit preshift in the first
rotation stage avoids an adder in the amount logic (huntzicker_2008),
and a six-stage TSPC pipeline realizes a right rotation as a
one-position left rotation followed by a left rotation selected by the
complement of the length (pereira_1995). The ILLIAC IV barrel switch
takes the radix complement of the count for left shifts and gates
zeros for end-off shifts (davis_1969), and the RS/6000 32-bit rotator
is bidirectional the same way (montoye_1990). Against data_reversal
the amount transform costs area and delay: at 32 bits in a 0.11 um
library the mask-based two's-complement design synthesizes to 8827
gates and 1.19 ns against 6141 gates and 0.94 ns for mask-based data
reversal (pillmeier_2002). It is the pick when the rotator already
exists and only one mux array may be spent.

## references

huntzicker_2008 -> S. Huntzicker, M. Dayringer, J. Soprano, A. Weerasinghe, D. M. Harris, D. Patil, "Energy-Delay Tradeoffs in 32-bit Static Shifter Designs", Proc. IEEE ICCD, 2008
pereira_1995 -> R. Pereira, J. A. Michell, J. M. Solana, "Fully Pipelined TSPC Barrel Shifter for High-Speed Applications", IEEE Journal of Solid-State Circuits, vol. 30, no. 6, pp. 686-690, 1995
davis_1969 -> R. L. Davis, "The ILLIAC IV Processing Element", IEEE Transactions on Computers, vol. C-18, no. 9, pp. 800-816, 1969
montoye_1990 -> R. K. Montoye, E. Hokenek, S. L. Runyon, "Design of the IBM RISC System/6000 Floating-Point Execution Unit", IBM Journal of Research and Development, 1990
pillmeier_2002 -> M. R. Pillmeier, M. J. Schulte, E. G. Walters III, "Design Alternatives for Barrel Shifters", Proc. SPIE 4791, Advanced Signal Processing Algorithms, Architectures, and Implementations XII, 2002
