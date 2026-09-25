# replicated_lanes: proposed changes to the space

* rearrangement value nearest_neighbor_routing with a routing_neighbors choice ({k+1, k-1, k+8, k-8} with end-around) — ILLIAC IV rearranges data by full-word neighbor connections between PE positions rather than by a permute unit. [davis_1969]
* choices permute_network (32 x 16 bytewise crossbar) and issue_pairing (one ALU-class plus one permute-class instruction per cycle) — the AltiVec permute unit's implementation and its co-issue rule are fixed design axes. [diefendorff_2000]
* choice lane_shapes {8x8, 4x16, 2x32, 1x64} for 64-bit registers and {16x8, 8x16, 4x32} for 128-bit registers, including a 4x32 floating-point arrangement — the packed element counts and widths are not declared anywhere in the family. [peleg1996, eisen_2007]
* choices lane_count, sublane_count, alus_per_lane, issue_width, and per-sublane register-file depth — vector units of 128 lanes with 8 sublanes or 16 ALUs per lane are outside the current two-choice family. [jouppi_2023, norrie_2021]
* choices element_format (2 x fp32) and horizontal_accumulate (PFACC) — 3DNow! packs two IEEE-compatible fp32 values and adds the halves of each source into two sums. [oberman_favor_1999]
* choice state_reuse_protocol (floating_point_alias_with_emms) — sharing physical registers with the floating-point stack requires an explicit empty-tag restore. [peleg1996]
* choices slice_composition (two 64-bit slices per 128-bit super-slice) and datatype_sharing (fixed-point/floating-point/scalar/SIMD on one symmetric engine) — Power9 composes wide operations from narrow slices that also serve scalar work. [sadasivam_2017]
* choice pipeline_symmetry (fully_symmetric) — both POWER8 VSU pipelines execute the VMX and VSX categories with per-pipeline register files synchronized in single-thread mode. [sinharoy_2015]
