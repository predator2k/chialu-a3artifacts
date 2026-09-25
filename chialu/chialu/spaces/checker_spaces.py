"""Concurrent error-detection checker spaces (rev 8).

Transcribed from chialu/knowledge/checkers.md (47 refs, 1956–2025). Three axes:
code choice x granularity x fault model. Separate codes (residue,
parity, Berger) add a parallel check channel; nonseparate AN codes
re-encode the datapath itself. Residue mod m aliases at ~1/m. The
comparator must itself be self-checking (two-rail), or the
checker-of-checker regress reopens — so every family opens a comparator
slot. The comparator space also carries the constant-weight
(m-out-of-n) checker and the majority voter that triplicated schemes
terminate in. Shipping practice (IBM z/Power): residue for
multiply/FMA, parity for dataflow, lockstep duplication + checkpoint
retry at core level.
"""

from adir import Bool, Enum, Range
from adir.spaces import Family, Space
from chialu.spaces.arith_spaces import cpa_space

MODULI = (3, 7, 15, 31, 63, 255)   # low-cost 2^a - 1


def two_rail_space() -> Space:
    """The comparator slot of every checker family: the plain word
    equality (direct_compare, the generator's default), the
    self-checking checker that terminates the regress, the
    constant-weight checker and the majority voter."""
    return Space(families=[
        Family(
            "direct_compare", behavior="neutral",
            papers=("lala_2001",),
            doc="a word equality: the predicted and the computed words "
                "compared bit for bit by one comparator, check_err its "
                "inequality; the generator's default and the cheapest "
                "compare, not self-checking (a fault inside the compare "
                "can mask a mismatch)"),
        Family(
            "two_rail_tree", behavior="neutral",
            papers=("carter_schneider_1968", "anderson_metze_1973",
                    "marouf_friedman_1978", "lala_2001"),
            design_choices={
                "tree_arity": Range(2, 4)},
            mutations=("rebalance_tree",),
            doc="morphic-cell tree: output is a valid alternating pair "
                "only when inputs are codewords and the tree is "
                "fault-free (totally self-checking)"),
        Family(
            "m_out_of_n_checker", behavior="neutral",
            papers=("anderson_metze_1973", "marouf_friedman_1978",
                    "lala_2001", "richards_1955"),
            design_choices={
                "code_class": Enum(("k_out_of_2k", "one_out_of_n")),
                "realization": Enum(("two_level_and_or",
                                           "cellular_threshold_array",
                                           "translator_cascade"))},
            mutations=("swap_realization", "insert_code_translator",
                       "collapse_to_two_rail_tree"),
            doc="constant-weight code checker: two majority-predicate "
                "subcircuits over balanced input groups map m-out-of-n "
                "code words to 01/10 and non-code words to 00/11, via a "
                "1-out-of-Z to 2-out-of-4 translator for arbitrary m, n; "
                "not a morphic-cell tree"),
        Family(
            "majority_voter", behavior="neutral",
            papers=("von_neumann_1956", "lyons_vanderkulk_1962",
                    "lala_2001"),
            design_choices={
                "inputs": Range(3, 7, 2)},
            mutations=("widen_vote_to_nmr", "demote_vote_to_compare"),
            doc="bit-wise majority of N replica outputs masks one faulty "
                "replica (floor((N-1)/2) for NMR); a modified voter "
                "names the outvoted module; not self-checking, so voter "
                "reliability bounds the scheme"),
    ], free_form_allowed=False)


def checker_space() -> Space:
    # the comparator slot: the self-checking checkers; a vote needs replicas, so the majority voter is the
    # duplication family's alone
    cmp_slot = {"comparator": Space([f for f in two_rail_space().families if f.name != "majority_voter"],
                                    free_form_allowed=False)}
    vote_slot = {"comparator": two_rail_space()}
    return Space(families=[
        Family(
            "residue", behavior="neutral",
            papers=("avizienis_1971", "langdon_tang_1970",
                    "piestrak_1994", "wei_2014"),
            design_choices={
                "modulus": Enum(MODULI),
                "generator_style": Enum(("csa_tree",
                                               "modular_ripple", "lut"))},
            components=dict(cmp_slot),
            mutations=("raise_modulus", "add_second_residue",
                       "split_endpoint_to_stage_checks",
                       "timeshare_checker", "swap_generator_tree_style"),
            doc="separate mod-m mirror; aliases at ~1/m; 2^a-1 moduli "
                "keep the generator an end-around-carry CSA tree"),
        Family(
            "inverse_residue", behavior="neutral",
            papers=("avizienis_gilley_1971", "avizienis_1973"),
            design_choices={
                "modulus": Enum((3, 7, 15)),
                "inverse_on": Enum(("check_channel",
                                          "both_channels"))},
            components=dict(cmp_slot),
            mutations=("raise_modulus", "revert_to_direct_residue"),
            doc="carry m-|N|_m so a check channel stuck at a plausible "
                "constant still mismatches (JPL STAR)"),
        Family(
            "multi_residue", behavior="neutral",
            papers=("rao_1970", "avizienis_1985"),
            design_choices={
                "moduli_count": Range(2, 4),
                "moduli_set": Enum(("low_cost_2a_minus_1",
                                          "general_coprime"))},
            components=dict(cmp_slot),
            mutations=("add_second_residue", "drop_residue_channel",
                       "promote_detect_to_correct"),
            doc="biresidue syndrome pair locates a single error — "
                "detection becomes correction"),
        Family(
            "an_code", behavior="neutral",
            papers=("brown_1960", "garner_1966", "rao_1974"),
            design_choices={
                "A": Enum((3, 7, 15, 31))},
            components=dict(cmp_slot, coded_adder=cpa_space()),
            mutations=("raise_A", "replace_an_with_separate_residue"),
            doc="nonseparate: operands premultiplied by A, every "
                "functional unit operates on codewords"),
        Family(
            "rns_redundant", behavior="neutral",
            papers=("watson_hastings_1966", "barsi_maestrini_1973"),
            design_choices={
                "base_moduli_count": Range(3, 8),
                "redundant_moduli": Range(1, 3)},
            mutations=("add_redundant_modulus",
                       "promote_detect_to_correct"),
            doc="compute in RNS; redundant moduli make out-of-range "
                "results detectable, digit errors correctable"),
        Family(
            "berger", behavior="neutral",
            papers=("lo_1992", "lala_2001"),
            design_choices={
                "construction": Enum(("berger", "bose_lin_method2"))},
            components=dict(cmp_slot, carry_replica=cpa_space()),
            mutations=("reduce_check_field_modulo",
                       "replace_berger_with_parity"),
            doc="zero-count symbol detects all unidirectional errors — "
                "matches ALUs whose single faults err unidirectionally"),
        Family(
            "parity_prediction_adder", behavior="neutral",
            papers=("sellers_1968", "langdon_tang_1970",
                    "nicolaidis_2003"),
            design_choices={
                "parity_groups": Range(1, 8),
                "carry_scheme": Enum(("duplicate_carry",
                                            "carry_dependent_sum")),
                "interleaving": Bool()},
            components=dict(cmp_slot, carry_replica=cpa_space()),
            mutations=("interleave_parity_groups", "swap_carry_scheme",
                       "upgrade_to_residue"),
            doc="result parity = operand parities XOR carry parity; "
                "needs an independent carry replica or a carry fault "
                "flips an even number of sum bits silently"),
        Family(
            "parity_prediction_multiplier", behavior="neutral",
            papers=("nicolaidis_1997", "nicolaidis_duarte_1999"),
            design_choices={
                "recoding": Enum(("none", "booth2"))},
            components=dict(cmp_slot, row_adder=cpa_space()),
            mutations=("split_endpoint_to_stage_checks",
                       "add_residue_side_channel"),
            doc="tree restructured so any single fault produces an odd "
                "(parity-visible) output error"),
        Family(
            "duplication", behavior="neutral",
            papers=("von_neumann_1956", "lyons_vanderkulk_1962",
                    "slegel_1999", "austin_1999", "sullivan_2018",
                    "burks1946", "check_slegel_1999", "schwarz_2002",
                    "lala_2001", "avizienis_gilley_1971"),
            design_choices={
                "replication": Range(2, 3)},
            components=dict(vote_slot),
            mutations=("replace_duplication_with_residue",
                       "demote_to_reduced_precision_replica",
                       "promote_compare_to_vote"),
            doc="the coverage ceiling at ~2x area, and the baseline "
                "every cheaper checker is measured against (G5 "
                "lockstep, DIVA trailing checker)"),
        Family(
            "reduced_precision", behavior="neutral",
            papers=("shim_2004", "eibl_2009", "seetharam_2013"),
            design_choices={
                "replica_width_bits": Range(4, 24, 4),
                "bound_type": Enum(("absolute", "relative_ulp"))},
            components={"replica_adder": cpa_space()},
            mutations=("widen_replica", "replace_with_residue_channel",
                       "gate_check_on_exponent_range"),
            doc="narrow replica flags disagreement beyond a bound; "
                "sub-linear area, coverage limited to large errors"),
    ], free_form_allowed=False)
