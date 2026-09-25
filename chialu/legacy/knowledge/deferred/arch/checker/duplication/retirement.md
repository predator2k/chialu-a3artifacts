---
family: duplication
pin: {comparison_point: retirement}
---
# retirement

A trailing checker: the core executes speculatively and hands each
completed instruction, its operands and result in program order to a
checker that recomputes the functional result and re-executes
architected register/memory communication, then compares at
retirement. A mismatch injects the corrected value, flushes the core
and restarts; a watchdog timer catches loss of forward progress. The
checker duplicates program function only, without prediction,
renaming or scheduling.

Comparing at retirement decouples the replica from the core's timing,
so the checker can use slower, area-efficient algorithms and a longer
latency: with enough buffering the average core slowdown is about 3
percent with no extra ports and near zero with an added cache read
port, and doubling or quadrupling checker latency adds under 1
percent. It loses to per-cycle comparison on what it guarantees: the
checker is a trusted component that may itself need replication,
architected storage must carry error-correcting codes, and no
measured coverage is reported. At the DNN level the same comparison
point is the final prediction or the full softmax likelihood vector,
which serves as the coverage baseline for checksum schemes at 64
times their MAC operations.

The generated checker compares at the module's outputs; comparison_point is not a pin it reads.

## references

austin_1999 -> T. M. Austin, "DIVA: A Reliable Substrate for Deep Submicron Microarchitecture Design", Proc. MICRO-32, pp. 196-207, 1999
ozen_2025 -> Ozen, Ozerdem, Orailoglu, "Linear Algorithmic Checksums for Deep-Neural-Network Error Detection: Fundamentals and Recent Advancements", IEEE Design & Test, pp. 26-40, 2025
