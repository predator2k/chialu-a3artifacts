"""Carry-propagate adder architecture spaces (rev 8).

Transcribed from chialu/knowledge/adders.md (67 refs, 1946–2021; one
[unverified]: Weinberger-Smith 1958, NBS Circular 591). Cross-cutting
dimensions: valency, sparsity, fanout, arrival profile. The named
prefix topologies are points of one lattice indexed by per-level fanout
(Knowles 2001; Harris 2003 (l,f,t) taxonomy), so they are a `topology`
choice of the parallel_prefix family, not separate families. Blocked
families open a leaf `block_adder` slot (ripple/Manchester/one-level
CLA/conditional-sum, plus a prefix block for the select-prefix
construction) — the recursion bottoms out there.

Rev 8 (2026-09-02): the reviewed new-family plan
chialu/knowledge/extract/new_families/adder.md is applied here; the
per-line record is adder.applied.md beside it. Rev 9 (2026-09-03): the
cross-plan lines of other.applied.md (prefix_comparator, end_around_carry).
Rev 10 (2026-09-12, the coverage check, docs/deferred-families.md):
every choice left here changes the library module's netlist; the
circuit-level choices (cell styles, buffering, polarity alternation,
dynamic phases, sizing), the sequential ones (pipelined chains), the
interface ones (borrow signals, flag outputs) and the ones the flow
cannot distinguish after synthesis are removed and recorded there.
"""

from adir import Bool, Enum, Range
from adir.spaces import Family, Space

# the named points and, as `harris`, the (l, f, t) point the log2_sparsity
# (l) and fanout_cap (2^f + 1) choices name (Harris 2003; the library's
# prefix graph generator builds any of them)
PREFIX_TOPOLOGIES = ("sklansky", "kogge_stone", "brent_kung",
                     "ladner_fischer", "han_carlson", "knowles_mixed", "harris")


def _parallel_prefix() -> Family:
    """The prefix family. One constructor serves cpa_space and the leaf
    block_adder_space: select-prefix (Tyagi 1993) puts a prefix carry
    evaluator in every block of a serial carry-select chain. valency
    above 2 (radix-3 and radix-4 nodes) is built for sklansky,
    kogge_stone and brent_kung."""
    return Family(
        "parallel_prefix", behavior="neutral",
        papers=("kogge_stone1973", "ladner_fischer1980",
                "brent_kung1982", "snir1986", "han_carlson1987",
                "knowles2001", "beaumont_smith2001", "harris2003",
                "lehman_burla1961", "zimmermann1997"),
        design_choices={
            "topology": Enum(PREFIX_TOPOLOGIES),
            "valency": Range(2, 4),
            "log2_sparsity": Range(0, 3),
            "fanout_cap": Range(2, 8)},
        mutations=("switch_topology", "increase_valency",
                   "increase_sparsity", "convert_to_ling",
                   "add_carry_select_tail",
                   "rebalance_prefix_for_nonuniform_arrival",
                   "prune_redundant_prefix_nodes"),
        doc="the O(log n) framework: named topologies are points of "
            "one lattice (Knowles; Harris (l,f,t)); depth+size >= "
            "2n-2 (Snir) is the frontier")


def _ripple_carry() -> Family:
    return Family(
        "ripple_carry", behavior="neutral",
        papers=("burks1946", "shams2002", "richards_1955",
                "sklansky1960b", "zimmermann1997", "ansari2021",
                "hinton_2001", "hatamian1986"),
        design_choices={
            "full_adder_logic": Enum(
                ("generate_propagate", "two_half_adders_or",
                 "xor_majority", "half_sum_mux_carry")),
            "chunk_width_bits": Range(1, 32)},
        mutations=("resize_carry_path_cells",
                   "map_to_fpga_carry_chain"),
        doc="smallest area/energy, O(n) delay; average longest "
            "carry ~log2(n) (Burks-Goldstine-von Neumann)")


def _manchester() -> Family:
    return Family(
        "manchester_carry_chain", behavior="neutral",
        papers=("kilburn1959", "mead_conway1980", "chan_schlag1990"),
        design_choices={
            "chain_segment_length": Range(2, 8),
            "variable_skip": Bool()},
        mutations=("retune_segment_length", "add_segment_skip_path"),
        doc="the kill/propagate/generate carry chain in segments; "
            "variable_skip bypasses a segment whose bits all propagate")


def _carry_lookahead() -> Family:
    return Family(
        "carry_lookahead", behavior="neutral",
        papers=("weinberger_smith1958", "macsorley1961", "chan1992",
                "pasca_2011"),
        design_choices={
            "group_size": Range(2, 8),
            "levels": Range(1, 4),
            "intergroup_carry": Enum(("ripple", "lookahead",
                                            "select"))},
        mutations=("increase_group_size", "add_lookahead_level",
                   "convert_to_prefix_tree", "convert_to_ling"),
        doc="group G/P recurrence (NBS 1958, IBM Stretch practice); "
            "ancestor of the prefix formulation; levels of groups of "
            "groups, the groups' carries rippled, looked ahead or "
            "selected")


def _conditional_sum() -> Family:
    return Family(
        "conditional_sum", behavior="neutral",
        papers=("sklansky1960", "sklansky1960b", "rothermel1989"),
        design_choices={
            "base_block_width": Range(1, 4),
            "selection_radix": Enum((2, 4))},
        mutations=("increase_base_block",
                   "convert_to_sklansky_prefix"),
        doc="recursive doubling of carry-select; its select pattern "
            "IS the Sklansky prefix topology; base blocks of a few bits "
            "ripple, and a level merges two or four blocks")


def block_adder_space() -> Space:
    """Leaf sub-adders used inside blocked families. parallel_prefix
    and conditional_sum join the three chains; none opens a slot, so
    the recursion bottoms out here."""
    return Space(families=[_ripple_carry(), _manchester(), _carry_lookahead(),
                           _parallel_prefix(), _conditional_sum()],
                 free_form_allowed=False)


def incrementer_space() -> Space:
    return Space(families=[
        Family(
            "prefix_and_incrementer", behavior="neutral",
            papers=("stan1997", "zimmermann1997"),
            design_choices={
                "structure": Enum(("ripple_and_chain",
                                         "prefix_and_tree",
                                         "select_blocks")),
                "topology": Enum(("sklansky", "brent_kung",
                                        "kogge_stone"))},
            mutations=("convert_chain_to_and_tree",
                       "split_prescaler_partition",
                       "fuse_into_compound_adder"),
            doc="the prefix operator collapses to AND; a partitioned "
                "prescaler makes counter period O(1) in width"),
    ], free_form_allowed=False)


def comparator_space() -> Space:
    """The lane's comparator (lt and eq of two binary words): a prefix
    structure of its own, or the subtractor form around an adder of the
    `subtractor` slot with the sum path unused."""
    return Space(families=[
        Family(
            "prefix_comparator", behavior="neutral",
            papers=("huang_wang2003", "abdel_hafeez2013",
                    "taghavizade_2024", "bund_2019"),
            design_choices={
                "structure": Enum(("msb_first_prefix",
                                         "tree_reduction")),
                "radix": Range(2, 4)},
            mutations=("convert_to_msb_first_scan",
                       "raise_node_radix"),
            doc="per-bit (equal, less) pairs reduced by an MSB-first scan "
                "or a balanced tree; radix is the bits a scan step groups "
                "or the arity of a tree node"),
        Family(
            "subtractor_comparator", behavior="neutral",
            papers=("richards_1955", "zimmermann1997", "gilchrist1955"),
            design_choices={
                "zero_detect": Enum(("sum_or_tree", "operand_xnor"))},
            components={"subtractor": cpa_space()},
            mutations=("strip_sum_path_from_adder",
                       "share_prefix_tree_with_adder"),
            doc="magnitude = the carry-out of A + not(B) + 1 through the "
                "slot's adder, the sum path unused; equality from the "
                "difference's zero test or the operands' XNOR tree"),
    ], free_form_allowed=False)


def cpa_space() -> Space:
    """The full carry-propagate adder space (the leaf of most
    recursions in the library)."""
    blocked = {"block_adder": block_adder_space()}
    return Space(families=[
        _ripple_carry(), _manchester(), _carry_lookahead(),
        Family(
            "carry_skip", behavior="neutral",
            papers=("lehman_burla1961", "majerski1967",
                    "oklobdzija_barnes1985", "guyot1987", "turrini1989",
                    "chan1992", "kantabutra1993", "kantabutra1993b"),
            design_choices={
                "block_width": Range(2, 16),
                "block_sizing": Enum(("uniform",
                                            "trapezoidal_variable",
                                            "dp_optimized")),
                "skip_levels": Range(1, 3),
                "skip_gate": Enum(("mux", "and_or_bypass"))},
            components=dict(blocked),
            mutations=("rebalance_block_sizes", "widen_center_blocks",
                       "add_skip_level", "merge_with_select_blocks"),
            doc="AND-of-propagates bypass; near-ripple area, O(sqrt n) "
                "at one level, trapezoidal sizing is the classic "
                "optimization target; dp_optimized sizes the blocks by "
                "a dynamic program under a unit-delay model"),
        Family(
            "carry_select", behavior="neutral",
            papers=("bedrij1962", "tyagi1993", "amelifard2005",
                    "ramkumar2012"),
            design_choices={
                "block_width": Range(2, 16),
                "block_sizing": Enum(("uniform", "square_root_ramp",
                                            "delay_balanced_dp",
                                            "delay_matched_doubling")),
                "duplication": Enum(("full_duplicate",
                                           "shared_add_one")),
                "select_source": Enum(("rippled_block_carries",
                                             "lookahead_tree"))},
            components=dict(blocked, add_one=incrementer_space()),
            mutations=("resize_blocks_square_root",
                       "replace_duplicate_with_increment",
                       "drive_selects_from_sparse_tree",
                       "convert_to_carry_increment"),
            doc="both-carry sums selected late; ~2x block area buys "
                "O(sqrt n) (ramped) or O(log n) (tree-fed selects); "
                "shared_add_one derives the carry-in-1 sum through the "
                "add_one incrementer slot (a ripple chain there is the "
                "binary-to-excess-one converter)"),
        _conditional_sum(),
        Family(
            "carry_increment", behavior="neutral",
            papers=("tyagi1993", "zimmermann1997"),
            design_choices={
                "block_width": Range(2, 16),
                "block_sizing": Enum(("uniform", "variable_ramp")),
                "intergroup_carry": Enum(("rippled",
                                                "lookahead_tree")),
                "increment_levels": Range(1, 2)},
            components=dict(blocked,
                            increment_stage=incrementer_space()),
            mutations=("rebalance_block_sizes",
                       "source_group_carries_from_prefix_tree",
                       "add_second_increment_level",
                       "convert_to_carry_select"),
            doc="carry-select minus the duplicate adder; Pareto-"
                "dominates select in cell-based flows (Zimmermann)"),
        _parallel_prefix(),
        Family(
            "sparse_prefix_hybrid", behavior="neutral",
            papers=("lynch_swartzlander1992", "mathew2003",
                    "oklobdzija2005", "zlatanovici2009", "zeydel2010"),
            design_choices={
                "log2_sparsity": Range(1, 3),
                "tree_topology": Enum(("sklansky", "kogge_stone",
                                             "han_carlson",
                                             "knowles_mixed")),
                "valency": Range(2, 4),
                "sum_block_style": Enum(("carry_select",
                                               "conditional_sum",
                                               "ripple_precompute"))},
            components={"sum_block": block_adder_space()},
            mutations=("increase_sparsity", "switch_tree_topology",
                       "increase_valency", "swap_sum_block_style"),
            doc="tree computes every 2^k-th carry, short blocks make "
                "sums; the production 32-64b style and the setting of "
                "the energy-delay-optimal literature (Intel 1-in-4); "
                "valency above 2 is built for sklansky and kogge_stone"),
        Family(
            "ling_prefix", behavior="neutral",
            papers=("ling1966", "ling1981", "doran1988", "naffziger1996",
                    "jackson_talwar2004", "dimitrakopoulos2005"),
            design_choices={
                "pseudo_carry_group": Range(1, 4),
                "topology": Enum(("sklansky", "kogge_stone",
                                        "han_carlson", "knowles_mixed")),
                "sum_recovery": Enum(("late_select_mux",
                                            "xor_correction"))},
            mutations=("convert_from_vanilla_prefix", "switch_topology",
                       "merge_with_sparse_select"),
            doc="pseudo-carry H removes ~one gate stage from carry "
                "formation; needs no special tree (one preprocessing "
                "change to any prefix topology); HP 930ps 64b flagship; "
                "pseudo_carry_group is the bits per pre-processed block "
                "(1: the per-bit H of the prefix Ling adders)"),
        Family(
            "compound_flagged_prefix", behavior="neutral",
            papers=("beaumont_smith1999", "burgess2002", "burgess2005"),
            design_choices={
                "outputs": Enum(("sum_sum1", "sum_sum1_summinus1")),
                "implementation": Enum(("dual_carry_tree",
                                              "flag_row")),
                "topology": Enum(PREFIX_TOPOLOGIES),
                "log2_sparsity": Range(0, 3),
                "fanout_cap": Range(2, 8),
                "late_carry_in": Bool()},
            mutations=("replace_dual_tree_with_flag_row",
                       "add_sum_minus_one_output", "fuse_rounding_select",
                       "drive_from_ling_core"),
            doc="one tree + a flag row yields sum/sum+1/sum-1 and "
                "absolute difference — FP rounding and negation "
                "without a second adder"),
        Family(
            "end_around_carry", behavior="neutral",
            papers=("zimmermann1999", "kalampoukas2000", "vergos2002",
                    "efstathiou2004", "jenkins_leon_1977"),
            design_choices={
                "modulus": Enum(("mod_2n_minus_1",
                                       "mod_2n_plus_1_diminished_one",
                                       "generic_p_correction")),
                "modulus_value": Range(3, 4095),
                "recirculation": Enum(("two_pass_prefix",
                                             "cyclic_prefix_level",
                                             "select_based")),
                "topology": Enum(PREFIX_TOPOLOGIES),
                "log2_sparsity": Range(0, 3),
                "fanout_cap": Range(2, 8)},
            components={"incrementer": incrementer_space()},
            mutations=("convert_two_pass_to_cyclic",
                       "add_diminished_one_correction",
                       "share_tree_with_binary_adder", "switch_modulus"),
            doc="carry-out re-enters for ones'-complement and modulo "
                "2^n±1 arithmetic — RNS channels, residue checkers, "
                "checksums; cyclic prefix removes the second pass; a "
                "generic modulus p (modulus_value, below 2^W) adds the "
                "constant 2^W - p on overflow or a forbidden state "
                "(generalized end-around carry); the re-entering carry "
                "passes through the incrementer slot"),
        Family(
            "approximate_truncated", behavior="selector",
            papers=("mahdiani2010", "zhu2010", "kahng_kang2012",
                    "shafique2015", "jiang2017"),
            algorithm_level=True,   # changes the computed function
            design_choices={
                "lower_part_width": Range(4, 32, 4),
                "lower_scheme": Enum(("truncate_constant",
                                            "or_gates",
                                            "segmented_subadders",
                                            "speculative_segments")),
                "speculation_window": Range(2, 8),
                "correction": Enum(("none", "configurable_stages"))},
            components={"upper_adder": block_adder_space(),
                        "correction_incrementer": incrementer_space()},
            mutations=("widen_exact_part", "switch_lower_scheme",
                       "add_correction_stage", "convert_to_exact"),
            doc="LOA/ETAII/ACA/GeAr line; error-tolerant contexts only "
                "— the ArithmeticError gate governs"),
        Family(
            "prefix_synthesis_nonuniform_arrival", behavior="neutral",
            papers=("stelling1996", "liu2003", "roy2013", "roy2021"),
            design_choices={
                "arrival_profile": Enum(("uniform", "multiplier_vee",
                                               "lsb_late", "msb_late"))},
            mutations=("rebalance_prefix_for_nonuniform_arrival",
                       "local_prefix_node_rewrite",
                       "reseed_search_from_named_topology"),
            doc="synthesize the prefix graph to a per-bit arrival "
                "profile (the multiplier final adder's V) instead of "
                "picking a named topology; the library's greedy "
                "construction (DP/rewrite/RL are the search methods of "
                "the literature, PrefixRL in NVIDIA silicon)"),
        Family(
            "fpga_carry_chain", behavior="neutral",
            papers=("hauck2000", "preusser2009"),
            design_choices={
                "chain_segment_length": Range(8, 64, 8),
                "prefix_over_chain": Bool()},
            mutations=("segment_and_pipeline_chain",
                       "overlay_prefix_on_chain"),
            doc="the hard ripple chain beats LUT prefix trees past "
                "64b; tunables are segmentation and a prefix overlay "
                "over the segments' carries, not topology"),
    ], free_form_allowed=True)
