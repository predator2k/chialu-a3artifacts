---
family: decimal_fma
pin: {structure: cascade}
---
# cascade

The multiplier completes the 2p-digit product, in BCD or in a redundant
digit set, while separate shifters pre-align the addend in parallel;
a wide decimal adder, a pre-corrected Kogge-Stone network on BCD or a
carry-free adder on redundant digits, then combines product and
addend. The decimal leading-zero anticipator runs beside that addition,
and post-alignment, special-case handling and one rounding follow.

It is the pick when the multiplier stays a reusable block or the unit
is pipelined deeply: the decimal64 design spans one to ten stages,
moving from 4.6 ns unpipelined to 0.61 ns per stage in LSI 65 nm, and
pre-alignment sits outside the combinational critical path. With a
redundant product and a carry-free adder the cascade is about 33.7%
faster and 16.6% smaller than the fastest previous combinational
design in STM 90 nm. The merged tree is the sibling when the aligned
addend should enter the reduction and one carry-propagate adder serve
the whole a*b+-c.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

akkas_2011 -> Akkas, Schulte, "A Decimal Floating-Point Fused Multiply-Add Unit with a Novel Decimal Leading-Zero Anticipator", IEEE ASAP, 2011
han_2016 -> Han, Zhang, Ko, "Decimal Floating-Point Fused Multiply-Add with Redundant Internal Encodings", IET Computers & Digital Techniques, 2016
