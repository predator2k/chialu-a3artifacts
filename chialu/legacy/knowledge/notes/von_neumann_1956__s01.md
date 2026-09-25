---
handle: von_neumann_1956#s01
parent: von_neumann_1956
citation: J. von Neumann, "Probabilistic Logics and the Synthesis of Reliable Organisms from Unreliable Components", in Automata Studies (AM-34), Princeton University Press, pp. 43-98, 1956
chapter: PROBABILISTIC LOGICS AND THE SYNTHESIS OF RELIABLE ORGANISMS FROM UNRELIABLE COMPONENTS
pdf_pages: 0-55
status: ok
kind: book_chapter
unit_classes: [other]
formats: [binary, analog excitation-level]
authority: textbook
pages_read: 56 / 56
---

## summary
The chapter defines logical automata built from unreliable organs and analyzes two error-control methods: triplicated networks with majority voting and multiplexed bundles with executive/restoring stages. Triplication provides bounded error only below component-error thresholds but grows exponentially with logical depth, while multiplexing can make final malfunction probability arbitrarily small by increasing bundle size. The chapter also develops an analog interpretation of bundle excitation levels, but that interpretation has an intrinsic noise limit.

## families
### duplication  (role: proposes)
mechanism: The same information enters three identical copies of a network, and a majority organ votes on each corresponding output. A rigorous recursive construction replaces each depth-reduced subnetwork by three error-safe copies, applies majority restoration, and then performs the next logical operation.   # p.22, p.24-p.26
choices:
  replication: 3   # p.22
  comparison_point: UNKNOWN   # p.22
  temporal_stagger: false   # p.22
new_choices:
  voter_structure: majority_organ — three-input organ selects the state carried by at least two inputs   # p.22
slots:
  comparator: UNKNOWN   # p.22
parameters: 3 copies; majority-organ fan-in 3; logical depth μ = n(P)   # p.22, p.24, p.26
results:
| metric | value | unit | technology / device | baseline | condition | page |
| component-error threshold, heuristic | ε < 1/6 | probability | abstract | total irrelevance at ε ≥ 1/6 | independent errors and special-case majority inputs | p.23 |
| stable error level | η₀ = ε + 3ε² + ... | probability | abstract | component error ε | heuristic repeated triplication | p.23 |
| example ultimate error | ~10 | % | abstract | ~8% component error | heuristic analysis | p.23 |
| component-error threshold, rigorous construction | ε < .0073 | probability | abstract | none | smallest acceptable root of equation (13) | p.26 |
| limiting stable error | .060 | probability | abstract | none | double root at ε = .0073 | p.26 |
| small-error expansion | η₁ = 4ε + 152ε² + ... | probability | abstract | component error ε | rigorous recursive construction | p.26 |
| component error for 2% ultimate error | .41 | % | abstract | 2% ultimate error | ε = .0041 | p.26 |
| organ-count growth | about 3^μ | basic organs | abstract | original network depth μ | rigorous recursive construction | p.26 |
| organ count at μ = 160 | ~2 x 10^76 | basic organs | abstract | single network | non-multiplexing procedure | p.44 |
| organ count at μ = 200 | ~2.5 x 10^95 | basic organs | abstract | μ = 160 | non-multiplexing procedure | p.44 |
errors_and_checks: Each output has a separate incorrect-message probability bounded by η₁; the analysis assumes independently malfunctioning organs with error probability ε.   # p.19, p.24
conditions: The heuristic voter improves error only when its three inputs should carry the same state and their errors are independent. The rigorous construction controls error but is impractical because its organ count grows exponentially with logical depth.   # p.21-p.26
evidence: Sections 8.2-8.4; Figures 26-29; equations (9)-(13)

## taxonomy
* Logical automata   # p.1-p.13
  * Circle-free networks -> unmapped   # p.13
  * Networks with cycles/feedback -> unmapped   # p.13
  * Basic-organ systems   # p.8-p.12
    * conjunction/disjunction/negation organs -> unmapped   # p.8-p.10
    * double-line representation -> unmapped   # p.9-p.10
    * Sheffer-stroke universal organ -> unmapped   # p.11-p.12
    * majority universal organ -> unmapped   # p.12
* Error control   # p.18-p.47
  * Single-line automata   # p.21-p.26
    * repeated identical networks with majority voting -> duplication   # p.22-p.23
    * recursively triplicated error-safe network -> duplication   # p.24-p.26
  * Multiple-line automata   # p.20-p.47
    * majority executive organ plus majority restoring organ -> multiplexed_restorative_logic   # p.27-p.30
    * Sheffer executive organ plus two-stage Sheffer restoring organ -> multiplexed_restorative_logic   # p.31-p.40
    * randomized bundle permutation between stages -> multiplexed_restorative_logic   # p.29, p.45-p.47
* Analog bundle interpretation   # p.48-p.54
  * continuous excitation-level algebra -> unmapped   # p.48-p.51
  * pulse-density/frequency modulation -> unmapped   # p.52-p.53
  * multilevel stable-fixpoint restoration -> multiplexed_restorative_logic   # p.53-p.54

## primary_sources
* Turing, 1936 — computable numbers and unlimited-memory automata equivalent to effectively constructive logic   # p.8, p.13, p.55
* McCulloch and Pitts, 1943 — logical calculus of nerve nets and the circle-free-machine classification   # p.1, p.8, p.13, p.55
* Shannon, 1948 — information measure and mathematical communication theory   # p.14-p.15, p.55
* Szilard, 1929 — information/entropy connection implicit in thermodynamic analysis   # p.15, p.55

## new_families
### multiplexed_restorative_logic  (domain: checker: concurrent error detection, closest: duplication, why_not: duplication replicates whole units, while multiplexing represents every signal by a large bundle and requires executive/restoring organs plus randomized interconnect)
mechanism: Each logical message is carried by N lines. More than (1-A)N stimulated lines represents a positive message, fewer than AN represents a negative message, and intermediate levels represent malfunction. Every logical operation uses a bundle-wide executive organ followed by a restoring organ that drives excitation toward a stable extreme. Permutations between stages randomize line associations so errors combine statistically rather than recur through identical feedback paths.   # p.20-p.21, p.27-p.40, p.45-p.47
choices:
  bundle_size: positive integer N   # p.20, p.27
  fiduciary_level: real A with 0 < A < 1/2   # p.20
  executive_organ: {majority, sheffer_stroke}   # p.27-p.32
  restoring_stages: {one_majority_stage, two_sheffer_stages}   # p.28-p.32
  randomizing_permutation: Bool   # p.29, p.45-p.47
  signal_interpretation: {binary_thresholded, analog_excitation_level}   # p.20-p.21, p.48-p.49
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum majority restoration | .096 | excitation-level change | abstract | unrestored bundle | input level .212 or .788 | p.30 |
| Sheffer restoration discrimination level | .618 | excitation level | abstract | majority level .5 | two Sheffer stages | p.32 |
| favorable fiduciary level | .07 | excitation level | abstract | none | complete quantitative Sheffer analysis | p.40 |
| maximum component-error probability | .0107 | probability | abstract | none | finite fixed bundle analysis | p.40 |
| analyzed component-error probability | .005 | probability | abstract | none | numerical evaluation | p.41 |
| malfunction estimate parameter | k = .062√N | dimensionless | abstract | none | large N and ε = .005 | p.41 |
| malfunction estimate | p(N) ~ (1/√N)10^(-8.6N/10,000) | probability | abstract | none | large N and ε = .005 | p.41 |
| computing-machine bundle size | N = 14,000 | lines | vacuum tubes | 2500 tubes, 5 microseconds/actuation | 8-hour mean free path between errors | p.42 |
| improved malfunction probability | 4.5 x 10^-17 | probability | vacuum tubes | N = 14,000 | N = 17,500 | p.42 |
| reliability improvement | 1,600 | times | vacuum tubes | N = 14,000 | 25% increase to N = 17,500 | p.42 |
| nervous-system bundle size | N = 28,000 | lines | neurons | 10,000-year mean free path | uncorrected organ-count estimate | p.42 |
| corrected nervous-system bundle size | N = 23,000 | lines | neurons | N = 28,000 | reduced relevant organ count | p.42 |
| typical demanding bundle size | ~20,000 | lines | abstract | none | examined industrial/natural requirements | p.43 |
| line-count overhead | N | times | abstract | single-line network | multiplexed construction | p.43 |
| organ-count overhead | 3N | times | abstract | single-organ network | executive plus restoring network | p.43 |
evidence: Sections 7.4 and 9-13; Figures 25, 30-38, 40-44; equations (14)-(30)

## space_gaps
* duplication.comparator needs a majority_voter family or slot value because the chapter's triplication schemes vote rather than compare two replicas.   # p.22-p.26
* The checker vocabulary lacks bundle-level redundancy with fiduciary thresholds, executive/restoring stages, and randomized interconnect.   # p.20-p.21, p.27-p.47
* multiplexed_restorative_logic needs an excitation_level_fixed_points choice for binary or multilevel analog restoration.   # p.53-p.54

## open_questions
* The rigorous properties of a suitable “randomizing” permutation are proposed but not proved.   # p.45-p.47
* The analysis assumes a constant independent error probability per organ; state/history/environment dependence and neuron-to-neuron variation remain unanalyzed.   # p.19, p.47
* The chapter does not establish whether biological nervous systems actually implement the proposed multiplexing organization.   # p.44-p.45
