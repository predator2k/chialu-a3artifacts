---
family: speculative_variable_latency
pin: {recovery: await_completion}
---
# await_completion

The self-timed recovery: no result is committed until the carry has
actually finished, so the adder signals done when its completion gate
fires or, in the speculative-completion form, when a matched
worst-case delay expires after the abort network has rejected the
early completion. The addition period therefore ends at the end of
the longest active carry sequence, and the remainder of the process
starts from that signal rather than from a fixed allowance.

This recovery is the pick inside an asynchronous datapath, where the
completion signal can control the next stage directly: the 1955
designs save almost eight-fold on average carry time over a
full-length allowance, and the speculative Brent-Kung adder finishes
early cases in five gate delays against seven for a synchronous
adder while late cases take nine. It loses to extra_cycle_correction
in a clocked pipeline, where a variable completion time cannot be
consumed and the rare long case is better absorbed as a stall.

## references

gilchrist1955 -> B. Gilchrist, J. H. Pomerene, S. Y. Wong, "Fast Carry Logic for Digital Computers", IRE Transactions on Electronic Computers, vol. EC-4, pp. 133-136, 1955.
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
kilburn1959 -> T. Kilburn, D. B. G. Edwards, D. Aspinall, "Parallel Addition in Digital Computers: A New Fast 'Carry' Circuit", Proceedings of the IEE - Part B, vol. 106, pp. 464-466, 1959.
nowick1996 -> S. M. Nowick, "Design of a Low-Latency Asynchronous Adder Using Speculative Completion", IEE Proceedings - Computers and Digital Techniques, vol. 143, no. 5, pp. 301-307, 1996.
