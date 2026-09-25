---
family: approximate_compressor
pin: {technique: configurable_error_recovery}
---
# configurable_error_recovery

An approximate partial-product tree with error recovery:
preprocessing replaces each operand-bit pair by its OR and AND terms,
each approximate adder cell cuts its carry chain after one
neighbouring position and emits a sum bit and an error bit, the cells
form a tree of ceil(log2 n) layers, OR gates accumulate the error
vectors approximately, and an accurate adder adds a selectable number
of most-significant error bits to the tree output; that count sets
accuracy against complexity.

Recovery is what separates the scheme from an inexact compressor
tree: the error is non-negative and the approximate sum never
exceeds the accurate sum, so adding back 6 or 7 error MSBs cuts NMED
and MRED sharply, after which returns flatten, while the error rate
stays high, about 20 percent at 12 recovered bits. With 10
recovered MSBs the 8 by 8 multiplier reaches 0.20 percent NMED and
0.62 percent MRED against 2.85 and 25.21 for the error-tolerant
multiplier baseline. The tree delay falls from 12 to 7 gate delays at
n = 8 and from 30 to 13 at n = 64 against Wallace or Dadda, and a 16
by 16 unit in 28 nm is 20 percent faster with 48 to 69 percent power
saving. It is the pick when a tunable mean error with a final
accurate adder is acceptable; no maximum-error bound is reported.

## references

liu2014 -> C. Liu, J. Han, F. Lombardi, "A Low-Power, High-Performance Approximate Multiplier with Configurable Partial Error Recovery", Design, Automation and Test in Europe (DATE), 2014
