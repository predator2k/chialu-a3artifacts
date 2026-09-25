---
family: segmented_carry_speculative
pin: {carry_in_scheme: carry_select_speculation}
---
# carry_select_speculation

Each block computes alternative sums or carries and a select unit
picks one from block propagate/generate signals or a short predictor:
ETAIV runs Type I and Type II X-bit carry generators concurrently and
a 2-to-1 mux driven by the Type I output selects the carry into the
most-significant sum block, and BCSA gives each l-bit block a
sub-adder, a carry predictor reading the current and next blocks, and
a Select unit choosing between the speculated carry and the preceding
sub-adder's carry-out.

The worst-case carry path spans two blocks and the average path is
close to one, so accuracy exceeds propagate_window at the same block
width: CSA is the most accurate of the equivalent designs, and CSA
with k above 3 reaches an error rate below 0.5 per cent. The cost is
duplicated hardware, since carry-select designs tend to need more
power and area than segmented designs; BCSA costs 5 to 7 per cent
delay and 4 to 5 per cent energy over GeAr but cuts EDP by 13 to 68
per cent against an exact CLA in 15nm FinFET. The sub_adder can be
ripple_carry, carry_lookahead or a Kogge-Stone parallel_prefix. It is
the pick for high-accuracy use where a plain window errs too often
and the duplicated paths fit the budget.

## references

ebrahimi2020 -> F. Ebrahimi-Azandaryani, O. Akbari, M. Kamal, A. Afzali-Kusha, M. Pedram, "Block-Based Carry Speculative Approximate Adder for Energy-Efficient Applications", IEEE Transactions on Circuits and Systems II, vol. 67, no. 1, pp. 137-141, 2020
jiang2017 -> H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
