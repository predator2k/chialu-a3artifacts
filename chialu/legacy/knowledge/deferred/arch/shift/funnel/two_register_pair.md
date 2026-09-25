---
family: funnel
pin: {input_forming: two_register_pair}
---
# two_register_pair

The source word is the concatenation of two full-width registers
rather than one operand duplicated, sign-extended or zero-filled, and
the window selected at the byte or bit offset straddles the register
boundary: AltiVec's double-vector shift builds successive byte-offset
vectors from an aligned register pair, and VIS faligndata concatenates
two 64-bit registers and extracts an eight-byte window at the offset
that alignaddr placed in the graphics status register.

It turns the shifter into an unaligned-access and double-width-shift
engine: two aligned loads plus alignaddr and faligndata, each at 1/1
cycles of latency and throughput, emulate an unaligned 64-bit load,
and long unaligned-load sequences approach two instructions per vector
because load and permute issue together; the AltiVec 5 x 5 median
filter reaches 1.2 cycles per output pixel with the double-vector
shift as its funnel. The single-operand siblings duplicate_for_rotate,
sign_extend and zero_fill build the 63-bit source word from one
operand's bits, zeros or its sign bit, and a shifts-only design drops
two of those input-generator gates. The pair is the pick when the
datapath must serve SIMD alignment, unaligned loads from aligned pairs
and multiword shifts; a rotate or arithmetic shift of one operand
keeps the single-operand forms.

## references

diefendorff_2000 -> K. Diefendorff, P. K. Dubey, R. Hochsprung, H. Scales, "AltiVec Extension to PowerPC Accelerates Media Processing", IEEE Micro, vol. 20, no. 2, pp. 85-95, 2000
tremblay_1996 -> M. Tremblay, J. M. O'Connor, V. Narayanan, L. He, "VIS Speeds New Media Processing", IEEE Micro, vol. 16, no. 4, pp. 10-20, 1996
huntzicker_2008 -> S. Huntzicker, M. Dayringer, J. Soprano, A. Weerasinghe, D. M. Harris, D. Patil, "Energy-Delay Tradeoffs in 32-bit Static Shifter Designs", Proc. IEEE ICCD, 2008
