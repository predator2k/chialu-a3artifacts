---
family: carry_select
pin: {duplication: bec_increment}
---
# bec_increment

The modified square-root carry-select block: the carry-in-0 ripple
adder is kept, the carry-in-1 adder is replaced by an (n+1)-bit
binary-to-excess-1 converter that increments the first adder's
output, and a multiplexer picks the direct or incremented result from
the incoming carry. The converter is smaller than a second adder, so
the block keeps carry-select's late selection while dropping most of
the duplicated logic.

Against full_duplicate the converter cuts cell area by about 10 to
17% and power by about 8 to 15% at 8 to 64 bits in TSMC 0.18 um, with
a delay overhead that falls from 14% to under 4% as width grows, so
the power-delay product is worse at 8 bits and better from 16 bits
up. It is the pick for area and power at moderate width; when the
second path can be reduced to a bare incrementer the design has
become carry_increment.

## references

ramkumar2012 -> B. Ramkumar, H. M. Kittur, "Low-Power and Area-Efficient Carry Select Adder", IEEE Transactions on VLSI Systems, vol. 20, no. 2, pp. 371-375, 2012.
