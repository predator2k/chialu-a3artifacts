# approximate_functional

Approximate division without a digit recurrence: leading-one detectors
normalize both operands, a cheap functional approximation replaces the
quotient loop, and a barrel shifter restores the exponent.
SEERAD rounds the divisor to 2^(K+L)/D from a few bits after its
leading one and forms D*A from shifted copies of A and one adder;
TruncApp inverts the retained divisor fraction bits, prepends a 1 and
multiplies by the truncated dividend; INZeD subtracts Mitchell binary
logarithms and a constant correction before inverse-log scaling;
DAXD/AAXD window k bits at each leading one and run a small exact core
divider; SAADI sums the series 1+|x|+...+|x|^t of x = 1-b with one
shared multiplier.

The method choice sets the error shape and the hardware. Uncorrected
logarithmic division errs on one side only, up to 12.5%, and the
divisor-rounding and truncated-reciprocal methods carry a comparable
ceiling, so their accuracy comes from more divisor groups or a longer
truncation length at more hardware and delay; SEERAD's four levels
span maximum errors from 37.5% to 6.25%. Constant bias correction in
the logarithm-subtraction path gives near-zero error bias (about
-0.02% for 32-by-16 INZeD) at 25 to 95 times lower area-delay product
than an accurate integer divider in TSMC 45 nm. Dynamic segmentation
keeps an exact core, so its error is bounded in quotient units and
shrinks with the window; static LSB truncation instead produces large
relative errors on small operands. The survey ranks AAXD for
high-accuracy, high-performance use, INZeD for the best efficiency at
moderate accuracy, and SEERAD-1 where error tolerance is high.

Segment or table width is the single accuracy knob of every method:
the window k, the truncation length t, the divisor group count or the
normalized width n. Bias correction is a constant subtraction, or a
per-order shift-add compensation in SAADI-EC, and moves the error
distribution toward zero at little cost. Runtime quality scaling is
real only where the datapath exposes it: SAADI terminates its series
at a chosen t and trades latency and energy over a 7x range, INZeD-t
truncates subtractor inputs, while SEERAD's levels and AAXD's k are
synthesized structures. All methods are single-cycle combinational
except SAADI, which iterates t multiplier cycles or replicates the
multiply-accumulate stage for II=1.

The family wins in error-resilient DSP with frequent division, such
as change detection, JPEG compression, foreground extraction and color
quantization, where it beats exact SRT and array dividers by an order
of magnitude or more in delay and energy; its advantage grows with
operand width because the steering logic grows as n log n while the
core grows as k^2. It loses whenever a worst-case relative bound in
the single-digit percent range is required, where curve-fitting or
LUT-heavy approximations and exact dividers remain.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/approx.py`: a reciprocal table product (divisor_round_pow2_lut, truncated_reciprocal_multiply on the dividend's top bits), exact small restoring cores on both operands' windows (dynamic_segment_exact_core), Mitchell's logarithms subtracted with a bias constant (log_subtract_corrected), or a one- to two-step Goldschmidt on the seed (iterative_quasi_convergence), the remainder back-multiplied without correction); the ArithmeticError gate governs.

## references

mitchell1962 -> J. N. Mitchell, "Computer Multiplication and Division Using Binary Logarithms", IRE Transactions on Electronic Computers, vol. EC-11, no. 4, pp. 512-517, 1962
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
zendegani2016 -> R. Zendegani, M. Kamal, A. Fayyazi, A. Afzali-Kusha, S. Safari, M. Pedram, "SEERAD: A High Speed yet Energy-Efficient Rounding-Based Approximate Divider", Design, Automation and Test in Europe (DATE), pp. 1481-1484, 2016
vahdat2017b -> S. Vahdat, M. Kamal, A. Afzali-Kusha, M. Pedram, Z. Navabi, "TruncApp: A Truncation-Based Approximate Divider for Energy Efficient DSP Applications", Design, Automation and Test in Europe (DATE), pp. 1635-1638, 2017
saadat2019 -> H. Saadat, H. Javaid, S. Parameswaran, "Approximate Integer and Floating-Point Dividers with Near-Zero Error Bias", 56th Design Automation Conference (DAC), 2019
hashemi2016 -> S. Hashemi, R. I. Bahar, S. Reda, "A Low-Power Dynamic Divider for Approximate Applications", 53rd Design Automation Conference (DAC), 2016
jiang2019 -> H. Jiang, L. Liu, F. Lombardi, J. Han, "Low-Power Unsigned Divider and Square Root Circuit Designs Using Adaptive Approximation", IEEE Transactions on Computers, vol. 68, no. 11, pp. 1635-1646, 2019
behroozi2019 -> S. Behroozi, J. Li, J. Melchert, Y. Kim, "SAADI: A Scalable Accuracy Approximate Divider for Dynamic Energy-Quality Scaling", 24th Asia and South Pacific Design Automation Conference (ASP-DAC), pp. 481-486, 2019
