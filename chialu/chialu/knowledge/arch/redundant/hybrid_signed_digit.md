# hybrid_signed_digit

A redundant number system that places a signed digit every d+1
positions and unsigned binary digits between them: a signed-digit cell
forms its carry and interim sum from the two signed operand digits and
the adjacent lower-order unsigned bits without waiting for the incoming
ripple carry, while carries ripple through the unsigned runs
concurrently and stop at the next signed position, so the longest carry
chain is d+1 for any word length. d=0 is the full signed-digit system
and d equal to the word length is two's complement; the spacing may be
uniform or not, the most-significant digit must be signed, and an
n-digit result needs n+1 positions when converted to radix-complement
form.

The sd_position_spacing choice trades cell area against carry length.
In static CMOS an unsigned cell is 32 transistors and a signed cell 42,
so the alternating d=1 word costs 74 transistors per two positions
against 84 for two full signed-digit cells while its critical path
grows from 5 to 6 delay units; the path then grows as 4.5 + 1.5d for
odd d and 5.5 + 1.5d for even d, and for a 24-digit adder the design is
slower than ripple carry once d passes 20, with area-time products
worsening before that. The spacing_uniform choice lets the signed
positions follow the operands: when input spacings align, the sum can
keep either operand's spacing or collapse to full signed-digit form
without added delay, so addition doubles as conversion. The
interior_adder and binary_run_adder choices set how each unsigned run
is resolved; the reference cells ripple.

The family wins in multioperand trees, where one final conversion is
amortized over many redundant additions: a 64x64 multiplier tree with
32 modified-Booth partial products costs about 67K transistors and 46.5
delay units in full signed-digit form, 72K and 53 units with d=1, and
about 66K and 53 units when the tree switches from signed-digit to
hybrid at an intermediate level, which is the AT-optimal choice
whenever its area is below 0.8774 of the full tree, with less
interconnect expected. It loses for two-operand addition, where the
redundant adder plus its conversion can be slower or larger than a
carry-lookahead or carry-skip adder. Arithmetic is exact and
feed-forward, with no fault model reported.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/redundant.py`: the adder of a `redundant_internal` core under this representation: a signed digit every `sd_position_spacing`-th position, uniform or growing (`spacing_uniform`), the binary runs between on the `interior_adder` family (or the `binary_run_adder` slot's family) accepting a carry in {-1, 0, 1}, the signed position absorbing the run's carry and sending a transfer in {-1, 0, 1} to the next run, and the exit conversion subtracting the negative digits' word). `python3 -m chialu.targets.rtl.families.redundant --width 32 --slot representation --kind adder --family hybrid_signed_digit --pins k=v,...` emits it for a rewrite.

## design choices

### interior_adder

| member | what it selects |
| --- | --- |
| `ripple` | the binary runs between the signed digits are ripple-carry adders. |
| `carry_select` | the runs are carry-select adders. |
| `prefix` | the runs are parallel-prefix adders, which the generator builds at the Kogge-Stone topology unless the run adder slot names another. |

## references

phatak_koren_1994 -> Phatak, Koren, "Hybrid Signed-Digit Number Systems: A Unified Framework for Redundant Number Representations with Bounded Carry Propagation Chains", IEEE Transactions on Computers, 1994
