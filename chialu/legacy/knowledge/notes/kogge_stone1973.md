---
handle: kogge_stone1973
citation: P. M. Kogge, H. S. Stone, "A Parallel Algorithm for the Efficient Solution of a General Class of Recurrence Equations", IEEE Transactions on Computers, vol. C-22, pp. 786-793, 1973.
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: []
authority: landmark
pages_read: 786-793 / 8
---

## summary
The document presents recursive doubling for computing every element of a class of recurrence equations in time proportional to \(\lceil\log_2 N\rceil\) with \(N\)-fold parallelism (pp.786-790). The document applies the algorithm to linear recurrences, polynomial evaluation, minimum/maximum reduction, matrix recurrences, and converted higher-order recurrences, but it does not describe an adder circuit (pp.790-792).

## families
### parallel_prefix  (role: proposes)
mechanism: Algorithm A stores one \(A(i)\)/\(B(i)\) pair per processor and recursively combines each pair with the pair \(2^{k-1}\) positions earlier. Each stage doubles the covered interval. The recurrence has the form \(x_i=f(b_i,g(a_i,x_{i-1}))\), where \(f\) is associative, \(g\) distributes over \(f\), and \(g\) is semiassociative through \(h\). After \(\lceil\log_2 N\rceil\) stages, every \(B(i)\) contains \(x_i\). The paper presents this as a general parallel recurrence algorithm rather than a carry-propagate adder topology. (pp.788-790, 792)
choices:
new_choices:
  none
slots:
  none
parameters: Sequence length \(N\); \(p\geq N\) processors in the main model; \(\lceil\log_2 N\rceil\) recursion steps; distance \(2^{k-1}\) at step \(k\); \(N/m\) processors for the grouped \(m\)th-order formulation after setup. (pp.787, 790-792)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| parallel computation time | proportional to \(\lceil\log_2 N\rceil\) | time | UNKNOWN; 1973 | serial computation proportional to \(N\) | \(N\)-fold parallelism | p.786 |
| recursion iterations | exactly \(\lceil\log_2 N\rceil\) | iterations | UNKNOWN; 1973 | UNKNOWN | Algorithm A computes all \(x_1,\ldots,x_N\) | p.792 |
| processor count after higher-order grouping | \(N/m\) | processors | UNKNOWN; 1973 | \(N\) processors for the direct state-vector formulation | \(m\) recurrence steps are grouped after initial setup | p.791 |
errors_and_checks: none
conditions: The machine has identical processors with local memories, a single instruction stream, masking, and communication between every processor pair; the communication method may change computational complexity (p.787). The algorithm requires associative \(f\), distributivity of \(g\) over \(f\), and a semiassociative \(g\) represented through \(h\) (pp.788-789). The constant hidden by the \(\lceil\log_2 N\rceil\) bound depends on the evaluation costs of \(f\), \(g\), and \(h\) (pp.791-792). When \(p<N\), the algorithm processes \(p\) sequence elements at a time (p.787). The document does not instantiate binary generate/propagate equations or identify an adder topology (pp.786-793).
evidence: Algorithm A and (9)-(10), pp.789-790; Figs. 1-3 and Table I, pp.788-790; applications in Table II, pp.790-791; higher-order reformulation (11)-(17), pp.790-791; correctness theorem and corollary, p.792.

## new_families
none

## space_gaps
* The `parallel_prefix` vocabulary has no choice for the operator requirements \(f\) associative, \(g\) distributive over \(f\), and \(g\) semiassociative through \(h\), which determine whether recursive doubling applies (pp.788-789).
* The `parallel_prefix` vocabulary has no choice for the processor communication/routing model, although the document states that data exchange can affect computational complexity (pp.787, 790).

## open_questions
* The document does not establish that its computation graph is the adder topology later named `kogge_stone`, so `topology: kogge_stone` must not be assigned from this document alone.
* The document leaves the cost of interprocessor communication for a future report (p.787).
