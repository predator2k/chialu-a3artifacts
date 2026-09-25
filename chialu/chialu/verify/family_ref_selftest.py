"""Check adapter coverage over the synthesis database's dense grid."""
from chialu import synthdb
from chialu.variant_contracts import inactive_parameters
from chialu.variant_legality import own_reason
from chialu.verify.family_ref import golden, no_golden_reason, NO_GOLDEN


def main():
    total = total_excluded = total_aliases = 0
    for kind in synthdb.KINDS_WITH_POINTS:
        count = gaps = excluded = aliases = 0
        for width in synthdb.DENSE_WIDTHS:
            for family, pins, _ in synthdb.points(kind, width):
                count += 1
                # The legacy grid supplies default component selectors
                # even on inactive branches. Project only those documented
                # aliases; this adapter inventory is not variant coverage.
                inactive = inactive_parameters(family, pins)
                active = {key: value for key, value in pins.items()
                          if not any(key == path or key.startswith(path + ".") for path in inactive)}
                aliases += active != pins
                if own_reason(family, active, width) is not None:
                    excluded += 1
                    continue
                adapter = golden(kind, family, active, width)
                if adapter is None:
                    reason = no_golden_reason(kind, family, active, width)
                    assert reason and reason in NO_GOLDEN.values(), (kind, family, pins, width)
                    gaps += 1
                else:
                    assert adapter.ports and len({p.name for p in adapter.ports}) == len(adapter.ports)
                    assert all(p.width > 0 and p.direction in ("input", "output") for p in adapter.ports)
                    vector = {p.name: 0 for p in adapter.ports if p.direction == "input"}
                    if adapter.nonzero_divisor:
                        vector["b"] = 1
                    adapter.expect(vector)
                    if adapter.algorithm is not None:
                        adapter.algorithm_expect(vector)
        total += count
        total_excluded += excluded
        total_aliases += aliases
        print(f"{kind}: {count} rows, {count - gaps - excluded} adapters, {gaps} NO_GOLDEN, "
              f"{excluded} geometry exclusions, {aliases} inactive aliases", flush=True)
    print(f"PASS {total} grid rows checked; {total_excluded} documented geometry exclusions, "
          f"{total_aliases} inactive aliases; not complete variant coverage")


if __name__ == "__main__":
    main()
