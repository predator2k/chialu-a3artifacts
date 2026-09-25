# online_msdf

Most-significant-digit-first division: operand digits arrive
serially, the first quotient digit appears after an online delay of a
few leading digits, and every later operand digit produces one
quotient digit. The residual w[j] = r^j (x[j] - q[j] d[j]) is kept in
carry-save or signed-digit form and updated without carry
propagation; each cycle appends a divisor digit, forms the shifted
residual with the new dividend digit and the partial-quotient
multiple, selects q[j+1] in {-1, 0, 1} from a truncated estimate with
three fractional bits, subtracts q[j+1] d[j+1], and appends the
quotient digit through on-the-fly conversion.

The online delay and the radix trade selection simplicity against
digits per cycle. At radix 2 with nonredundant operands and a
redundant quotient the delay is 4, and a single pair of selection
constants at plus or minus 1/4 suffices; supplying the dividend in
bit-parallel form cuts the delay to 3. Higher radices keep a delay of
4 digits in the radix-10 derivation but need divisor intervals and a
staircase selection function, so radix 2 is what the shipped units
use. Redundant quotient digits make the selection regions overlap,
which is what allows truncated estimates instead of full comparisons,
and redundant operands allow the carry-free residual update; a
nonredundant result representation cannot avoid full carry
propagation, so the result is always redundant.

Against conventional carry-save digit recurrence the online form
costs two [3:2] adders instead of one, six registers instead of five,
a three-fractional-bit estimate instead of one bit, and a longer
cycle; the critical path is two multiplexers, a 4-bit carry-propagate
adder and a carry-save adder. The family is fixed-iteration at about
n plus the delay cycles.

It wins where the quotient feeds another online operator without
waiting for the full result: rotation-factor pipelines, and
large-number arithmetic where the divider updates a signed residual
of up to 2048 positions carry-free while four leading slices convert
the top digits to nonredundant form and predict the next digit, at a
size only slightly above the online multiplier. It loses to
conventional digit recurrence whenever operands are parallel and no
downstream consumer is online.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: the on-line recurrence unrolled at radix 2 or 4: the divisor and dividend digits join one per stage after `online_delay` digits (at least 4 at radix 2, 3 at radix 4), the partial quotient's multiple of each new divisor digit at weight r^-delta and the digit's multiple of the divisor known so far through the `residual_adder` family, the digit from the `digit_select` slot over the assimilated residual (its table generated with the residual bound tightened for the on-line terms), the quotient on the fly). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## references

ercegovac_2004 -> M. D. Ercegovac and T. Lang, "Digital Arithmetic", Morgan Kaufmann, 2004
trivedi_1977 -> Trivedi, Ercegovac, "On-Line Algorithms for Division and Multiplication", IEEE Transactions on Computers, 1977
ercegovac_lang_1988 -> Ercegovac, Lang, "On-Line Scheme for Computing Rotation Factors", Journal of Parallel and Distributed Computing, 1988
guyot_1989 -> Guyot, Herreros, Muller, "JANUS, an On-Line Multiplier/Divider for Manipulating Large Numbers", 9th IEEE Symposium on Computer Arithmetic, 1989
