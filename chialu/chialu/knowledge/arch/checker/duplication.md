# duplication

Concurrent error detection by replication: two identical copies of the
unit execute the same operation and a comparator flags any
disagreement, or three copies feed a majority voter that masks the
disagreeing output instead of only detecting it. The copies run in
lockstep under a common clock, or the checking copy trails the
functional copy by one cycle so the leading result is usable before
the compare, or a trailing checker re-executes each retired
instruction in program order and compares at retirement. A mismatch
stops the clock, invokes reset/restore/resume from protected state, or
injects the corrected value, flushes the core, and restarts.

Replication count trades detection for masking. A duplex pair detects
but cannot say which copy failed, nor distinguish a module fault from
a comparator fault; a triplicated unit masks one failure immediately
at only voter delay, and costs about 3.6x the gates of the unprotected
ripple adder in abstract gate counts. Voting pays off only when the
modules are reliable enough, and a voter that fails more often than a
module makes the redundant system worse than the simplex one; the
recursive triplication that keeps error bounded regardless of depth
grows organ count exponentially and is impractical.

The comparison point trades checker simplicity against exposure. A
per-cycle cross-compare of complete I-unit and E-unit copies keeps
checking logic out of the arithmetic critical path and reaches almost
100% coverage, at the price of a second full unit. A one-cycle stagger
lets the leading copy's result be consumed before the delayed
comparison, which is how exponent and control macros are protected in
z196 at under 14% of accelerator area. A retirement-point checker
duplicates program function only, may use slower area-efficient
algorithms, and buffering makes the core insensitive to checker
latency, so DIVA slows the core about 3% on average without extra
ports.

The contract has two holes: identical transients in both copies and
faults in the comparator itself go undetected, so the comparator and
the checker stay trusted components. The family is the coverage
ceiling and the reference against which cheaper checkers are measured,
and it wins where logic does not preserve an arithmetic code, such as
control, exponent, and decimal engines, or where one processor's
erroneous result would corrupt many downstream values while leaving a
checksum consistent. It loses to residue on arithmetic dataflow and to
algorithmic checksums on DNN inference, where full duplication doubles
the work.

The generated checker (`chialu/targets/rtl/alu_checker.py`) realizes this family: a pruned copy of the reference datapath compared bit for bit; replication 3 compares two copies, and the majority_voter comparator votes the copies and the output.

## references

burks1946 -> A. W. Burks, H. H. Goldstine, J. von Neumann, "Preliminary Discussion of the Logical Design of an Electronic Computing Instrument", Institute for Advanced Study report, 1946 (reprinted in B. Randell, The Origins of Digital Computers, Springer).
von_neumann_1956 -> J. von Neumann, "Probabilistic Logics and the Synthesis of Reliable Organisms from Unreliable Components", in Automata Studies (AM-34), Princeton University Press, pp. 43-98, 1956
lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
austin_1999 -> T. M. Austin, "DIVA: A Reliable Substrate for Deep Submicron Microarchitecture Design", Proc. MICRO-32, pp. 196-207, 1999
slegel_1999 -> T. J. Slegel et al., "IBM's S/390 G5 Microprocessor Design", IEEE Micro, vol. 19, no. 2, pp. 12-23, 1999
lipetz_schwarz_2011 -> D. Lipetz, E. Schwarz, "Self Checking in Current Floating-Point Units", Proc. 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 73-76, 2011
carlough_2011 -> Carlough, Collura, Mueller, Kroener, "The IBM zEnterprise-196 Decimal Floating-Point Accelerator", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), 2011
townsend_2003 -> W. J. Townsend, J. A. Abraham, E. E. Swartzlander, "Quadruple Time Redundancy Adders", Proc. 16th IEEE Symposium on Computer Arithmetic (ARITH-16), pp. 250-256, 2003
