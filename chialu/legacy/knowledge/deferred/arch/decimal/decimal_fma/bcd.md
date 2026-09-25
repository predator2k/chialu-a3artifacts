---
family: decimal_fma
pin: {internal_encoding: bcd}
---
# bcd

Significands stay in BCD through the datapath: DPD operands are decoded
to BCD, the 16-digit by 16-digit product and the extended addend are
aligned as 32-digit BCD values by separate left/right decimal barrel
shifters, and a pre-corrected Kogge-Stone network performs the
32-digit decimal addition or subtraction with a decimal leading-zero
anticipator in parallel. Rounding is a decimal increment on BCD digits.

It is the pick when the final adder must be a standard decimal
carry-propagate adder and the DPD codec sits at the unit boundary in
any case, because no digit-set conversion is needed anywhere; the
decimal64 unit pipelines from one to ten stages in LSI 65 nm. The
redundant sibling keeps the product carry-free until the rounder and
gains latency and area, at the price of a nonstandard digit code and a
rounder that also performs the digit-set and absolute-value
conversion.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

akkas_2011 -> Akkas, Schulte, "A Decimal Floating-Point Fused Multiply-Add Unit with a Novel Decimal Leading-Zero Anticipator", IEEE ASAP, 2011
