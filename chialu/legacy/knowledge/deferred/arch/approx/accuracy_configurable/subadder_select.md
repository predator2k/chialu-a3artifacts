---
family: accuracy_configurable
pin: {reconfig_grain: subadder_select}
---
# subadder_select

The addition is partitioned into k-bit basic units joined by
multiplexers, and runtime control signals combine units into longer
sub-adders and choose how many low-order operand bits the carry-in
prediction observes. Each multiplexer selects a carry from the
less-significant unit or from a local prediction component; the
maximum sub-adder length mainly sets worst-case error and the
prediction length mainly sets error rate. ACAA instead varies the
width of its overlapping 2k-bit subadders.

GDA at N=32 with k=4 exposes 16 modes, GDA44 is exact, and the
reconfigurable GDA is 19% smaller than a reconfigurable ACA with under
1% accurate-mode delay increase (ye2013). ACAA's overlapped subadders
give O(log k) logical depth but a long synthesized critical path, and
multistage compensation can repair prediction errors at added latency
(jiang2017). The grain is the pick when many graded modes with two
independent accuracy controls are wanted and no recomputation cycle is
acceptable. It loses to carry_chain_switch on area, since SARA reports
half the routed area of GDA, and to correction_stage when the exact
mode must detect its own errors, because GDA has no error detector and
its delay varies with the control-selected carry path (jiang2020).

## references

ye2013 -> R. Ye, T. Wang, F. Yuan, R. Kumar, Q. Xu, "On Reconfiguration-Oriented Approximate Adder Design and Its Application", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 48-54, 2013
jiang2017 -> H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
