"""Shifters, bit-count units, saturation, subword-SIMD spaces (rev 8).

Transcribed from chialu/knowledge/shift_simd.md (34 refs, 1969–2018; one
[unverified]). Structure reuse is the domain's dominant optimization —
a funnel window subsumes shift/rotate/extract, bit-reversal redirects an
LZD to trailing-zero duty, one PP grid serves all lane modes — and
subword SIMD is an overlay on scalar structures (carry kill/insert at
lane boundaries), not a separate datapath. Rev 8 (the coverage check of
2026-09-12, docs/deferred-families.md): every choice left here changes
the library module's text, the FPGA mapping family and the choices that
name an interface, a sequential control or an output the unit has no op
for are removed, and the leading-zero counters of the float datapath
(`lzc_space`) are the bit-count families themselves.
"""

from adir import Bool, Enum, Range
from adir.spaces import Family, Space
from chialu.spaces.arith_spaces import cpa_space


def _barrel(rotator: bool = False) -> Family:
    """The barrel mux tree; as a rotator (one direction, no fill) it keeps
    the stage radix, the select encoding and the stage order alone."""
    choices = {
        "stage_radix": Enum((2, 4, 8, "full_width_single_stage")),
        "select_encoding": Enum(("binary", "one_hot_decoded")),
        "stage_order": Enum(("small_shift_first", "large_shift_first"))}
    if not rotator:
        choices["direction_handling"] = Enum(("mirrored_datapath", "data_reversal", "amount_negation"))
        choices["sticky_collect"] = Bool()
    return Family(
        "barrel_mux_tree", behavior="neutral",
        papers=("davis_1969", "pillmeier_2002", "pereira_1995",
                "mead_conway1980"),
        design_choices=choices,
        mutations=("increase_stage_radix",
                   "swap_stage_order_for_late_select_arrival",
                   "convert_barrel_to_funnel",
                   "add_data_reversal_for_bidirectionality"),
        doc="ceil(log_r N) mux stages (ILLIAC IV lineage); data-reversal "
            "designs give least area")


def rotator_space() -> Space:
    """The plain rotator a masked shifter turns by: the barrel's stages."""
    return Space(families=[_barrel(rotator=True)], free_form_allowed=False)


def shifter_space() -> Space:
    return Space(families=[
        _barrel(),
        Family(
            "funnel", behavior="neutral",
            papers=("lee_1989", "huntzicker_2008", "pillmeier_2002"),
            design_choices={
                "window_mux_radix": Enum((2, 4, 8)),
                "amount_preprocess": Enum(
                    ("ones_complement_for_right", "subtract_from_n")),
                "sticky_collect": Bool()},
            mutations=("raise_window_mux_radix",
                       "merge_extract_path_with_rotate_path"),
            doc="2N-1-bit concatenation + sliding N-bit window: one "
                "datapath for shift/rotate/extract; wins the energy-delay "
                "frontier at radix 4-8"),
        Family(
            "masked_merged", behavior="neutral",
            papers=("lee_1989", "grohoski_1990", "hilewitz_2006",
                    "hilewitz_2008", "lee_1996", "bloch_1959"),
            design_choices={
                "mask_generator": Enum(
                    ("thermometer_decode", "two_thermometer_and", "lut")),
                "merge_style": Enum(("and_or_merge", "per_bit_mux")),
                "sticky_collect": Bool()},
            components={"rotator": rotator_space()},
            mutations=("fuse_shift_with_mask",
                       "share_rotator_between_shifts_and_field_ops",
                       "generalize_rotator_to_butterfly_network"),
            doc="rotator + decoded mask + merge: rotate-and-mask in one "
                "pass (POWER rlwinm lineage); butterfly networks strictly "
                "generalize it"),
        Family(
            "butterfly_network", behavior="neutral",
            papers=("hilewitz_2006", "hilewitz_2008"),
            design_choices={
                "network": Enum(("inverse_butterfly", "butterfly")),
                "sticky_collect": Bool()},
            execution_style="feed_forward",
            mutations=("specialize_to_rotate_and_mask",),
            doc="lg(n)-stage switch networks under per-switch controls; "
                "the rotation is a closed-form control pattern on the "
                "inverse butterfly, and the butterfly composes the inverse "
                "permutation; the pex/pdep and permutation forms need ops "
                "the unit does not carry"),
    ], free_form_allowed=True)


def _popcount() -> Family:
    return Family(
        "popcount_counter_tree", behavior="neutral",
        papers=("thornton_1970", "swartzlander_1973", "mula_2018"),
        design_choices={
            "counter_primitive": Enum(
                ("full_adder_3_2", "compressor_4_2", "counter_7_3",
                 "lut_rom")),
            "tree_shape": Enum(("balanced_tree", "wallace_style",
                                      "linear_chain"))},
        components={"final_adder": cpa_space()},
        mutations=("widen_counter_primitive",
                   "share_tree_with_multiplier_reduction"),
        doc="counter tree to log2(N)+1 bits; shares structure with "
            "PP reduction (CDC 6600 onward)")


def _lzd_cell_tree() -> Family:
    return Family(
        "lzd_cell_tree", behavior="neutral",
        papers=("oklobdzija_1994", "schmookler_2001",
                "dimitrakopoulos_2008", "tsen_2007"),
        design_choices={
            "block_primitive": Enum(("pair_cell", "nibble_cell")),
            "output_form": Enum(("binary_count",
                                       "one_hot_shift_controls")),
            "valid_flag_propagation": Bool()},
        mutations=("convert_lzd_to_lza",
                   "emit_one_hot_for_shifter",
                   "fuse_count_with_normalize_shifter"),
        doc="clz as a tree of valid/position cells from pair or nibble "
            "leaves (Oklobdzija); the one-hot form drives a shifter's "
            "stages directly")


def _prefix_lzc() -> Family:
    return Family(
        "prefix_lzc", behavior="neutral",
        papers=("dimitrakopoulos_2008",),
        design_choices={
            "prefix_topology": Enum(("kogge_stone", "sklansky",
                                           "brent_kung")),
            "count_form": Enum(("popcount_of_complement",
                                      "lookahead_flags"))},
        components={"counter": popcount_space()},
        mutations=("switch_prefix_topology",
                   "replace_popcount_with_lookahead_flags"),
        doc="a prefix OR from the msb marks the positions at or below the "
            "leading one; the count is a popcount of the unmarked "
            "positions or the lookahead-flag encoding of the leading-one "
            "flags (Dimitrakopoulos)")


def _priority_encoder() -> Family:
    return Family(
        "priority_encoder", behavior="neutral",
        papers=("wang_2000", "delgado_frias_2000"),
        design_choices={
            "lookahead_group": Range(4, 16, 4),
            "levels": Range(1, 3),
            "output_form": Enum(("one_hot_then_encode",
                                       "direct_binary"))},
        mutations=("add_priority_lookahead_level",
                   "convert_ripple_to_tree"),
        doc="the kill chain is the delay; lookahead groups cut it "
            "~2.5x for ~10% transistors")


def popcount_space() -> Space:
    """The population counter a prefix counter counts with."""
    return Space(families=[_popcount()], free_form_allowed=False)


def lzc_space() -> Space:
    """Leading-zero count/detect: exact count of a completed result, or
    the encoder back-end of an LZA string (the float datapath's slot)."""
    return Space(families=[_lzd_cell_tree(), _prefix_lzc(), _priority_encoder()],
                 free_form_allowed=False)


def bitcount_space() -> Space:
    """popcount / clz / ctz / priority encode: the lane's bitcount slot."""
    from chialu.spaces.adder_spaces import incrementer_space
    return Space(families=[
        _popcount(),
        _lzd_cell_tree(),
        Family(
            "trailing_zero", behavior="neutral",
            papers=("leiserson_1998",),
            design_choices={
                "strategy": Enum(("reverse_then_lzd",
                                        "isolate_then_encode",
                                        "debruijn_multiply_index")),
                "isolate_circuit": Enum(("twos_complement_and",
                                               "ripple_kill_chain"))},
            components={"lzd": lzc_space(),
                        "negation_incrementer": incrementer_space()},
            mutations=("reuse_lzd_via_bit_reversal",
                       "replace_encode_with_debruijn_index"),
            doc="ctz = bit-reverse into the lzd slot's detector, or isolate "
                "the lowest set bit (a & -a through the incrementer slot, or "
                "a kill chain) and encode it, directly or by a de Bruijn "
                "multiply and a table"),
        _priority_encoder(),
    ], free_form_allowed=False)


def subword_space() -> Space:
    """The lane_count parameter's implementation families: how one wide
    datapath becomes k narrow lanes."""
    return Space(families=[
        Family(
            "partitioned_carry_chain", behavior="neutral",
            papers=("lee_1995", "lee_1996", "fridman_2000", "perri_2004"),
            design_choices={
                "boundary_mechanism": Enum(
                    ("carry_kill_gate", "carry_select_mux",
                     "guard_bit_insertion"))},
            mutations=("segment_carry_chain_for_lanes",
                       "add_guard_bits_at_boundaries",
                       "extend_prefix_tree_with_lane_kills"),
            doc="carry kill/insert at lane boundaries; the segments are "
                "the served lanes' declared adder family (core.adder.m*, "
                "one family across the modes one adder serves); near-zero "
                "incremental area (MAX-1 on a shipping 32-bit ALU)"),
        Family(
            "replicated_lanes", behavior="neutral",
            papers=("diefendorff_2000",),
            mutations=("merge_lanes_into_shared_datapath",),
            doc="per-lane units + a first-class permute unit (AltiVec "
                "corner); vs the shared_segmented corner (MAX/MMX)"),
    ], free_form_allowed=True)
