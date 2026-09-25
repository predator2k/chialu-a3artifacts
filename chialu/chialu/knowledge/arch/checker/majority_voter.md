# majority_voter

Bit-wise majority of N replica outputs: three (or an odd N) identical
modules feed voting circuits that deliver the value most of them
agree on, so one failed module (floor((N-1)/2) for NMR) is masked
rather than flagged, and a modified voter can indicate which module
was outvoted. It is the comparator of a duplication scheme whose
replication is three or more; unlike two_rail_tree it is not
self-checking, so the voter's own reliability bounds the arrangement
and sets an optimum module count.

The number of inputs is the replication of the scheme it terminates:
three is TMR with a two-out-of-three rule, and a wider odd N is the
NMR core of a hybrid scheme that keeps voting after its spares are
exhausted. The disagreement indication adds the detectors that name
the outvoted module, which the hybrid scheme needs to switch in a
spare and a plain TMR arrangement can omit. The voter is the
executive organ of von Neumann's multiplexed logic, where a majority
organ followed by a restoring organ drives a bundle's excitation
toward a stable extreme; the registry keeps the organ and not the
bundle.

Where the vote sits and how often it is replicated are choices of the
duplication family (voter_replication, voter_placement,
module_granularity): one voter or three per trio, at each driven
module's input, once at a shared source output, or omitted on a
direct connection. The trade is reliability against size. With
perfect voters, partitioning a computer into 60 triplicated modules
reaches a reliability of 0.95 over the nonredundant machine's mean
time to failure, and imperfect voters at about 0.999 give an optimum
near 1000 modules at about six times the nonredundant size. TMR
helps only when the unreplicated module reliability exceeds 0.5, and
whole-computer triplication loses to the simplex machine beyond its
mean time to failure, so each module's operating interval must be
short against its own. The analysis assumes permanent, independent
failures; transient faults are masked by the same vote. Against
two_rail_tree the voter buys masking instead of detection at three
replicas instead of two, and against duplication's compare it loses
the self-checking guarantee. Execution is feed-forward.

The generated checker (`chialu/targets/rtl/alu_checker.py`) realizes this family in the comparator slot under duplication: inputs - 1 reference copies and the output voted bit for bit, check_err = the output differs from the vote, disagreement_indication adds any disagreement among the inputs; under another family the direct compare stays, because a vote needs replicas.

## references

lyons_vanderkulk_1962 -> R. E. Lyons, W. Vanderkulk, "The Use of Triple-Modular Redundancy to Improve Computer Reliability", IBM Journal of Research and Development, vol. 6, no. 2, pp. 200-209, 1962
lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
von_neumann_1956 -> J. von Neumann, "Probabilistic Logics and the Synthesis of Reliable Organisms from Unreliable Components", in Automata Studies (AM-34), Princeton University Press, pp. 43-98, 1956
