# dynamic_segment

Multiply only a k-bit window of each operand located at its leading
one: leading-one detectors find each operand's most significant 1,
that bit with the next k-2 bits and an inserted 1 standing in for the
expected value of the discarded low portion form a k-bit segment, a k
x k exact core multiplies the two segments, and a barrel shifter
restores the product's scale by the sum of the two segment positions.
Static selection instead picks the segment from two or three fixed
positions with OR-gate detection and multiplexers; the rounded form
factors each operand as 2^k X, truncates and rounds X-1 to short odd
midpoints, and adds the cross terms instead of full partial products.

The segment width is the accuracy knob: at n = 16 the maximum error
falls from 26.56% at k = 4 to 1.54% at k = 8, and the k = 6 design
saves 70% area and 71% power against an accurate Wallace tree in an
industrial 65-nm library. Savings grow with operand width, because k
stays fixed while the steering logic grows as O(n log n) and the
arithmetic as O(k^2). Segment selection trades accuracy against
steering cost: following the leading one is more accurate than a static
partition, but the detectors, multiplexers and barrel shifter can
dominate the reduced core at small widths, whereas static selection's
auxiliary logic scales linearly with the segment width, needs the
segment to be at least half the operand, and gains a third position when
it is exactly half. The rounded form's accuracy depends strongly on the
rounding width and weakly on operand width, so its core stays unchanged
as operands widen. The segment width is fixed per circuit variant in
every reported design, and the runtime knob is a mutation the space
exposes.

Unbiasing decides the error contract. Forcing the last retained bit to
1 compensates the otherwise negative error, so the result error is
near-zero-mean with a Gaussian fit, and rounding to odd midpoints gives
near-zero mean relative error with an almost normal distribution;
unbiased errors suit accumulative operations. Analytical maximum and
expected errors are functions of n and k, there is no runtime detection
or correction, and the family belongs to error-tolerant signal
processing, vision and classification workloads. The core slot may hold
an exact tree or a logarithmic multiplier fed by the window. Signed
operation adds two's-complement pre- and post-processing, which costs
part of the saving. Against plain truncation the window keeps the
magnitude-carrying bits, so a static 10-bit segment passes the
perceptual threshold where an 8-bit truncated multiplier degrades every
tested application. Execution is feed-forward.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/approx.py`: a `segment_width` window at each operand's leading one (or fixed at the top), rounded or truncated, unbiased by the forced lsb, a rounding correction or the cascade fill, the exact small product when both operands fit the window, the window product through the `core_multiplier` family shifted back); the ArithmeticError gate governs.

## design choices

### unbiasing

| member | what it selects |
| --- | --- |
| `none` | the truncated window is used as it is. |
| `lsb_set_to_one` | the window's lowest kept bit is forced to one, which centres the error. |
| `round_and_correct` | the window is rounded and a correction term is added. |
| `poc_cascade_fill` | the positions below the window are filled by the cascade of the leading-one detector's output. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| a window of each operand is selected at runtime and multiplied | - | `a \d+-bit window per operand` |

## references

hashemi2015 -> S. Hashemi, R. I. Bahar, S. Reda, "DRUM: A Dynamic Range Unbiased Multiplier for Approximate Applications", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), 2015
narayanamoorthy2015 -> S. Narayanamoorthy, H. A. Moghaddam, Z. Liu, T. Park, N. S. Kim, "Energy-Efficient Approximate Multiplication for Digital Signal Processing and Classification Applications", IEEE Transactions on VLSI Systems, vol. 23, no. 6, pp. 1180-1184, 2015
vahdat2019 -> S. Vahdat, M. Kamal, A. Afzali-Kusha, M. Pedram, "TOSAM: An Energy-Efficient Truncation- and Rounding-Based Scalable Approximate Multiplier", IEEE Transactions on VLSI Systems, vol. 27, no. 5, pp. 1161-1173, 2019
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
yin2021 -> P. Yin, C. Wang, H. Waris, W. Liu, Y. Han, F. Lombardi, "Design and Analysis of Energy-Efficient Dynamic Range Approximate Logarithmic Multipliers for Machine Learning", IEEE Transactions on Sustainable Computing, vol. 6, no. 4, pp. 612-625, 2021
