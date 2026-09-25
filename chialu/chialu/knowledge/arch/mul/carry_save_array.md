# carry_save_array

A two-dimensional array of carry-save cells: the multiplicand is gated
with every multiplier bit so that all partial products exist at once,
and each row of full adders (3:2 counters) adds one partial product
into a running sum/carry pair without carry propagation, sums moving
vertically and carries diagonally, until a final carry-propagate row
resolves the last two rows into the product. Delay grows linearly with
operand width, every cell sees the same neighbours, so the wiring is
the most regular of any parallel multiplier, and any row boundary can
take a register, which makes the array pipelinable at bit level with
one product per full-adder delay.

The signed scheme decides how the sign rows are absorbed. Treating the
top bit of each operand as negative weight and adding positive and
negative partial products directly in two-bit gated adder cells avoids
pre-complementing the operands, which matters when the sign bits
arrive last, and gave a 40 ns 17x17 multiplier in 1971 ECL. The
Baugh-Wooley transform instead folds the negative rows into
complemented terms plus five constant bits, so the array stays
uniform with every coefficient positive and no added delay, at the
cost of needing the complement of every operand bit; the modified
forms change the two most-significant columns, may omit the redundant
top product bit unless the product of the two most negative operands
is needed, and let one 4x4 block serve signed and unsigned operation.

Pipelining the rows is a later version's structure; it trades throughput against register area. One
row per stage reached 70 MHz for an 8x8 array in 2.5 um CMOS with 2N
stages, a registered half-adder final row that spreads the last carry
across stages, and operand bits skewed before the AND gates to halve
the skew registers; the price was 4.4x the nonpipelined area
(registers, clock buffers and clock routing each roughly doubling it)
and a clock skew budget below one full-adder delay. Bit-plane ordering
of partial products lets one LSB per plane be dropped without
accumulation error, which suits fixed-coefficient DSP arrays. The
carry-propagate slot is the only carry chain: a uniform final row, one
with sum-skip every four cells, or an adder driven by the arrival
profile.

Trees are faster: a Wallace-like network sums so quickly that further
optimization gains little, and level count alone does not predict
delay once wire length and asymmetric cell inputs reorder paths (wire
was 1.25 ns of a 2.0 ns critical path in 0.6 um BiCMOS). The array is
smaller with shorter wires, becomes competitive as wire cost rises,
and is exact; splitting the rows into two concurrently reduced halves
merged before the long carry is the historical middle ground.

## the library's module

The seed instantiates the library's generated multiplier for this family
(`chialu/targets/rtl/families/mul.py`: the AND array with the Baugh-Wooley terms added row by row into a sum and a carry vector, or Pezaris' array whose sign-row products enter at negative weight through mixed-sign cells; then the final adder of the `cpa.*` choices: any adder family, or the arrival-driven regions of `hybrid_arrival_driven`). `python3 -m chialu.targets.rtl.families.mul
--width 32 --family carry_save_array --signed --sv mul32.sv` emits it for a rewrite.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
bewick1994 -> G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
baugh1973 -> C. R. Baugh, B. A. Wooley, "A Two's Complement Parallel Array Multiplication Algorithm", IEEE Transactions on Computers, vol. C-22, no. 12, pp. 1045-1047, 1973
pezaris1971 -> S. D. Pezaris, "A 40-ns 17-Bit by 17-Bit Array Multiplier", IEEE Transactions on Computers, vol. C-20, no. 4, pp. 442-447, 1971
hatamian1986 -> M. Hatamian, G. L. Cash, "A 70-MHz 8-bit x 8-bit Parallel Pipelined Multiplier in 2.5-um CMOS", IEEE Journal of Solid-State Circuits, vol. SC-21, no. 4, pp. 505-513, 1986
blankenship1974 -> P. E. Blankenship, "Comments on 'A Two's Complement Parallel Array Multiplication Algorithm'", IEEE Transactions on Computers, 1974
noll_1991 -> Noll, "Carry-Save Architectures for High-Speed Digital Signal Processing", Journal of VLSI Signal Processing, 1991
thornton_1964 -> J. E. Thornton, "Parallel Operation in the Control Data 6600", Proc. AFIPS Fall Joint Computer Conference, pp. 33-40, 1964.
