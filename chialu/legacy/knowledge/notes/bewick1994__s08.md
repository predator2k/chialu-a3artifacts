---
handle: bewick1994#s08
parent: bewick1994
citation: G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
chapter: Sign Extension in Booth Multipliers
pdf_pages: 152-157
status: ok
kind: thesis_chapter
unit_classes: [BINARY_ALU]
formats: [unsigned binary, two's-complement signed binary]
authority: thesis
pages_read: 6 / 6
---

## summary
The appendix derives compact sign-extension constants for unsigned and two's-complement signed Booth multipliers. The unsigned construction replaces leading sign strings with conditional bits and reduces the maximum dot-diagram height by one, while the signed construction eliminates one partial product and changes the clearing condition.   # p.152, p.154-p.157

## families
### booth_recoded_parallel  (role: defines)
mechanism: The construction assumes that every negated partial product has complemented data and leading zeroes, plus a 1 at its least-significant bit. The leading-one triangle is summed into fixed constants, and conditional S terms clear those constants for positive partial products. Signed multiplication sign-extends the multiplicand before complementing it and uses an EXCLUSIVE-NOR of the multiplicand sign and the high-order selection bit to control clearing.
choices:
  booth_radix: 2 [outside domain]   # p.152
  hard_multiple_gen: UNKNOWN   # p.153
  sign_extension: prevention_constant   # p.154
  negative_pp_encoding: ones_complement_plus_neg_bit   # p.152
new_choices:
  operand_interpretation: {unsigned, twos_complement_signed} — selects the unsigned or signed sign-extension rules   # p.152, p.156
  most_significant_partial_product: {zero_padded_positive, eliminated_after_multiplier_sign_extension} — unsigned multiplication pads the multiplier with two zeroes, while signed multiplication removes that partial product   # p.152, p.156
  sign_extension_clear_control: {selection_high_bit, multiplicand_sign_xnor_selection_high_bit} — signed multiplication includes the multiplicand sign in the clearing condition   # p.154, p.156
slots:
  reduction: UNKNOWN   # p.155
  hard_multiple_adder: UNKNOWN   # p.153
parameters: 16x16 bits; non-bottom unsigned partial products are 17 bits and the bottom partial product is 16 bits   # p.152
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum dot-diagram height reduction | 1 | item in a column | abstract | Figure A.4 | combine the top partial product's S term with its two leading ones | p.154 |
| signed partial-product reduction | 1 | partial product | abstract | unsigned 16x16 example | sign-extend the multiplier into the selection bits and omit the unsigned positive-result partial product | p.156 |
errors_and_checks: The summed sign-extension construction is exactly equivalent to explicit two's-complement leading-one strings; no accuracy or fault-checking result is stated.   # p.154
conditions: The worked construction applies to a 16x16 unsigned Booth 2 example and is stated to be adaptable to higher Booth algorithms and redundant Booth partial-product generation.   # p.152
conditions: The unsigned bottom partial product remains positive because two zeroes pad the multiplier.   # p.152
conditions: Signed multiplication clears leading ones when the multiplicand sign and the selected multiple's sign produce a positive partial product.   # p.156
evidence: Sections A.1, A.1.1, and A.2; Figures A.1-A.6   # p.152-p.157

## taxonomy
* Sign Extension in Booth Multipliers   # p.152
  * Sign Extension for Unsigned Multiplication   # p.152
    * positive partial products -> booth_recoded_parallel   # p.153
    * negative partial products -> booth_recoded_parallel   # p.153
    * negative partial products with summed sign extension -> booth_recoded_parallel   # p.154
    * complete Booth 2 multiplication with conditional S terms -> booth_recoded_parallel   # p.155
    * complete Booth 2 multiplication with height reduction -> booth_recoded_parallel   # p.155
  * Signed Multiplication   # p.156
    * two's-complement signed multiplication with multiplier sign extension, multiplicand sign extension, and EXCLUSIVE-NOR clearing control -> booth_recoded_parallel   # p.156-p.157

## primary_sources
none

## new_families
none

## space_gaps
* `booth_recoded_parallel.booth_radix` lacks the chapter's printed `Booth 2` value.   # p.152
* `booth_recoded_parallel` lacks an unsigned/signed operand-interpretation choice that governs the most-significant partial product and sign-clearing logic.   # p.152, p.156
* `booth_recoded_parallel` lacks a choice for the conditional logic that clears compacted sign-extension constants.   # p.154, p.156

## open_questions
* The chapter does not state whether its term `Booth 2` corresponds to the vocabulary's radix numbering, so the merge pass must not reinterpret the printed value.   # p.152
* The chapter states that the technique adapts to higher Booth algorithms and redundant Booth generation but does not give those constants or configurations.   # p.152
* The chapter does not identify the reduction-tree family or the circuit used to generate hard multiples.   # p.153, p.155
