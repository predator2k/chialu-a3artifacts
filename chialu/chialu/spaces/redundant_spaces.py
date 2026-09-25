"""Redundant / signed-digit / RNS arithmetic spaces (rev 7).

Transcribed from chialu/knowledge/redundant_online.md (60 refs, 1958–2024, all
Crossref-verified). Redundancy buys carry-freedom and costs conversion:
signed-digit and carry-save representations make addition O(1) per
step, RNS splits words into independent narrow channels — and each pays
at the boundary (conversion, comparison, scaling). The on-line families
(`online_space`: MSDF operators streaming digits over cycles) are
deferred with the single-cycle scope (docs/deferred-families.md); their
definitions are kept under legacy/knowledge/deferred/spaces_deferred.py.
"""

from adir import Bool, Enum, Range
from adir.spaces import Family, Space
from chialu.spaces.arith_spaces import adder_tree_space, cpa_space


def signed_digit_space() -> Space:
    """Internal-representation families for carry-free addition."""
    return Space(families=[
        Family(
            "generalized_signed_digit", behavior="neutral",
            papers=("avizienis_1961", "parhami_1990", "parhami_1993",
                    "ercegovac_1992"),
            design_choices={
                "radix": Enum((2, 4, 8, 16)),
                "redundancy": Enum(("minimal", "intermediate",
                                          "maximal")),
                "digit_encoding": Enum(("sign_magnitude",
                                              "twos_complement",
                                              "borrow_save", "one_hot")),
                "addition_scheme": Enum(("carry_free",
                                               "two_stage_limited_carry")),
                "final_conversion": Enum(("cpa", "on_the_fly"))},
            components={"cpa": cpa_space()},
            mutations=("raise_radix", "widen_digit_set_to_maximal",
                       "change_digit_encoding",
                       "replace_final_cpa_with_on_the_fly_conversion",
                       "restrict_redundancy_to_selected_positions"),
            doc="digit set {-a..a}; carries propagate at most one or "
                "two positions (Avizienis 1961; Parhami's GSD "
                "unification)"),
        Family(
            "hybrid_signed_digit", behavior="neutral",
            papers=("phatak_koren_1994", "srinivas_parhi_1992"),
            design_choices={
                "sd_position_spacing": Range(1, 8),
                "spacing_uniform": Bool(),
                "interior_adder": Enum(("ripple", "carry_select",
                                              "prefix"))},
            components={"binary_run_adder": cpa_space(),
                        "cpa": cpa_space()},
            mutations=("increase_spacing", "decrease_spacing",
                       "make_spacing_nonuniform",
                       "degenerate_to_full_sd",
                       "degenerate_to_twos_complement"),
            doc="SD digits every d-th position, binary between: carry "
                "bounded by d — interpolates 2c and full SD"),
        Family(
            "carry_save_datapath", behavior="neutral",
            papers=("wallace1964", "dadda1965", "swartzlander_1980",
                    "noll_1991", "silberman_1998"),
            design_choices={
                "compressor": Enum(("3_2", "4_2", "5_3", "7_3")),
                "carry_overflow_correction": Bool()},
            components={"assimilator": cpa_space()},
            mutations=("merge_ops_into_one_reduction_tree",),
            doc="sum+carry pairs across chained ops; assimilate once at "
                "the end (merged arithmetic, Swartzlander 1980)"),
        Family(
            "redundant_binary_multiplier", behavior="neutral",
            papers=("takagi_1985", "harata_1987", "kuninobu_1987",
                    "makino_1996", "he_chang_2009"),
            design_choices={
                "rb_encoding": Enum(("sign_magnitude_2bit",
                                           "plus_minus_pair",
                                           "np_coding")),
                "booth_radix": Enum(("none", 2, 4)),
                "rbnb_converter": Enum(("cpa", "carry_select",
                                              "on_the_fly"))},
            components={"final_converter": cpa_space()},
            mutations=("add_booth_encoding", "change_rb_encoding",
                       "fuse_two_nb_rows_per_rb_row",
                       "replace_final_cpa_with_carry_select_converter"),
            doc="PPs summed as {-1,0,1} digits in a regular binary tree "
                "of constant-time RB adders (8.8ns 54x54, Makino)"),
    ], free_form_allowed=False)


def rns_space() -> Space:
    """Residue-number-system computation (checking lives in
    checker_spaces; this is RNS as the datapath)."""
    return Space(families=[
        Family(
            "rns_channel_arithmetic", behavior="neutral",
            papers=("garner_1959", "zimmermann1999", "vergos2002",
                    "efstathiou2004", "ma_1998", "piestrak_1994",
                    "noll_1991"),
            design_choices={
                "modulus_form": Enum(("pow2_minus_1", "pow2",
                                            "pow2_plus_1", "generic")),
                "channel_width_n": Range(4, 32),
                "pow2_plus_1_encoding": Enum(("normal",
                                                    "diminished_one")),
                "multiplier_reduction": Enum(
                    ("rom", "csa_with_periodic_folding",
                     "booth_modular", "iterative_carry_save_msd_estimate")),
                "remainder_estimate_digits": Range(4, 5)},
            components={"modular_adder": cpa_space()},
            mutations=("swap_modulus_form", "switch_to_diminished_one",
                       "replace_rom_with_csa_folding",
                       "add_channel_to_moduli_set"),
            doc="independent narrow channels; 2^n±1 moduli give "
                "end-around-carry / diminished-1 adder structure"),
        Family(
            "rns_reverse_converter", behavior="neutral",
            papers=("huang_1983", "piestrak_1995", "wang_2000b",
                    "wang_2002", "molahosseini_2010"),
            design_choices={
                "algorithm": Enum(("crt", "mixed_radix",
                                         "new_crt_i", "new_crt_ii")),
                "moduli_count": Range(3, 5),
                "implementation": Enum(("rom", "adder_based"))},
            components={"modular_adder": cpa_space()},
            mutations=("switch_crt_to_mixed_radix",
                       "adopt_new_crt_to_shrink_final_modulus",
                       "extend_moduli_count",
                       "co_select_moduli_set_with_converter"),
            doc="residue-to-binary dominates whether RNS wins overall; "
                "algorithm x moduli-set co-selection is the game"),
        Family(
            "rns_forward_converter", behavior="neutral",
            papers=("jenkins_leon_1977", "jullien_1978", "piestrak_1994",
                    "kawamura_2000", "chang_2015"),
            design_choices={
                "implementation": Enum(("rom_per_chunk",
                                              "segmented_rom_modular_add",
                                              "periodic_csa_moma",
                                              "channel_modular_mac")),
                "chunk_bits": Range(1, 64),
                "moduli_count": Range(3, 64),
                "final_reduction": Enum(("modular_adder", "rom"))},
            components={"modular_adder": cpa_space(),
                        "column_reducer": adder_tree_space()},
            mutations=("split_word_into_chunks",
                       "segment_rom_into_partial_sums",
                       "replace_rom_with_periodic_csa",
                       "fold_csa_tree_into_register_stage",
                       "reuse_channel_mac_for_conversion",
                       "co_select_moduli_set_with_converter"),
            doc="binary or radix-2^r word to residues, channel by "
                "channel: chunk tables of 2^j mod m summed by modular "
                "adders, a periodic end-around carry-save tree for "
                "memoryless channels, or the channel MACs of a crypto "
                "datapath in n steps; the entry tax paired with "
                "rns_reverse_converter"),
        Family(
            "rns_scaling_comparison", behavior="neutral",
            papers=("jullien_1978", "vu_1985", "shenoy_kumaresan_1989",
                    "dimauro_1993", "sousa_2015", "watson_hastings_1966"),
            design_choices={
                "method": Enum(("rom_mrc", "crt_fraction_estimate",
                                      "diagonal_function")),
                "exactness": Enum(("exact",
                                         "approximate_with_correction"))},
            components={"modular_adder": cpa_space()},
            mutations=("relax_to_approximate_scaling_with_bounded_error",),
            doc="the RNS-hard ops: partial positional reconstruction "
                "without a full reverse conversion"),
    ], free_form_allowed=True)
