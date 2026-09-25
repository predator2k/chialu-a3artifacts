# lane_width_gating

Narrow-operand exploitation in a wide datapath: a detector finds an
operand's upper bits all zero (or all ones when negative), a stored
significance tag says so, or a static mode fixes precision, and the
unit responds by gating the upper lanes (clock-gating their latches and
muxing zeros or sign onto the high result bits, isolating operands so
the idle region stays quiet, or power-gating it) or by packing several
narrow operations into the wide unit. One detection funds both: gated
lanes cut switching energy and shorten the active critical path, which
voltage scaling turns into more savings, and packed lanes raise
throughput, but an implementation applies one of the two at a time.

The detection choice sets where the width information lives. Result
time detection with 16-bit and 33-bit thresholds stores a tag in the
issue window and requires both operands to fit before the high lanes
are gated; it cuts integer-unit power by about 54% on SPECint and 58%
on MediaBench against opcode-based clock gating in a 64-bit model,
loses 13% of its opportunities on SPECint if loads are not tagged, and
pays a few milliwatts for the zero detector and result muxes.
Significance tags carried through caches, registers and pipeline
latches (two or three bits per 32-bit word, 6 to 9% of storage) reach
the whole pipeline, with about 33% less ALU activity and over 40% less
register-file and latch activity at byte granularity on MediaBench,
less at halfword. A static mode has no detection cost and zeroes the
unused low bits, so it keeps the best 8-bit throughput per area and
remains close to optimal when 8-bit work is a third of the mix.

The gating choice trades depth of savings against implementation
effort: operand isolation alone leaves every register clocked,
byte-level latch clock gating adds the register savings, and enabling
rectangular partial-product regions only when both operands' width
controls agree extends the idea into a multiplier at 4- or 8-bit
granularity (finer fights Booth-2 grouping). The operation_packing
choice turns the same idle cells into throughput: packing 4-bit
operations four to a 16-bit multiplier holds throughput while frequency
and supply fall, for 36% energy reduction at 0.9 V from gating alone
and a further 55% at 0.75 V with packing in 40 nm. Lane organization is
the performance side of that trade; byte-serial pipelines cost 79% more
cycles per instruction, semi-parallel 24%, and byte-parallel skewed
with bypasses 2%.

The family wins on media and neural-network workloads with narrow
values and per-layer precision, and loses when scalable interconnect
and detection overheads outweigh savings on full-width work. Arithmetic
stays exact at the selected width; no fault model is reported, and
execution is feed-forward.

The family has no combinational module (narrow-operand detection funds clock gating and packed scheduling: a sequential control, not a combinational datapath), so a seed that declares it stays as generated; it is listed as an exception in `chialu.targets.rtl.families.subword.EXCEPTIONS`.

## references

brooks_1999 -> D. Brooks, M. Martonosi, "Dynamically Exploiting Narrow Width Operands to Improve Processor Power and Performance", Proc. HPCA-5, pp. 13-22, 1999
canal_2000 -> R. Canal, A. Gonzalez, J. E. Smith, "Very Low Power Pipelines Using Significance Compression", Proc. MICRO-33, pp. 181-190, 2000
moons2017 -> B. Moons, R. Uytterhoeven, W. Dehaene, M. Verhelst, "DVAFS: Trading Computational Accuracy for Energy Through Dynamic-Voltage-Accuracy-Frequency-Scaling", Design, Automation and Test in Europe (DATE), pp. 488-493, 2017
camus2019 -> V. Camus, L. Mei, C. Enz, M. Verhelst, "Review and Benchmarking of Precision-Scalable Multiply-Accumulate Unit Architectures for Embedded Neural-Network Processing", IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 9, no. 4, pp. 697-711, 2019
zhang_2020 -> H. Zhang, S.-B. Ko, "Design of Power Efficient Posit Multiplier", IEEE Transactions on Circuits and Systems II: Express Briefs, 2020
