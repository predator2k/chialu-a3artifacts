"""ADIR aliases of carry-save and RNS CPAs agree within their original domains.

The representation assimilator and channel modular-adder are global.
Conflicting fixed per-mode choices need either a common binding or an
indexed interface; this test requires an explicit error instead of
choosing one.
"""
import hashlib
import json
import re
from pathlib import Path
import tempfile

from chialu.modules import generators
from chialu.modules.alu import ALU
from chialu.targets import derive
from chialu.targets.rtl.alu_seed import structure_manifest
from chialu.verify.elaboration import elaborate
from chialu.verify.generator_binding_selftest import bind
from chialu.eda import conformance


LANE = "core.adder.m0"
ALIAS = "core.representation.assimilator"
BASE = {"core.family": {"fixed": "redundant_internal"},
        "core.representation.family": {"fixed": "carry_save_datapath"}}


def instance(extra, multimode=False, rns=False):
    fixed = {"modes": {"count": 1, "format": "int8"}, "check_en": False,
             "flags": ["carry", "int_overflow", "overflow"]}
    runtime = {"ops": ["add", "sub", "adc", "sbb"]}
    if multimode:
        fixed.pop("modes")
        runtime["modes"] = [{"count": 1, "format": "int8"}, {"count": 1, "format": "int16"}]
    base = {"core.family": {"fixed": "rns_internal"},
            "core.channels.family": {"fixed": "rns_channel_arithmetic"},
            "core.channels.channel_width_n": {"fixed": 4}} if rns else BASE
    return bind(ALU, fixed, {**base, **extra}, runtime)


def families(inst, overrides=None):
    return generators.families_of(inst.ctx(), structure_manifest(generators.spec_of(inst.ctx())), overrides)


def require_same(inst, family, pins, overrides=None, alias=ALIAS):
    selected = families(inst, overrides)
    lane_family, lane_pins = selected[LANE]
    owner, component = alias.rsplit(".", 1)
    prefix = component + "."
    representation = selected[owner][1]
    alias_family = representation[prefix+"family"]
    alias_pins = {key[len(prefix):]: value for key, value in representation.items()
                  if key.startswith(prefix) and key != prefix+"family"}
    assert lane_family == alias_family == family, selected
    assert lane_pins == alias_pins, selected
    assert all(lane_pins[key] == value for key, value in pins.items()), selected
    return selected


def rejected(callback, fragment):
    try:
        callback()
    except ValueError as error:
        assert fragment in str(error), error
    else:
        raise AssertionError(f"alias conflict was accepted: {fragment}")


def verify(inst, directory, expected_module, width, parameters=None):
    directory.mkdir(parents=True, exist_ok=True)
    source = generators.core_seed(inst.ctx())
    target = dict(generators.spec_of(inst.ctx()), n_random=96, seed=197)
    files = derive.verify_files(target, directory)
    result = conformance(source, files)
    assert result["pass"], result
    (directory / "seed.sv").write_text(source)
    hierarchy = elaborate(source, "alu_core", directory / "elaborated")
    found = [node for node in hierarchy if node["module"] == expected_module]
    assert found and all(node["ports"]["a"]["width"] == width for node in found), found
    for key, value in (parameters or {}).items():
        assert all(node["parameters"][key] == value for node in found), found
    result["source_sha256"] = hashlib.sha256(source.encode()).hexdigest()
    result["actual_exit_instances"] = found
    (directory / "result.json").write_text(json.dumps(result, indent=2))
    return result


def verify_rns(inst, directory, widths, family):
    """Inspect the actual channel additions, not a matching converter CPA."""
    directory.mkdir(parents=True, exist_ok=True)
    source = generators.core_seed(inst.ctx())
    files = derive.verify_files(dict(generators.spec_of(inst.ctx()), n_random=96, seed=199), directory)
    result = conformance(source, files)
    assert result["pass"], result
    (directory / "seed.sv").write_text(source)
    hierarchy = elaborate(source, "alu_core", directory / "elaborated")
    channels = []
    for channel, width in enumerate(widths):
        match = re.search(r"// channel " + str(channel) + r":[^\n]*\n\s+(\w+)\s+(?:#\([^\n]*\)\s+)?(u\d+)\s*\(", source)
        assert match, channel
        module, name = match.groups()
        copies = [node for node in hierarchy if node["module"] == module and node["instance"] == name]
        assert copies and all(node["ports"]["a"]["width"] == width for node in copies), copies
        if family == "parallel_prefix":
            assert module == f"fam_prefix_brent_kung_w{width}", module
        else:
            assert module == "fam_adder_ripple_carry", module
            assert all(node["parameters"]["CHUNK"] == 3 and node["parameters"]["FORM"] == 2 for node in copies), copies
        channels.extend(copies)
    result.update(source_sha256=hashlib.sha256(source.encode()).hexdigest(), actual_channel_instances=channels)
    (directory / "result.json").write_text(json.dumps(result, indent=2))


def rns_cases(root):
    alias = "core.channels.modular_adder"
    widths = {"pow2": [4, 4, 5], "pow2_plus_1": [4, 4, 5],
              "pow2_minus_1": [4, 5, 7], "generic": [4, 4, 4]}
    for form, channel_widths in widths.items():
        for family in ("parallel_prefix", "ripple_carry"):
            pins = {"topology": "brent_kung"} if family == "parallel_prefix" else {"chunk_width_bits": 3, "full_adder_logic": "xor_majority"}
            fixed = {LANE+".family": {"fixed": family}, "core.channels.modulus_form": {"fixed": form},
                     **{LANE+"."+key: {"fixed": value} for key, value in pins.items()}}
            selected = instance(fixed, rns=True)
            require_same(selected, family, pins, alias=alias)
            verify_rns(selected, root / form / family, channel_widths, family)
    reverse = instance({alias+".family": {"fixed": "parallel_prefix"}, alias+".topology": {"fixed": "brent_kung"},
                        "core.channels.modulus_form": {"fixed": "generic"}}, rns=True)
    require_same(reverse, "parallel_prefix", {"topology": "brent_kung"}, alias=alias)
    assert generators.declared_vars(reverse.ctx(), "baseline")[LANE+".topology"] == "brent_kung"
    verify_rns(reverse, root / "fixed_channel", widths["generic"], "parallel_prefix")
    narrowed = instance({LANE+".family": {"search": ["ripple_carry", "parallel_prefix"]},
                         alias+".family": {"search": ["parallel_prefix"]},
                         LANE+".topology": {"search": ["sklansky", "brent_kung"]},
                         alias+".topology": {"search": ["brent_kung", "kogge_stone"]},
                         "core.channels.modulus_form": {"fixed": "generic"}}, rns=True)
    names = (LANE+".family", alias+".family", LANE+".topology", alias+".topology")
    before = {name: narrowed.bindings[name].to_json() for name in names}
    require_same(narrowed, "parallel_prefix", {"topology": "brent_kung"}, alias=alias)
    assert {name: narrowed.bindings[name].to_json() for name in names} == before
    verify_rns(narrowed, root / "search_intersection", widths["generic"], "parallel_prefix")
    fixed = {LANE+".family": {"fixed": "parallel_prefix"}, LANE+".topology": {"fixed": "brent_kung"}}
    rejected(lambda: families(instance({**fixed, alias+".family": {"fixed": "ripple_carry"}}, rns=True)), "conflicting explicit aliases")
    rejected(lambda: families(instance({**fixed, alias+".topology": {"fixed": "kogge_stone"}}, rns=True)), "conflicting explicit aliases")
    rejected(lambda: families(instance({**fixed, alias+".family": {"search": ["ripple_carry"]}}, rns=True)), "empty intersection")
    rejected(lambda: families(instance({**fixed, alias+".topology": {"search": ["sklansky"]}}, rns=True)), "empty intersection")
    restricted = instance({**fixed, LANE+".valency": {"search": [2]}}, rns=True)
    rejected(lambda: families(restricted, {LANE+".valency": 3}), "outside the user-bound")
    rejected(lambda: families(reverse, {LANE+".family": "ripple_carry"}), "conflicting explicit aliases")
    multiple = instance({**fixed, "core.adder.m1.family": {"fixed": "parallel_prefix"},
                         "core.adder.m1.topology": {"fixed": "kogge_stone"}}, multimode=True, rns=True)
    rejected(lambda: families(multiple), "per-mode channel interface")
    print("PASS 10 RNS ADIR/RTL channel cases and 7 explicit/domain/multimode rejections", flush=True)


def main():
    root = Path(tempfile.mkdtemp(prefix="chialu-exit-alias-binding-"))
    prefix = {LANE+".family": {"fixed": "parallel_prefix"}, LANE+".topology": {"fixed": "brent_kung"}}
    direct = instance(prefix)
    require_same(direct, "parallel_prefix", {"topology": "brent_kung"})
    declared = generators.declared_vars(direct.ctx(), "baseline")
    assert declared[ALIAS+".family"] == "parallel_prefix" and declared[ALIAS+".topology"] == "brent_kung", declared
    assert not any(key.endswith(("chunk_width_bits", "full_adder_logic")) for key in declared), declared
    baseline, values, _ = generators.seed(direct.ctx(), "baseline")
    assert "fam_prefix_brent_kung_w9" in baseline and values[ALIAS+".topology"] == "brent_kung"
    verify(direct, root / "fixed_lane", "fam_prefix_brent_kung_w9", 9)

    reverse = instance({ALIAS+".family": {"fixed": "parallel_prefix"}, ALIAS+".topology": {"fixed": "brent_kung"}})
    require_same(reverse, "parallel_prefix", {"topology": "brent_kung"})
    verify(reverse, root / "fixed_assimilator", "fam_prefix_brent_kung_w9", 9)

    narrowed = instance({LANE+".family": {"search": ["ripple_carry", "parallel_prefix"]},
                         ALIAS+".family": {"search": ["parallel_prefix"]},
                         LANE+".topology": {"search": ["sklansky", "brent_kung"]},
                         ALIAS+".topology": {"search": ["brent_kung", "kogge_stone"]}})
    domain_names = [LANE+".family", ALIAS+".family", LANE+".topology", ALIAS+".topology"]
    before = {name: narrowed.bindings[name].to_json() for name in domain_names}
    require_same(narrowed, "parallel_prefix", {"topology": "brent_kung"})
    assert {name: narrowed.bindings[name].to_json() for name in domain_names} == before
    verify(narrowed, root / "search_intersection", "fam_prefix_brent_kung_w9", 9)

    chunks = instance({LANE+".family": {"fixed": "ripple_carry"},
                       LANE+".chunk_width_bits": {"search": {"min": 2, "max": 8, "step": 1}},
                       ALIAS+".chunk_width_bits": {"search": {"min": 3, "max": 9, "step": 3}},
                       LANE+".full_adder_logic": {"fixed": "xor_majority"}})
    require_same(chunks, "ripple_carry", {"chunk_width_bits": 3, "full_adder_logic": "xor_majority"})
    verify(chunks, root / "range_intersection", "fam_adder_ripple_carry", 9, {"W": 9, "CHUNK": 3, "FORM": 2})

    nested = instance({LANE+".family": {"fixed": "carry_select"}, LANE+".block_width": {"fixed": 3},
                       LANE+".block_adder.family": {"fixed": "parallel_prefix"},
                       LANE+".block_adder.topology": {"fixed": "brent_kung"}})
    require_same(nested, "carry_select", {"block_width": 3, "block_adder.family": "parallel_prefix",
                                          "block_adder.topology": "brent_kung"})
    verify(nested, root / "nested_alias", "fam_prefix_brent_kung_w3", 3)

    # Inactive search axes remain inactive; a user-fixed inactive pin is
    # rejected even when another alias would otherwise agree with it.
    inactive = instance({**prefix, LANE+".log2_sparsity": {"search": [0]}, ALIAS+".log2_sparsity": {"search": [1]}})
    assert "log2_sparsity" not in require_same(inactive, "parallel_prefix", {"topology": "brent_kung"})[LANE][1]
    rejected(lambda: families(instance({**prefix, ALIAS+".log2_sparsity": {"fixed": 1}})), "inactive")
    rejected(lambda: families(instance({**prefix, ALIAS+".family": {"fixed": "ripple_carry"}})), "conflicting explicit aliases")
    rejected(lambda: families(instance({**prefix, ALIAS+".family": {"fixed": "parallel_prefix"},
                                        ALIAS+".topology": {"fixed": "kogge_stone"}})), "conflicting explicit aliases")
    rejected(lambda: families(direct, {ALIAS+".family": "ripple_carry"}), "conflicting explicit aliases")
    rejected(lambda: families(instance({**prefix, ALIAS+".family": {"search": ["ripple_carry"]}})), "empty intersection")
    rejected(lambda: families(instance({**prefix, ALIAS+".topology": {"search": ["sklansky"]}})), "empty intersection")
    rejected(lambda: families(instance({LANE+".family": {"fixed": "ripple_carry"},
                                        LANE+".chunk_width_bits": {"search": [2, 4]},
                                        ALIAS+".chunk_width_bits": {"search": [3, 6]}})), "empty intersection")
    restricted = instance({**prefix, LANE+".valency": {"search": [2]}})
    rejected(lambda: families(restricted, {LANE+".valency": 3}), "outside the user-bound")
    multiple = instance({**prefix, "core.adder.m1.family": {"fixed": "parallel_prefix"},
                         "core.adder.m1.topology": {"fixed": "kogge_stone"}}, multimode=True)
    rejected(lambda: families(multiple), "per-mode representation interface")
    print(f"PASS 5 ADIR-to-RTL alias cases, nested/default/domain checks and 9 explicit rejections; {root}")
    rns_cases(root / "rns")


if __name__ == "__main__":
    main()
