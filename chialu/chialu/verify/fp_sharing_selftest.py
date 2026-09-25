"""Bit-exact FP stage sharing, including independent simultaneous lanes."""
from pathlib import Path
import tempfile

from adir.registry import underlying
from chialu import eda
from chialu.targets import derive
from chialu.targets.rtl.alu_seed import default_partition, structure_manifest
from chialu.verify.alu_ref import normalize_spec


def main():
    directory = Path(tempfile.mkdtemp(prefix="chialu-fp-sharing-"))
    spec = normalize_spec({
        "unit": "alu", "dut_name": "alu_core", "check_en": False,
        "modes": [{"format": fmt, "count": 2} for fmt in ("fp16", "bf16", "fp8e5m2")],
        "ops": ["fadd", "fsub", "fmul", "fmin", "fmax", "fcmp"],
        "rounding": ["RNE", "RTZ", "RDN", "RUP", "SR"], "sr_bits": 1,
        "n_random": 256, "seed": 923,
    })
    manifest = structure_manifest(spec)
    selections = {f"core.{kind}.m{mi}": (family, {}) for mi in range(3) for kind, family in (
        ("rounder", "dedicated_per_op"), ("unpacker", "per_unit_unpack"),
        ("fp_adder", "single_path"), ("fp_multiplier", "sig_mul_then_round"),
        ("fp_comparator", "integer_compare_on_bits"))}
    files = derive.verify_files(spec, directory / "verify")

    def partition(groups):
        used = {member for group in groups for member in group}
        return [(f"group{i}", tuple(group)) for i, group in enumerate(groups)] + [
            (name, members) for name, members in default_partition(manifest) if name not in used]

    def render(kind, family, groups, pins=None):
        families = dict(selections)
        for mi in range(3):
            families[f"core.{kind}.m{mi}"] = (family, pins or {})
        return derive.seed_alu_text(spec, partition(groups), families=families).text

    def verify(name, text):
        (directory / f"{name}.sv").write_text(text)
        result = underlying(eda.conformance)(text, files)
        assert result["pass"], (name, result)
        print(name, "PASS", flush=True)

    for kind, families in (("rounder", ("dedicated_per_op", "shared_per_lane")),
                           ("unpacker", ("per_unit_unpack", "shared_per_lane"))):
        for family in families:
            # Only lane 0 shares. Each mode's lane 1 must remain independent.
            text = render(kind, family, [[f"m{mi}.l0.{kind}" for mi in range(3)]])
            assert f"u_shared_{kind}_l0_m0_1_2" in text
            for mi in range(3):
                assert f"u_shared_{kind}_l1_m{mi}" in text
            assert f"u_shared_{kind}_l1_m0_1" not in text
            verify(f"{kind}_{family}", text)
            if kind == "unpacker":
                # Without normalization, the selected decoder shares its
                # exponent subtraction rather than an LZC or a shifter.
                text = render(kind, family, [[s.id for s in manifest if s.kind == kind]],
                              {"denormal_handling": "in_datapath"})
                assert "shared_exp_code - shared_exp_bias" in text
                verify(f"{kind}_{family}_stored", text)
        # Two explicit groups of the same kind, at different lane positions.
        groups = [[f"m{mi}.l0.{kind}" for mi in (0, 1)],
                  [f"m{mi}.l1.{kind}" for mi in (1, 2)]]
        text = render(kind, families[0], groups)
        assert f"u_shared_{kind}_l0_m0_1" in text
        assert f"u_shared_{kind}_l1_m1_2" in text
        verify(f"{kind}_two_groups", text)

    def refuses(call, message):
        try:
            call()
        except ValueError as error:
            assert message in str(error), error
        else:
            raise AssertionError(f"expected refusal: {message}")

    for kind, family in (("fp_adder", "single_path"), ("rounder", "shared_per_lane"),
                         ("unpacker", "shared_per_lane")):
        refuses(lambda: render(kind, family, [[f"m2.l0.{kind}", f"m2.l1.{kind}"]]),
                "put each lane in its own group")
    refuses(lambda: render("rounder", "shared_per_lane", [["m0.l0.rounder", "m1.l1.rounder"]]),
            "common lane position")
    mixed = dict(selections)
    mixed["core.rounder.m1"] = ("shared_per_lane", {})
    refuses(lambda: derive.seed_alu_text(spec, partition([["m0.l0.rounder", "m1.l0.rounder"]]),
                                         families=mixed), "identical families and pins")
    print(f"PASS 8 bit-exact shared designs and 5 repairable refusals; {directory}")


if __name__ == "__main__":
    main()
