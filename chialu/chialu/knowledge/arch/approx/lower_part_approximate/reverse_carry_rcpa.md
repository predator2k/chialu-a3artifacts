---
family: lower_part_approximate
pin: {lower_cell: reverse_carry_rcpa}
---
# reverse_carry_rcpa

Reverse carry propagation: in the lower section the carry runs from
the higher-significance cell toward the lower one, so an unfinished
carry loses weight along its path, and a forecast signal, which is an
operand bit, the AND of the operand bits or their OR, resolves each
cell's outputs and supplies the carry at the point where the exact
forward-carry MSB section joins. Under frequency over-scaling the
lower-order outputs fail first, which bounds the error magnitude.

The reverse-carry cells are the pick for the delay and energy-delay
corner: the AND-forecast cell is 29 percent smaller than an exact
full adder in transistors with a 38 percent shorter carry delay, the
32-bit hybrids improve delay by 27 percent and energy-delay product
by 31 percent on average over the studied approximate adders in
45-nm CMOS, and an 8-bit approximate section reaches the relative
error of 4-bit truncation. The operand-bit forecast has the smallest
delay for short approximate sections, the AND forecast for long ones.
Against the OR cell the design costs about 2.5 percent more energy
for a lower error, and its critical path rises again once the
reverse-carry section dominates.

## references

pashaeifar2018 -> M. Pashaeifar, M. Kamal, A. Afzali-Kusha, M. Pedram, "Approximate Reverse Carry Propagate Adder for Energy-Efficient DSP Applications", IEEE Transactions on VLSI Systems, vol. 26, no. 11, pp. 2530-2541, 2018
venkatesan2011 -> R. Venkatesan, A. Agarwal, K. Roy, A. Raghunathan, "MACACO: Modeling and Analysis of Circuits for Approximate Computing", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 667-673, 2011
