# carry_save_datapath

Arithmetic kept in redundant sum-plus-carry form across a chain of
operations: a full adder, which is a 3:2 counter, or a 4:2 compressor
reduces three or four operand vectors to one sum vector and one carry
vector without horizontal carry propagation, so each reduction level
costs a constant delay independent of width; the intermediate result
stays as a sum/carry pair through the next multiply, add, shift or
accumulate, and one carry-propagate adder assimilates the pair only
when the answer must be standardized, transferred or tested for sign.
Merged arithmetic applies the same rule to sums of products, summing
the pseudoproducts before any carry propagates.

The compressor choice sets the cell and the level count: the 3:2 cell
is one full-adder delay per level and the cell of the carry-save array
and the Wallace tree, the 4:2 cell halves the vectors per level with a
carry-out that depends on its inputs rather than its carry-in, and a
higher counter keeps three words of state to use one level. The
assimilation point decides where the carry-propagate adder sits:
deferred to the end of the chain, one carry propagation serves a whole
operand group, while a vector-merging adder at an operation boundary
pays when keeping the pair would duplicate the following operation. A
redundant accumulator keeps a product, a partial remainder or a running
sum as two words between iterations; the shipping examples propagate
only the low bits each iteration or assimilate only the three to six
leading bits that digit selection needs. The assimilator slot is open
to any carry-propagate family, and a CSA array delivers balanced
arrivals to it, so replacing only that adder yields most of the
speed-up; wrapping the level carries back in gives modular sums.

The family wins wherever several operands or several dependent
operations precede one result: for K products of N-bit words merged
arithmetic needs KN + K + N carry-save cycles against 2KN + N + 1 when
each product is completed, a saving approaching 50 percent, and a 4:2
iterative accumulator runs at almost twice the speed of a conventional
partially pipelined array at equal hardware. Its costs are two words of
state per value, so registers double, sign and overflow tests that need
assimilation or a separate sign estimate, and a carry-overflow
correction at the sign position, which a modified sign full adder
provides at no area or delay. A floating-point accumulator predicts
mantissa overflow inside the loop instead of assimilating: a toggle
detector reads the three most significant bits of both vectors, 18 of the
27 patterns imply overflow, and a predicted overflow right-shifts the
result and increments the exponent. That prediction is conservative,
because 6 of those 18 patterns put the transition one position lower, and
it costs six logic levels, which took the accumulator's critical path from
9 to 15 FO4 in 90 nm. Full-adder-level pipelining of the chain
removes the 60 to 80 percent synchronization overhead of a
two-dimensional ripple pipeline. The datapath is feed-forward, and it
loses to a plain carry-propagate adder when a single operation stands
alone or the result is inspected after every step.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/redundant.py`: the adder of a `redundant_internal` core under this representation: the operands and the carry-in through one `compressor` level (the unused inputs of the wider counters are the merged operands of a longer chain, zero in a single op) and the `assimilator` family; `carry_overflow_correction` drops the carry word's bit above the modulus; the assimilation point and a redundant accumulator concern a chain of ops, one op here, as the module header says). `python3 -m chialu.targets.rtl.families.redundant --width 32 --slot representation --kind adder --family carry_save_datapath --pins k=v,...` emits it for a rewrite.

## design choices

### compressor

| member | what it selects |
| --- | --- |
| `3_2` | the full adder: three column inputs to a sum and a carry. |
| `4_2` | the 4:2 compressor: four inputs and a lateral carry to a sum and a carry. |
| `5_3` | a 5:3 column counter: five inputs to a sum, a carry and a second carry two positions up. |
| `7_3` | a 7:3 column counter, which the generator builds as the same counter with its two spare inputs tied to zero. |

## references

swartzlander_1980 -> Swartzlander, "Merged Arithmetic", IEEE Transactions on Computers, 1980
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
thornton_1970 -> J. E. Thornton, "Design of a Computer: The Control Data 6600", Scott, Foresman and Co., 1970
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
kilburn1959 -> T. Kilburn, D. B. G. Edwards, D. Aspinall, "Parallel Addition in Digital Computers: A New Fast 'Carry' Circuit", Proceedings of the IEE - Part B, vol. 106, pp. 464-466, 1959.
anderson1967 -> S. F. Anderson, J. G. Earle, R. E. Goldschmidt, D. M. Powers, "The IBM System/360 Model 91: Floating-Point Execution Unit", IBM Journal of Research and Development, vol. 11, no. 1, pp. 34-53, 1967
santoro1989 -> M. R. Santoro, M. A. Horowitz, "SPIM: A Pipelined 64x64-bit Iterative Multiplier", IEEE Journal of Solid-State Circuits, vol. 24, no. 2, pp. 487-493, 1989
noll_1991 -> Noll, "Carry-Save Architectures for High-Speed Digital Signal Processing", Journal of VLSI Signal Processing, 1991
vangal_2006 -> S. Vangal, Y. Hoskote, N. Borkar, A. Alvandpour, "A 6.2-GFlops Floating-Point Multiply-Accumulator With Conditional Normalization", IEEE Journal of Solid-State Circuits, vol. 41, no. 10, 2006
