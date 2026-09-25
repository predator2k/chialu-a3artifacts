---
family: embedded_fpu_block
pin: {composition: linked_multiplier_adder}
---
# linked_multiplier_adder

The Chong flexible embedded FPU: a dual-precision floating-point
multiplier, 53x53 or two 24x24, and a dual-precision adder, 53-bit or
a 26-bit and a 27-bit pair, joined by a configurable
multiplier-to-adder link, with configuration multiplexers that expose
the multiplier, the adder, a 64-bit right shifter and a 54-bit left
shifter for integer use, and optional input and output registers.

The pick when one hard block must serve fp64, two-lane fp32 and
integer circuits: against an FPGA without embedded FPUs the block
improves fp64 area by 5.2x and delay by 5.8x and fp32 by 4.4x and 4.2x
on a Virtex-II model, and integer circuits gain 1.21x in area and
1.71x in delay. Dedicated shifter ports let a shifter and the adder
work at once, while the arithmetic ports are shared to limit the pin
count. The block holds one multiplier and one adder, so a longer
reduction spans several blocks, where the bus sibling chains subblocks
internally. The link is the cascade form of bridge_fma seen from the
block level.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

chong_2009 -> Y. J. Chong, S. Parameswaran, "Flexible Multi-Mode Embedded Floating-Point Unit for Field Programmable Gate Arrays", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2009
