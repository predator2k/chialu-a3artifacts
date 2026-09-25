---
family: speculative_variable_latency
pin: {detection: completion_sensing}
---
# completion_sensing

The carry-completion adder's detector: each stage carries two chains,
one for a 1 carry and one for a 0 carry, both starting off, and a
stage whose addend bits determine the carry starts a sequence on the
proper chain while incoming sequences stop there. Every stage forwards
exactly one state only after receiving a lower-order state, and an
n-input AND gate, or a cascaded or tree equivalent, asserts completion
when either chain has reached every position; the sum pulse follows.

The detector wins where the whole adder is asynchronous and the
average, not the worst case, sets throughput, which is the setting of
the 1955 accumulators and the independent-dependent carry adder. It
pays with 19 elements per bit against 8 for a conventional diode
adder, a completion gate whose realization decides the efficiency,
inputs that must stay stable and be cleared before the next
operation, and the risk of transient false completion. A propagate-run
detector is the pick when the adder is synchronous and the base
adder is a prefix tree, because it needs no dual-line chain.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
gilchrist1955 -> B. Gilchrist, J. H. Pomerene, S. Y. Wong, "Fast Carry Logic for Digital Computers", IRE Transactions on Electronic Computers, vol. EC-4, pp. 133-136, 1955.
macsorley1961 -> O. L. MacSorley, "High-Speed Arithmetic in Binary Computers", Proceedings of the IRE, vol. 49, no. 1, pp. 67-91, 1961
sklansky1960b -> J. Sklansky, "An Evaluation of Several Two-Summand Binary Adders", IRE Transactions on Electronic Computers, vol. EC-9, no. 2, pp. 213-226, 1960.
lehman_burla1961 -> M. Lehman, N. Burla, "Skip Techniques for High-Speed Carry-Propagation in Binary Arithmetic Units", IRE Transactions on Electronic Computers, vol. EC-10, pp. 691-698, 1961.
