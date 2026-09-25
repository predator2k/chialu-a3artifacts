---
family: lut_plus_poly
pin: {basis: minimax_remez}
---
# minimax_remez

Minimax coefficients for the local polynomial: for each interval the
coefficients come from a Remez-style least-maximum fit of the
residual function over the reduced interval, so a given error target
is met at the lowest degree, degree 3 in single and 6 in double
precision for the table-driven exponential with 32 entries and
degree 2 for a hardware interpolator with 6 or 7 index bits. An
enhanced minimax generation rounds C1, adjusts C2 for that rounding
and recomputes C0 to compensate for both.

The minimax basis is the default whenever the coefficient store is
fixed at design time, because degree sets the multiplier count and
latency, and the FPGA generators sweep degrees 1 to 4 with
per-coefficient widths from a minimax fit packed around DSP input
widths. The fit is per interval, so a correctly rounded library
evaluates a degree-7 quick polynomial and a degree-14 accurate one
over the same 128 reduction entries, and Gal's accurate tables also
use a minimax polynomial in the offset from the perturbed point. A
per-function bias then centers the aggregate error from coefficient
and squarer truncation. Taylor coefficients replace it only when the
constants must be generated on the fly under a small constant memory
or when a two-term expansion suffices.

The library's module for lut_plus_poly realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
tang_1989 -> P. T. P. Tang, "Table-Driven Implementation of the Exponential Function in IEEE Floating-Point Arithmetic", ACM Transactions on Mathematical Software, vol. 15, no. 2, pp. 144-157, 1989
oberman_2005 -> S. F. Oberman, M. Y. Siu, "A High-Performance Area-Efficient Multifunction Interpolator", 17th IEEE Symposium on Computer Arithmetic (ARITH-17), pp. 272-279, 2005
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
dedinechin_2007 -> F. de Dinechin, C. Q. Lauter, J.-M. Muller, "Fast and Correctly Rounded Logarithms in Double-Precision", RAIRO Theoretical Informatics and Applications, vol. 41, no. 1, pp. 85-102, 2007
