---
family: recursive_karatsuba
pin: {base_multiplier: fpga_dsp_block}
---
# fpga_dsp_block

The embedded DSP block as the base multiplier: each diagonal and
subtractive cross product maps onto one signed 18-bit (Virtex-4) or
one 17x25 (Virtex-6) multiplier, the DSP cascade hides the input
subtractions, and the direct N-part expansion uses N(N+1)/2 blocks,
so DSP count rather than logic delay is the quantity the split
minimizes.

DSP-block Karatsuba is the pick when blocks are the scarce resource
above 64x64 bits: a 119-bit seven-part multiplier takes 28 DSPs
against 49 for the standard decomposition on Virtex-4 (18 cycles,
322 MHz, 2053 slices) and 28 against 34 on Virtex-5, and 113x113
takes 29 DSPs against 34 for the best non-Karatsuba tiling. It loses
when the block granularity is large (36-bit Stratix multipliers) or
asymmetric (Virtex-5 18x25), and every saved block costs LUTs for
the pre-subtractions and the merged post-addition tree; the array
and Booth-tree base multipliers are the siblings on ASIC, where the
breakeven sits at 32 to 64 bits.

## references

pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
kumm2018 -> M. Kumm, O. Gustafsson, F. de Dinechin, J. Kappauf, P. Zipf, "Karatsuba with Rectangular Multipliers for FPGAs", 25th IEEE Symposium on Computer Arithmetic (ARITH), 2018
