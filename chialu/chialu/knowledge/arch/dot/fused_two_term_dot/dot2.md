---
family: fused_two_term_dot
pin: {second_op: dot2}
---
# dot2

The fused dot-product unit proper: Y = A*B + C*D from two multiplier
trees, an exponent comparison that aligns the smaller product, a 4:2
reduction tree that merges the four carry-save vectors, and one
normalization and rounding step, with no add/subtract pair sharing
the tail. The wide-accumulator extension adds a 2w-bit addend e to
the same unrounded datapath, sorts the three terms by magnitude and
adds them at increasing widths.

It is the pick when the workload is products summed in pairs and one
rounding per pair is the accuracy target: in 45 nm fp32 the unit is
about 70% of the area of a parallel discrete dot product and 27%
faster, and its FFT butterfly error is about 40% below the discrete
operations. The FP8-to-FP16 and FP16-to-FP32 form cuts GEMM execution
cycles by up to 10% against FP16 FMAs and is more accurate than two
sequential FMAs at every tested accumulation length, without a claim
of correct rounding for all inputs. The add/subtract pair or the
combined butterfly primitive is preferred when the same tail must
also serve A+B and A-B.

The library realizes this choice as a pin of the generated fused_two_term_dot module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

saleh_2008 -> H. H. Saleh, E. E. Swartzlander, "A Floating-Point Fused Dot-Product Unit", IEEE ICCD, 2008
bertaccini_2022 -> L. Bertaccini, G. Paulin, T. Fischer, S. Mach, L. Benini, "MiniFloat-NN and ExSdotp: An ISA Extension and a Modular Open Hardware Unit for Low-Precision Training on RISC-V Cores", ARITH, 2022
