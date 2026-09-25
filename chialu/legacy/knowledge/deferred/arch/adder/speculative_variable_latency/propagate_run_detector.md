---
family: speculative_variable_latency
pin: {detection: propagate_run_detector}
---
# propagate_run_detector

A combinational error detector that ORs the products of every
propagate chain of length K+1: a speculative adder that assumes no
carry travels further than K bits is wrong exactly when such a run
exists, so the detector flags the mispredicted sums without
producing any sum itself. Its inputs are the bit propagates, or the
checking nodes of a pruned prefix graph, and its products can be
augmented with kill conditions to sharpen the condition.

The detector is the pick for a synchronous or prefix-based speculative
adder because it is shallow, with a critical path about two thirds of
a fast adder's in 0.18-µm CMOS, and its products double as local late
enables for the affected sum cells. Its precision is the design
decision: a conservative, necessary-only condition never accepts a
wrong sum but aborts correct ones and raises the average latency,
while a necessary-and-sufficient condition lowers the error
probability, and Han-Carlson graphs mispredict less often than
Kogge-Stone ones. Completion sensing is the alternative when the
base adder is an asynchronous ripple chain.

## references

nowick1996 -> S. M. Nowick, "Design of a Low-Latency Asynchronous Adder Using Speculative Completion", IEE Proceedings - Computers and Digital Techniques, vol. 143, no. 5, pp. 301-307, 1996.
verma2008 -> A. K. Verma, P. Brisk, P. Ienne, "Variable Latency Speculative Addition: A New Paradigm for Arithmetic Circuit Design", Design, Automation and Test in Europe (DATE), 2008
esposito2015 -> D. Esposito, D. De Caro, E. Napoli, N. Petra, A. G. M. Strollo, "Variable Latency Speculative Han-Carlson Adder", IEEE Transactions on Circuits and Systems I, vol. 62, no. 5, pp. 1353-1361, 2015.
