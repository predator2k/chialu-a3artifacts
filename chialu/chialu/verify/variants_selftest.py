"""Check complete products, nested family selection, rank inversion and disjoint shards."""
import itertools
from adir import Bool, Enum, Range
from adir.spaces import Family, Space
from chialu.variants import Axis, compile_family


def main():
    child = Space([Family("left", {"n": Range(2, 5)}), Family("right", {"flag": Bool()})])
    family = Family("parent", {"radix": Enum((2, 4)), "count": Range(1, 3)}, {"cell": child})
    product = compile_family(family)
    expected = []
    for radix, count in itertools.product((2, 4), (1, 2, 3)):
        expected += [{"radix": radix, "count": count, "cell.family": "left", "cell.n": n} for n in range(2, 6)]
        expected += [{"radix": radix, "count": count, "cell.family": "right", "cell.flag": flag} for flag in (False, True)]
    assert product.count == len(expected) == 36
    assert [product.at(i) for i in product.ordinals()] == expected
    assert [product.rank(p) for p in expected] == list(range(36))
    shards = [set(product.ordinals(shard=i, shards=7)) for i in range(7)]
    assert set.union(*shards) == set(range(36))
    assert sum(map(len, shards)) == 36
    assert list(product.ordinals(start=9, stop=21, shard=2, shards=7)) == [9, 16]
    assert product.complete({"cell.family": "right", "cell.flag": True}) == expected[5]
    for invalid in ({"radix": 3}, {"cell.family": "right", "cell.n": 2}, {"unknown": 1}):
        try:
            product.complete(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(invalid)
    axis = Axis("wide", Range(0, 2_000_000))
    assert axis.count == 2_000_001 and axis.at(1_000_001) == 1_000_001
    large = compile_family(Family("large", {str(i): Range(0, 999) for i in range(30)}))
    assert large.count == 10 ** 90
    assert large.rank(large.at(large.count - 1)) == large.count - 1
    assert next(large.ordinals(start=10 ** 89, shard=3, shards=11)) % 11 == 3
    cyclic = Family("cycle")
    cyclic.components["self"] = Space([cyclic])
    try:
        compile_family(cyclic)
    except ValueError:
        pass
    else:
        raise AssertionError("a cycle was silently truncated")
    print("PASS complete products, all Range members, large ordinals, schema validation and shards")


if __name__ == "__main__":
    main()
