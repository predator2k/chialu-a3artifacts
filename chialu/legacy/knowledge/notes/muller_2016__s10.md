---
handle: muller_2016#s10
parent: muller_2016
citation: J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
chapter: Range Reduction
pdf_pages: 183-201
status: ok
kind: book_chapter
unit_classes: [VEC_SFU]
formats: [radix-2 fixed-point, radix-2 floating-point, radix-10 floating-point, IEEE-754 single-precision, IEEE-754 double-precision]
authority: textbook
pages_read: 19 / 19
---

## summary
The chapter defines additive and multiplicative range reduction, then concentrates on accurate additive reduction for elementary functions. It classifies Cody–Waite, Payne–Hanek, modular, and table-augmented methods and derives worst-case/error bounds that determine the required internal precision. It also describes multiplier-like architectures for modular reduction and their hardware-sharing options.

## families
### range_reduction  (role: taxonomizes)
mechanism: Additive reduction computes x* = x − kC, while multiplicative reduction computes x* = x/C^k. Cody–Waite splits C into exactly representable terms; Payne–Hanek multiplies the input mantissa by only the exponent-selected middle bits of 4/π; modular range reduction replaces powers of two by small congruent residues modulo C and performs a short second reduction. Continued fractions identify the smallest possible reduced arguments and therefore the precision required for accurate reduction.   # p.183, p.187-200
choices:
  method: [cody_waite (p.187), payne_hanek (p.194), modular_mrr (p.197), table_augmented (p.201)]
  split_constant_terms: [2 (p.188), 3 (p.188)]
  reduction_type: [additive (p.183), multiplicative (p.183)]
  worst_case_bound_proven: true   # p.189-193
new_choices:
  reduction_interval: symmetrical | positive — selects [−C/2−ε,+C/2+ε] or [−ε,C+ε]   # p.197
  redundant_reduction: true | false — permits multiple valid pairs (x*,k) when ε > 0   # p.197
  reduced_argument_representation: wider_format | multiple_machine_numbers — preserves information lost through cancellation   # p.185
  constant_term_storage: combined | separate_terms — separate terms avoid accuracy loss in the second subtraction   # p.188
  input_form: fixed_point | floating_point — selects the residue indexing and error bound   # p.198, p.200
  first_reduction_accumulation: redundant_number_system | adder_tree | both — structures the modular residue sum   # p.200
  operand_recoding: none | booth | modified_booth — reduces the number of first-reduction terms   # p.201
slots:
  none
parameters: Cody–Waite single precision uses C1 = 201/64 = 3.140625 and C2 = 9.67653589793 × 10−4 for C = π; double precision uses C1 = 3217/1024 = 3.1416015625 and C2 = −8.908910206761537356617 × 10−6   # p.188
results:
| metric | value | unit | technology / device | baseline | condition | page |
| required reduction precision | m significant radix-r digits with absolute error less than r^(−m−log_r(ε)) | radix-r digits | abstract | exact reduced argument | worst-case reduced magnitude ε | p.193 |
| worst-case guard digits | 29.2 | radix-2 digits | abstract | none | r=2, n=24, C=π/2, emax=127; worst case 16367173 × 2^+72 | p.193 |
| worst-case guard digits | 30.2 | radix-2 digits | abstract | none | r=2, n=24, C=π/4, emax=127; worst case 16367173 × 2^+71 | p.193 |
| worst-case guard digits | 31.6 | radix-2 digits | abstract | none | r=2, n=24, C=ln(2), emax=127; worst case 8885060 × 2^−11 | p.193 |
| worst-case guard digits | 28.4 | radix-2 digits | abstract | none | r=2, n=24, C=ln(10), emax=127; worst case 9054133 × 2^−18 | p.193 |
| worst-case guard digits | 11.7 | radix-10 digits | abstract | none | r=10, n=10, C=π/2, emax=99; worst case 8248251512 × 10^−6 | p.193 |
| worst-case guard digits | 11.9 | radix-10 digits | abstract | none | r=10, n=10, C=π/4, emax=99; worst case 4124125756 × 10^−6 | p.193 |
| worst-case guard digits | 11.7 | radix-10 digits | abstract | none | r=10, n=10, C=ln(10), emax=99; worst case 7908257897 × 10^+30 | p.193 |
| worst-case guard digits | 60.9 | radix-2 digits | abstract | none | r=2, n=53, C=π/2, emax=1023; worst case 6381956970095103 × 2^+797 | p.193 |
| worst-case guard digits | 61.9 | radix-2 digits | abstract | none | r=2, n=53, C=π/4, emax=1023; worst case 6381956970095103 × 2^+796 | p.193 |
| worst-case guard digits | 66.8 | radix-2 digits | abstract | none | r=2, n=53, C=ln(2), emax=1023; worst case 5261692873635770 × 2^+499 | p.193 |
| worst-case guard digits | 122.79 | radix-2 digits | abstract | none | r=2, n=113, C=π/2, emax=1024; worst case 614799 · · · 1953734 × 2^+797 | p.193 |
| direct Payne–Hanek example accuracy | 8 | significant bits | abstract | exact sin(x) | 16-bit mantissa, x=1.011000000000000 × 2^4 | p.194 |
| Payne–Hanek middle precision | p = j + m − n | bits | abstract | exact reduction | −log2(ε) < j and at least m significant result bits | p.196 |
| Payne–Hanek approximation | 0.732303330876108523957991 · · · | value | abstract | sin(x)=0.732303330876108523957972 · · · | x=1.1₂ × 2^200, n=53, p=20 | p.196 |
| Payne–Hanek worst-case approximation | −4.68692219155 · · · × 10^−19 | value | abstract | cos(x)=−4.68716592425462761112 · · · × 10^−19 | worst-case double-precision input, p=20 | p.197 |
| Payne–Hanek improved approximation | −4.6871659242546274384634 · · · × 10^−19 | value | abstract | cos(x)=−4.68716592425462761112 · · · × 10^−19 | same input, p=60 | p.197 |
| modular first-reduction terms | at most N − ν + 1 | terms | abstract | none | fixed-point input below 2^N | p.198 |
| modular first-reduction range | [−(N−ν+2)C/2, +(N−ν+2)C/2] | value interval | abstract | none | fixed-point reduction | p.198 |
| modular second-reduction width | floor(log2((N−ν+2)C/2)) + ceil(−log2(ε)) | bits | abstract | none | truncated intermediate r̂ | p.198 |
| fixed-point absolute error bound | 2^(−q−1)(N−ν+1) | absolute error | abstract | exact reduced argument | residues and kC stored with q fractional bits | p.199 |
| fixed-point storage precision | p + ceil(log2(N−ν+1)) | fractional bits | abstract | p-bit input accuracy | modular reduction | p.199 |
| example first-reduction cost | 19 | terms | abstract | none | N=20, ν=2, C=π | p.199 |
| example second-reduction table address | 8 | address bits | abstract | none | C=π, ε=0.172 · · · > 2^−3, r∈[−10π,+10π] | p.199 |
| floating-point absolute error bound | (n+1)2^(−q−1) | absolute error | abstract | exact reduced argument | residues and kC stored with q fractional bits | p.200 |
| floating-point storage precision | q = j + t − 1 + ceil(log2(n+1)) | fractional bits | abstract | t significant result bits | −log2(ε) < j | p.200 |
| recoded first-reduction terms | halved | terms | abstract | unrecoded modular reduction | Booth or modified Booth representation | p.201 |
| alternate high-radix decomposition | eight 8-bit parts | parts | abstract | Cody–Waite for small and Payne–Hanek for very large arguments | arguments of reasonable size | p.201 |
errors_and_checks: The reduced argument generally requires a wider format or several machine numbers. Naive subtraction may lose almost all accuracy near a multiple of C. Continued-fraction worst cases determine guard precision; Payne–Hanek bounds discarded right-hand bits by 2^(−n−p); modular reduction gives explicit fixed-point and floating-point absolute-error bounds.   # p.185, p.187, p.192-193, p.196, p.199-200
conditions: Multiplicative reduction is straightforward and errorless when C is a power of the number-system radix.   # p.185
  Cody–Waite is inexpensive but is restricted to small arguments when last-bit accuracy is required for every input.   # p.187-188
  Payne–Hanek remains accurate and efficient for large arguments, but p must cover the worst-case loss.   # p.196-197
  Modular reduction requires a convergence interval longer than C for redundant reduction; ordinary CORDIC and enlarged polynomial/rational domains can provide that interval.   # p.197
  Modular reduction can share hardware with multiplication, which can save silicon area.   # p.200-201
  The table-augmented high-radix method targets reasonable-size arguments between the Cody–Waite and Payne–Hanek ranges.   # p.201
evidence: Sections 9.1-9.6; Tables 9.1-9.3; Figure 9.1; Examples 9-13; Equations 9.2-9.8.

## taxonomy
* Range reduction   # p.183
  * Additive reduction   # p.183
    * Naive machine-precision subtraction -> range_reduction   # p.187
    * Multiple-precision evaluation -> range_reduction   # p.187
    * Split-constant reduction   # p.187-188
      * Two constants -> range_reduction [method=cody_waite, split_constant_terms=2]   # p.188
      * Three constants -> range_reduction [method=cody_waite, split_constant_terms=3]   # p.188
      * Three constants with double-double arithmetic and 64-bit k -> range_reduction [method=cody_waite, split_constant_terms=3]   # p.188
    * Middle-bit product reduction -> range_reduction [method=payne_hanek]   # p.194-197
    * Modular range reduction -> range_reduction [method=modular_mrr]   # p.197-201
      * Fixed-point reduction -> range_reduction   # p.198-200
      * Floating-point reduction -> range_reduction   # p.200
      * Redundant-number/adder-tree architecture -> range_reduction   # p.200
      * Booth-recoded architecture -> range_reduction   # p.201
      * On-the-fly modular reduction -> range_reduction   # p.201
    * High-radix table reduction -> range_reduction [method=table_augmented]   # p.201
    * Fused-multiply-add-assisted design conditions -> range_reduction   # p.201
  * Multiplicative reduction -> range_reduction [reduction_type=multiplicative]   # p.183, p.185

## primary_sources
* Cody and Waite, year UNKNOWN — split-constant range reduction   # p.187-188
* Kahan, year UNKNOWN — continued-fraction search for worst range-reduction cases   # p.192
* Smith, year UNKNOWN — independently found a similar worst-case method   # p.192
* Payne and Hanek, year UNKNOWN — middle-bit accurate range-reduction algorithm   # p.194
* Daumas et al., year UNKNOWN — modular range-reduction algorithm   # p.197
* Gal and Bachelis, year UNKNOWN — split-constant reduction with terms kept separate   # p.188
* Tang, year UNKNOWN — table-driven exponential reduction with C=ln(2)/32 and separated terms   # p.184, p.188
* Lefèvre and Muller, year UNKNOWN — on-the-fly modular range reduction   # p.201
* Defour, Kornerup, Muller and Revol, year UNKNOWN — high-radix table reduction for reasonable-size arguments   # p.201
* Li, Boldo and Daumas, year UNKNOWN — range-reduction design conditions with fused multiply-add   # p.201

## new_families
none

## space_gaps
* The method domain lacks naive_machine_precision and multiple_precision values.   # p.187
* The method domain lacks separated_split_constants for the Gal–Bachelis/Tang variant.   # p.188
* The method domain lacks on_the_fly_modular and high_radix_modular values.   # p.201
* The family lacks choices for symmetrical/positive intervals and redundant reduction.   # p.197
* The family lacks an accumulation slot for redundant adders, adder trees, or multiplier-shared hardware.   # p.200-201
* The family lacks a Booth-recoding choice for modular first reduction.   # p.201

## open_questions
* Publication years for sources cited only by bibliography numbers are not present in the chapter text.
* The magnitude boundaries between CRLIBM’s four reduction methods are not specified.   # p.188
* The high-radix table method’s accuracy bound and table sizes beyond eight 8-bit input parts are not specified.   # p.201
* The fused-multiply-add design conditions are attributed but not stated.   # p.201
