# fpga_mapped

A barrel shifter or rotator mapped to the FPGA fabric: either the
multiplexer stages are regrouped so that each stage's multiplexer
width matches the LUT input count, or the shift becomes a
multiplication by a one-hot power of two in an idle embedded
multiplier, which rotates an 8-bit byte in one cycle in one MULT18X18.
A 32-bit single-cycle shifter splits the input into four bytes, uses
four multiplier shifters for the fine shift from the three low shift
bits and thirty-two 4-to-1 multiplexers for the bulk byte reordering
from the two high bits; a four-cycle version reuses one multiplier
shifter under a state machine.

The mapping choice trades configurable logic against placement and
multiplier occupancy: the multiplier form needs 9 CLBs plus four
multipliers where the traditional 32-bit design needs 64 CLBs on a
Virtex-II, but it requires one-hot control and locks the shifter to
the multiplier locations, and the four-cycle reuse trades a four-cycle
latency for a single multiplier. A 4:1 multiplexer placed in parallel
with each 4-LUT, sharing the LUT's data inputs and, across the two
LUTs of a CLB, the select inputs, cuts fp64 adder area by 17% and
multiplier area by 10% and raises the average clock rate of five fp64
benchmarks by 11.6% on a modeled Virtex-II Pro, at 16.1% more routing
tracks, a 1.83% slower 4-LUT and 0.35% more silicon; the shared select
lines follow from adding no CLB inputs. The shared-ALU multiplexer
form is the option when the shifter shares a datapath multiplexer with
an ALU.

The function is exact, so no accuracy contract applies; the rotate
returns bits shifted out of the MSB end at the LSB end. Execution is
feed-forward for the single-cycle forms and multicycle for the reused
multiplier.

## references

gigliotti_2004 -> P. Gigliotti, "Implementing Barrel Shifters Using Multipliers", Xilinx Application Note XAPP195, 2004
beauchamp_2008 -> M. J. Beauchamp, S. Hauck, K. D. Underwood, K. S. Hemmert, "Architectural Modifications to Enhance the Floating-Point Performance of FPGAs", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, 2008
