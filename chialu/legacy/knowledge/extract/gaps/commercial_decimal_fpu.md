# commercial_decimal_fpu: proposed changes to the space

* slots for error-detection mechanisms (residue, duplication, parity) — the z900 replicates the fixed-point unit, the z10 uses residue-3 on the significand dataflow and parity on interfaces, and the z196 recovery unit flushes and restarts [carlough_2011, schwarz_2009, busaba_2001]
* `implementation` value for per-operation mixed full hardware and millicode-controlled hardware assists — the G5 runs multiply under hardware control but iterates a one-digit divide assist from millicode [check_slegel_1999]
* choices for execution-unit replication (`dfu_instances`), heterogeneous BFU/DFU/VXU grouping and shared issue width — the z13 carries two DFUs inside two VFUs behind two shared issue positions [curran_2015]
* a binary counterpart family for queued commercial IEEE binary coprocessors with hardware/software completion boundaries [darley_1990]
* a codec slot for the `decimal_encoding_codec` family — DPD-to-BCD decoding and result encoding are explicit steps of the execution path [duale_2007]
* a value for an iterative chunked binary-decimal conversion structure — the z900 decimal-assist macro and the z15 distinguish conversion hardware from multiply/divide hardware [saporito_2020, busaba_2001]
* choice `decimal_operation_set: {dfp_only, dfp_and_decimal_fixed}` — the z10 DFU serves both IEEE DFP and legacy decimal fixed-point instructions [schwarz_2009]
* execution-style value or choice `issue_structure: fully_pipelined` — the POWER8 DFU is fully pipelined with a 13-cycle dependent latency, against the family's variable-iteration label [sinharoy_2015]
* `datapath_width_digits` value 8 — the G5 fixed-point unit has an 8-digit decimal adder [slegel_1999]
* parameter `pipeline_depth` and choice `optimization_target: common_business_workload_cases` — the z196 uses a 4-stage pipeline that favours fixed-point decimal latency, and the z900 shortens iterations for typical data through leading-zero detection and operand selection [carlough_2011, busaba_2001]
