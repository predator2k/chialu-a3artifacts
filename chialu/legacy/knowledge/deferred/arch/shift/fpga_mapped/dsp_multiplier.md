---
family: fpga_mapped
pin: {mapping: dsp_multiplier}
---
# dsp_multiplier

The shift is a multiplication by a one-hot power of two in an embedded
multiplier: an 8-bit input times a one-hot SHIFT[7:0] in one MULT18X18
yields the rotation in one clock cycle. The 32-bit single-cycle design
splits the word into four bytes, applies four multiplier shifters for
the fine shift from S[2:0], and reorders bytes with thirty-two 4-to-1
multiplexers from S[4:3]; the four-cycle design reuses one multiplier
with input multiplexers, clock-enabled output registers and a state
machine.

It is the pick when multipliers sit idle and configurable logic is
scarce: the single-cycle 32-bit shifter uses 9 CLBs plus four
multipliers against 64 CLBs for the traditional design on a Virtex-II,
with the one-hot encoder in one CLB and the output multiplexers in
eight, and the four-cycle form drops to one multiplier at four cycles
of latency. The costs are one-hot control, a rotate rather than a
shift, and lost placement flexibility because the shifters are locked
to multiplier locations. LUT multiplexer stages remain the sibling
when the multipliers are needed for arithmetic.

## references

gigliotti_2004 -> P. Gigliotti, "Implementing Barrel Shifters Using Multipliers", Xilinx Application Note XAPP195, 2004
