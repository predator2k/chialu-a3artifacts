---
family: twin_precision_subword
pin: {base_scheme: baugh_wooley}
---
# baugh_wooley

Twin precision over a plain (non-recoded) partial-product matrix
with Baugh-Wooley sign handling: NAND-XOR partial-product generation
makes the inversions selectable per mode, XOR gates on the product
MSBs and correction ones complete each lane's two's-complement
product, and the most-significant narrow product needs one extra
half-adder level. Three-input AND gates under two mode signals zero
the unused partial products, and the narrow products sit low in the
tree to shorten their paths.

The Baugh-Wooley form has the simpler mode control and the better
delay and power behaviour of the two base schemes: at 16 bits the
full-width mode costs 9% delay and under 1% power over a
conventional multiplier, two parallel 8-bit products draw 42% less
power than the 16-bit conventional one, and the transistor count
rises 8%. Its area overhead is the larger, 11% against 3% for
modified_booth at 32 bits in 65 nm, because the un-recoded matrix is
bigger. It is the pick when independent per-operand sign control at
run time matters, which is how the FPGA DSP block decomposes a 9-bit
signed multiplier recursively into two or four lanes.

## references

sjalander_2004 -> M. Sjalander, H. Eriksson, P. Larsson-Edefors, "An Efficient Twin-Precision Multiplier", Proc. IEEE ICCD, pp. 30-33, 2004
sjalander2009 -> M. Sjalander, P. Larsson-Edefors, "Multiplication Acceleration Through Twin Precision", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 17, no. 9, pp. 1233-1246, 2009
rasoulinezhad_2019 -> S. Rasoulinezhad, H. Zhou, L. Wang, P. H. W. Leong, "PIR-DSP: An FPGA DSP Block Architecture for Multi-Precision Deep Neural Networks", IEEE Symposium on Field-Programmable Custom Computing Machines (FCCM), 2019
