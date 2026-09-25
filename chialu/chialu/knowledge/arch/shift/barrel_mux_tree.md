# barrel_mux_tree

A variable shifter as a cascade of multiplexer stages, one per shift-amount digit: at radix 2, stage i either passes its input or displaces it by 2^i, so an n-bit shift takes ceil(log2 n) stages of n-bit 2:1 muxes, O(n log n) area and O(log n) delay, independent of the shift distance. Rotation is the primitive: a shift is a rotation followed by a mask that inserts zeros or the sign, and both directions come from one rotator by mirroring the datapath, by reversing the data at input and output, or by negating the amount, where a left shift by k is a right rotate by n - k, with a one-bit preshift under one's complement. Sticky bits are the OR of the shifted-out bits. Feed-forward.

stage_radix trades stage count against mux width and wiring. The ILLIAC IV switch covers 64 bits in three radix-4 levels, and a radix-16 network was estimated at more than 30% less hardware and 1.3x less delay than radix 2; in 90-nm static CMOS a mixed 5-8 barrel reaches the minimum delay of 340 ps (12.6 FO4) for all shift types, fanout splitting helps only the valency-2 form, and above a 360-ps target a folded funnel of valency 4-8 has the lower energy, which is what convert_barrel_to_funnel is for. select_encoding sets where the decode lives: binary keeps the control narrow, one-hot or partial decode moves it off the datapath, cuts control and data wiring against the fully encoded and fully decoded extremes, and lets the rotator reuse the merge cells and wires of a parallel-prefix adder so the result mux disappears. A sum-addressed decode takes the shift-amount adder off the path entirely: a 4:2 compressor leaves the exponent difference in carry-save form, each 2-bit segment is unary-decoded as if its carry-in were zero, and the segment's group carry rotates that decode left by one position, which brought an alignment shifter to 21 FO4 in IBM 90nm SOI-low-k, 10 FO4 below a conventional aligner. direction_handling is where area goes: either data-reversal design has the lowest area, and the mask-based one has the lowest delay at every width because zero and overflow flags are computed from the masks in parallel with the rotation, 6,141 gates and 0.94 ns at 32 bits in 0.11-µm cells against 8,827 gates and 1.19 ns with a two's-complement amount; a mirrored datapath doubles the muxes but needs no amount logic.

stage_order and the wires decide the cycle. Coarse-first ordering with the fine stage last is the alignment-shifter norm, with binary preshift, 16-position, and 4-position stages and sticky collection at the end; a first stage restricted to rotation within a byte and corrected by the next stage's select cuts the longest-line fanout from 38 loads to 4 at 30% more area, and a final stage can double as the ALU output mux. A three-level alignment shifter whose levels select 0 to 3, multiples of 4 and nine multiples of 16 up to 128 maps a 53-bit input onto a 136-bit output, and a bypass port in the last level keeps a negative shift count from shifting and lets the first two levels resolve their amounts earlier. An incomplete normalization shifter pays in passes rather than in area: a three-level left shifter of maximum count 63 normalizes an ordinary sum in one pass and a mass-cancellation result in two or three. Aligner and normalizer can share 4:1 transmission-gate mux stages, whose output inverters drive the long horizontal wires better than an AOI mux does. sticky_collect costs under 1% of an embedded FPGA shifter. On FPGAs the mux tree is expensive enough that a dedicated shifter block or the embedded multipliers replace it. The shifter is often the largest delay and area item of the datapath it serves, which is why the family is worth tuning per instance.

## design choices

### select_encoding

| member | what it selects |
| --- | --- |
| `binary` | each stage is controlled by one bit of the binary amount. |
| `one_hot_decoded` | the amount is decoded to one-hot lines that control the stages. |

### stage_radix

| member | what it selects |
| --- | --- |
| `2` | 2:1 muxes, one stage per amount bit. |
| `4` | 4:1 muxes, one stage per two amount bits. |
| `8` | 8:1 muxes, one stage per three amount bits. |
| `full_width_single_stage` | one stage of full-width muxes, so the whole amount is decoded at once. |

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
thornton_1970 -> J. E. Thornton, "Design of a Computer: The Control Data 6600", Scott, Foresman and Co., 1970
davis_1969 -> R. L. Davis, "The ILLIAC IV Processing Element", IEEE Transactions on Computers, vol. C-18, no. 9, pp. 800-816, 1969
montoye_1990 -> R. K. Montoye, E. Hokenek, S. L. Runyon, "Design of the IBM RISC System/6000 Floating-Point Execution Unit", IBM Journal of Research and Development, 1990
pillmeier_2002 -> M. R. Pillmeier, M. J. Schulte, E. G. Walters III, "Design Alternatives for Barrel Shifters", Proc. SPIE 4791, Advanced Signal Processing Algorithms, Architectures, and Implementations XII, 2002
huntzicker_2008 -> S. Huntzicker, M. Dayringer, J. Soprano, A. Weerasinghe, D. M. Harris, D. Patil, "Energy-Delay Tradeoffs in 32-bit Static Shifter Designs", Proc. IEEE ICCD, 2008
wijeratne_2007 -> S. B. Wijeratne, et al., "A 9-GHz 65-nm Intel Pentium 4 Processor Integer Execution Unit", IEEE Journal of Solid-State Circuits, vol. 42, no. 1, pp. 26-37, 2007.
silberman_1998 -> J. Silberman, et al., "A 1.0-GHz Single-Issue 64-Bit PowerPC Integer Processor Using Dynamic Logic", IEEE Journal of Solid-State Circuits, vol. 33, no. 11, pp. 1600-1608, 1998.
jessani_1996 -> R. M. Jessani, C. H. Olson, "The Floating-Point Unit of the PowerPC 603e Microprocessor", IBM Journal of Research and Development, vol. 40, no. 5, 1996
mueller_2005 -> S. M. Mueller et al., "The Vector Floating-Point Unit in a Synergistic Processor Element of a CELL Processor", ARITH-17, pp. 59-67, 2005
oh_2006 -> H.-J. Oh et al., "A Fully Pipelined Single-Precision Floating-Point Unit in the Synergistic Processor Element of a CELL Processor", IEEE Journal of Solid-State Circuits, vol. 41, no. 4, 2006
