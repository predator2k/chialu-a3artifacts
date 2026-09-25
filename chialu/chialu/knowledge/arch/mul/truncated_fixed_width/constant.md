---
family: truncated_fixed_width
pin: {correction_scheme: constant}
---
# constant

One correction constant, the representable value within the n+k
retained columns closest to the additive inverse of the expected
reduction-plus-rounding error, is added into the kept matrix; its one-
bits enter as extra inputs, converting half adders to full adders, so
no separate correction adder exists. Unrestricted, the constant makes
the average error zero; restricted to the retained columns it bounds
the average error by 2^(-n-k-1).

On FPGAs the free bits of DSP tiles that cross the truncation line
serve as the constant. It is the pick for tree reduction, because a data-dependent correction
can raise the matrix height while a constant never does, and for
faithful results: the total error stays below 2^k, and the array and
Dadda savings are 25% to 35% of a conventional rounded multiplier. It
loses to variable correction when the error distribution must centre
on zero for accumulations, since variable correction costs only n-k-1
more gates, and to the minimum-mean-square and min-max functions when
the retained-column budget must buy the lowest error.

## references

schulte1993 -> M. J. Schulte, E. E. Swartzlander, "Truncated Multiplication with Correction Constant", VLSI Signal Processing VI, pp. 388-396, 1993
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
walters2005 -> E. G. Walters, M. J. Schulte, "Efficient Function Approximation Using Truncated Multipliers and Squarers", 17th IEEE Symposium on Computer Arithmetic (ARITH-17), 2005
