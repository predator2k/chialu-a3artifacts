---
family: accuracy_configurable
pin: {reconfig_grain: correction_stage}
---
# correction_stage

The accuracy knob is the number of enabled correction stages behind an
approximate first sum. ACA produces an approximate sum in the first
pipeline stage and applies carry-error corrections in later stages,
each raising accuracy; a mode power-gates the trailing stages, so one
datapath offers an exact mode and several approximate modes. GeAr's
form detects a missed carry between sub-adders with an AND gate and
recomputes the selected sub-adders in extra cycles until the carry has
propagated.

The recovery circuits stay in place in exact mode, so ACA's accurate
mode draws about 11.5% more power than a conventional four-stage
pipelined 32-bit adder in TSMC 65 nm while modes 2 to 4 save 12% to
52%, and real SPEC patterns give higher accuracy than random ones
(kahng_kang2012). GeAr's correction is variable latency: one erroneous
sub-adder costs one extra cycle and k-1 erroneous sub-adders can need k
cycles, and GeAr permits every prediction width from 1 to N-R where GDA
restricts it to architecture-dependent multiples (shafique2015). The
grain is the pick when an exact mode with detected errors must sit
beside the approximate modes; subadder_select and carry_chain_switch
change the carry path without recomputation and carry no detector, so
they win on latency and area when detection is not required.

## references

kahng_kang2012 -> A. B. Kahng, S. Kang, "Accuracy-Configurable Adder for Approximate Arithmetic Designs", 49th Design Automation Conference (DAC), pp. 820-825, 2012
shafique2015 -> M. Shafique, W. Ahmad, R. Hafiz, J. Henkel, "A Low Latency Generic Accuracy Configurable Adder", 52nd Design Automation Conference (DAC), 2015
