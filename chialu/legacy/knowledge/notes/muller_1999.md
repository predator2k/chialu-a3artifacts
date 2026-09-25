---
handle: muller_1999
citation: J.-M. Muller, "A Few Results on Table-Based Methods", Reliable Computing, vol. 5, no. 3, pp. 279-288, 1999
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed24, fixed53]
authority: incremental
pages_read: 279-288 / 10
---

## summary
The paper analyzes table-bound elementary-function evaluation and introduces tripartite/general multipartite table methods based on order-1 Taylor expansions. The paper also presents an order-2 additive-table method and concludes that table-bound methods suit single precision but require excessive memory for double precision.

## families
### direct_lut  (role: analyzes)
mechanism: A straightforward implementation addresses one table with all n input bits and returns the stored function value. The table becomes impractical unless n is very small. # p.279
choices:
new_choices:
  none
slots:
  none
parameters: n-bit fixed-point argument in [1/2, 1) # p.279
results: none
errors_and_checks: none
conditions: The method is usable only when n is very small because table memory grows with n address bits. # p.279
evidence: §1, p.279

### bipartite  (role: analyzes)
mechanism: The bipartite table method splits x into three k-bit parts and approximates f(x) as α(x1,x2)+β(x1,x3). Two table outputs feed one final addition, and leading zero bits of β need not be stored. # pp.280-282
choices:
  symmetric: false # pp.280-281
new_choices:
  input_partition: three k-bit subwords — The address decomposition determines the two table arguments. # pp.280-281
slots:
  none
parameters: k ≈ n/3; 24-bit sine example uses k=9, 25-bit summation, a 25 x 2^17 table, and a 7 x 2^15 table # p.281
results:
| metric | value | unit | technology / device | baseline | condition | page |
| memory size | 428 | Kbytes | UNKNOWN; 1999 | none | straightforward bipartite, 24-bit sine | p.286 |
| error bound | 0.625 x 2^-24 | none | UNKNOWN; 1999 | none | straightforward bipartite, 24-bit sine | p.286 |
| memory size | 244 | Kbytes | UNKNOWN; 1999 | none | Schulte and Stine bipartite, 24-bit sine | p.286 |
errors_and_checks: The general approximation error is bounded by 2^-3k max f"; the 24-bit sine example has approximation error approximately 2^-27 and table-value truncation error less than 2^-25. # p.281
conditions: Symmetry and unequal subword sizes can reduce the tables. # p.281 The method still requires large tables for single precision and is far from implementable for double precision. # p.282
evidence: §2.1, equations (2.1)-(2.3), Figure 1, pp.280-282; Table 1, p.286

### stam  (role: compares)
mechanism: The symmetric table addition method splits x into m possibly unequal subwords and expands around the midpoint selected by the first two subwords. The result is approximated by m-1 table values, with each table addressed by x1 and one other subword. # p.285
choices:
  tables: 3 (four-subword case) / 4 (five-subword case) # p.286
new_choices:
  subword_widths: equal_or_different — The m subwords may have different sizes. # p.285
  expansion_point: interval_midpoint — The Taylor expansion uses the midpoint determined by the first two subwords. # p.285
slots:
  none
parameters: m subwords; m-1 additions/table values; the first two subwords jointly represent approximately half of the input word for approximately 2^-n error # p.285
results:
| metric | value | unit | technology / device | baseline | condition | page |
| memory size | 92 | Kbytes | UNKNOWN; 1999 | none | four-subword method, 24-bit sine | p.286 |
| memory size | 74.5 | Kbytes | UNKNOWN; 1999 | none | five-subword method, 24-bit sine | p.286 |
errors_and_checks: The order-1 Taylor error requires the first two subwords to represent approximately half the input word to obtain error approximately 2^-n. # p.285
conditions: STAM and the multipartite method require similar memory for the compared 24-bit sine implementations. # p.286
evidence: §2.4, pp.285-286; Table 1, p.286

### multipartite  (role: proposes)
mechanism: The order-1 method splits x into 2p+1 k-bit parts and expresses f(x) as p+1 table values obtained from nested approximations of f'. The tripartite case uses five parts, three lookup tables, carry-save addition, and a final addition. The order-2 variant uses eight lookup terms followed by a carry-save tree. # pp.282-287
choices:
  tables: 3 (tripartite) / 4 (seven-subword example) / 8 [outside domain] (order-2 example) # pp.282-287
new_choices:
  approximation_order: {1, 2} — The Taylor order changes table addressing, table count, additions, and memory. # pp.282-287
  input_partition: 2p+1_equal_k_bit_parts — The order-1 generalization uses an odd number of equal-width parts. # pp.283-285
  summation_structure: {carry_save_tree_then_final_add, unspecified} — The tripartite and order-2 examples use carry-save summation. # pp.284,287
slots:
  none
parameters: tripartite uses five k-bit parts and three tables; the fixed53 order-1 example uses 2p+1=7, k=8, and 55-bit final summation; the order-2 example splits x into five k-bit parts and adds eight table terms # pp.282-287
results:
| metric | value | unit | technology / device | baseline | condition | page |
| memory size | 74 | Kbytes | UNKNOWN; 1999 | none | tripartite order-1 method, 24-bit sine | p.286 |
| error bound | 1.38 x 2^-24 | none | UNKNOWN; 1999 | none | tripartite order-1 method, 24-bit sine | p.286 |
| memory size | around 20 | Gbytes | UNKNOWN; 1999 | none | order-1 method, n=53, 2p+1=7, k=8 | p.285 |
| memory size | around 20 | Kbytes | UNKNOWN; 1999 | none | order-2 method, single precision | p.287 |
| memory size | around 100 | Mbytes | UNKNOWN; 1999 | none | order-2 method, double precision | p.287 |
errors_and_checks: The tripartite approximation error is bounded using max f"; the general order-1 error is bounded by p2^(-2p-1)k max f"; the order-2 example has error of order 2^-5k. # pp.283,285,287
conditions: Large p is impractical because the method replaces a few multiplications with many additions. # p.285 Order-1 methods do not appear applicable beyond single precision. # p.285 The order-2 method reduces single-precision memory but still requires around 100 Mbytes for double precision. # p.287
evidence: §§2.2-2.4, equations (2.4)-(2.6), Figure 2, pp.282-286; §3, equation (3.1), pp.286-287; Table 1, p.286

## new_families
none

## space_gaps
* The multipartite `tables` domain ends at 6, but the order-2 method uses eight table terms. # p.287
* The multipartite vocabulary lacks an `approximation_order` choice distinguishing the documented order-1 and order-2 constructions. # pp.282-287
* The bipartite/STAM/multipartite families lack choices for input-subword count and unequal subword sizing, although these choices affect table memory. # pp.281,285

## open_questions
* Table 1 gives no error bound for the Schulte and Stine bipartite/STAM rows, so those bounds remain UNKNOWN.
* The paper does not specify whether Kbytes/Mbytes/Gbytes use decimal or binary multiples.
