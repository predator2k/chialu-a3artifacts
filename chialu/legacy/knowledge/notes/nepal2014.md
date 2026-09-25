---
handle: nepal2014
citation: K. Nepal, Y. Li, R. I. Bahar, S. Reda, "ABACUS: A Technique for Automated Behavioral Synthesis of Approximate Computing Circuits", Design, Automation and Test in Europe (DATE), 2014
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [fixed8]
authority: landmark
pages_read: 6 / 6
---

## summary
ABACUS automatically generates approximate RTL/behavioral designs by transforming an abstract syntax tree and evaluating the variants in standard ASIC/FPGA flows. An iterative stochastic greedy search identifies accuracy/power/area Pareto-frontier designs for FIR filtering, perceptron classification, and block matching. The 45 nm experiments report up to 33.2% power saving and 38.3% area saving under an allowed 8% accuracy degradation. (pp.2-5)

## families
### approximate_logic_synthesis  (role: proposes)
mechanism: ABACUS parses a behavioral HDL design into an abstract syntax tree, applies HDL-aware approximation operators, and writes the modified tree back as readable RTL/behavioral HDL. Simulation rejects variants outside an application-specific accuracy threshold. Synthesis supplies power/area results. An iterative stochastic greedy algorithm randomly selects transformation operators and locations, ranks accepted variants with a weighted accuracy/power/area fitness function, and uses the highest-ranked variant as the next generation's parent. (pp.2-4)
choices:
  method: behavioral_transform   # pp.2-3
new_choices:
  intermediate_representation: abstract_syntax_tree — the representation traversed and modified by approximation operators   # pp.2-3
  transformation_operator: {data_type_simplification, operation_transformation, arithmetic_expression_transformation, variable_to_constant_substitution, loop_transformation} — the behavioral changes applied to the AST   # p.3
  search_method: iterative_stochastic_greedy — the method used to constrain combinatorial variant exploration   # p.4
  fitness_objectives: accuracy_power_area — the weighted objectives used to rank accepted variants   # p.4
slots: none
parameters: FIR/perceptron use 10 generations with 5 variants per generation; block matching uses 15 generations with 6 variants per generation; fitness weights are α1=0.8, α2=0.12, and α3=0.08; the FIR uses 8-bit fixed-point coefficients and image inputs.   # pp.4-5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| accuracy threshold | 90.9 | % | 45 nm (2014) | exact FIR filter | allowed 8% degradation | p.5 |
| accuracy achieved | 93.9 | % | 45 nm (2014) | exact FIR filter | best accepted FIR design | p.5 |
| power saving | 10.4 | % | 45 nm (2014) | exact FIR filter | accuracy achieved 93.9% | p.5 |
| area saving | 15.8 | % | 45 nm (2014) | exact FIR filter | accuracy achieved 93.9% | p.5 |
| accuracy threshold | 76.2 | % | 45 nm (2014) | exact perceptron | allowed 8% degradation | p.5 |
| accuracy achieved | 82.9 | % | 45 nm (2014) | exact perceptron | best accepted perceptron design | p.5 |
| power saving | 33.2 | % | 45 nm (2014) | exact perceptron | accuracy achieved 82.9% | p.5 |
| area saving | 38.3 | % | 45 nm (2014) | exact perceptron | accuracy achieved 82.9% | p.5 |
| accuracy threshold | 28.0 | dB | 45 nm (2014) | exact block matching | allowed 8% degradation | p.5 |
| accuracy achieved | 30.0 | dB | 45 nm (2014) | exact block matching | best accepted block-matching design | p.5 |
| power saving | 23.0 | % | 45 nm (2014) | exact block matching | accuracy achieved 30.0 dB | p.5 |
| area saving | 19.4 | % | 45 nm (2014) | exact block matching | accuracy achieved 30.0 dB | p.5 |
| exact-design area | 16711.18 | um2 | 45 nm (2014) | none | FIR filter | p.5 |
| exact-design power | 0.94 | mW | 45 nm (2014) | none | FIR filter | p.5 |
| exact-design area | 19183.12 | um2 | 45 nm (2014) | none | perceptron | p.5 |
| exact-design power | 1.28 | mW | 45 nm (2014) | none | perceptron | p.5 |
| exact-design area | 42532.87 | um2 | 45 nm (2014) | none | block matching | p.5 |
| exact-design power | 5.51 | mW | 45 nm (2014) | none | block matching | p.5 |
errors_and_checks: Accuracy is measured with application testbenches. FIR quality uses an MSE-derived measure, perceptron quality uses classification outputs, and block-matching quality uses PSNR. Table II permits at most 8% degradation. Six datasets are used per design, with three for variant generation and three for evaluation; reported accuracy is the average over the three evaluation datasets. No formal error bound or fault-detection mechanism is reported.   # pp.4-5
conditions: ABACUS targets applications that tolerate computational inaccuracies. (p.1) ABACUS requires a representative testbench and a preset application-specific accuracy threshold. (p.4) ABACUS modifies computational datapaths but does not modify control signals in the reported experiments. (p.5) The reported power/area benefits depend on the application and accepted accuracy loss. (pp.5-6) Standard approximate arithmetic components and voltage scaling can complement the behavioral transformations. (p.2)
evidence: Fig. 1 and §III describe flow integration; Fig. 2 and §III-A define the AST transformations; §III-B gives the search algorithm and fitness function; Tables I-II and Fig. 3 report the 45 nm experiments; Fig. 5 and Table III compare component truncation with ABACUS and count transformations. (pp.2-6)

## new_families
none

## space_gaps
* `approximate_logic_synthesis` needs explicit choices for behavioral intermediate representation, transformation-operator set, and design-space search method; `method: behavioral_transform` alone does not distinguish the mechanisms established by ABACUS. (pp.2-4)
* The `error_constraint` domain lacks application-level testbench metrics such as MSE, classification accuracy, and PSNR. (pp.4-5)

## open_questions
* Table I labels the FIR quality measure as MSE but reports `98.63%`; the document does not define how MSE is converted to this percentage. (p.5)
* The document does not identify which transformation operators produced each Table II design, so the reported savings cannot be attributed to individual transformations. (pp.5-6)
