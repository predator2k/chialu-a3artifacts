# Task

A Yosys/ABC script for one fixed RTL block (a 32-bit ALU with a 16 x 16
multiplier) under a fixed liberty file and clock. The evaluator runs in
seconds, so the budget is thousands of iterations. An equivalence check of the mapped netlist
against the RTL makes the area number impossible to game. The domain
library is `chirecipe/` beside this file; the PDK descriptors and the
liberty files come from chiALU.
