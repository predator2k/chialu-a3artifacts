"""Reject incomplete, stale and unsupported complete-product coverage claims."""
from pathlib import Path
import tempfile

from adir import Range
from adir.spaces import Family
from chialu.variants import Entry, compile_family
from chialu.verify.variant_coverage import Coverage


def main():
    directory = Path(tempfile.mkdtemp(prefix="chialu-coverage-test-"))
    product = compile_family(Family("large", {"n": Range(0, 10**40)}))
    assert product.count == 10**40 + 1
    assert product.rank(product.at(10**40 - 7)) == 10**40 - 7
    entry = Entry("test", product, "synthetic complete product")
    coverage = Coverage(directory, revision="one")
    scope = coverage.scope(entry, {"width": 8})
    assert not coverage.report([scope])["complete"]
    for ordinal in (0, 10**40):
        coverage.record(scope, ordinal, {"status": "pass", "generation": "pass", "golden": "pass"})
    report = coverage.report([scope])
    assert report["uncovered"] == str(10**40 - 1)
    coverage.record(scope, 1, {"status": "unproved", "detail": "solver timeout"})
    assert coverage.report([scope])["uncovered"] == str(10**40 - 1)
    try:
        coverage.record(scope, 2, {"status": "pass", "generation": "pass"})
    except ValueError:
        pass
    else:
        raise AssertionError("generation alone counted as verified")
    coverage.evidence("circuit", {"status": "pass"})
    other = Coverage(directory, revision="two")
    assert other.evidence("circuit") is None
    assert other.get(other.scope(entry, {"width": 8}), 0) is None
    tiny = Entry("test", compile_family(Family("tiny", {"n": Range(0, 1)})), "synthetic")
    scope = coverage.scope(tiny, {"width": 8})
    coverage.record(scope, 0, {"status": "pass", "generation": "pass", "golden": "pass"})
    assert not coverage.report([scope])["complete"]
    coverage.record(scope, 1, {"status": "pass", "generation": "pass", "golden": "pass"})
    assert coverage.report([scope])["complete"]
    assert not coverage.report([scope])["fidelity_complete"]
    for ordinal in (0, 1):
        coverage.record(scope, ordinal, {"status": "pass", "generation": "pass", "golden": "pass", "fidelity_status": "pass"})
    assert coverage.report([scope])["fidelity_complete"]
    print("PASS complete counts, huge ordinals, missing proofs, solver timeouts and source invalidation")


if __name__ == "__main__":
    main()
