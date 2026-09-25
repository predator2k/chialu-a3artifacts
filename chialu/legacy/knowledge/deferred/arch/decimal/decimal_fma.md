# decimal_fma

a*b+c with one decimal rounding: the significand multiplier generates
decimal partial products from a signed-digit-recoded multiplier and
reduces them in a decimal carry-save tree while the addend is pre-
aligned in parallel over a width of up to 4p digits. The merged form
injects the middle 2p digits of the aligned addend into the tree, so
one decimal carry-propagate adder yields the 2p-digit intermediate;
the cascade form completes the product first and adds the aligned
addend in a wide decimal adder. A decimal leading-zero anticipator
runs beside the addition, and post-alignment plus one rounding under
the IEEE directions delivers the p-digit result with its cohort.

The structure choice trades a second carry-propagate pass against
alignment width: the merged tree spends 4p digits of alignment and
lets one operation selector serve FMA, multiplication and
addition/subtraction from the same tree, whereas the cascade keeps the
multiplier a separate block and takes its pre-alignment off the
critical path. Internal encoding decides where carries resolve: BCD
keeps a standard digit code and a decimal prefix adder, while a
redundant digit set keeps the product carry-free from reduction to the
rounder, which then performs the only digit-set conversion together
with absolute-value conversion and rounding; the redundant cascade is
about 33.7% faster and 16.6% smaller than the fastest previous
combinational design in STM 90 nm. Combining binary and decimal shares
the multiplier and final adder, which dominate the unit, for about 23%
less area than separate units and a decimal mode about 6% faster than
the fastest stand-alone decimal FMA in TSMC 65 nm LP, but the shared
unit runs seven stages and adds more latency than a four-stage adder.

The multiplier-tree slot is parallel in every reported design, and the
pipeline partition ranges from a combinational unit to ten stages,
which moves the LSI 65-nm cascade from 4.6 ns to 0.61 ns per stage
with nonmonotonic area. The contract is IEEE decimal: one rounding
after a*b+-c, five directions plus two Java BigDecimal directions in
the units that offer them, NaN/infinity handling and flags; exact
results target the preferred quantum exponent min(Q(a)+Q(b), Q(c))
and avoid normalization, inexact results use the least possible
exponent, and the addend-anchored case needs a leading-zero count of
up to p+4 digits. DPD decoding and encoding can be dropped when the
processor stores decoded operands. Verification is by directed and
random vectors rather than an error bound. Execution is feed-forward
with II=1 when pipelined.

No unit template opens `decimal_misc_space`: the family belongs to a decimal floating-point unit (or a conversion between number systems) that the ALU, dot and SFU templates do not provision, so no seed declares it and the library has no module for it; the BCD ALU's decimal adders, multipliers and dividers come from `chialu/targets/rtl/families/decimal.py`.

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
samy_2010 -> Samy, Fahmy, Raafat, Mohamed, ElDeeb, Farouk, "A Decimal Floating-Point Fused-Multiply-Add Unit", 53rd IEEE Midwest Symposium on Circuits and Systems (MWSCAS), 2010
akkas_2011 -> Akkas, Schulte, "A Decimal Floating-Point Fused Multiply-Add Unit with a Novel Decimal Leading-Zero Anticipator", IEEE ASAP, 2011
han_2016 -> Han, Zhang, Ko, "Decimal Floating-Point Fused Multiply-Add with Redundant Internal Encodings", IET Computers & Digital Techniques, 2016
wahba_2017 -> Wahba, Fahmy, "Area Efficient and Fast Combined Binary/Decimal Floating Point Fused Multiply Add Unit", IEEE Transactions on Computers, 2017
