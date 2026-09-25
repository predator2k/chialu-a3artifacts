---
family: pp_perforation
pin: {correction: error_correction_vector}
---
# error_correction_vector

Exact recovery on demand for the underdesigned multiplier: a decoder
inspects the input vector for the operand-group patterns that make a
2x2 block err, derives the total error amount those patterns
contribute, and a residual adder adds that amount to the inexact
product, so the same datapath has an accurate mode beside its
inaccurate mode.

It is the pick where an error-intolerant mode must share silicon with
the approximate one: the extension costs about 5 to 10 percent area on
average across 2- to 16-bit widths, up to about 14 percent, and a
similar power overhead in inaccurate mode in 45 nm, and accurate mode
runs at 0.85 times the original frequency. Against `none` it gives up
part of the power saving the underdesigned cells bought; against the
operand-swap corrections of row perforation it restores exactness
rather than only lowering the mean error. Error-intolerant
applications require it, and error-tolerant ones leave it out.

## references

kulkarni2011 -> P. Kulkarni, P. Gupta, M. Ercegovac, "Trading Accuracy for Power with an Underdesigned Multiplier Architecture", 24th International Conference on VLSI Design, pp. 346-351, 2011
mittal2016 -> S. Mittal, "A Survey of Techniques for Approximate Computing", ACM Computing Surveys, vol. 48, no. 4, 2016
