---
handle: mrazek2016
citation: V. Mrazek, S. S. Sarwar, L. Sekanina, Z. Vasicek, K. Roy, "Design of Power-Efficient Approximate Multipliers for Approximate Artificial Neural Networks", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), 2016
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [int8, int12]
authority: incremental
pages_read: 8 / 8
---

## summary
The paper uses Cartesian Genetic Programming (CGP) to evolve gate-level approximate multipliers under maximum-error/exact-zero constraints for uniform neural networks. Retraining lets the MNIST/SVHN networks trade classification accuracy for multiplier power/area reductions.

## families
### approximate_logic_synthesis  (role: extends)
mechanism: CGP represents multiplier netlists as directed acyclic graphs of two-input Boolean nodes. Mutation changes a gate function/input connection/output connection, while exhaustive candidate evaluation minimizes the number of active gates subject to maximum arithmetic error and exact multiplication by zero. # p.3–4
choices:
  method: cgp_evolution  # p.3–4
  error_constraint: wce  # p.3
  formal_verification: none  # p.3–4
new_choices:
  exact_zero_constraint: Bool — requires M(a,0)=M(0,a)=0 for every operand  # p.3
slots:
  none
parameters: 7-bit and 11-bit unsigned cores; manual sign extension to 8-bit and 12-bit; ε={0.5%, 1%, 2%, 5%, 10%, 15%, 20%}; 300/900 CGP nodes; λ=5; h=1; 30/120 minute searches  # p.4–5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power | 250.0 | µW | IBM 45nm | accurate multiplier | int8, ε=0% | p.7 |
| power | 201.0 | µW | IBM 45nm | int8 ε=0% | int8, ε=0.5% | p.7 |
| power | 175.0 | µW | IBM 45nm | int8 ε=0% | int8, ε=1% | p.7 |
| power | 107.0 | µW | IBM 45nm | int8 ε=0% | int8, ε=2% | p.7 |
| power | 58.6 | µW | IBM 45nm | int8 ε=0% | int8, ε=5% | p.7 |
| power | 45.2 | µW | IBM 45nm | int8 ε=0% | int8, ε=10% | p.7 |
| power | 22.3 | µW | IBM 45nm | int8 ε=0% | int8, ε=15% | p.7 |
| power | 22.9 | µW | IBM 45nm | int8 ε=0% | int8, ε=20% | p.7 |
| area | 440.0 | µm | IBM 45nm | accurate multiplier | int8, ε=0% | p.7 |
| area | 367.7 | µm | IBM 45nm | int8 ε=0% | int8, ε=0.5% | p.7 |
| area | 316.6 | µm | IBM 45nm | int8 ε=0% | int8, ε=1% | p.7 |
| area | 218.3 | µm | IBM 45nm | int8 ε=0% | int8, ε=2% | p.7 |
| area | 129.9 | µm | IBM 45nm | int8 ε=0% | int8, ε=5% | p.7 |
| area | 109.5 | µm | IBM 45nm | int8 ε=0% | int8, ε=10% | p.7 |
| area | 63.2 | µm | IBM 45nm | int8 ε=0% | int8, ε=15% | p.7 |
| area | 65.8 | µm | IBM 45nm | int8 ε=0% | int8, ε=20% | p.7 |
| power | 831.0 | µW | IBM 45nm | accurate multiplier | int12, ε=0% | p.7 |
| power | 417.0 | µW | IBM 45nm | int12 ε=0% | int12, ε=0.5% | p.7 |
| power | 475.0 | µW | IBM 45nm | int12 ε=0% | int12, ε=1% | p.7 |
| power | 284.0 | µW | IBM 45nm | int12 ε=0% | int12, ε=2% | p.7 |
| power | 247.0 | µW | IBM 45nm | int12 ε=0% | int12, ε=5% | p.7 |
| power | 125.0 | µW | IBM 45nm | int12 ε=0% | int12, ε=10% | p.7 |
| power | 115.0 | µW | IBM 45nm | int12 ε=0% | int12, ε=15% | p.7 |
| power | 111.0 | µW | IBM 45nm | int12 ε=0% | int12, ε=20% | p.7 |
| area | 1175.0 | µm | IBM 45nm | accurate multiplier | int12, ε=0% | p.7 |
| area | 664.9 | µm | IBM 45nm | int12 ε=0% | int12, ε=0.5% | p.7 |
| area | 720.8 | µm | IBM 45nm | int12 ε=0% | int12, ε=1% | p.7 |
| area | 523.8 | µm | IBM 45nm | int12 ε=0% | int12, ε=2% | p.7 |
| area | 483.0 | µm | IBM 45nm | int12 ε=0% | int12, ε=5% | p.7 |
| area | 285.0 | µm | IBM 45nm | int12 ε=0% | int12, ε=10% | p.7 |
| area | 262.4 | µm | IBM 45nm | int12 ε=0% | int12, ε=15% | p.7 |
| area | 252.5 | µm | IBM 45nm | int12 ε=0% | int12, ε=20% | p.7 |
errors_and_checks: Every candidate has absolute error at most ε·(2^(2n)−1), and multiplication by zero is exact for either operand; candidate behavior is exhaustively evaluated over all operand pairs. # p.3, p.5
conditions: The synthesized approximate multipliers do not prolong the delay of their accurate starting multipliers. The method excludes ε above 20% because classification accuracy drops significantly. # p.6, p.5
evidence: §3.1–3.2, §4.1, §5.1, Figure 5, Table 1

### approximate_mac_nn  (role: proposes)
mechanism: One selected approximate multiplier is used uniformly throughout the approximated fully connected/convolutional layers. Each candidate network is retrained, tested, and accepted against an application quality constraint; otherwise ε is reduced and the process repeats. # p.4
choices:
  multiplier_source: evolved_cgp  # p.3–4
  error_bias_policy: unconstrained  # p.3
  precision_scaling: none  # p.4–5
  retraining: true  # p.4, p.6
new_choices:
  exact_zero_multiplication: Bool — preserves the dominant zero-operand cases in the evaluated networks  # p.3
slots:
  none
parameters: MLP 28×28-300-10 for MNIST; LeNet-6 for SVHN; int8/int12; 852 multipliers and 2×852 networks; 5 or 10 retrains; 3 GHz for int8 and 2.5 GHz for int12 neurons  # p.4–6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplication power reduction | 81.9% | % | IBM 45nm | accurate int8 multiplier | ε=10%; SVHN accuracy −1.89%; MNIST accuracy −0.36% | p.7 |
| multiplication power reduction | 91% | % | IBM 45nm | accurate int8 multiplier | ε=15%; SVHN accuracy degradation less than 2.80% | p.7 |
| SVHN accuracy | 87.00 | % | IBM 45nm | accurate network | int8, ε=0% | p.7 |
| SVHN accuracy | 86.54 | % | IBM 45nm | int8 ε=0% | int8, ε=5% | p.7 |
| SVHN accuracy | 85.11 | % | IBM 45nm | int8 ε=0% | int8, ε=10% | p.7 |
| SVHN accuracy | 84.20 | % | IBM 45nm | int8 ε=0% | int8, ε=15% | p.7 |
| SVHN accuracy | 82.52 | % | IBM 45nm | int8 ε=0% | int8, ε=20% | p.7 |
| MNIST accuracy | 97.67 | % | IBM 45nm | accurate network | int8, ε=0% | p.7 |
| MNIST accuracy | 97.58 | % | IBM 45nm | int8 ε=0% | int8, ε=5% | p.7 |
| MNIST accuracy | 97.31 | % | IBM 45nm | int8 ε=0% | int8, ε=10% | p.7 |
| MNIST accuracy | 97.42 | % | IBM 45nm | int8 ε=0% | int8, ε=15% | p.7 |
| MNIST accuracy | 97.22 | % | IBM 45nm | int8 ε=0% | int8, ε=20% | p.7 |
| SVHN accuracy | 87.04 | % | IBM 45nm | accurate network | int12, ε=0% | p.7 |
| SVHN accuracy | 86.68 | % | IBM 45nm | int12 ε=0% | int12, ε=5% | p.7 |
| SVHN accuracy | 85.81 | % | IBM 45nm | int12 ε=0% | int12, ε=10% | p.7 |
| SVHN accuracy | 84.95 | % | IBM 45nm | int12 ε=0% | int12, ε=15% | p.7 |
| SVHN accuracy | 83.06 | % | IBM 45nm | int12 ε=0% | int12, ε=20% | p.7 |
| MNIST accuracy | 97.70 | % | IBM 45nm | accurate network | int12, ε=0% | p.7 |
| MNIST accuracy | 97.61 | % | IBM 45nm | int12 ε=0% | int12, ε=5% | p.7 |
| MNIST accuracy | 97.48 | % | IBM 45nm | int12 ε=0% | int12, ε=10% | p.7 |
| MNIST accuracy | 97.38 | % | IBM 45nm | int12 ε=0% | int12, ε=15% | p.7 |
| MNIST accuracy | 96.18 | % | IBM 45nm | int12 ε=0% | int12, ε=20% | p.7 |
errors_and_checks: Classification accuracy after retraining is the application-level quality contract; multiplier maximum error and exact-zero behavior constrain circuit-level errors. # p.3–4
conditions: Exact multiplication by zero is necessary because more than 80% of observed multiplications have a zero operand. SVHN is more sensitive than MNIST, and SVHN degradation is around 1% when ε≤5%. # p.3, p.7
evidence: §2.4, §3.4, §4.2, §5.2, Figures 3–7, Table 1

## new_families
none

## space_gaps
* `approximate_logic_synthesis` lacks an application-specific exact-function constraint such as exact multiplication by zero. # p.3
* `approximate_mac_nn.multiplier_source` covers evolved CGP circuits, but the family lacks the iterative application-quality feedback that reduces ε after retraining fails. # p.4

## open_questions
* The paper prints the Table 1 area unit as `µm`; whether the intended unit is `µm²` is not settled by the document.
* The gate-level structures of the selected evolved multipliers are not classified into a multiplier family beyond their accurate initial architectures.
