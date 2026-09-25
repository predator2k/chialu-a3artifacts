---
handle: zhang_2020
citation: H. Zhang, S.-B. Ko, "Design of Power Efficient Posit Multiplier", IEEE Transactions on Circuits and Systems II: Express Briefs, 2020
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [posit8_0, posit8_1, posit16_1, posit32]
authority: incremental
pages_read: 5 / 5
---

## summary
The document proposes a posit multiplier that divides its maximum-width mantissa multiplier into independently enabled regions controlled by each operand's regime width. The 8-bit, 16-bit, and 32-bit implementations reduce average power by 16% against standard posit multipliers with negligible area/timing overhead. # p.861, p.865

## families
### posit_adder_multiplier  (role: extends)
mechanism: The datapath extracts the sign/regime/exponent/mantissa, multiplies the mantissas, processes the sign/exponent, normalizes, packs, and rounds the result. The mantissa multiplier retains the maximum width of nb − es bits but is decomposed into regions. Regime-derived controls enable only the regions required by the actual mantissa widths, which suppresses toggling in the multiplier and downstream final addition/rounding. # p.862–865
choices:
  es_bits: 0 and 1 (reported instances)   # p.864–865
  regime_decode: lzc_plus_shifter   # p.862
  approximation: none   # p.864
new_choices:
  mantissa_region_granularity_bits: 4 for 8-bit/16-bit; 8 for 32-bit — width used to partition each mantissa operand   # p.863–864
slots:
  none
parameters: Posit(nb, es); nb = 8, 16, or 32; Posit(16,1) uses a 15-bit mantissa multiplier partitioned into one 3-bit region and three 4-bit regions; Posit(8) uses two regions; Posit(32) uses four 8-bit regions. # p.862–864
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power reduction | 16 | % average | STM-90nm library, 1.00V, 25°C (2020) | normal posit multipliers [8], [9] | 8-bit, 16-bit, and 32-bit evaluated designs | p.865 |
| power reduction | 8 | % | STM-90nm library, 1.00V, 25°C (2020) | normal posit multiplier | Posit(8,0) | p.864 |
| power reduction | 3 | % | STM-90nm library, 1.00V, 25°C (2020) | normal posit multiplier | Posit(8,1) | p.864 |
| power reduction | more than 20 | % | STM-90nm library, 1.00V, 25°C (2020) | normal posit multipliers | 16-bit and 32-bit designs | p.864 |
| area overhead | 4 | % | STM-90nm library, 1.00V, 25°C (2020) | normal Posit(16,1) multiplier | complete proposed Posit(16,1) design | p.865 |
| mantissa-multiplier power reduction | 28 | % | STM-90nm library, 1.00V, 25°C (2020) | normal Posit(16,1) multiplier module | proposed Posit(16,1) | p.865 |
| final-adder power reduction | 30 | % average | STM-90nm library, 1.00V, 25°C (2020) | normal Posit(16,1) final adder | proposed Posit(16,1) | p.865 |
| whole-design power reduction | 22 | % | STM-90nm library, 1.00V, 25°C (2020) | normal Posit(16,1) multiplier | proposed Posit(16,1) | p.865 |
errors_and_checks: No approximation metric or concurrent checker is reported. Functionality was verified with extensive SoftPosit-generated vectors before and after synthesis. # p.864
conditions: The control overhead masks much of the benefit in the small 8-bit designs. # p.864 Posit formats with larger exponent widths obtain less benefit because their mantissa widths shrink. # p.865 Equal-width IEEE multipliers have better timing/area/power because their fixed component widths omit posit extraction/packing. # p.864
evidence: §II–V; Fig. 3–7; Table I–III, p.862–865.

### lane_width_gating  (role: extends)
mechanism: Each operand's shift_rg value determines its actual mantissa width as mant_bit = nb − es − shift_rg. Separate controls for the multiplicand and multiplier enable rectangular partial-product regions only when both corresponding controls are active. Disabled regions produce zeros, which also suppresses toggling in later addition and rounding. # p.863–865
choices:
  detection: regime_bit_width [outside domain]   # p.863
  gating: partial_product_region_enable [outside domain]   # p.863
new_choices:
  region_granularity_bits: 4 or 8 — width of an independently enabled operand region   # p.863–864
  control_source: shift_rg — regime-width signal reused from posit component extraction   # p.863
slots:
  none
parameters: Posit(16,1) uses four horizontal/four vertical regions, 2-bit control per operand, and 16 PPG modules; Posit(8) uses 1-bit control per operand; Posit(32) uses 8-bit regions and four regions per operand. # p.863–864
results: none separately reported
errors_and_checks: none
conditions: A 2-bit granularity is possible but incurs more resource overhead because Booth-2 PPG uses three multiplier bits per partial product. # p.864
evidence: §III-A–C; Fig. 5–6; Table I, p.863–864.

### booth_recoded_parallel  (role: instantiates)
mechanism: The maximum-width mantissa multiplier uses radix-4 modified Booth multiplication. For Posit(16,1), the 15-bit multiplier produces eight 16-bit partial products. The proposed implementation partitions both operand dimensions and implements 16 controlled Booth-2 PPG modules. # p.862–863
choices:
  booth_radix: 4   # p.862
new_choices:
  none
slots:
  none
parameters: 15-bit mantissas, eight 16-bit partial products, and 16 controlled PPG modules for Posit(16,1). # p.862–863
results: none separately reported
errors_and_checks: none
conditions: Zero-filled unused multiplier bits can become ones in negative Booth partial products, so an unpartitioned multiplier continues toggling despite short actual mantissas. # p.862
evidence: §III; Fig. 5–6, p.862–864.

## new_families
none

## space_gaps
* `lane_width_gating.detection` needs a `regime_bit_width` value for posit mantissa-width detection. # p.863
* `lane_width_gating.gating` needs a `partial_product_region_enable` value for controlled PPG regions. # p.863
* `posit_adder_multiplier` needs a mantissa-multiplier slot that accepts `booth_recoded_parallel`; its existing `sig_datapath` slot accepts only adder families. # p.862

## open_questions
* Table II's exact absolute delay/area/power values and some per-format percentage changes are unreadable in the supplied raster rendering; only narrative values are recorded. # p.864
* The evaluated Posit(32, es) exponent-width values are not stated in the prose. # p.864–865
* The partial-product reduction structure and final-adder family are not identified. # p.862–864
