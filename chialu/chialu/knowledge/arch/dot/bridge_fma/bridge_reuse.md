---
family: bridge_fma
pin: {composition_style: bridge_reuse}
---
# bridge_reuse

Bridge hardware between independent add and multiply units: the multiplier array's sum and carry output enters the
bridge, which combines it with a 161-bit pre-aligned addend from the
adder path and performs the classic-FMA alignment, combination and
normalization, and the adder's add/round stage selects the bridge
result and completes the single rounding. The ARM form forwards an
unrounded 106-bit mantissa into a separate add pipeline and takes
the augend only when that pipeline begins.

Bridge reuse is the pick when the add and multiply units must keep
their own latency and parallel issue: standalone operations stay 30
to 70 percent faster and 50 to 70 percent lower in peak power than
through a classic FMA, the FMA itself gains about 12 percent over an
add following a multiply, and dependent FMAs issue at add latency,
which gives 2n+1 cycles for n products with 2-cycle pipelines
against 4n and about 6 percent on SpecFP. The costs are about 40
percent more area than the add-plus-multiply block, 20 percent more
FMA latency and power than a classic FMA in 65 nm SOI, and bridge
logic that is clock-gated outside FMA instructions. The cascade is
the sibling when a single rounding is not required.

The library realizes this choice as a pin of the generated bridge_fma module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

quinnell_2008 -> E. Quinnell, E. E. Swartzlander, C. Lemonds, "Bridge Floating-Point Fused Multiply-Add Design", IEEE Transactions on VLSI Systems, vol. 16, no. 12, pp. 1726-1730, 2008
quinnell_2007 -> E. Quinnell, E. E. Swartzlander, C. Lemonds, "Floating-Point Fused Multiply-Add Architectures", 41st Asilomar Conference on Signals, Systems and Computers, 2007
lutz_2011 -> D. R. Lutz, "Fused Multiply-Add Microarchitecture Comprising Separate Early-Normalizing Multiply and Add Pipelines", Proc. 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 123-128, 2011.
lutz_2019 -> D. R. Lutz, "ARM Floating Point 2019: Latency, Area, Power", 26th IEEE Symposium on Computer Arithmetic, 2019
