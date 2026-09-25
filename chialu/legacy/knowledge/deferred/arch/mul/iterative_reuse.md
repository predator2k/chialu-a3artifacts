# iterative_reuse

A fraction of the partial-product tree is instantiated and cycled. Each
pass feeds the next group of multiplier bits, Booth-recoded or not,
through the partial tree, and a 4:2 carry-save accumulator shifts and
adds the pass result to the redundant running product, so the product
stays in carry-save form across passes and one carry-propagate addition
finishes it. The feedback loop encloses only the final compressor
stages, so the iteration period is a couple of carry-save delays rather
than the whole tree, and temporary storage between the tree stages lets
a pass enter the tree while the previous pass is still being
accumulated.

The instantiated fraction trades hardware against pass count. The
Model 91 built about 20% of a 28-CSA two-cycle full tree and retired 12
multiplier bits per 20 ns pass over five passes; SPIM built an
eight-input 4:2 tree that takes a quarter of its 32 Booth partial
products per cycle, chosen over two- and four-input trees as the
area/speed point, and finishes a 64x64 multiply in seven array cycles;
the CDC 6600 split the multiplier into two 24-bit halves that each
cycle three carry-save layers four times, six bits per step, before a
final merge. A pipelined 4:2 compressor tree packs one 4:2 adder, which
is two CSA cells, per pipe stage, while a plain CSA reduction tree
holds the temporary storage at the recoder, multiple gates, and chosen
CSA levels.

Overlapping iterations by pipelining is where the family earns its
latency. Closing the accumulating loop around the last two carry-save
adders instead of from tree output to tree input cut the Model 91 loop
time by a factor of 2.5, from 20 to 8 clock periods, and the SPIM core
runs a 64x64 fractional multiply in under 120 ns with a 47 ns
initiation interval at 85 MHz in 1.6 um CMOS, with a stoppable on-chip
ring oscillator matched to the CSA delay that idles the array between
multiplies. The precondition is small latch delays and a clock matched
to the combinational CSA delay; temporary-storage placement has to
satisfy the short-path/long-path timing relation.

The family is fixed-iteration and wins where a full tree is too large
and a shift-add multiplier too slow, approaching full-array throughput
and latency with a fraction of the hardware. It loses to the full tree
once area is available and one multiply per cycle is required, and the
partial tree is the natural block to share with a MAC datapath.

The family's defining structure is sequential (a fractional tree cycled with an accumulator), so the library has no combinational module for it; a seed that declares it stays behavioral and the family is listed as an exception (`mul_ext.SEQUENTIAL_MUL`).

## references

anderson1967 -> S. F. Anderson, J. G. Earle, R. E. Goldschmidt, D. M. Powers, "The IBM System/360 Model 91: Floating-Point Execution Unit", IBM Journal of Research and Development, vol. 11, no. 1, pp. 34-53, 1967
santoro1989 -> M. R. Santoro, M. A. Horowitz, "SPIM: A Pipelined 64x64-bit Iterative Multiplier", IEEE Journal of Solid-State Circuits, vol. 24, no. 2, pp. 487-493, 1989
thornton_1970 -> J. E. Thornton, "Design of a Computer: The Control Data 6600", Scott, Foresman and Co., 1970
