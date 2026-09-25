---
family: rns_channel_arithmetic
pin: {multiplier_reduction: booth_modular}
---
# booth_modular

The Booth-recoded channel multiplier: radix-4 Booth partial products
are reduced by carry-save and 4:2 compressors and merged by a
channel-specific Sklansky adder, which discards the carry-out in the
2^n channel and wraps it end-around in the 2^n-1 and 2^(n+1)-1
channels. A DNN multiply-accumulate is decomposed across such
channels of 5, 5 and 6 bits with a profiled range extension for
accumulation.

It is the pick when energy per multiply is the target and the
channels are logic rather than tables: the 19-bit RNS multiplier
built this way has 4.62x lower energy, 2.1x lower delay and 9.72x
smaller energy-delay product than a 16-bit binary multiplier in 45 nm
NanGate at about half its area, while the RNS adder is only about 5%
to 8% better than a binary adder of the same range. Booth halves the
partial-product count, but in the modulo 2^n +/- 1 trees it does not
always reduce cell-based area or tree delay, so the plain folded tree
remains the choice when the recoding and correction terms outweigh
the saved rows.

The library realizes this reduction as radix-4 Booth rows reduced by the modulus, the negative rows as m minus their magnitude, summed and reduced once (`chialu/targets/rtl/families/redundant.py`).

## references

samimi_2020 -> Samimi, Kamal, Afzali-Kusha, Pedram, "Res-DNN: A Residue Number System-Based DNN Accelerator Unit", IEEE Transactions on Circuits and Systems I, 2020
zimmermann1999 -> R. Zimmermann, "Efficient VLSI Implementation of Modulo (2^n +/- 1) Addition and Multiplication", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999
