---
family: masked_merged
pin: {mask_generator: thermometer_decode}
---
# thermometer_decode

The mask from a binary-to-thermometer converter: the shift amount is
decoded into a string of ones up to the shift position, the per-bit
mask information falls out of AND gates and OR trees over that string,
and the mask is applied to the rotated value with inverting logic so
the final rotating-multiplexer inverter disappears. The same mask
selects zero fill or sign extension, and the masker adds one gate from
the rotated value to the output.

It is the pick for a static shifter whose mask must be ready when the
rotation is, since the converter runs in parallel with the rotator and
costs one gate on the data path; two thermometer codes ANDed together
are the extension for a field with both bounds, and a lookup table
trades the OR trees for decode area. The thermometer nodes near both
extremes switch rarely, so energy estimates need node-specific
activity factors, and a right-rotate-only barrel drops the masker
altogether, saving two AND gates in the 32-bit 90 nm study.

## references

huntzicker_2008 -> S. Huntzicker, M. Dayringer, J. Soprano, A. Weerasinghe, D. M. Harris, D. Patil, "Energy-Delay Tradeoffs in 32-bit Static Shifter Designs", Proc. IEEE ICCD, 2008
