---
family: lane_width_gating
pin: {detection: static_mode}
---
# static_mode

The precision is set by a mode rather than detected per value: unused
LSBs are gated to zero while the MSBs keep computing, lowering
switching activity and the active critical path. DVAS turns
the timing slack into a lower supply at fixed frequency; DVAFS also
packs reduced-precision operations into the idle arithmetic cells so
that frequency and system voltage fall at constant throughput. The
conventional baseline keeps every register clocked, since the mode
brings no selective clock gating.

A 40-nm multiplier scaled from 16b to 4b reduces switching activity
12.5x under DVAS and 3.2x under DVAFS, and the voltage headroom saves
36% energy at 0.9 V and a further 55% at 0.75 V; the scalable
arithmetic needs its own power domain because decoders and memories
do not scale with it (moons2017). In a 28-nm benchmark the data-gated
baseline has the best 8b throughput per area and energy efficiency,
since scalable interconnects add overhead, and stays near optimal
when 8b operations are 33% of the mix (camus2019). Static mode is the
pick when the application sets the precision in advance and the
datapath can be voltage scaled; msb_zero_detect and significance_tags
are the choice when narrowness varies per operand and must be found at
runtime.

## references

moons2017 -> B. Moons, R. Uytterhoeven, W. Dehaene, M. Verhelst, "DVAFS: Trading Computational Accuracy for Energy Through Dynamic-Voltage-Accuracy-Frequency-Scaling", Design, Automation and Test in Europe (DATE), pp. 488-493, 2017
camus2019 -> V. Camus, L. Mei, C. Enz, M. Verhelst, "Review and Benchmarking of Precision-Scalable Multiply-Accumulate Unit Architectures for Embedded Neural-Network Processing", IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 9, no. 4, pp. 697-711, 2019
