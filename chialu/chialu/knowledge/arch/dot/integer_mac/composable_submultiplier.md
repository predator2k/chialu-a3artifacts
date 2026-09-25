---
family: integer_mac
pin: {array_style: composable_submultiplier}
---
# composable_submultiplier

Identical narrow submultipliers, 2b x 8b when one operand scales and 2b
x 2b when both do, are combined through configurable shift-add logic
into a full-precision multiply, and the same submultipliers run as
independent low-precision multipliers when the operands narrow. The
composition is spatial: every submultiplier works every cycle, the
shift-add stage weights each partial result, and the accumulation mode
keeps the narrow products apart or sums them into one result.

The divide-and-conquer array is the precision-scalable MAC that gains
throughput rather than only energy: at 28 nm the two-dimensional design
in Sum Apart mode reaches 14.5x the throughput of a full-precision
conventional MAC at symmetric 2b scaling, for up to 4.4x its area, and
the two-level Sum Together design saves 68 percent energy against data
gating. Scaling one dimension covers the weight-only case at a smaller
cost, a 15 percent energy saving with 5 percent of operations at 8b. Bit
Fusion is the same composition with 2-bit bricks formed over cycles (the
bit-serial style is deferred with the single-cycle scope). The style loses to a conventional array when the
layers use the full width, since the combination logic is overhead
there, and to twin-precision subword gating when area is the constraint,
because gating one partial-product matrix adds less than replicating the
combination adders.

The composition also serves a fixed-point mode inside a merged
fixed/floating unit, where two 8-bit two's complement pairs packed
into the 16-bit operands feed two 8-bit multipliers whose products a
(4,2) CSA adds before the sign extension to a 32-bit accumulator.

The library realizes this choice as a pin of the generated integer_mac module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

camus2019 -> V. Camus, L. Mei, C. Enz, M. Verhelst, "Review and Benchmarking of Precision-Scalable Multiply-Accumulate Unit Architectures for Embedded Neural-Network Processing", IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 9, no. 4, pp. 697-711, 2019
zhang_2018 -> H. Zhang, H. J. Lee, S.-B. Ko, "Efficient Fixed/Floating-Point Merged Mixed-Precision Multiply-Accumulate Unit for Deep Learning Processors", ISCAS 2018
