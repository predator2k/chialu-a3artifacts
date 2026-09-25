"""The fault gate fails a candidate that exposes too few injection sites
(audit of exp3: flattened or renamed designs passed with 0 sites and
escape_max 0.0)."""
from pathlib import Path

import pytest

RUN = Path(__file__).resolve().parents[1] / "run"
FLAT = RUN / "exp3.int_subword_alu.adaevolve.r2" / "programs" / "315a80d75cf0.sv"
SEED = RUN / "exp3.int_subword_alu.adaevolve.r2" / "seeds" / "int_subword_alu.baseline" / "program.sv"


def _case(tmp_path):
    from chialu.targets.derive import checker_rtl, seed_alu_text, verify_files, detect_budget
    from chialu.targets.rtl.families import library_closure
    from chialu.verify.alu_ref import normalize_spec
    spec = normalize_spec({
        'unit': 'alu', 'dut_name': 'alu_core', 'check_en': True,
        'modes': [{'format': 'int8', 'count': 1}], 'ops': ['add', 'sub', 'adc'],
        'checker_family': 'berger', 'checker_name': 'alu_checker',
        'carry_replica': {'family': 'end_around_carry', 'modulus': 'generic_p_correction', 'modulus_value': 3},
        'n_random': 128, 'n_random_masks': 128,
    })
    spec['detect'] = detect_budget(spec, 128)
    checker = checker_rtl(spec)
    checker += library_closure(checker)
    return seed_alu_text(spec).text, verify_files(spec, tmp_path, checker), checker


def test_seed_passes_and_renamed_units_fail(tmp_path):
    from adir.registry import underlying
    from chialu import eda
    rtl, files, checker = _case(tmp_path)
    seed = underlying(eda.fault)(rtl, files, checker, 300)
    assert seed['pass'], seed['detail']
    assert seed['sites'] > 0
    # the seed's own count as the reference passes
    again = underlying(eda.fault)(rtl, files, checker, 300, seed_sites=seed['sites'])
    assert again['pass'], again['detail']
    # the same logic with its unit modules renamed away: no injection site is left
    renamed = rtl.replace("alu_core_u_", "alu_core_blk_")
    assert renamed != rtl
    conf = underlying(eda.conformance)(renamed, files)
    assert conf['pass'], conf['detail']          # still correct, so only the site gate can stop it
    r = underlying(eda.fault)(renamed, files, checker, 300)
    assert r['pass'] is False
    assert "0 injection sites" in r['detail']
    # a seed reference far above what the candidate exposes fails too
    r = underlying(eda.fault)(rtl, files, checker, 300, seed_sites=4 * seed['sites'])
    assert r['pass'] is False and "of the seed's" in r['detail']


def test_site_violations_rules():
    from chialu.eda import site_violations
    assert site_violations({"checked": 10, "with_sites": 10, "sites": 40}) == []
    assert "0 injection sites" in site_violations({"checked": 10, "with_sites": 0, "sites": 0})[0]
    assert "pairs" in site_violations({"checked": 10, "with_sites": 4, "sites": 12})[0]
    assert site_violations({"checked": 10, "with_sites": 10, "sites": 40}, seed_sites=80) == []
    assert "seed" in site_violations({"checked": 10, "with_sites": 10, "sites": 39}, seed_sites=80)[0]


@pytest.mark.skipif(not (FLAT.is_file() and SEED.is_file()), reason="exp3 run not present")
def test_real_flattened_candidate_has_no_sites():
    from chialu.verify import fault_sites
    assert fault_sites.sites_by_pair(SEED.read_text()), "the seed exposes unit sites"
    assert not any(fault_sites.sites_by_pair(FLAT.read_text()).values())
