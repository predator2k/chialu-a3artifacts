# approximate_truncated

An n-bit addition split into an h-bit accurate upper part and a k-bit
lower part that is computed inexactly: the upper adder is any exact
adder, and the lower scheme decides what the k least-significant bits
produce. In the nonzeroing-truncation form the truncated operand bits
are forced to complementary constants (A_i = NOT B_i), which makes the
summed truncation error zero-mean; AND/OR input buffers under control
signals force every truncated ripple stage to inputs 0 and 1, so its
carry is 0 and its switching activity is suppressed, while conventional
full adders remain at every bit position and the exact/approximate
boundary stays configurable at run time.

The lower part width is the energy/quality knob: widening the exact
part moves the design back toward the exact adder, and at k = 8 of 16
bits the truncated adder takes about half the energy of the exact
16-bit adder in 28-nm FDSOI, for about 1% delay and 4.5% area spent on
the input buffers. The lower scheme trades lower-part logic against
error statistics: forcing constants spends no logic in the lower bits,
and complementary constants cut mean error distance by 60 to 67% and
lift PSNR by 6.7 to 8.5 dB over zeroing truncation at the same k. A
correction stage buys accuracy back with added stages, and the upper
adder slot sets the delay of the exact part.

The family belongs to error-tolerant multimedia, machine-learning, DSP
and wireless contexts only, and the ArithmeticError gate governs its
use. The accuracy contract is statistical: the reported evaluation is
PSNR and mean error distance, there is no fault-detection mechanism,
and there is no formal worst-case bound. The constant choice depends on
the operation, because addition wants complementary truncated bits,
subtraction is best with equal truncated bits and so favours zeroing,
and multiplication is excluded since its energy depends strongly on the
selected constants. Signed and unsigned addition behave the same.
Execution is feed-forward.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/adder_ext.py`: an exact upper adder of the `upper_adder` family over the top W - k bits and the low k bits by forced complementary constants, OR gates, an isolated sub-adder or a speculative window, with an optional correction stage that increments the upper sum when the speculation missed; the ArithmeticError gate governs).

## design choices

### correction

| member | what it selects |
| --- | --- |
| `none` | the speculated carry stands. |
| `configurable_stages` | a correction stage compares the true lower carry with the speculation and increments the upper sum when the prediction missed. |

This correction is active only for `speculative_segments`; explicitly
binding it for a different lower scheme is rejected. It is a construction
choice in the current interface, which has no runtime correction-enable
port. The correction incrementer repairs a missed carry on every operation.

The entire lower region and speculation window must fit their requested
geometry. The generator rejects oversized choices instead of clipping them.
`python -m chialu.verify.approximate_truncated_selftest` enumerates every
active own-pin binding at width 40, including every Range value. It checks
the implemented integer algorithm with exact default children and reports
sample mathematical errors separately; those samples are not full bounds
and do not certify arbitrary nested children or whole-ALU routing.

### lower_scheme

| member | what it selects |
| --- | --- |
| `truncate_constant` | every lower sum bit is forced to one and no carry leaves the low part. |
| `or_gates` | the lower sum is the OR of the operands and the carry is the AND of their top low bits. |
| `segmented_subadders` | the low part is an exact sub-adder whose carry does not cross into the upper part. |
| `speculative_segments` | the low part is exact and the carry into the upper part is speculated from a window at its top. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the upper part stays exact and the low part is the approximation | - | `the upper \d+ bits exact` |

## references

frustaci2019 -> F. Frustaci, S. Perri, P. Corsonello, M. Alioto, "Energy-Quality Scalable Adders Based on Nonzeroing Bit Truncation", IEEE Transactions on VLSI Systems, vol. 27, no. 4, pp. 964-968, 2019
