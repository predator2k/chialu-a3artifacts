"""A candidate that reaches a file outside its own text (an `include of a
sibling run's program, a $readmem of a table) is rejected by lint,
conformance and synthesis before any tool runs."""
from pathlib import Path

import pytest

from adir.registry import underlying
from chialu import eda

ROOT = Path(__file__).resolve().parents[1]
CHEAT = ROOT / "run/exp3.int_subword_alu.plain.r1/programs/424e994ee1a0.sv"
SEED = ROOT / "run/exp3.int_subword_alu.plain.r1/seed/program.sv"

CLEAN = "module m(input logic [3:0] a, output logic [3:0] y);\n  assign y = ~a; // see \"/abs\" ../x\nendmodule\n"


@pytest.mark.parametrize("text,kind", [
    ('`include "alu_core.sv"\n' + CLEAN, "`include"),
    ('  `include "/data2/x/run/r/best.sv"\n' + CLEAN, "`include"),
    ("module t; reg [7:0] m[0:3]; initial $readmemh(\"x.hex\", m); endmodule\n", "$readmemh"),
    ("module t; integer f; initial f = $fopen(\"out.txt\"); endmodule\n", "$fopen"),
    ('module t; initial $display("../a"); endmodule\n', "relative path"),
    ('module t; initial $display("/abs/file"); endmodule\n', "absolute path"),
    ('module t; initial $display("x/run/exp3.r1/y"); endmodule\n', "run directory"),
])
def test_flagged(text, kind):
    refs = eda.external_refs(text)
    assert refs and any(kind in r for r in refs), refs


def test_clean_text_and_comments_pass():
    assert eda.external_refs(CLEAN) == []
    assert eda.external_refs("/* `include \"x.sv\" $readmemh */\n" + CLEAN) == []


@pytest.mark.skipif(not SEED.is_file(), reason="run artifacts absent")
def test_seed_passes():
    assert eda.external_refs(SEED.read_text()) == []


@pytest.mark.skipif(not CHEAT.is_file(), reason="run artifacts absent")
def test_known_cheating_candidate_fails_every_evaluator():
    text = CHEAT.read_text()
    assert any("`include" in r for r in eda.external_refs(text))
    r = underlying(eda.lint)(text)
    assert r["ok"] is False and r["detail"].startswith("external reference")
    c = underlying(eda.conformance)(text, {})
    assert c["pass"] is False and c["detail"].startswith("external reference")
    s = underlying(eda.synth_ppa)(text, "alu_core", "nangate45", 1000)
    assert s["ok"] is False and s["detail"].startswith("external reference")


def test_lint_still_passes_clean_text():
    r = underlying(eda.lint)(CLEAN)
    assert r["ok"], r["detail"]


SYSTEM = ('module alu_core(input logic [3:0] a, output logic [3:0] y);\n'
          '  initial $system("touch pwned");\n  assign y = ~a;\nendmodule\n')
INCLUDE = '`include "/data2/x/run/r/best.sv"\n' + CLEAN


@pytest.mark.parametrize("text", [SYSTEM, INCLUDE])
def test_fault_synth_unit_yosys_stat_refuse_external_refs(text, tmp_path, monkeypatch):
    """fault runs in parallel with lint, and synth_unit / yosys_stat run a
    tool on the text: each refuses a candidate with an external reference
    before any build, simulation or cache lookup."""
    def boom(*a, **k):
        raise AssertionError("a tool ran on a candidate with an external reference")
    monkeypatch.setattr(eda, "_candidate_build", boom)
    monkeypatch.setattr(eda, "_sim_bundle", boom)
    monkeypatch.setattr(eda, "frontend_source", boom)
    monkeypatch.setattr(eda, "SYNTH_CACHE_DIR", tmp_path / "cache")
    f = underlying(eda.fault)(text, {"masks.hex": "1\n", "vectors.hex": "0\n"}, "")
    assert f["pass"] is False and f["detail"].startswith("external reference"), f
    u = underlying(eda.synth_unit)(text, [{"_": ["u0"], "sv": "alu_core"}], "nangate45", 1000)
    assert u["ok"] is False and u["detail"].startswith("external reference"), u
    assert u["area_um2"] is None and not (tmp_path / "cache").exists()
    y = underlying(eda.yosys_stat)(text, "alu_core")
    assert y["ok"] is False and y["detail"].startswith("external reference") and y["cells"] is None, y
