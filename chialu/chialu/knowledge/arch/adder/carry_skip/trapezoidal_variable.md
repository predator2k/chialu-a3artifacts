---
family: carry_skip
pin: {block_sizing: trapezoidal_variable}
---
# trapezoidal_variable

Variable block widths that grow from both ends toward the middle of the
operand: a carry generated near the low end ripples only a short block
before it starts skipping, a carry absorbed near the high end finishes
in a short block, and the middle blocks are wide because a carry
crossing them has already skipped several. Lehman and Burla's 60-bit
example is 4/5/6/7/8/8/7/6/5/4; the one-level optimum places block
columns under a triangle and the two-level optimum under a pyramid of
sections.

The variable profile is the pick over uniform blocks whenever the skip
delay is not negligible against the ripple delay, since it cuts the
worst-case time with no increase in equipment (19 to 15 time units in
the 60-bit example). Oklobdzija and Barnes construct the optimal
symmetric distribution from bounded histogram columns and prove it
optimal for skip-to-ripple ratios from 2 to 7, and Guyot's transf and
transf2 hole-filling algorithms extend it to two levels and to a
quadratic wire-delay model. It loses to dp_optimized sizing when the
delay functions are arbitrary or the arrivals are non-uniform, and it
excludes ones'-complement end-around-carry units, whose wrap-around
breaks the end-to-middle symmetry.

## references

lehman_burla1961 -> M. Lehman, N. Burla, "Skip Techniques for High-Speed Carry-Propagation in Binary Arithmetic Units", IRE Transactions on Electronic Computers, vol. EC-10, pp. 691-698, 1961.
oklobdzija_barnes1985 -> V. G. Oklobdzija, E. R. Barnes, "Some Optimal Schemes for ALU Implementation in VLSI Technology", 7th IEEE Symposium on Computer Arithmetic (ARITH-7), 1985.
guyot1987 -> A. Guyot, B. Hochet, J.-M. Muller, "A Way to Build Efficient Carry-Skip Adders", IEEE Transactions on Computers, vol. C-36, no. 10, 1987.
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
