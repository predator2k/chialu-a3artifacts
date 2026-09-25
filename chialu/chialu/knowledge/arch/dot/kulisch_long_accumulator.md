# kulisch_long_accumulator

Exact accumulation of floating-point products in a fixed-point register
wide enough to cover every product exponent: each unrounded 2p-bit
significand product is shifted by its exponent sum into the long
accumulator and added there, no intermediate rounding occurs, and one
conversion back to floating point performs the single rounding after
the whole sum. The minimum width is 2emax - 2emin + 2p bits, about 554
bits for binary32 and 4196 for binary64, plus margin bits so that a
bounded number of products cannot overflow; the sum is exact and
independent of term order, and the posit quire is the same register at
ISA level.

The organization choice sets the frequency, because a full-width carry
propagation cannot close a GHz cycle. A monolithic register with one
wide adder resolves every carry immediately and is practical only for
small formats or bounded application ranges, where a binary16
accumulator is barely larger than an FMA. The segmented form partitions
the carry chain into k-bit chunks separated by registers, so the
recurrence holds only a k-bit carry and the representation is partial
carry-save; a chunk of 32 bits reaches 400 MHz on a Virtex-4 with one
register per 32 bits of overhead, and smaller chunks buy frequency with
more registers. Banked sub-adders delay the inter-word carries by a
cycle, and converting inputs to two's complement at entry replaces the
replicated add/subtract and separate carry/borrow storage with one
addition and one carry path, with 64 bits the best sub-adder width in
most cases. The carry resolution follows the organization: immediate
for the wide adder, latched carry and borrow propagated in later cycles
between segments, or a sweep at the end, which flushes zeros for a
number of cycles at no hardware cost or runs a pipelined propagation
when the running value must be readable. A centralized variant stores
the register in banked SRAM behind one shared accumulator, with
all-ones/all-zeros metadata to speed the rare long carry.

The family wins where the sum must be exact or reproducible regardless
of term count: on a Kintex 7 the exact accumulator uses roughly 10x the
resources of a regular floating-point accumulator and cuts the latency
of a 1000-product sum by roughly 10x, because it issues one product per
cycle, and an fp64 accelerator at over 900 MHz in 45 nm runs about 3x
faster than reproducible software. It loses to the application-specific
window accumulator and to block floating point where product magnitudes
and term counts are bounded, since the generic width costs a shifter as
wide as the register. The execution is fixed-iteration: one product per
cycle, then the flush or propagation cycles, then the conversion, which
may overflow or underflow and in some designs rounds only towards zero.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: the one-operation form of the long fixed-point word: the products and c shifted to their weights and added over `accumulator_width_bits` (at least the exact frame), monolithic, in segments with the carries resolved immediately, kept as a carry word for one final add, or swept once at the end, in banks each term reaches, or as a fast low and a slow high part; the accumulator register across operations is state the unit has none of). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## design choices

### carry_resolution

| member | what it selects |
| --- | --- |
| `immediate` | each addition into the long word propagates its carry at once. |
| `carry_save_deferred` | the carries are held in a carry word and resolved later. |
| `periodic_sweep` | the carries are resolved by a sweep over the segments rather than per addition. |

### organization

| member | what it selects |
| --- | --- |
| `monolithic` | the long word is one adder. |
| `segmented_lazy_carry` | the word is cut into 32-bit segments whose carries resolve by the carry resolution chosen. |
| `banked_sub_adders` | the segments are banked sub-adders. |
| `two_speed` | 16-bit segments, which is the narrower split of the same structure. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the accumulation is one long fixed-point word, whose width and organization the module states | - | `the long fixed-point word \(\d+ bits, \w+, carries \w+\)` |

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
brunie_2017 -> N. Brunie, "Modified Fused Multiply and Add for Exact Low Precision Product Accumulation", ARITH-24, pp. 106-113, 2017
koenig_2017 -> J. Koenig, D. Biancolin, J. Bachrach, K. Asanovic, "A Hardware Accelerator for Computing an Exact Dot Product", ARITH-24, pp. 114-121, 2017
uguen_2017 -> Y. Uguen, F. de Dinechin, "Design-Space Exploration for the Kulisch Accumulator", HAL preprint hal-01488916, 2017
uguen_2019 -> Y. Uguen, L. Forget, F. de Dinechin, "Evaluating the Hardware Cost of the Posit Number System", International Conference on Field Programmable Logic and Applications (FPL), 2019
