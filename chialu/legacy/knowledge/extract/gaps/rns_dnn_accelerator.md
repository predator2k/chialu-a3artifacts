# rns_dnn_accelerator: proposed changes to the space

* `activation_handling` values for ReLU by residue sign detection and max pooling or comparison in RNS (exact rather than approximate) — the accelerators on record keep ReLU and pooling in residue form without Taylor approximation [samimi_2020, garner_1959, salamat_2018]
* choice `output_conversion: {reverse_convert, rns_argmax_only}` — a classifier can return the winning index from a residue maximum without reverse conversion [garner_1959]
* choices or slots for moduli-set selection, overflow control by base extension and scaling, memory compression and the local weight storage hierarchy — the row-stationary accelerator's energy depends on all four [samimi_2020]
* choice for the computation substrate (CMOS PE array versus processing-in-memory crossbar) — the in-memory design places modular additions and table accesses inside memristor arrays [salamat_2018]
