---
family: accuracy_configurable
pin: {reconfig_grain: carry_chain_switch}
---
# carry_chain_switch

The carry chain is cut into segments, and a mode-controlled multiplexer
at each boundary selects the accurate carry from the lower segment or a
predicted carry. SARA divides an N-bit ripple-carry adder into K
segments and reuses the boundary full adder's generate bit as the
prediction, so no redundant computation and no detection or correction
circuit exists; SARA-DAR inspects W propagate bits above a boundary and
takes the prediction only when all W propagate.

SARA's effective critical paths span L, 2L, ..., K·L full-adder stages
across its K configurations, and a larger K shortens the approximate
path but raises expected error and area (xu2018). At 100 dB PSNR SARA4
and SARA8 reach about half the PDP of GDA in Nangate 45 nm with 50%
less routed area than GDA and 39% less than RAP-CLA, which applies the
same carry mux to lookahead carry generation, and SARA-DAR's
self-configuration keeps the JPEG DCT PSNR within 0.4 dB of an accurate
adder. The grain is the pick when area and energy per mode dominate and
no runtime detector is needed; it loses to correction_stage when the
exact mode must detect its own errors, and to subadder_select when
worst-case error and error rate need separate controls (jiang2020).

## references

xu2018 -> W. Xu, S. S. Sapatnekar, J. Hu, "A Simple Yet Efficient Accuracy-Configurable Adder Design", IEEE Transactions on VLSI Systems, vol. 26, no. 6, pp. 1112-1125, 2018
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
