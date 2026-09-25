"""Prove complete pin products of blocked adders by checked component substitution."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
from math import prod
from collections import defaultdict

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.families.adder_ext import TEMPLATES, TEMPLATE_CHOICES
from chialu.variant_legality import own_reason
from chialu.variants import catalog, canonical
from chialu.verify.family_ref import golden
from chialu.verify.formal import miter, prove_source, proof_key, toolchain
from chialu.verify.symbolic import compile_reference
from chialu.verify.variant_coverage import source_revision


def _verify(task):
    from chialu.targets.rtl.families.selftest import run_python_case
    from chialu.verify.family_tb import emit
    key, source, module, kind, family, pins, width, directory, timeout = task
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    adapter = golden(kind, family, pins, width)
    bench = emit(module.name, module.params, adapter, n=64)
    try:
        simulation = run_python_case("", "simulation", bench, directory, module.text or "")
        if not simulation.endswith(": PASS"):
            return key, {"status": "failed",
                         "source_bytes": len(source.encode()), "detail": simulation}
        result = prove_source(source, directory, timeout)
        result["simulation"] = simulation
        return key, result
    except Exception as error:
        return key, {"status": "unproved", "detail": f"{type(error).__name__}: {error}"}


def prepare(entry, width, directory, revision, timeout=60):
    product = entry.product
    directory = Path(directory).resolve()
    family_name = product.name
    if set(TEMPLATE_CHOICES[family_name]) != {a.name for a in product.axes}:
        raise ValueError("the template's own choices differ from the complete family schema")
    obligations, parent_rows, leaf_rows = {}, [], {}

    def obligation(module, kind, family, pins, w):
        adapter = golden(kind, family, pins, w)
        source = miter(module, adapter)
        key = proof_key(source)
        obligations.setdefault(key, (key, source, module, kind, family, pins, w, str(directory / "proofs" / key), timeout))
        return key

    widths = defaultdict(set)
    kinds = {}
    for ordinal in range(product.own_count):
        pins = product.own_at(ordinal)
        invalid = own_reason(family_name, pins, width)
        if not invalid:
            # the width contract the ALU's slots apply (alu_contracts): e.g. every selected skip level of a
            # carry-skip adder must contain more than one group, which a narrow adder cannot give
            from chialu.targets.rtl.families.alu_contracts import alu_family_requirements
            need = alu_family_requirements("adder", family_name, pins)
            if width < need["minimum_width"]:
                invalid = f"width {width} below the family's minimum {need['minimum_width']}: " + \
                          "; ".join(r["reason"] for r in need["constraints"] if r["minimum_width"] > width)
        if invalid:
            parent_rows.append({"ordinal": ordinal, "pins": pins, "excluded": invalid})
            continue
        template = TEMPLATES[family_name](width, pins, "composition_parent")
        used = defaultdict(set)
        for component in template.components.values():
            used[component.slot].add(component.width)
            widths[component.slot].add(component.width)
            if component.slot in kinds and kinds[component.slot] != component.kind:
                raise ValueError("one slot requires incompatible component contracts")
            kinds[component.slot] = component.kind

        def contract(component):
            name = f"binary_{component.kind}_contract_w{component.width}"
            leaf = "ripple_carry" if component.kind == "adder" else "prefix_and_incrementer"
            text = compile_reference(golden(component.kind, leaf, {}, component.width), name)
            return FAM.Module(name, {}, text)

        module = FAM.Module(template.name, {}, template.render(contract))
        key = obligation(module, "adder", family_name, pins, width)
        parent_rows.append({"ordinal": ordinal, "pins": pins, "widths": {k: sorted(v) for k, v in used.items()}, "proof": key})
    for slot in product.slots:
        leaf_rows[slot.name] = []
        for family in slot.families:
            if family.slots:
                raise ValueError("a nested child needs its own composition certificate")
            for ordinal in family.ordinals():
                pins = family.at(ordinal)
                row = {"family": family.name, "schema_hash": family.fingerprint, "ordinal": ordinal, "pins": pins, "proofs": {},
                       "needs_width": {}}
                excluded = own_reason(family.name, pins)
                if excluded:
                    row["excluded"] = excluded
                else:
                    for w in sorted(widths[slot.name]):
                        kind = kinds[slot.name]
                        factory = FAM.adder_module if kind == "adder" else FAM.incrementer_module
                        # the binding the parent's render gives (adder_ext.render_template): a ripple tail
                        # narrower than its chunk is realized when the slot also holds a full chunk
                        from chialu.targets.rtl.families.fidelity import component_binding
                        try:
                            with component_binding(family.name, pins, sorted(widths[slot.name]), slot.name):
                                module = factory(family.name, pins, w)
                        except ValueError:   # a child the factory refuses at this width: the parent's render refuses it too
                            module = None
                        row["proofs"][str(w)] = obligation(module, kind, family.name, pins, w) if module else None
                        chunk = pins.get("chunk_width_bits")
                        if module and family.name == "ripple_carry" and isinstance(chunk, int) and chunk > w:
                            # a partial tail: legal only beside a slot width that holds the full chunk
                            row["needs_width"][str(w)] = chunk
                leaf_rows[slot.name].append(row)
    return obligations, parent_rows, leaf_rows, {k: sorted(v) for k, v in widths.items()}


def count_coverage(product, parents, children, results):
    """Count disjoint own-choice cells and the intersection of each child's width obligations.

    A child is legal under a parent when the factory realizes it at every width the parent's slot uses
    (a ripple tail narrower than its chunk only beside a width that holds the whole chunk); a child the
    factory refuses at one of them is refused by the parent's render too, so that cell is excluded."""
    legal_children = {slot: [row for row in rows if "excluded" not in row] for slot, rows in children.items()}
    raw_per_parent = prod(slot.count for slot in product.slots)
    covered, excluded = 0, 0

    def realized(row, used_widths):
        top = max(used_widths, default=0)
        return all(row["proofs"].get(str(w)) is not None and row.get("needs_width", {}).get(str(w), 0) <= top
                   for w in used_widths)

    for parent in parents:
        if "excluded" in parent:
            excluded += raw_per_parent
            continue
        legal, counts = [], []
        for slot, rows in legal_children.items():
            used_widths = parent["widths"].get(slot, [])
            usable = [row for row in rows if realized(row, used_widths)]
            legal.append(len(usable))
            counts.append(sum(all(results.get(row["proofs"][str(w)], {}).get("status") == "proved"
                                  for w in used_widths) for row in usable))
        excluded += raw_per_parent - prod(legal)
        if results.get(parent["proof"], {}).get("status") != "proved":
            continue
        covered += prod(counts)
    return covered, excluded


def run(entry, width, directory, jobs=4, timeout=60):
    product = entry.product
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    revision = source_revision()
    obligations, parent_rows, leaf_rows, widths = prepare(entry, width, directory, revision, timeout)
    # Submit distinct circuits, while retaining every declaration ordinal in the manifest.
    results = {}
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        futures = {}
        for key, task in obligations.items():
            record = Path(task[-2]) / "checked.json"
            if record.exists():
                result = json.loads(record.read_text())
                source_file = record.parent / "miter.sv"
                if (result.get("status") == "proved" and result.get("toolchain") == toolchain()
                        and source_file.exists() and source_file.read_text() == task[1]):
                    results[key] = result
                    continue
            futures[pool.submit(_verify, task)] = key
        for future in as_completed(futures):
            key, result = future.result()
            results[key] = result
            destination = Path(obligations[key][-2]) / "checked.json"
            destination.write_text(json.dumps(result, indent=2) + "\n")
            if len(results) % 100 == 0 or result["status"] != "proved":
                print(canonical({"width": width, "checked_circuits": len(results), "distinct_circuits": len(obligations),
                                 "last_status": result["status"], "detail": result.get("detail", "")}), flush=True)
    covered, excluded = count_coverage(product, parent_rows, leaf_rows, results)
    report = {"scope": "native family with every declared pin and every required component width",
              "revision": revision, "entry": entry.id, "width": width, "declared": str(product.count),
              "legal": str(product.count - excluded), "excluded": str(excluded), "covered": str(covered),
              "uncovered": str(product.count - excluded - covered), "complete": covered + excluded == product.count,
              "parent_choices": product.own_count, "component_choices": {slot.name: slot.count for slot in product.slots},
              "component_widths": widths, "distinct_circuits": len(obligations),
              "parents": parent_rows, "children": leaf_rows, "proofs": results}
    destination = directory / product.name / f"w{width}"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(canonical({k: v for k, v in report.items() if k not in ("parents", "children", "proofs")}), flush=True)
    return report


def check_report(report, directory):
    """Reconstruct every obligation and reject missing, stale or mismatched evidence."""
    revision = source_revision()
    if report["revision"] != revision:
        raise ValueError("composition report is stale")
    entry = next((e for e in catalog(kinds=["adder"], families=TEMPLATES) if e.id == report["entry"]), None)
    if entry is None:
        raise ValueError("composition schema is absent")
    tasks, parents, children, widths = prepare(entry, report["width"], directory, revision)
    if report["parents"] != parents or report["children"] != children or report["component_widths"] != widths:
        raise ValueError("composition report omits or changes a declared binding or a required width")
    results = report["proofs"]
    if set(results) != set(tasks):
        raise ValueError("composition report omits an obligation")
    for key, task in tasks.items():
        result = results[key]
        if result["status"] != "proved":
            continue
        if result.get("toolchain") != toolchain():
            raise ValueError("proof tools differ from the current toolchain")
        proof_dir = Path(task[-2])
        source = task[1]
        if (proof_dir / "miter.sv").read_text() != source or result.get("source_sha256") != hashlib.sha256(source.encode()).hexdigest():
            raise ValueError("proof source differs from the reconstructed obligation")
        if "SAT proof finished - no model found: SUCCESS!" not in (proof_dir / "yosys.log").read_text():
            raise ValueError("a passing solver result is absent")
        if result.get("simulation") != "simulation: PASS":
            raise ValueError("Python golden simulation evidence is absent")
    covered, excluded = count_coverage(entry.product, parents, children, results)
    expected = {"covered": str(covered), "excluded": str(excluded), "declared": str(entry.product.count),
                "legal": str(entry.product.count-excluded), "uncovered": str(entry.product.count-excluded-covered),
                "complete": covered + excluded == entry.product.count}
    if any(report.get(k) != value for k, value in expected.items()):
        raise ValueError("composition totals differ from the reconstructed disjoint cells")
    return expected


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--widths", default="8,16")
    ap.add_argument("--families", default=",".join(TEMPLATES))
    ap.add_argument("--out", required=True)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--check-report")
    args = ap.parse_args(argv)
    if args.jobs < 1:
        ap.error("--jobs must be positive")
    if args.check_report:
        report = check_report(json.loads(Path(args.check_report).read_text()), args.out)
        print(canonical(report))
        return 0 if report["complete"] else 1
    if set(args.families.split(",")) - TEMPLATES.keys():
        ap.error("a requested family has no registered composition template")
    entries = list(catalog(kinds=["adder"], families=args.families.split(",")))
    if any(int(w) < 1 for w in args.widths.split(",")):
        ap.error("widths must be positive")
    reports = [run(entry, int(w), Path(args.out), args.jobs, args.timeout) for entry in entries for w in args.widths.split(",")]
    return 0 if all(report["complete"] for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
