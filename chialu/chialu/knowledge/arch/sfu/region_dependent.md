# region_dependent

Function evaluation whose approximation method is chosen per input
region: a comparison of the argument against stored thresholds routes
it either to a table-free polynomial in the small-argument region,
where one polynomial meets the required accuracy, or to the
accurate-table construction outside it, where a nearby accurate
table value carries the result; the logarithm routines route the
near-one interval to a dedicated procedure and every other input to
exponent/significand reduction followed by the table-driven
procedure. The region count fixes how many methods and thresholds
exist, and the segmenter slot names how the boundaries are decoded.

The region count trades thresholds and separate error budgets
against the reach of each method: the verified libraries use two
regions per routine with function-specific boundaries (sin at
41.5/256, cos at 31.5/256, tan at 15.5/256, arctan at 1/16, sinh at
0.16, cosh at 0.12, and the logarithm near-one interval between
e^-1/16 and e^1/16), and every added region is another method with
its own approximation error to certify. The segmenter in these
libraries is an exact comparison against stored IEEE constants,
which is cheaper than any decoded segmentation, and the exceptional
NaN, infinity, zero and domain cases are resolved before the region
is selected.

The family wins where a function has a region that a single table
or polynomial cannot cover economically, such as the logarithm near
one or the trigonometric functions at small arguments, and it keeps
the accurate-table construction for the rest of the domain; the
small-argument polynomials reach a relative error below 6e-20 for
tan and 6.2e-20 for arctan on the RT-PC. Its cost is the comparison
and the duplicated evaluation paths, so a function that one method
covers over the whole reduced domain picks a single table-and-
polynomial family instead. The evaluation is feed-forward: one
comparison, one selected path.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: `regions` regions, each with the lowest polynomial degree that meets the target). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family region_dependent --pins k=v,...` emits the module with its modeled error for a rewrite.

## references

gal_1991 -> S. Gal, B. Bachelis, "An Accurate Elementary Mathematical Library for the IEEE Floating Point Standard", ACM Transactions on Mathematical Software, vol. 17, no. 1, pp. 26-45, 1991
tang_1990 -> P. T. P. Tang, "Table-Driven Implementation of the Logarithm Function in IEEE Floating-Point Arithmetic", ACM Transactions on Mathematical Software, vol. 16, no. 4, pp. 378-400, 1990
