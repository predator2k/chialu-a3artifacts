# masked_merged

Shift, rotate, extract and deposit in one pass through a rotator and
a mask: a barrel rotator turns the operand by the shift amount while,
in parallel, a mask generator decodes the shift amount and field
bounds into a per-bit mask, and a merge network ANDs the rotated data
with the mask and ORs in the fill or the second operand, so a logical
shift is a rotate with zero fill, an arithmetic shift a rotate with
sign fill, and rotate-mask-and-merge, the POWER rlwinm lineage,
inserts a rotated field into a target word. The mask is ready when the
rotation is, and the masker adds one gate to the data critical path.

mask_generator sets how the mask arrives: a binary-to-thermometer
converter followed by AND gates and OR trees yields the per-bit mask
information, two thermometer codes ANDed together bound a field at
both ends, and a lookup table trades the OR trees for decode area; the
thermometer nodes near both extremes switch rarely, so energy
estimates need node-specific activity factors. merge_style trades the
AND-OR merge, which with inverting logic absorbs the rotator's final
inverter, against a per-bit mux; a deposit path, the insert route that
turns the shifter into a field unit, needs an insert op the unit lacks. The POWER fixed-point unit
goes furthest: rotation and addition share one merge network, mask
generation runs beside the rotation, and the selected operation
reaches the macro output without a separate adder-versus-rotator
result mux, at 550 ps for the 64-bit unit in 0.25 um dynamic logic,
with extra cross-direction wires to complete the rotator.

The family wins wherever one rotator must serve shifts and field
operations in a single cycle, and it degrades gracefully: a
right-rotate-only barrel drops the masker for two AND gates, and an
FPGA ALU spreads the operation over two cycles, reusing a byte rotator
and doing the AND in the logic unit and the signed-right extension in
the adder unit, with no loss of processor frequency. It loses to a
butterfly network, which strictly generalizes the rotate-and-mask
form, once arbitrary bit permutations or gather and scatter are
required, and the rotator slot is where the radix and select encoding
of the barrel are chosen.

## design choices

### mask_generator

| member | what it selects |
| --- | --- |
| `thermometer_decode` | one thermometer per direction, selected by the operation. |
| `two_thermometer_and` | a low and a high bound thermometer ANDed together. |
| `lut` | a table over the direction and the amount. |

### merge_style

| member | what it selects |
| --- | --- |
| `and_or_merge` | the rotation and the fill are merged by AND and OR gates. |
| `per_bit_mux` | a multiplexer per bit selects between them. |

## references

silberman_1998 -> J. Silberman, et al., "A 1.0-GHz Single-Issue 64-Bit PowerPC Integer Processor Using Dynamic Logic", IEEE Journal of Solid-State Circuits, vol. 33, no. 11, pp. 1600-1608, 1998.
huntzicker_2008 -> S. Huntzicker, M. Dayringer, J. Soprano, A. Weerasinghe, D. M. Harris, D. Patil, "Energy-Delay Tradeoffs in 32-bit Static Shifter Designs", Proc. IEEE ICCD, 2008
metzgen_2004 -> P. Metzgen, "A High Performance 32-bit ALU for Programmable Logic", Proc. ACM/SIGDA International Symposium on FPGAs, pp. 61-70, 2004
