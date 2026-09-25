# operand_rounding: proposed changes to the space

* slots for the three barrel shifters and the summation adder (a Kogge-Stone adder in the reference design) — the instantiated components are open to substitution [zendegani2017]
* `rounding` tie rule for `nearest_pow2`: an operand of the form 3 x 2^(p-2) rounds upward except that three rounds to two — the rule decides the error at the midpoints [zendegani2017]
* choice `sign_handling: {unsigned, exact_negation, approximate_negation}` — selects the U-RoBA, S-RoBA or AS-RoBA hardware and changes cost and accuracy on negative inputs [zendegani2017]
* choice `minus_one_bypass: Bool` — detects an approximate-negation operand of -1 and returns the negated other operand, bounding the 100 percent worst case at added delay and power [zendegani2017]
