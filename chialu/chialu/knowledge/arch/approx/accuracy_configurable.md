# accuracy_configurable

Runtime accuracy selection in a feed-forward adder or multiplier: the
datapath is built for its exact configuration and mode signals decide
how much of it participates. In the ACA form later pipeline stages
correct the carry errors of an early approximate sum, so gating
successive correction stages yields one exact and several approximate
modes. Other grains act on segment carries: boundary multiplexers pick
the lower block's accurate carry or a locally predicted one, control signals merge basic units into longer sub-adders or widen
the prediction window, and the truncation form forces low-order
full-adder inputs to constants. Gating the idle logic turns each mode
into an energy point.

The reconfiguration grain fixes what accurate mode costs. Staged
correction keeps the recovery circuits present in every mode, so the
32-bit four-stage ACA in TSMC 65 nm draws 11.5% more power than a
conventional pipelined adder when exact and about half that adder's
power in its loosest mode. Sub-adder selection gives two independent
controls, because the maximum sub-adder length sets worst-case error
while the prediction length sets error rate, and its delay varies with
the selected carry path. A carry-chain switch that reuses the boundary
generate bit as the predicted carry adds no redundant computation, so
SARA is 39% smaller than RAP-CLA and 50% smaller than GDA in Nangate
45 nm; a larger segment count shortens the approximate path but raises
error and area. Truncation-width control keeps the ripple hardware and
suppresses activity rather than gating it, which beats a static
truncated adder at equal width only because it can retarget.

Error detection changes the execution contract. GeAr flags the
conjunction of a predicted carry and the preceding carry-out and
recomputes the selected sub-adders, so a one-cycle adder becomes a
k-cycle one in the worst case; per-block EDC in a multiplier costs about
4% to 7% area at 0.18 um and stalls a cycle after a miss. Without
detection the accuracy contract is statistical, with no universal error
bound, and the detector covers carry-prediction misses rather than
physical faults.

The family wins where the quality target or power budget moves at
runtime, for example switching a multiplier to approximate mode above a
power threshold, since a static approximate design of the same
configuration cannot adapt. It loses when the target is fixed: every
unit is sized for the most accurate mode, the control multiplexers sit
on the datapath, and outputs are invalid during a mode transition, so
freezing to the static point recovers the overhead. More modes buy
finer energy points at the cost of more switches, which matters most
in small multipliers.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/approx.py`: sub-adders with correction stages (the exact carry between blocks) enabled up to a static operating mode, the truncation-width grain zeroing the low blocks the mode drops; the runtime knob needs a control the unit interface lacks, so `operating_mode` fixes the point (the middle mode by default)); the ArithmeticError gate governs.

## references

kahng_kang2012 -> A. B. Kahng, S. Kang, "Accuracy-Configurable Adder for Approximate Arithmetic Designs", 49th Design Automation Conference (DAC), pp. 820-825, 2012
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
ye2013 -> R. Ye, T. Wang, F. Yuan, R. Kumar, Q. Xu, "On Reconfiguration-Oriented Approximate Adder Design and Its Application", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 48-54, 2013
shafique2015 -> M. Shafique, W. Ahmad, R. Hafiz, J. Henkel, "A Low Latency Generic Accuracy Configurable Adder", 52nd Design Automation Conference (DAC), 2015
xu2018 -> W. Xu, S. S. Sapatnekar, J. Hu, "A Simple Yet Efficient Accuracy-Configurable Adder Design", IEEE Transactions on VLSI Systems, vol. 26, no. 6, pp. 1112-1125, 2018
frustaci2019 -> F. Frustaci, S. Perri, P. Corsonello, M. Alioto, "Energy-Quality Scalable Adders Based on Nonzeroing Bit Truncation", IEEE Transactions on VLSI Systems, vol. 27, no. 4, pp. 964-968, 2019
lin2013 -> C.-H. Lin, I.-C. Lin, "High Accuracy Approximate Multiplier with Error Correction", IEEE International Conference on Computer Design (ICCD), pp. 33-38, 2013
akbari2017 -> O. Akbari, M. Kamal, A. Afzali-Kusha, M. Pedram, "Dual-Quality 4:2 Compressors for Utilizing in Dynamic Accuracy Configurable Multipliers", IEEE Transactions on VLSI Systems, vol. 25, no. 4, pp. 1352-1361, 2017
