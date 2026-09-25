---
handle: he_chang_2009
citation: He, Chang, "A New Redundant Binary Booth Encoding for Fast 2^n-Bit Multiplier Design", IEEE Transactions on Circuits and Systems I, 2009
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int8, int16, int32, int64]
authority: incremental
pages_read: 10 / 10
---

## summary
The paper proposes covalent redundant binary Booth encoding (CRBBE), which polarizes two adjacent Booth-encoded digits to generate one redundant binary partial product without a correction vector. The evaluated radix-16 CRBBE-4 multiplier uses a redundant binary adder tree and an arrival-grouped RB-to-NB converter for power-of-two operand lengths from 8 to 64 b. CRBBE-4 has the lowest delay and energy-delay product among the six compared encoding schemes. # p.1195–1201

## families
### redundant_binary_multiplier  (role: extends)
mechanism: CRBBE binds two adjacent Booth encoders and polarizes their digits into an opposite-polarity dipole. Each dipole directly forms a positive–negative-complement-coded RB partial product from the difference of two multiples. CRBBE-4 binds two radix-4 encoders, uses a dedicated carry-free RBA for the exceptional hard multiple, produces one RB partial product per four multiplier bits, and eliminates the correction vector associated with negative multiples and NB-to-RB conversion. # p.1195–1198
choices:
  rb_encoding: positive_negative_complement [outside domain]   # p.1193–1198
  booth_radix: 16 [outside domain]   # p.1196–1199
  rbnb_converter: cpa   # p.1198
new_choices:
  rb_booth_encoding: covalent_adjacent_digit_polarization — two adjacent Booth digits are mapped to an opposite-polarity dipole that directly forms one RB partial product   # p.1195–1197
  correction_vector: none — negative-multiple and NB-to-RB compensation rows are eliminated   # p.1195–1197
slots:
  final_converter: carry_lookahead [intergroup_carry=select]   # p.1198
parameters: evaluated operand widths 8, 16, 32, and 64 b; CRBBE-4 radix 16; RB partial-product reduction rate 1/4; 64 × 64-b design uses 16 CRBBE-4/RBPPG slices, 16 RB partial products, a 4-stage RBA tree, and concurrent converter groups of 4, 4, 8, 16, and 96 digits   # p.1197–1199
results:
| metric | value | unit | technology / device | baseline | condition | page |
| speed improvement | 8.50 | % faster | Artisan TSMC 0.18-μm standard-cell library; 2009 | RBBE-4 | average over 8/16/32/64 b; 1.8V, 25 C | p.1199 |
| speed improvement | 10.68 | % faster | Artisan TSMC 0.18-μm standard-cell library; 2009 | NBBE-2 | average over 8/16/32/64 b; 1.8V, 25 C | p.1199 |
| speed improvement | 12.82 | % faster | Artisan TSMC 0.18-μm standard-cell library; 2009 | TCM | average over 8/16/32/64 b; 1.8V, 25 C | p.1199 |
| speed improvement | 19.58 | % faster | Artisan TSMC 0.18-μm standard-cell library; 2009 | NBBE-3 | average over 8/16/32/64 b; 1.8V, 25 C | p.1199 |
| speed improvement | 12.60 | % faster | Artisan TSMC 0.18-μm standard-cell library; 2009 | PRBBE-3 | average over 8/16/32/64 b; 1.8V, 25 C | p.1199 |
| area overhead | 10.83 | % | Artisan TSMC 0.18-μm standard-cell library; 2009 | most compact multiplier design, not named in prose | average over 8/16/32/64 b | p.1199 |
| energy-delay product reduction | 19.40 | % less | Artisan TSMC 0.18-μm standard-cell library; 2009 | RBBE-4 | average over 8/16/32/64 b; 1.8V, 25 C | p.1200 |
| energy-delay product reduction | 7.11 | % less | Artisan TSMC 0.18-μm standard-cell library; 2009 | NBBE-2 | average over 8/16/32/64 b; 1.8V, 25 C | p.1200 |
| energy-delay product reduction | 16.91 | % less | Artisan TSMC 0.18-μm standard-cell library; 2009 | TCM | average over 8/16/32/64 b; 1.8V, 25 C | p.1200 |
| energy-delay product reduction | 16.08 | % less | Artisan TSMC 0.18-μm standard-cell library; 2009 | NBBE-3 | average over 8/16/32/64 b; 1.8V, 25 C | p.1200 |
| energy-delay product reduction | 13.02 | % less | Artisan TSMC 0.18-μm standard-cell library; 2009 | PRBBE-3 | average over 8/16/32/64 b; 1.8V, 25 C | p.1200 |
errors_and_checks: The multiplier implements exact RB multiplication; gate-level functionality was checked in ModelSim with randomly generated input patterns. Power estimates use Monte Carlo simulation with more than 99.9% confidence that error is below 3%. # p.1198–1199
conditions: CRBBE-4 is evaluated only for power-of-two widths from 8 to 64 b. NBBE-2 dissipates the least energy at 8 and 16 b, while CRBBE-4 has the lowest EDP across the comparison. CRBBE above radix 16 is not pursued because some radix-32 hard multiples cannot be generated efficiently. All compared designs use the same RBA tree/RB-to-NB converter and are optimized for minimum delay with logic restructuring disabled. # p.1197–1200
evidence: §III, Tables V–VI, Figs. 5–7, §IV, Figs. 8–9, §V, Tables VII–VIII, Figs. 10–11, pp.1195–1200

## new_families
none

## space_gaps
* `rb_encoding` lacks the paper's positive–negative-complement coding value. # p.1193–1198
* `booth_radix` for `redundant_binary_multiplier` lacks radix 16. # p.1196–1199
* `redundant_binary_multiplier` lacks a choice for covalent adjacent-digit polarization and correction-vector elimination. # p.1195–1197
* `redundant_binary_multiplier` lacks a reduction slot for the binary tree of carry-free RB adders. # p.1198–1199
* `final_converter` cannot explicitly name the paper's hybrid carry-lookahead/carry-select converter as a composite family. # p.1198

## open_questions
* The provided document text does not expose the numeric cells of Tables VII and VIII, so absolute delay/energy/area/EDP results remain UNKNOWN. # p.1199–1200
* The prose identifies a 10.83% area penalty against “the most compact multiplier design” without naming that baseline. # p.1199
