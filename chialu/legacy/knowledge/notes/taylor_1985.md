---
handle: taylor_1985
citation: Taylor, "Radix 16 SRT Dividers with Overlapped Quotient Selection Stages", 7th IEEE Symposium on Computer Arithmetic, 1985
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp32, fp64, ieee_extended, int64]
authority: landmark
pages_read: 64-71 / 8
---

## summary
The paper compares radix-16 SRT dividers assembled from overlapped radix-2 or radix-4 quotient-selection stages with irredundant or carry-save remainders. Radix-4 stages provide the best cost/performance tradeoff, and radix-4 Option B is implemented in the S-1 Mark IIB divider. # p.64, p.70-p.71

## families
### srt_high_radix  (role: compares)
mechanism: Each iteration selects redundant quotient digits from leading remainder/divisor bits, forms a divisor multiple, updates the partial remainder, and accumulates the quotient. A radix-16 step is decomposed into four radix-2 stages or two radix-4 stages. Later quotient-selection stages are replicated for possible earlier digits and evaluated concurrently; carry-save remainders remove carry propagation from the iterative partial-remainder path. # p.65-p.68
choices:
  radix: 16  # p.65
  digit_redundancy: minimal; maximal  # p.65-p.67
  overlapped_stages: 2; 4 [outside domain]  # p.68-p.69
new_choices:
  quotient_selection_stage_radix: {2, 4} — radix of each QS stage used to assemble the radix-16 step  # p.65, p.68-p.69
  quotient_digit_set: {-1,0,1} | {-2,-1,0,1,2} | {-3,-2,-1,0,1,2,3} — redundancy and divisor-multiple alternatives  # p.64, p.67
  overlap_organization: {cascaded, pairwise, partial, maximal} — amount and grouping of speculative QS-stage replication  # p.68-p.69
  remainder_representation: {irredundant, carry_save} — whether partial-remainder formation propagates carries during each iteration  # p.66-p.67
slots:
  digit_select: qds_table [implemented by a narrow adder and logic]  # p.66-p.69
parameters: radix 16; four quotient bits per cycle; 64-bit operands; 53-bit rounded fraction; 17 or 18 cycles in evaluated SRT designs; implemented cycle time 12.5 nanoseconds; eight ECL gate arrays  # p.64, p.69-p.70
results:
| metric | value | unit | technology / device | baseline | condition | page |
| double divide time | 178 | ns | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 644 ns | 4C, digits {-3,...,3}, carry-save remainder, 18 cycles | p.70 |
| total cost | 1870 | cells | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 600 cells | 4C, digits {-3,...,3} | p.70 |
| double divide time | 184 | ns | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 644 ns | 4C, digits {-2,...,2}, carry-save remainder, 18 cycles | p.70 |
| total cost | 1600 | cells | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 600 cells | 4C, digits {-2,...,2} | p.70 |
| double divide time | 203 | ns | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 644 ns | 2D, digits {-1,0,1}, carry-save remainder, 18 cycles | p.70 |
| total cost | 1800 | cells | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 600 cells | 2D, digits {-1,0,1} | p.70 |
| double divide time | 209 | ns | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 644 ns | 2C, digits {-1,0,1}, carry-save remainder, 18 cycles | p.70 |
| total cost | 1560 | cells | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 600 cells | 2C, digits {-1,0,1} | p.70 |
| double divide time | 216 | ns | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 644 ns | 4B, digits {-3,...,3}, carry-save remainder, 18 cycles | p.70 |
| total cost | 1670 | cells | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 600 cells | 4B, digits {-3,...,3} | p.70 |
| double divide time | 223 | ns | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 644 ns | 4B, digits {-2,...,2}, carry-save remainder, 18 cycles | p.70 |
| total cost | 1430 | cells | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 600 cells | 4B, digits {-2,...,2} | p.70 |
| double divide time | 238 | ns | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 644 ns | 4A, digits {-3,...,3}, irredundant remainder, 17 cycles | p.70 |
| total cost | 1260 | cells | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 600 cells | 4A, digits {-3,...,3} | p.70 |
| double divide time | 252 | ns | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 644 ns | 4A, digits {-2,...,2}, irredundant remainder, 17 cycles | p.70 |
| total cost | 1030 | cells | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 600 cells | 4A, digits {-2,...,2} | p.70 |
| double divide time | 274 | ns | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 644 ns | 2B, digits {-1,0,1}, carry-save remainder, 18 cycles | p.70 |
| total cost | 1470 | cells | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 600 cells | 2B, digits {-1,0,1} | p.70 |
| double divide time | 287 | ns | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 644 ns | 2A, digits {-1,0,1}, irredundant remainder, 17 cycles | p.70 |
| total cost | 1200 | cells | Motorola MCA II ECL macrocell model, 1985 | radix-2 non-restoring: 600 cells | 2A, digits {-1,0,1} | p.70 |
| cycle time | 12.5 | nanoseconds | S-1 Mark IIB, eight ECL gate arrays, 1985 | none | implemented radix-4 Option B | p.64, p.70 |
| single-precision divide time | 150 | nanoseconds | S-1 Mark IIB, eight ECL gate arrays, 1985 | single-precision multiply: 50 nanoseconds | register-to-register execution | p.64, p.71 |
| double-precision divide time | 225 | nanoseconds | S-1 Mark IIB, eight ECL gate arrays, 1985 | double-precision multiply: 50 nanoseconds | register-to-register execution | p.64, p.71 |
| extended-precision divide time | 275 | nanoseconds | S-1 Mark IIB, eight ECL gate arrays, 1985 | extended-precision multiply: 50 nanoseconds | register-to-register execution | p.71 |
errors_and_checks: Subtractive normalization produces correctly rounded quotients and exact remainders; the evaluated costs include hardware for IEEE-standard quotient rounding. # p.64, p.69
conditions: Radix-16 designs cost two to three times as much as radix-2 non-restoring hardware but run about four times faster in the same technology. # p.64-p.65 Radix-4 stages are cheaper and faster than overlapped radix-2 stages for the evaluated radix-16 designs. # p.71 Carry-save remainders reduce the iteration delay but require extra registers/adders and delayed quotient/remainder resolution. # p.66-p.67 A multiple-chip implementation requires a redundant remainder and keeps the critical quotient-selection path on one chip because interchip delays are substantial. # p.70
evidence: Abstract; §§2-9; Figures 1-6; Tables 1-8, p.64-p.71

## new_families
none

## space_gaps
* srt_high_radix lacks choices for quotient-selection stage radix, explicit quotient-digit set, overlap organization, and remainder representation. # p.65-p.69
* qds_table lacks a declared family definition covering the paper's narrow-adder-plus-logic quotient selector. # p.67-p.69

## open_questions
* The document does not state a semiconductor feature size for the Motorola MCA II ECL arrays.
* The hypothetical single-chip comparison assumes up to 1800 cells, while the 4C maximal-redundancy design totals 1870 cells. # p.65, p.70
