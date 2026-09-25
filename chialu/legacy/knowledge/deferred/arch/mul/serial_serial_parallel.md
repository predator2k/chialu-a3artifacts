# serial_serial_parallel

Multiplication with one or both operands entering one digit per cycle,
LSB first: a serial-parallel unit holds the multiplicand in parallel
and gates it into a chain of delayed full-adder stages under each
multiplier bit, so partial products accumulate as a carry-save
add-and-shift and the low product bits leave serially; a serial-serial
unit takes both operands as they arrive, generates the new row and
diagonal (or column) of partial products each step, and sums them in a
counter-based summator holding a carry-save residual. Execution is
fixed-iteration, n cycles for one serial operand and 2n for two, plus a
terminal drain through a serial adder or an (n-1)-bit ripple adder.

The serial_operands choice trades start-up against cell cost. With one
serial operand the equipment scales with the multiplicand width and is
independent of the multiplier length, one operation issues every N bit
times despite an N+K bit-time delay when words are overlapped, and a
constant multiplicand can be hardwired so minimum signed-digit recoding
leaves two adders for a 6-bit coefficient. With both serial the product
starts leaving while operands still arrive, at zero latency in the
slice design whose N-1 cells of (5,3) counters also absorb the
symmetric x_i*y_i term online (which is the squarer mode), but each
slice carries an AND, a counter and a mux in its critical path and the
unit needs a [4:2] adder plus five registers per position.

The digit_size_bits choice buys cycles with multiples: pairing
multiplier bits replaces every alternate full adder by a selector over
precomputed multiples, five-level recoding to -2X..2X halves the stage
count to K/2, and going past that gains nothing because 3X needs its
own adder; chaining p adder-subtractors in the circulating path handles
2p multiplier digits per circulation when adjacent positions are paired
so at most one nonzero digit reaches each input. The
end_reconfigure_to_ripple choice cuts the terminal (n-1)-clock drain to
an (n-1)-full-adder ripple, which is about one third faster than
carry-save add-shift for about one third more hardware ((5n-1)t against
8nt with 4(n-1) against 3(n-1) full-adder equivalents).

The family is the floor of the area axis, with up to 40% area saving
against a parallel MAC in 28 nm, and it pays in throughput and in
clock-tree energy over the repeated cycles: at full precision a
one-dimensional bit-serial MAC spends 3.3x the energy per operation of
a data-gated parallel unit, a two-dimensional one 14x, and only the
4-bit-digit one-dimensional design stays competitive at 1.5x. The
grouping parameter spans the whole continuum from m^2 cells at depth
log m to m cells at depth m log m. Arithmetic is exact; rounding the
high half is one injected LSB, and two's-complement operands need
sign-extension logic whose corner cases show up as Booth overflow.

The family's defining structure is sequential (serial operands over the cycles), so the library has no combinational module for it; a seed that declares it stays behavioral and the family is listed as an exception (`mul_ext.SEQUENTIAL_MUL`).

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
ercegovac_2004 -> M. D. Ercegovac and T. Lang, "Digital Arithmetic", Morgan Kaufmann, 2004
tocher_1958 -> Tocher, "Techniques of Multiplication and Division for Automatic Binary Computers", Quarterly Journal of Mechanics and Applied Mathematics, 1958
karatsuba1962 -> A. Karatsuba, Yu. Ofman, "Multiplication of Multidigit Numbers on Automata", Doklady Akademii Nauk SSSR, vol. 145, no. 2, pp. 293-294, 1962 (Engl. transl. Soviet Physics-Doklady, vol. 7, pp. 595-596, 1963)
lyon1976 -> R. F. Lyon, "Two's Complement Pipeline Multipliers", IEEE Transactions on Communications, vol. COM-24, pp. 418-425, 1976
gnanasekaran1985 -> R. Gnanasekaran, "A Fast Serial-Parallel Binary Multiplier", IEEE Transactions on Computers, vol. C-34, pp. 741-744, 1985
ienne1994 -> P. Ienne, M. A. Viredaz, "Bit-Serial Multipliers and Squarers", IEEE Transactions on Computers, vol. 43, no. 12, pp. 1445-1450, 1994
camus2019 -> V. Camus, L. Mei, C. Enz, M. Verhelst, "Review and Benchmarking of Precision-Scalable Multiply-Accumulate Unit Architectures for Embedded Neural-Network Processing", IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 9, no. 4, pp. 697-711, 2019
