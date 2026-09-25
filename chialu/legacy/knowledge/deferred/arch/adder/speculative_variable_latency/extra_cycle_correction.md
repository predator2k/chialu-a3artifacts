---
family: speculative_variable_latency
pin: {recovery: extra_cycle_correction}
---
# extra_cycle_correction

The pipelined recovery: the speculative sum is valid after one clock
cycle whenever the detector stays silent, and a detected long carry
stalls new input while a recovery network, which is the pruned prefix
levels or a lookahead over the block carries, produces the exact sum
in the next cycle. A valid/stall handshake exposes the two latencies
to the surrounding pipeline, and the clock period covers the longer
of the speculative sum and the detector.

This recovery is the pick when the adder sits in a clocked pipeline
and errors are rare: with the speculative sum correct in more than
99.99 percent of cases the average latency is 1.0001 cycles, giving
a 1.5x average speedup over a synthesized fast adder at 0.18 µm, and
the 65-nm speculative Han-Carlson adder reaches its minimum delay
this way. It has no gain in a purely combinational setting, because
the recovery path is as long as a conventional adder, and it loses to
await_completion when the datapath is asynchronous. The FPGA split
adder applies the same policy across a guessed boundary carry.

## references

verma2008 -> A. K. Verma, P. Brisk, P. Ienne, "Variable Latency Speculative Addition: A New Paradigm for Arithmetic Circuit Design", Design, Automation and Test in Europe (DATE), 2008
esposito2015 -> D. Esposito, D. De Caro, E. Napoli, N. Petra, A. G. M. Strollo, "Variable Latency Speculative Han-Carlson Adder", IEEE Transactions on Circuits and Systems I, vol. 62, no. 5, pp. 1353-1361, 2015.
metzgen_2004 -> P. Metzgen, "A High Performance 32-bit ALU for Programmable Logic", Proc. ACM/SIGDA International Symposium on FPGAs, pp. 61-70, 2004
