---
family: lower_part_approximate
pin: {lower_cell: xor_xnor_axa}
---
# xor_xnor_axa

Approximate XOR/XNOR-based cells: a 10-transistor accurate full adder
is reduced to 6 or 8 transistors by building the cell from an
inverter with pass transistors (AXA1, approximate sum and carry), a
four-transistor XNOR with a pass-transistor block (AXA2, exact carry),
or that block with two more pass transistors for a better sum (AXA3,
exact carry). Removing transistors lowers node capacitance and logic
complexity.

The cells are the pick when transistor count and dynamic power per
lower bit are the constraint: AXA2 has the fewest transistors, AXA3
the lowest dynamic power and the smallest total error distance with
an exact carry, and AXA1 the shortest carry delay but static power
above the accurate cell. They pay with pass-transistor threshold loss,
which gives non-full-swing outputs and lower noise margin and may
need output drivers, and with a carry delay that for AXA2 is no
better than the accurate cell's. The inexact InXA cells and the OR
cell are the siblings when an exact carry or no carry at all is wanted.

## references

yang2013 -> Z. Yang, A. Jain, J. Liang, J. Han, F. Lombardi, "Approximate XOR/XNOR-Based Adders for Inexact Computing", 13th IEEE International Conference on Nanotechnology (IEEE-NANO), pp. 690-693, 2013
