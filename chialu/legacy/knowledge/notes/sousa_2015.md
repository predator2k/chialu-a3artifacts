---
handle: sousa_2015
citation: Sousa, "2^n RNS Scalers for Extended 4-Moduli Sets", IEEE Transactions on Computers, 2015
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [rns_integer]
authority: incremental
pages_read: 14 / 14
---

## summary
The paper proposes exact, memoryless 2^n scalers that operate directly in RNS channels for augmented 3-moduli sets and extended 4-moduli sets. The hierarchical CRT/MRS formulation avoids reverse conversion, binary scaling, and forward conversion. ASIC/FPGA implementations compare the proposed scalers with earlier direct scalers and RC–Sc–FC implementations.

## families
### rns_scaling_comparison  (role: proposes)
mechanism: The scaler embeds division by 2^n into a hierarchical reconstruction. The first level applies CRT-derived channel equations to {2^n−1, 2^(n+x), 2^n+1}; a second MRS-derived level incorporates m4 for extended sets. Bitwise rotations/concatenations, end-around-carry CSAs, and modulo CPAs implement the equations without reverse and forward conversions. The channels compute scaled residues in parallel, and the first-level reconstructed value R3↔1 feeds the second level when m4 is present. # pp.3-8
choices:
  operation: scale # p.1
  method: hierarchical_crt_mrs [outside domain] # pp.2-5
  exactness: exact # pp.2,13
new_choices:
  scale_factor: 2^n — the constant divisor embedded in the channel equations # pp.3-5
  moduli_set: "{2^n−1, 2^(n+x), 2^n+1[, m4]}" — selects an augmented 3-moduli set or an extended 4-moduli set # pp.2,13
  hierarchy_levels: "1 or 2" — one CRT level serves three moduli; a second MRS level incorporates m4 # pp.3-5
slots:
  none
parameters: 0 ≤ x ≤ n; experimental n = 8, 16; graphs also cover n = 4, 8, 16, 24; 3-moduli DR = 4n−1 bits for x=n; 4-Mod A DR = 4n bits; 4-Mod B DR = 4n+1 bits; 4-Mod C DR = 6n bits. # pp.5-6,10-13
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 0.74 (0.024) | ns | 2015; UMC 90 nm ASIC | [15] | 3-moduli, n=8; parenthesis normalized to DR | p.11 |
| delay | 0.92 (0.015) | ns | 2015; UMC 90 nm ASIC | [15] | 3-moduli, n=16; parenthesis normalized to DR | p.11 |
| area | 5.6 (0.18) | ×10^3 µm^2 | 2015; UMC 90 nm ASIC | [15] | 3-moduli, n=8; parenthesis normalized to DR | p.11 |
| area | 12.2 (0.19) | ×10^3 µm^2 | 2015; UMC 90 nm ASIC | [15] | 3-moduli, n=16; parenthesis normalized to DR | p.11 |
| power | 9.8 (0.32) | mW | 2015; UMC 90 nm ASIC | [15] | 3-moduli, n=8; parenthesis normalized to DR | p.11 |
| power | 19.4 (0.31) | mW | 2015; UMC 90 nm ASIC | [15] | 3-moduli, n=16; parenthesis normalized to DR | p.11 |
| delay | 6.1 (0.20) | ns | 2015; Virtex 4 xc4vlx200ff1513-11 | [15] | 3-moduli, n=8; parenthesis normalized to DR | p.11 |
| delay | 7.0 (0.11) | ns | 2015; Virtex 4 xc4vlx200ff1513-11 | [15] | 3-moduli, n=16; parenthesis normalized to DR | p.11 |
| area | 210 (6.77) | slices | 2015; Virtex 4 xc4vlx200ff1513-11 | [15] | 3-moduli, n=8; parenthesis normalized to DR | p.11 |
| area | 324 (5.14) | slices | 2015; Virtex 4 xc4vlx200ff1513-11 | [15] | 3-moduli, n=16; parenthesis normalized to DR | p.11 |
| delay | 2.25 (0.070) | ns | 2015; UMC 90 nm ASIC | RC–Sc–FC [22] | 4-Mod A, n=8; parenthesis normalized to DR | p.11 |
| delay | 2.78 (0.043) | ns | 2015; UMC 90 nm ASIC | RC–Sc–FC [22] | 4-Mod A, n=16; parenthesis normalized to DR | p.11 |
| area | 17.5 (0.55) | ×10^3 µm^2 | 2015; UMC 90 nm ASIC | RC–Sc–FC [22] | 4-Mod A, n=8; parenthesis normalized to DR | p.11 |
| area | 40.6 (0.63) | ×10^3 µm^2 | 2015; UMC 90 nm ASIC | RC–Sc–FC [22] | 4-Mod A, n=16; parenthesis normalized to DR | p.11 |
| power | 85.8 (2.68) | mW | 2015; UMC 90 nm ASIC | RC–Sc–FC [22] | 4-Mod A, n=8; parenthesis normalized to DR | p.11 |
| power | 213.5 (3.34) | mW | 2015; UMC 90 nm ASIC | RC–Sc–FC [22] | 4-Mod A, n=16; parenthesis normalized to DR | p.11 |
| delay | 4.11 (0.125) | ns | 2015; UMC 90 nm ASIC | RC–Sc–FC [22] | 4-Mod B, n=8; parenthesis normalized to DR | p.11 |
| delay | 4.71 (0.072) | ns | 2015; UMC 90 nm ASIC | RC–Sc–FC [22] | 4-Mod B, n=16; parenthesis normalized to DR | p.11 |
| area | 32.6 (0.99) | ×10^3 µm^2 | 2015; UMC 90 nm ASIC | RC–Sc–FC [22] | 4-Mod B, n=8; parenthesis normalized to DR | p.11 |
| area | 73.0 (1.12) | ×10^3 µm^2 | 2015; UMC 90 nm ASIC | RC–Sc–FC [22] | 4-Mod B, n=16; parenthesis normalized to DR | p.11 |
| power | 149.1 (4.52) | mW | 2015; UMC 90 nm ASIC | RC–Sc–FC [22] | 4-Mod B, n=8; parenthesis normalized to DR | p.11 |
| power | 318.6 (4.9) | mW | 2015; UMC 90 nm ASIC | RC–Sc–FC [22] | 4-Mod B, n=16; parenthesis normalized to DR | p.11 |
| delay | 1.65 (0.034) | ns | 2015; UMC 90 nm ASIC | RC–Sc–FC [25] | 4-Mod C, n=8; parenthesis normalized to DR | p.11 |
| delay | 1.86 (0.019) | ns | 2015; UMC 90 nm ASIC | RC–Sc–FC [25] | 4-Mod C, n=16; parenthesis normalized to DR | p.11 |
| area | 18.7 (0.39) | ×10^3 µm^2 | 2015; UMC 90 nm ASIC | RC–Sc–FC [25] | 4-Mod C, n=8; parenthesis normalized to DR | p.11 |
| area | 38.4 (0.4) | ×10^3 µm^2 | 2015; UMC 90 nm ASIC | RC–Sc–FC [25] | 4-Mod C, n=16; parenthesis normalized to DR | p.11 |
| power | 66.7 (1.39) | mW | 2015; UMC 90 nm ASIC | RC–Sc–FC [25] | 4-Mod C, n=8; parenthesis normalized to DR | p.11 |
| power | 127.8 (1.33) | mW | 2015; UMC 90 nm ASIC | RC–Sc–FC [25] | 4-Mod C, n=16; parenthesis normalized to DR | p.11 |
| area-delay-product improvement | 57% | % | 2015; 90 nm CMOS ASIC | [15] | maximum; augmented 3-moduli, DR 4n−1 bits | p.13 |
| area-delay-product improvement | 146% | % | 2015; 90 nm CMOS ASIC | RC–Sc–FC [25] | maximum; 4-Mod C, DR 6n bits | p.13 |
| energy-per-scaling improvement | 64.9% | % | 2015; 90 nm CMOS ASIC | [15] | maximum; augmented 3-moduli | p.13 |
| energy-per-scaling improvement | 263% | % | 2015; 90 nm CMOS ASIC | RC–Sc–FC [25] | maximum; 4-Mod C | p.13 |
errors_and_checks: The formulation provides exact scaling; synthesizable VHDL functionality was thoroughly tested, but no numerical error rate or formal verification coverage is reported. # pp.1,10
conditions: All moduli are pairwise coprime. The generic second-level cost depends on x, m4, and the multiplicative inverse; special m4 values reduce multipliers to bitwise operations. FPGA gains are negligible for low n because LUT implementation and interconnect dominate. ASIC energy estimates assume 20% switching activity and minimum-delay synthesis without manual optimization. # pp.3,8,10-11
evidence: Equations (9)-(43), Sections 3-5, Figs. 2-6, Tables 2-5, and Figs. 7-9, pp.3-13.

## new_families
none

## space_gaps
* `rns_scaling_comparison.method` lacks `hierarchical_crt_mrs`, which is the paper's central exact scaling method. # pp.2-5
* `rns_scaling_comparison` lacks choices for scale factor/moduli-set structure/hierarchy depth. # pp.2-5
* `rns_scaling_comparison` lacks component slots for channel modular adders, end-around-carry CSAs, and the second-level modulo multiplier. # pp.7-9

## open_questions
* Equation (44) defines an improvement ratio greater than 1, while the prose reports improvements of 146% and 263%; the merge pass must not reinterpret these figures as percentage reductions. # pp.10,12-13
* The accepted-manuscript header does not provide the final volume/issue/page metadata. # p.1
