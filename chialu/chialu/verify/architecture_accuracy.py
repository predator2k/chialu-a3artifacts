"""Score verified architectural outputs against the ideal numerical operation."""
from chialu.verify.errors import ErrorReport
from chialu.verify.formats import BlockFormat


def dot_error_report(verification):
    """Use outputs already checked bit-for-bit against the architectural golden.

    The caller must establish algorithm conformance before using this report
    as a measurement of RTL outputs. Flags and expansion outputs remain part
    of that exact contract; this report measures the primary d output.
    """
    from chialu.verify import dot_ref as D
    spec = verification.spec
    if spec.get("dot_contract") != "architecture":
        raise ValueError("an explicit architecture contract is required")
    lay = D.dot_layout(spec)
    ideal = dict(spec, dot_contract="fused")
    report = ErrorReport()
    for mode in lay["modes"]:
        fmt = mode["fd"]
        if hasattr(fmt, "max_finite"):
            maximum = abs(fmt.max_finite())
        elif hasattr(fmt, "max_int"):
            maximum = max(abs(fmt.min_int), abs(fmt.max_int))
        else:
            maximum = 1
        report.out_max_mag = max(report.out_max_mag, maximum)
    for index, (metadata, packed) in enumerate(zip(verification.meta, verification.expected)):
        mode = metadata["mode"]
        ctrl = D.vector_ctrl(spec, metadata.get("ctrl"))
        expected, _ = D.dot_expected(ideal, lay, mode, metadata["a"], metadata["b"],
                                    metadata.get("c"), ctrl, metadata.get("words"))
        actual = verification._data_field(packed)
        fmt = lay["modes"][mode]["fd"]
        if isinstance(fmt, BlockFormat):
            for element, (ev, av) in enumerate(zip(fmt.decode(expected), fmt.decode(actual))):
                report.add_values(ev, av, fmt.ulp_at(expected), tag=f"v{index}:{element}")
        else:
            report.add(fmt, expected, actual, tag=f"v{index}")
    return report


def dot_accuracy(verification):
    from chialu.verify.harness import _one_budget
    report = dot_error_report(verification)
    budget = verification.spec.get("budget")
    if budget is not None and not isinstance(budget, dict):
        raise ValueError("a Dot architecture error budget must be one metric-to-bound mapping")
    passed, violations = _one_budget(budget).verdict(report) if budget else (None, [])
    return {"reference": "fused mathematical operation with the same formats and controls",
            "source": "architectural outputs verified exactly against RTL for every stimulus vector",
            "mathematical_metrics": report.summary(), "budget": budget,
            "budget_pass": passed, "budget_violations": violations}
