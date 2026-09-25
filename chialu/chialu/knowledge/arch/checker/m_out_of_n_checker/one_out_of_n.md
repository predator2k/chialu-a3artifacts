---
family: m_out_of_n_checker
pin: {code_class: one_out_of_n}
---
# one_out_of_n

A one-hot validity checker: a switching network indicates whether one
and only one signal is active among the checked output lines, and
the construction expands to any number of lines. It is the m = 1
member of the constant-weight checkers, which the general partition
construction leaves out.

The checker is required where an odd-count check is not enough: a
component-reduced biquinary adder can raise three of its outputs
after a fault, which passes an odd-count checker and fails the
one-and-only-one test. It costs a network over every checked line
rather than a parity tree, so it is the pick for decoded or one-hot
digit encodings and loses to a parity check when the fault model
never raises more than one extra line. The textbook lists 1-out-of-n
as its own applicability class beside k-out-of-2k and arbitrary
m-out-of-n; k_out_of_2k is the sibling for balanced codes and
arbitrary_m_out_of_n for every other weight above one.

The generated checker realizes this variant (`checker.comparator.code_class: one_out_of_n`): every pair (p_i, ~q_i) as a 1-out-of-2 word, merged by the two-rail tree.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
