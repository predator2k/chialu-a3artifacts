---
handle: karatsuba1962
citation: A. Karatsuba, Yu. Ofman, "Multiplication of Multidigit Numbers on Automata", Doklady Akademii Nauk SSSR, vol. 145, no. 2, pp. 293-294, 1962 (Engl. transl. Soviet Physics-Doklady, vol. 7, pp. 595-596, 1963)
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer]
authority: landmark
pages_read: 2 / 2
---

## summary
The document constructs a binary multiplication automaton with characteristics \(N \sim m^{\log_2 3}\) and \(T \sim \log m\) by reducing multiplication to addition and recursive squaring. The document also analyzes a grouped serial/parallel multiplication scheme parameterized by a group size \(s\).

## families
### recursive_karatsuba  (role: proposes)
mechanism: Multiplication is replaced by addition and squaring through \(ab=[(a+b)^2-(a-b)^2]/4\). Squaring a \(2m\)-digit number is reduced to three \(m\)-digit squarings plus additions and multiplications by powers of two. Recursive application gives the stated automaton-complexity bound. # pp.595-596
choices:
  split_kind: two_way   # p.595
new_choices:
  none
slots:
  none
parameters: two \(m\)-digit binary inputs; \(2m+1\) output sections; each recursive \(2m\)-digit squaring produces three \(m\)-digit squarings   # pp.595-596
results:
| metric | value | unit | technology / device | baseline | condition | page |
| N | \(m^{\log_2 3}\) | UNKNOWN | UNKNOWN; result year 1962 | conventional parallel digit-product method: \(N \sim m^2\) | binary multiplication automaton | p.595 |
| T | \(\log m\) | UNKNOWN | UNKNOWN; result year 1962 | conventional parallel digit-product method: \(T \sim \log_2 m\) | binary multiplication automaton | p.595 |
| recursive subproblem count | 3 | \(m\)-digit squarings | UNKNOWN; result year 1962 | one \(2m\)-digit squaring | additions and power-of-two multiplications are additional operations | p.596 |
errors_and_checks: none
conditions: Division by four presents no great difficulty in the binary number system, while the required additions and power-of-two multiplications are realizable economically using devices from [1]. # pp.595-596 Theorem 2 remains valid for automata without feedback loops. # p.596
evidence: Theorem 2 and multiplication-to-squaring identity on p.595; three-squaring reduction, lemma, and no-feedback statement on p.596.

### serial_serial_parallel  (role: analyzes)
mechanism: The multiplier is divided into groups containing \(s\) places. Products associated with digits inside each group are formed sequentially, while results associated with different groups are added in parallel. The endpoints are the fully parallel conventional method at \(s=1\) and sequential formation with accumulated addition at \(s=m\). # p.595
choices:
  serial_operands: one   # p.595
  digit_size_bits: 1   # p.595
new_choices:
  group_size: \(s,\ 1 \le s \le m\) — number of multiplier places processed sequentially within each parallel group   # p.595
slots:
  none
parameters: \(m\)-digit binary operands; group size \(s\), with \(1 \le s \le m\)   # p.595
results:
| metric | value | unit | technology / device | baseline | condition | page |
| N | \(m^2/s\) | UNKNOWN | UNKNOWN; result year 1962 | none | uniform with respect to \(s\), \(1 \le s \le m\) | p.595 |
| T | \(s\log_2 m\) | UNKNOWN | UNKNOWN; result year 1962 | none | uniform with respect to \(s\), \(1 \le s \le m\) | p.595 |
| N | \(m^2\) | UNKNOWN | UNKNOWN; result year 1962 | none | \(s=1\), conventional parallel digit products | p.595 |
| T | \(\log_2 m\) | UNKNOWN | UNKNOWN; result year 1962 | none | \(s=1\), conventional parallel digit products | p.595 |
| N | \(m\) | UNKNOWN | UNKNOWN; result year 1962 | none | \(s=m\), sequential digit products accumulated by addition | p.595 |
| T | \(m\log m\) | UNKNOWN | UNKNOWN; result year 1962 | none | \(s=m\), sequential digit products accumulated by addition | p.595 |
errors_and_checks: none
conditions: The estimates depend on the addition automaton described in Theorem 2 of [1], whose implementation is not reproduced. # p.595 The no-feedback-loop statement covers the \(s=1\) case rather than every value of \(s\). # p.596
evidence: Theorem 1, formulas (1)-(2), and the grouped multiplier construction on p.595; no-feedback qualification on p.596.

## new_families
none

## space_gaps
* `serial_serial_parallel` lacks a choice for the number or size of independently parallel digit groups; the document varies `group_size` \(s\) from 1 to \(m\). # p.595

## open_questions
* The definitions and physical units of automaton characteristics \(N\) and \(T\) are imported from [1] and are not reproduced. # p.595
* The document does not specify the recursion base case or a fixed recursion depth. # pp.595-596
