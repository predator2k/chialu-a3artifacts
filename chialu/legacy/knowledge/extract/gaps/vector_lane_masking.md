# vector_lane_masking: proposed changes to the space

* `masked_write` value for architectures that support both merging and zeroing predication per instruction — SVE selects the behavior per operation [stephens_2017]
* `mask_storage` value `integer_register` — VIS keeps the per-component mask in a scalar integer register and applies it with partial stores [tremblay_1996]
* choices `predicate_granularity` (per byte with element-size selection) and `predicate_partitioning` (before-break partitions and nested sub-partitions) — the scalable predicate file exposes both as architectural decisions [stephens_2017]
