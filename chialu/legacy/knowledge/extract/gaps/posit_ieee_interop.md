# posit_ieee_interop: proposed changes to the space

* choices runtime_configurable_posit_es and per_operand_format_selection — the unified MAC selects the posit exponent size at runtime and configures the format of each operand and of the result independently. [crespo_2022]
* interop_style value separate_parallel_datapaths — PERCIVAL keeps the fp32/fp64 FPU and adds a separate posit unit and register file instead of converters or one unified datapath. [mallasen_2022]
* choice register_file_organization (separate_fpr_prf) — Clarinet keeps floating-point and posit values in independent register files with FCVT conversions between them. [sharma_2023]
* choice accelerator_coexistence {none, separate_rocc_posit_fpu} — a RoCC posit accelerator with its own register file coexists with the IEEE-754 FPU under custom opcodes. [tiwari_2021]
* choices fp_subnormal_handling (pre_normalize) and nan_handling (excluded) — FP-to-posit conversion normalizes subnormal mantissas first and omits NaN detection when the posit format has no NaN. [jaiswal_2018]
