---
handle: muller_2016#s08
parent: muller_2016
citation: J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
chapter: The CORDIC Algorithm
pdf_pages: 145-168
status: ok
kind: book_chapter
unit_classes: [VEC_SFU]
formats: [binary radix-2, radix-2 signed-digit, carry-save, radix-10, floating-point]
authority: textbook
pages_read: 24 / 24
---

## summary
The chapter defines conventional CORDIC rotation/vectoring and Walther’s unified circular/linear/hyperbolic iteration. It classifies scale-factor compensation, redundant implementations, double/correcting/branching/differential variants, and inverse-trigonometric applications. It gives convergence domains, scale factors, digit-selection bounds, and implementation costs in abstract units.

## families
### cordic  (role: defines)
mechanism: Each iteration updates x/y with additions and shifts by 2^-n and updates z with a precomputed elementary angle. Rotation mode selects d_n from sign(z_n); vectoring mode selects d_n from sign(-y_n). Walther’s generalized recurrence uses m=1, 0, or -1 for circular, linear, or hyperbolic coordinates. Hyperbolic convergence requires repeated iterations at indices 4, 13, 40, and subsequent indices of the stated sequence.
choices:
  mode: both   # p.146, p.149
  coordinate_set: unified   # p.149, p.150
  topology: UNKNOWN   # p.146
  iterations: UNKNOWN   # p.146
  scale_compensation: UNKNOWN   # p.151
  angle_recoding: true for the known-angle variant   # p.168
new_choices:
  scale_compensation_method: input prescaling | merged shift-add factors | altered microangles — methods for removing or absorbing the accumulated similarity factor   # p.146, p.151, p.153
slots:
  none
parameters: d_n ∈ {-1,+1}; m ∈ {1,0,-1}; w_k ∈ {arctan 2^-k, 2^-k, tanh^-1 2^-k}; hyperbolic indices 4, 13, 40, ..., (3^(j+1)-1)/2 are repeated   # p.146, p.149, p.150
results:
| metric | value | unit | technology / device | baseline | condition | page |
| convergence-angle bound | 1.7432866204723400035... | radians | abstract | UNKNOWN | conventional circular rotation | p.146 |
| circular scale factor K | 1.646760258121... | dimensionless | abstract | UNKNOWN | conventional circular iteration | p.146 |
| hyperbolic scale factor K' | 0.82815936096021562707619832... | dimensionless | abstract | UNKNOWN | repeated-index hyperbolic iteration | p.149 |
| hyperbolic rotation bound | 1.1181730155265... | radians | abstract | UNKNOWN | hyperbolic rotation mode | p.149 |
| inverse-function error | close to 2^-n | absolute angle error | abstract | UNKNOWN | double-CORDIC cos^-1/sin^-1 after step n | p.167 |
| transcendental microcode size | about 500 | lines | Intel 8087 / UNKNOWN | UNKNOWN | whole transcendental set | p.168 |
errors_and_checks: The double-CORDIC cos^-1/sin^-1 result has error close to 2^-n; small vectoring-mode inputs can produce large numerical errors, but the cited remedies are not described.   # p.167, p.168
conditions: CORDIC is attractive when one simple shift-and-add algorithm must compute many functions, although the chapter states that it is not the fastest method for multiplication/logarithm/exponential.   # p.145
evidence: Sections 7.2-7.3, 7.8-7.9; Tables 7.1-7.3; Algorithms 11-13.

### redundant_high_radix_cordic  (role: taxonomizes)
mechanism: Redundant signed-digit or carry-save arithmetic accelerates the additions, but allowing d_n=0 makes the scale factor data-dependent. Digit selection uses a truncated residual. Constant-factor variants use double rotations or periodic correcting rotations; another variant computes 1/K concurrently with the CORDIC iterations.
choices:
  residual_arithmetic: signed_digit | carry_save   # p.154, p.155
  radix: 2   # p.154, p.155
  scale_handling: online_scale_computation | double_rotation | correcting_iterations   # p.155, p.156, p.158
  coarse_fine_hybrid: UNKNOWN   # p.153
new_choices:
  digit_set: {-1,0,+1} — permits redundant selection but makes the scale factor variable   # p.153, p.155
  selection_window: first fractional digit | finite digit window — residual digits inspected to choose d_n   # p.154, p.158
slots:
  none
parameters: signed-digit selection truncates 2^n z_n after one fractional digit; carry-save selection uses the same truncation; correcting rotation repeats an extra iteration every arbitrary m steps   # p.154, p.155, p.158
results:
| metric | value | unit | technology / device | baseline | condition | page |
| signed-digit truncation error | ≤ 1/2 | residual units | abstract | UNKNOWN | z_n* versus 2^n z_n | p.154 |
| carry-save truncation error | 0 to 1 | residual units | abstract | UNKNOWN | 2^n z_n minus z_n* | p.155 |
| double-rotation scale factor | 1.3559096738634793803... | dimensionless | abstract | conventional K | circular double rotation | p.156 |
| double-rotation convergence interval half-width | 1.91577691... | radians | abstract | UNKNOWN | interval [-A,+A] | p.156 |
| correcting overhead | 1 extra iteration every m steps | iterations | abstract | UNKNOWN | arbitrary integer m | p.158 |
errors_and_checks: The Robertson-diagram selection intervals guarantee that the next residual remains between -r_(n+1) and r_(n+1).   # p.154, p.155
conditions: Redundant representations make the arithmetic operations quick, while digit selection and the variable scale factor become the principal difficulties.   # p.153, p.155
evidence: Sections 7.4-7.5; Figure 7.2; Tables 7.4; Equations 7.12-7.15.

### redundant_cordic  (role: proposes)
mechanism: Branching CORDIC uses two parallel conventional CORDIC modules when a residual window cannot determine the sign. The modules try d_n=+1 and d_n=-1; a later ambiguous residual identifies the previously correct branch, so two modules suffice regardless of the number of branchings.
choices:
  internal_representation: borrow_save [outside domain]   # p.161
  scale_factor_fix: branching   # p.158
  radix: 2   # p.161
new_choices:
  branch_modules: 2 — number of conventional iterations evaluated in parallel   # p.158, p.159
slots:
  none
parameters: eval(z_n)=0 implies |z_n|≤2^-n+1; signed-digit eval uses a 3-digit reduced value in [-7,+7]   # p.159, p.161
results:
| metric | value | unit | technology / device | baseline | condition | page |
| parallel module count | 2 | CORDIC modules | abstract | 1 conventional module | any number of branchings | p.158, p.159 |
| eval window | 3 | signed digits | abstract | UNKNOWN | radix-2 signed-digit implementation | p.161 |
| residual bound | < 3 × 2^-n+1 | absolute residual | abstract | UNKNOWN | each branch residual | p.159 |
errors_and_checks: At least one branch residual remains within the conventional tail bound; the chapter records a corrected eval bound that replaces the erroneous bound in the original paper.   # p.159
conditions: Branching occurs only when the inspected digit window cannot determine the residual sign.   # p.158
evidence: Section 7.6; Algorithm 8; Equation 7.16.

## taxonomy
* Conventional CORDIC
  * circular
    * rotation mode -> cordic   # p.146, p.150
    * vectoring mode -> cordic   # p.147, p.149, p.150
  * linear
    * rotation mode -> cordic   # p.150
    * vectoring mode -> cordic   # p.150
  * hyperbolic
    * rotation mode -> cordic   # p.149, p.150
    * vectoring mode -> cordic   # p.149, p.150
* Scale-factor compensation
  * merged factors (1+α_i2^-i) -> cordic   # p.151, p.152
  * altered angles arctan(2^-n±2^-m) -> cordic   # p.153
* Redundant CORDIC with variable factor
  * signed-digit implementation -> redundant_high_radix_cordic   # p.154
  * carry-save implementation -> redundant_high_radix_cordic   # p.155
  * on-the-fly K or 1/K -> redundant_high_radix_cordic   # p.155
  * constant-factor methods
    * double rotation -> redundant_high_radix_cordic   # p.156
    * correcting rotation -> redundant_high_radix_cordic   # p.158
    * branching CORDIC -> redundant_cordic   # p.158
    * differential CORDIC -> differential_cordic   # p.162
* Inverse trigonometric applications
  * double-CORDIC cos^-1 -> cordic   # p.165, p.167
  * double-CORDIC sin^-1 -> cordic   # p.167
  * approximate K_n t without double rotations -> cordic   # p.168
* Variations
  * decimal-binary conversion -> cordic   # p.168
  * radix-10 CORDIC -> decimal_cordic_transcendental   # p.168
  * radix-4 CORDIC -> cordic   # p.168
  * very-high-radix rotation -> cordic   # p.168
  * pipelined architectures -> cordic   # p.168
  * dimensions greater than 2 -> cordic   # p.168
  * known-angle recoding -> cordic   # p.168
  * paired iterations -> cordic   # p.168
  * prediction-based CORDIC -> cordic   # p.168
  * online CORDIC -> online_arithmetic_unit   # p.168
  * floating-point CORDIC -> cordic   # p.168

## primary_sources
* Volder, 1959 — introduced CORDIC rotation using shift-and-add steps.   # p.145
* Walther, 1971 — generalized CORDIC to logarithms, exponentials, and square roots.   # p.145, p.149
* Despain, UNKNOWN; Haviland and Tuszinsky, UNKNOWN — merged shift-add scale-factor compensation.   # p.151
* Deprettere, Dewilde, and Udo, UNKNOWN — altered elementary angles to obtain scale factor 1 or 2.   # p.153
* Ercegovac and Lang, UNKNOWN — computed K or 1/K on the fly.   # p.155
* Takagi et al., UNKNOWN; Delosme, UNKNOWN — independently proposed double rotation.   # p.156
* Takagi et al., UNKNOWN — proposed correcting rotation.   # p.158
* Duprat and Muller, UNKNOWN — introduced branching CORDIC.   # p.158
* Phatak, UNKNOWN — corrected and improved branching CORDIC.   # p.158, p.159
* Dawid and Meyr, UNKNOWN — introduced differential CORDIC.   # p.162
* Lang and Antelo, UNKNOWN — computed sin^-1/cos^-1 without double rotations.   # p.168
* Antelo et al., UNKNOWN — proposed radix-4 and very-high-radix CORDIC.   # p.168
* Hu and Naganathan, UNKNOWN — proposed known-angle recoding to reduce iterations.   # p.168

## new_families
### differential_cordic  (domain: redundant: online arithmetic, closest: redundant_cordic, why_not: the existing family lacks differential absolute-residual propagation and digit-pipelined sign generation)
mechanism: Differential CORDIC computes the same ±1 decisions as conventional CORDIC while propagating absolute residuals online in radix-2 signed-digit arithmetic. Each stage subtracts a stored elementary angle without carry propagation, derives the next absolute residual, and updates the direction from its sign. Rotation/vectoring retain the conventional constant scale factor; the method extends directly to hyperbolic mode.
choices: mode: {rotation, vectoring, both}; coordinate_set: {circular, hyperbolic}; residual_representation: {signed_digit, carry_save}; digit_order: {msdf}; restoring_conversion: Bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| residual-stage online delay | 1 | digit time | abstract | UNKNOWN | signed-digit subtraction of arctan 2^-n | p.162 |
| initial sign delay | as large as the word length | digit times | abstract | UNKNOWN | least-significant digit is the only nonzero digit | p.162, p.163 |
evidence: Sections 7.7; Figure 7.4; Algorithms 9-10.

## space_gaps
* cordic lacks a radix choice for the chapter’s radix-4, radix-10, and very-high-radix variants.   # p.168
* cordic lacks scale-compensation values for merged shift-add factors and altered microangles.   # p.151, p.153
* redundant_high_radix_cordic lacks a branching scale-handling value.   # p.158
* cordic lacks function/application choices for cos^-1 and sin^-1 double rotations.   # p.165, p.167

## open_questions
* The chapter does not fix an iteration count, word length, pipeline topology, or finite-precision rounding contract.
* The publication years of most cited primary sources are not present in the supplied chapter text.
