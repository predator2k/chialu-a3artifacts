"""Check that space selection preserves the database's points and baselines."""
from chialu import synthdb
from chialu.targets.rtl.families.selftest import space_points


def main():
    kinds = ("adder", "multiplier", "shifter", "comparator", "lzc", "bitcount")
    widths = (8, 16)
    expected = [(kind, width, family, pins, label)
                for kind in kinds for width in widths
                for family, pins, label in synthdb.points(kind, width)]
    assert list(space_points(kinds, widths, None, 7)) == expected
    first = list(space_points(kinds, widths, 3, 7))
    assert first == list(space_points(kinds, widths, 3, 7))
    assert first != list(space_points(kinds, widths, 3, 8))
    for kind in kinds:
        for width in widths:
            points = synthdb.points(kind, width)
            selected = [p[2:] for p in first if p[:2] == (kind, width)]
            bases = {}
            for point in points:
                bases.setdefault(point[0], point)
            assert all(point in selected for point in bases.values())
            assert len(selected) == len(bases) + min(3, len(points) - len(bases))
    print(f"PASS {len(expected)} enumerated points; deterministic samples retain every family baseline")


if __name__ == "__main__":
    main()
