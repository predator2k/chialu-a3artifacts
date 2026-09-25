"""Check that component coverage requires every width and preserves unused-slot combinations."""
from adir import Bool
from adir.spaces import Family, Space
from chialu.variants import compile_family
from chialu.verify.composition_selftest import count_coverage


def main():
    leaf = Space([Family("leaf", {"choice": Bool()})])
    product = compile_family(Family("parent", {"branch": Bool()}, {"a": leaf, "b": leaf}))
    parents = [{"proof": "parent0", "widths": {"a": [2, 4]}},
               {"proof": "parent1", "widths": {"a": [4], "b": [4]}}]
    children = {"a": [{"proofs": {"2": "a02", "4": "a04"}}, {"proofs": {"2": "a12", "4": "a14"}}],
                "b": [{"proofs": {"4": "b04"}}, {"proofs": {"4": "b14"}}]}
    results = {name: {"status": "proved"} for name in ("parent0", "parent1", "a02", "a12", "a14", "b04")}
    assert count_coverage(product, parents, children, results) == (3, 0)
    results.update({name: {"status": "proved"} for name in ("a04", "b14")})
    assert count_coverage(product, parents, children, results) == (8, 0)
    results["a04"] = {"status": "unproved"}
    assert count_coverage(product, parents, children, results) == (4, 0)
    children["a"][0]["excluded"] = "a documented restriction"
    assert count_coverage(product, parents, children, results) == (4, 4)
    print("PASS disjoint composition counts, all required widths, inactive slots and missing child proofs")


if __name__ == "__main__":
    main()
