---
family: carry_lookahead
pin: {intergroup_carry: lookahead}
---
# lookahead

Full lookahead above the groups: the group generate/propagate signals
feed a global network that produces every group carry directly from
the carry-in, and a further level combines sections or supergroups,
so no carry ripples between blocks at any level. The 64-bit ECL
example uses sixteen uniform 4-bit groups and a two-stage global
network for a critical path of 4 NOR and 1 XOR stages; the Model 91
and ILLIAC IV adders stack three levels of 4-bit groups.

Between-group lookahead is the fastest intergroup option and speeds
every input-to-output path, so it is the pick whenever the adder sets
the cycle and the technology's fan-in and fan-out allow one more
level; a 50-bit full lookahead adder takes 12 logical levels against
100 for ripple. Its cost is that each level is bounded by gate
fan-in (4 inputs and 5-output wire-OR in the ECL design) and that
the late global carry needs a fast path through the output stage.
Rippling the group carries is the choice when lookahead cells must
stay independent, and a carry-select stage is the choice when
precomputed upper sums are cheaper than one more lookahead level.

## references

bewick1994 -> G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
anderson1967 -> S. F. Anderson, J. G. Earle, R. E. Goldschmidt, D. M. Powers, "The IBM System/360 Model 91: Floating-Point Execution Unit", IBM Journal of Research and Development, vol. 11, no. 1, pp. 34-53, 1967
davis_1969 -> R. L. Davis, "The ILLIAC IV Processing Element", IEEE Transactions on Computers, vol. C-18, no. 9, pp. 800-816, 1969
macsorley1961 -> O. L. MacSorley, "High-Speed Arithmetic in Binary Computers", Proceedings of the IRE, vol. 49, no. 1, pp. 67-91, 1961
langdon_tang_1970 -> G. G. Langdon, C. K. Tang, "Concurrent Error Detection for Group Look-ahead Binary Adders", IBM Journal of Research and Development, vol. 14, no. 5, pp. 563-573, 1970
