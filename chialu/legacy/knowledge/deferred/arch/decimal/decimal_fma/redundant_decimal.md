---
family: decimal_fma
pin: {internal_encoding: redundant_decimal}
---
# redundant_decimal

The product stays in a redundant digit set, the 4-bit two's-complement
code [-8,7] or the set [-6,6], from multiplier reduction to rounding:
a carry-free decimal adder combines the aligned addend and the
redundant product, the leading-zero anticipator runs in parallel, and
the rounder performs the only digit-set conversion together with
absolute-value conversion and IEEE rounding.

It is the pick for latency: the redundant cascade is about 33.7%
faster and 16.6% smaller than the fastest previous combinational
design in STM 90 nm, at 87.1 FO4 normalized, and the [-6,6] adder is
what lets a merged binary/decimal unit share its final adder. The cost
is a nonstandard digit code, a rounder that also converts, and
conversion logic beside the rounding path. BCD is the sibling when a
standard decimal prefix adder and a plain decimal increment are
preferred.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

han_2016 -> Han, Zhang, Ko, "Decimal Floating-Point Fused Multiply-Add with Redundant Internal Encodings", IET Computers & Digital Techniques, 2016
wahba_2017 -> Wahba, Fahmy, "Area Efficient and Fast Combined Binary/Decimal Floating Point Fused Multiply Add Unit", IEEE Transactions on Computers, 2017
