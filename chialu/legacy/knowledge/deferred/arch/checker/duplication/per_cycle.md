---
family: duplication
pin: {comparison_point: per_cycle}
---
# per_cycle

Lockstep duplex comparison: two identical copies of the unit run the
same instruction stream under one clock, and on every clock cycle a
comparator (the recovery unit and L1 cache in the S/390 G5, a circuit
over the accumulator in the 1946 proposal) matches their outputs; a
mismatch stops the machine or invokes hardware recovery before the
result is used. The second copy may run one cycle behind so the
leading result is usable before the delayed compare.

Per-cycle comparison is the coverage ceiling: the G5 recovery
algorithm is described as essentially 100 percent effective for any
transient processor error, and the duplicated z900 and z990 units
reach almost 100 percent detection, with only identical transients in
both copies and comparator faults escaping. The price is a full
second copy plus comparator, at least 100 percent hardware redundancy
and about 29 percent longer calculation time for a 32-bit adder in a
2-micron gate array; it wins where checking logic must stay out of
arithmetic critical paths and results must be trusted the cycle they
appear, which is why z10 keeps it for the exponent dataflow. A
retirement-point checker instead compares only architected results
and tolerates a slower, simpler replica.

The generated checker compares at the module's outputs; comparison_point is not a pin it reads.

## references

lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
burks1946 -> A. W. Burks, H. H. Goldstine, J. von Neumann, "Preliminary Discussion of the Logical Design of an Electronic Computing Instrument", Institute for Advanced Study report, 1946 (reprinted in B. Randell, The Origins of Digital Computers, Springer).
slegel_1999 -> T. J. Slegel et al., "IBM's S/390 G5 Microprocessor Design", IEEE Micro, vol. 19, no. 2, pp. 12-23, 1999
lipetz_schwarz_2011 -> D. Lipetz, E. Schwarz, "Self Checking in Current Floating-Point Units", Proc. 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 73-76, 2011
johnson_1988 -> B. W. Johnson, J. H. Aylor, H. H. Hana, "Efficient Use of Time and Hardware Redundancy for Concurrent Error Detection in a 32-Bit VLSI Adder", IEEE Journal of Solid-State Circuits, vol. 23, no. 1, pp. 208-215, 1988
