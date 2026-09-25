# speculative_variable_latency

Addition timed by the actual carry rather than the worst case: the
average longest carry chain of a random n-bit addition is below log2 n
(5.6 stages at 40 bits), so the adder answers for that case and treats
a long chain as the exception. The completion-sensing form ripples
separate carry and no-carry signals through every position and
asserts done once one of the two has reached each stage. The
speculative form assumes no propagate chain exceeds K bits, computes
the sum with a pruned prefix graph or split carry chains, and runs a
detector that ORs every length-(K+1) propagate product; a detected
long chain aborts to a late carry path or stalls for a correction
cycle.

The execution style is variable-iteration. The speculation window sets the misprediction rate against the depth
of the speculative stage, and widening it moves the design toward a
fixed-latency prefix adder. The detection choice trades encoding
against a wide gate: completion sensing needs a dual-line chain and a
completion gate whose realization (cascaded two-input, unit-delay or
log-depth multiple-input) changes the average time and the
efficiency, must hold its inputs stable and cleared between
operations, and must avoid transient false completion; a propagate-run
detector is a shallow AND-OR network with a critical path about two
thirds of the base adder's in 0.18-µm CMOS, and its precision matters,
because a necessary-only condition aborts correct results while a
necessary-and-sufficient condition lowers the error probability. The
recovery choice trades asynchrony against a pipeline: awaiting
completion gives an early case a few gate delays faster than the
synchronous adder and a late case slower, while an extra correction
cycle keeps a one-cycle pipeline whose average latency is 1.0001
cycles when the speculation is correct in more than 99.99 percent of
cases, for a 1.5x average speedup over a synthesized fast adder at
0.18 µm. A purely combinational version gains nothing, because the
recovery path is as long as a conventional fast adder.

The base adder slot ranges from the ripple chains of the 1955
completion adders through a Brent-Kung tree with abort network to a
pruned Han-Carlson graph, which at 64 bits in 65 nm reaches about
225 ps against 280 ps non-speculative with 20 percent less area and
9 percent less power. The family wins under tight timing and loses
when the constraint is relaxed, because detection and correction
overhead then dominate; the completion-sensing form also pays more
elements per bit than a conventional adder and its input restrictions
can nullify the average-time gain.

The family's defining structure is sequential (the rare long carry takes a spare cycle), so the library has no combinational module for it; a seed that declares it stays behavioral and the family is listed as an exception (`adder_ext.SEQUENTIAL_ADD`).

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
gilchrist1955 -> B. Gilchrist, J. H. Pomerene, S. Y. Wong, "Fast Carry Logic for Digital Computers", IRE Transactions on Electronic Computers, vol. EC-4, pp. 133-136, 1955.
sklansky1960b -> J. Sklansky, "An Evaluation of Several Two-Summand Binary Adders", IRE Transactions on Electronic Computers, vol. EC-9, no. 2, pp. 213-226, 1960.
macsorley1961 -> O. L. MacSorley, "High-Speed Arithmetic in Binary Computers", Proceedings of the IRE, vol. 49, no. 1, pp. 67-91, 1961
nowick1996 -> S. M. Nowick, "Design of a Low-Latency Asynchronous Adder Using Speculative Completion", IEE Proceedings - Computers and Digital Techniques, vol. 143, no. 5, pp. 301-307, 1996.
verma2008 -> A. K. Verma, P. Brisk, P. Ienne, "Variable Latency Speculative Addition: A New Paradigm for Arithmetic Circuit Design", Design, Automation and Test in Europe (DATE), 2008
esposito2015 -> D. Esposito, D. De Caro, E. Napoli, N. Petra, A. G. M. Strollo, "Variable Latency Speculative Han-Carlson Adder", IEEE Transactions on Circuits and Systems I, vol. 62, no. 5, pp. 1353-1361, 2015.
