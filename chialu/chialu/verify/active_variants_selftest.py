"""Check conditional product counts against exhaustive small domains and huge ranges."""
from adir import Bool, Enum, Range
from adir.spaces import Family, Space

from chialu.active_variants import compile_active
from chialu.variant_contracts import active_binding
from chialu.variants import canonical, compile_family


def main():
    raw = compile_family(Family("carry_select", {
        "block_sizing": Enum(("uniform", "square_root_ramp")), "block_width": Range(2, 3),
        "duplication": Enum(("full_duplicate", "shared_add_one"))}, {
        "block_adder": Space([Family("cell", {"variant": Range(1, 3)})]),
        "add_one": Space([Family("increment", {"variant": Bool()})])}))
    expected = {canonical(active_binding(raw, raw.at(index), project=True)) for index in range(raw.count)}
    active = compile_active(raw)
    actual = {canonical(active.at(index)) for index in range(active.count)}
    assert active.count == len(expected) == 27 and actual == expected
    assert all(active.rank(active.at(index)) == index for index in range(active.count))
    shards = [set(active.ordinals(shard=shard, shards=5)) for shard in range(5)]
    assert set.union(*shards) == set(range(active.count)) and sum(map(len, shards)) == active.count
    huge = compile_family(Family("end_around_carry", {
        "modulus": Enum(("mod_2n_minus_1", "generic_p_correction")),
        "modulus_value": Range(3, 10**30),
        "recirculation": Enum(("two_pass_prefix", "select_based")), "topology": Enum(("sklansky",))}))
    indexed = compile_active(huge)
    assert indexed.count == 10**30
    assert indexed.rank(indexed.at(indexed.count - 1)) == indexed.count - 1
    assert len(indexed.branches) == 3
    invalid = active.at(0) | {"add_one.family": "increment", "add_one.variant": False}
    try:
        active.rank(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("explicit inactive child counted as an active binding")
    from pathlib import Path
    import tempfile
    from chialu.variants import Entry
    from chialu.verify.variant_coverage import Coverage
    ledger = Coverage(Path(tempfile.mkdtemp(prefix="chialu-active-ledger-")), revision="active-index-test")
    legacy_scope = ledger.scope(Entry("adder", raw, "test"), {"width": 8})
    active_scope = ledger.scope(Entry("adder", active, "test"), {"width": 8})
    assert legacy_scope != active_scope
    assert [row["declared"] for row in ledger.report([legacy_scope, active_scope])["entries"]] == ["48", "27"]
    print("PASS exact conditional counts, unique bindings, rank inversion, shards and a 10**30 range")


if __name__ == "__main__":
    main()
