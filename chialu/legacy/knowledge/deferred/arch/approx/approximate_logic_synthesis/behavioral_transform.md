---
family: approximate_logic_synthesis
pin: {method: behavioral_transform}
---
# behavioral_transform

Behavioral HDL is parsed into an abstract syntax tree, HDL-aware
approximation operators are applied to the tree, and the result is
written back as readable RTL. Simulation against an application
testbench rejects variants outside an accuracy threshold, synthesis
supplies power and area, and an iterative stochastic greedy search
ranks accepted variants by a weighted accuracy/power/area fitness and
breeds from the best.

It is the pick when the design exists above the gate level, when
interpretable RTL must come out, or when the circuit is large, because
behavioral synthesis yields coarser design points with better
scalability than gate or Boolean methods. At an allowed 8% quality
degradation it saved 10% to 33% power and 16% to 38% area across an FIR
filter, a perceptron and block matching in 45 nm. It needs a
representative testbench and a preset threshold, gives no formal error
bound, and modifies datapaths rather than control; approximate
components and voltage scaling can complement it. Gate-level siblings
give finer approximation control.

## references

nepal2014 -> K. Nepal, Y. Li, R. I. Bahar, S. Reda, "ABACUS: A Technique for Automated Behavioral Synthesis of Approximate Computing Circuits", Design, Automation and Test in Europe (DATE), 2014
scarabottolo2020 -> I. Scarabottolo, G. Ansaloni, G. A. Constantinides, L. Pozzi, S. Reda, "Approximate Logic Synthesis: A Survey", Proceedings of the IEEE, vol. 108, no. 12, pp. 2195-2213, 2020
