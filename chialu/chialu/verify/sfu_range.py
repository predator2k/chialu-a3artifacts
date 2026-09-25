"""Enumerate complete finite SFU input domains for implementation error reports."""
from itertools import product


def complete_plan(layout, limit=65536):
    if limit < 1:
        raise ValueError("range_max_vectors must be positive")
    if layout["slots"]:
        return None, {"complete": False, "reason": "writable table contents are not a fixed mathematical function"}
    bits = layout["x_w"] + (layout["v_max"] * layout["sr_bits"] if layout["sr"] else 0)
    controls = layout["controls"]
    names = list(controls)
    combinations = list(product(*(controls[name] for name in names)))
    upper = (1 << bits) * len(combinations) * len(layout["modes"]) * len(layout["functions"])
    if upper > limit:
        return None, {"complete": False, "reason": "complete input domain exceeds the enumeration limit; an analytic range contract is required",
                      "upper_bound_vectors": str(upper), "limit": limit}
    vectors, metadata = [], []
    for mode, (count, fmt) in enumerate(layout["modes"]):
        for function in range(len(layout["functions"])):
            for values in combinations:
                ctrl = dict(zip(names, values))
                for packed in range(1 << layout["x_w"]):
                    if not all(fmt.valid((packed >> (lane * fmt.width)) & ((1 << fmt.width) - 1)) for lane in range(count)):
                        continue
                    random_width = layout["v_max"] * layout["sr_bits"] if layout["sr"] else 0
                    for random_word in range(1 << random_width):
                        vector = {"x": packed}
                        if len(layout["modes"]) > 1:
                            vector["mode"] = mode
                        if layout["total"] > 1:
                            vector["fn_sel"] = function
                        words = None
                        if layout["sr"]:
                            vector["sr_rnd"] = random_word
                            words = [(random_word >> (i * layout["sr_bits"])) & ((1 << layout["sr_bits"]) - 1)
                                     for i in range(layout["v_max"])]
                        for name in names:
                            if len(controls[name]) > 1:
                                vector[name + "_sel"] = controls[name].index(ctrl[name])
                        vectors.append(vector)
                        metadata.append({"mode": mode, "fn": function, "x": packed, "ctrl": ctrl, "words": words, "exact": False})
    return (vectors, metadata, [], []), {"complete": True, "method": "exhaustive simulation",
                                       "vectors": len(vectors), "scope": "every legal mode/function/control and valid operand pattern, including all random words and unused input bits"}


def result_of(verification, report):
    from chialu.sfu_accuracy import mode_of
    decision = verification.spec.get("sfu_accuracy") or {}
    reporting = mode_of(verification.spec) == "report_error"
    domain = verification.spec.get("_sfu_range_plan") or {"complete": False, "reason": "stimulus is a sample"}
    metrics = report.summary()
    complete = bool(domain["complete"] and getattr(verification, "range_execution_complete", False))
    result = {"accuracy_mode": mode_of(verification.spec), "budget_applied": not reporting,
              "algorithm_pass": getattr(verification, "algorithm_pass", None),
              "first_mismatches": getattr(verification, "algorithm_mismatches", []),
              "precision_target": decision.get("precision_target", verification.spec.get("budget")),
              "user_target": decision.get("user_target"), "sampled_metrics": metrics,
              "error_range_complete": complete, "range_evidence": domain}
    if complete:
        finite = report.n_special_mismatch == 0
        result["error_range"] = {"max_ulp": metrics["max_ulp"] if finite else None,
                                 "max_abs": metrics["max_abs"] if finite else None,
                                 "max_abs_exact": str(report.max_abs) if finite else None,
                                 "reference": "correctly rounded mathematical result",
                                 "finite_bound": finite,
                                 "special_mismatch_count": report.n_special_mismatch}
        if not finite:
            result["error_range"]["finite_subset"] = {"max_ulp": metrics["max_ulp"], "max_abs_exact": str(report.max_abs)}
    return result
