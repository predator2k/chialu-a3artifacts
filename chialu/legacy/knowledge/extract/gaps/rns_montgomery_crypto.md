# rns_montgomery_crypto: proposed changes to the space

* `base_extension` values `mixed_radix_with_auxiliary_base` and `iterated_approximations` — the ring algorithm preserves the result in auxiliary residues during RNS-to-MRS conversion, and the modified reduction uses iterated approximate extensions [bajard_1998, posch_posch_1995]
* `channel_width` domain admitting 9 to 10 bits and `channel_count_per_base` above 64 — the ring design suggests small moduli in about 80 channels [bajard_1998]
* choices `processor_mapping: {ring_n_processors, time_multiplexed_p_processors}`, `input_A_representation: {MRS, RNS_with_overlapped_conversion}` and `output_recovery: second_application_with_permuted_bases` — the physical processor count, the conversion task and the recovery pass are separate decisions [bajard_1998]
* choices `pipeline_depth` and `gpr_per_channel` — the 5- or 6-stage Rower pipelines and 16 registers per channel set the overlapped point-operation schedule [guillermin_2010]
* choice `approximate_base_extension_tolerance: off_by_one_without_correction` — whether the reduction stays correct when the extension returns t + P1 [posch_posch_1995]
