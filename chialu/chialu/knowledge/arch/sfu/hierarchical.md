# hierarchical

Piecewise polynomial evaluation over a recursively segmented domain:
an outer level splits the input range into segments that are uniform
or whose sizes grow or shrink by powers of two, each outer segment is
subdivided into its own number of uniform inner segments, and the
coefficient address is formed by leading-zero or leading-one detection
plus a barrel shift for the outer index and by a lookup for the inner
one. ROM0 stores per outer segment the inner address width and the
offset into ROM1, and ROM1 stores the spline coefficients. The outer
scheme is chosen from the histogram variance of a balanced-error
segmentation, and the outer address width is searched for the fewest
segments.

Hierarchy depth trades segment count against cascade depth. Each added
level approaches the minimum segment count of an ideal balanced-error
segmentation with diminishing returns and one more LUT stage on the
path, so the reported implementations stop at two levels. With two
levels the segment counts sit above the balanced-error optimum, 19
against 12 and 80 against 48 for the evaluated degree-2 functions,
but an unsuitable outer scheme costs 63 segments where the selected
one costs 19, and the family needs over 2x fewer segments than uniform
segmentation for ln(1 + x). The per-level scheme fixes where the
segments concentrate; the powers-of-two progressions cover functions
that are steep at one end or in the middle, and uniform inner
segmentation keeps the inner address a plain field.

The accuracy contract is a supplied maximum absolute approximation
error enforced by the segmentation algorithm, and the final datapath
optimization gives faithful rounding with at most 1 ulp output error.
The address logic is cheaper than the comparator network of a
balanced-error segmentation, 33 ns against 67 ns of combinatorial
delay for an 8-bit degree-1 evaluator on a Virtex-II. The family wins
for highly nonlinear functions and tight error requirements, and it
loses ground when a function has several arbitrarily placed
singularities, because the outermost split then needs comparators or
decision-diagram logic that adds area and delay. Execution is
feed-forward.

The library realizes this segmenter inside the segmented-polynomial engine (`chialu/targets/rtl/families/sfu.py`: a coarse split into regions, each subdivided uniformly by its fit error, the index as a region base plus a sub-index).

## references

lee_2009 -> D.-U. Lee, R. C. C. Cheung, W. Luk, J. D. Villasenor, "Hierarchical Segmentation for Hardware Function Evaluation", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 17, no. 1, pp. 103-116, 2009
