---
id: saturation_by_overflow_mask
tier: word
applies_to: [adder, alu, shift]
preserves: bit_exact
check: tb
effect: area-
sources: [seander_bithacks]
---
# Saturate with a mask instead of a wide mux

pattern: `r = ovf ? (sign ? MIN : MAX) : sum` as a 3:1 mux row

rewrite: `sat = {W{~sign_of_true_result}} ^ {1'b1, {W-1{1'b0}}}` (the extreme of the right sign), then `r = (sum & ~{W{ovf}}) | (sat & {W{ovf}})` — AND/OR rows driven by the overflow flag; overflow itself is `cin_msb ^ cout_msb` of the adder

when: saturating add/sub ops, clamps in DSP datapaths
