---
handle: austin_1999
citation: T. M. Austin, "DIVA: A Reliable Substrate for Deep Submicron Microarchitecture Design", Proc. MICRO-32, pp. 196-207, 1999
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [UNKNOWN]
authority: landmark
pages_read: 196-207 / 12
---

## summary
DIVA adds a functional checker at retirement that recomputes instruction results, re-executes register/memory communication, and permits only verified results to commit. Detected errors are corrected before the core is flushed and restarted. Detailed timing simulation reports a 3% average slowdown for the least-resourced checker configuration. # p.198, p.199-p.200, p.203, p.207

## families
### duplication  (role: extends)
mechanism: The DIVA core executes speculatively and sends each completed instruction, its operands, and its result in program order to a trailing checker. Parallel CHKcomp and CHKcomm pipelines independently recompute functional results and re-execute architected register/memory communication. A mismatch supplies a corrected value, flushes the core, and restarts execution. A watchdog detects loss of forward progress. The checker duplicates program function rather than performance mechanisms such as prediction, renaming, and dynamic scheduling. # p.198-p.200, p.202, p.205
choices:
  replication: 2   # p.199
  comparison_point: retirement   # p.198-p.199
new_choices:
  replica_scope: function_only — The checker duplicates architectural function while excluding core performance mechanisms.   # p.202, p.205
  communication_verification: in_order_reexecution — CHKcomm rereads architected register/memory operands and compares them with core-supplied inputs.   # p.199-p.200
  recovery: correct_flush_restart — The checker injects the corrected value, resets its pipelines, flushes the core, and restarts execution.   # p.200-p.201
  forward_progress_watchdog: true — Timer expiration injects the next instruction so the checker can complete it and restart the core.   # p.198, p.200
  checker_datapath: heterogeneous_simple_algorithms — CHKcomp may use slower, area-efficient algorithms rather than duplicate the core implementation.   # p.199, p.205
slots:
  comparator: UNKNOWN   # p.199-p.200
parameters: 4-instruction-wide checker; CHKcomp latency one cycle longer than the checked functional unit; 2-cycle CHKcomm baseline; watchdog reset to 60 cycles; baseline resources are 4 shared architected-register ports and 2 shared cache ports.   # p.203
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average core slowdown | 3% | % | simulation; node/device UNKNOWN; 1999 | unchecked core | no extra register-file or memory ports (+O) | p.203 |
| maximum benchmark slowdown | 14% | % | simulation; node/device UNKNOWN; 1999 | unchecked core | Turbo3D, no extra ports (+O) | p.203 |
| average core slowdown | 0.1% | % | simulation; node/device UNKNOWN; 1999 | unchecked core | one extra data-cache read port (+M) | p.204 |
| average core slowdown | 0.03% | % | simulation; node/device UNKNOWN; 1999 | unchecked core | extra register and memory ports (+R+M) | p.204 |
| slowdown increase | 0.7% | % | simulation; node/device UNKNOWN; 1999 | baseline DIVA checker (+O) | 2x checker latency | p.204 |
| slowdown increase | 0.8% | % | simulation; node/device UNKNOWN; 1999 | baseline DIVA checker (+O) | 4x checker latency | p.204 |
| average core slowdown | 2.6% | % | simulation; node/device UNKNOWN; 1999 | baseline DIVA checker (+O) | one random exception per 1000 core cycles | p.204 |
| exception-handling penalty | at least 8 | cycles | simulation; node/device UNKNOWN; 1999 | fault-free DIVA execution | penalty can increase while the faulty instruction reaches retirement | p.204 |
errors_and_checks: The paper claims detection and recovery of all permanent/transient functional and electrical faults in the core, provided that the checker is functionally correct/electrically robust, architected storage uses error-correcting coding, and the fetched-instruction record is communicated correctly. No measured coverage, alias rate, or false-alarm rate is reported.   # p.198-p.200
conditions: Sufficient buffering makes performance largely insensitive to checker latency. Shared cache/register ports can cause structural hazards, with cache bandwidth producing the larger measured effect. Frequent exceptions incur restart costs, and complete core lockup performs poorly while execution waits for the 60-cycle watchdog. The checker itself remains a trusted component and may require replication or TMR for protection against checker faults.   # p.202-p.204, p.206
evidence: Figure 1 (p.198); Figures 2-4 and §§2.1-2.4 (p.199-p.202); Table 1 and §§3.1-3.4 (p.202-p.204); Figures 6-7 and §§3.5-3.7 (p.204-p.205); Figures 8-9 and §5 (p.206); §6 (p.206-p.207)

## new_families
none

## space_gaps
* The duplication family needs choices for function-only heterogeneous replicas, independent communication checking, corrective restart, and watchdog-based forward-progress recovery. # p.198-p.200, p.205

## open_questions
* The paper does not quantify checker area or power because no circuit-level or silicon implementation was built. # p.202, p.204-p.205
* The exact catastrophic-failure and graceful-degradation performance fractions are illegible in the supplied document text. # p.204, p.206
