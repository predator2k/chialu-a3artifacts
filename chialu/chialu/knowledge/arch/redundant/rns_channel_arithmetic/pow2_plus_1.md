---
family: rns_channel_arithmetic
pin: {modulus_form: pow2_plus_1}
---
# pow2_plus_1

The modulo 2^n+1 channel: the residue needs n+1 bits in normal
encoding or n bits in diminished-1 encoding, the adder is an
end-around-carry structure with an inverted feedback bit and constant
correction terms, and the multiplier folds its higher partial-product
bits back as complemented low bits into an end-around carry-save
tree with a 2^n special-case unit. It completes the {2^n-1, 2^n,
2^n+1} set whose product gives about 3n bits of range with three
near-equal channels.

It is the pick when the moduli set must stay balanced and special:
the channel costs slightly more area than the 2^n-1 channel and an
integer multiplier of the same width, with delay within a few percent
at 8 to 32 bits in 0.25 um cells, and in diminished-1 form its
residue reduction is two fixed carry-save stages. It is the natural
home of Fermat-number transforms. Generic moduli win when the range
must be tuned finely or when many small channels with tables are
cheaper, and the 2^n and 2^n-1 channels alone are preferred when the
correction terms of the plus-one form are not worth a third balanced
channel.

The library realizes this modulus form as the classic set {2^n - 1, 2^n, 2^n + 1} with the 2^n + 1 channel in the normal or the diminished-one encoding (`chialu/targets/rtl/families/redundant.py`).

## references

ma_1998 -> Ma, "A Simplified Architecture for Modulo (2^n + 1) Multiplication", IEEE Transactions on Computers, 1998
zimmermann1999 -> R. Zimmermann, "Efficient VLSI Implementation of Modulo (2^n +/- 1) Addition and Multiplication", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999
chang_2015 -> Chang, Molahosseini, Zarandi, Tay, "Residue Number Systems: A New Paradigm to Datapath Optimization for Low-Power and High-Performance Digital Signal Processing Applications", IEEE Circuits and Systems Magazine, 2015
