# saturating_clamp: proposed changes to the space

* choices `feedback_format: {twos_complement, carry_save}`, `internal_pipeline_registers: Bool` and `overflow_logic: {distributed_sdc_odl, pipelined_odc}`, plus a slot for the carry-propagate adder of temporary-sum generation or final assimilation — these define the four parallel saturating multioperand adder designs [balzola_2001]
* choices `saturation_signedness: {signed, unsigned}`, a mixed signed-input unsigned-output semantics value, and `overflow_policy: {wraparound, saturate}` — the packed instruction variants expose all three [lee_1995, lee_1996, peleg1996]
* `detect` value for a limited-MSD / vector-merging detector with an `inspected_msd_digits` parameter and an explicit uncertainty contract [noll_1991]
* `detect` value `partial_product_and_boundary_carry_or_reduce` with `saturation_limit_selection: unsigned_max_or_signed_extrema` — overflow derived from discarded partial products and boundary carries inside the multiplier tree [schulte_2000]
