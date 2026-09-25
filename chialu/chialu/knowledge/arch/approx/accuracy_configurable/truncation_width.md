---
family: accuracy_configurable
pin: {reconfig_grain: truncation_width}
---
# truncation_width

The accuracy knob is how many low-order bits are dropped at runtime
while the full-width hardware stays in place. In the nonzeroing
truncation adder one control bit per truncatable position forces that
full adder's inputs to 0 and 1, suppressing its dynamic energy with
the ripple-carry chain unchanged. In TOSAM the hardware is sized for
the largest truncation and rounding pair (h,t), and mode signals
power-gate unused adders and AND gates and select the active
partial-product subset.

The grain adds no redundant logic: the nonzeroing adder keeps the same
RCA for every k from 0 to 8 at 16 bits and saves up to 20% energy
against a static approximate adder at equal k in 28-nm FDSOI, and a
static design cannot follow a changing quality target (frustaci2019).
TOSAM's 32-bit T2, T6 and T9 modes share one 9-bit final adder, T2 is
the fastest and lowest-power mode, and the lower modes carry idle
power-gated hardware because every unit is sized for the largest (h,t)
(vahdat2019). The grain is the pick when an existing truncated design
must scale energy against quality without changing its critical path.
It has no error detection, so correction_stage wins when the exact mode
must detect its own errors.

## references

frustaci2019 -> F. Frustaci, S. Perri, P. Corsonello, M. Alioto, "Energy-Quality Scalable Adders Based on Nonzeroing Bit Truncation", IEEE Transactions on VLSI Systems, vol. 27, no. 4, pp. 964-968, 2019
vahdat2019 -> S. Vahdat, M. Kamal, A. Afzali-Kusha, M. Pedram, "TOSAM: An Energy-Efficient Truncation- and Rounding-Based Scalable Approximate Multiplier", IEEE Transactions on VLSI Systems, vol. 27, no. 5, pp. 1161-1173, 2019
