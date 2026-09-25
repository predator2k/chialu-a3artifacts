"""chiALU's priors and tactic sources for ADIR: the structure-grain area
surrogate (ml/) as a ranking prior, and the tactic sources the prompt
sampler draws from. `declaration_features` is the one featurization of
a declaration block, shared with the trainer in ml/surrogate.py."""
from __future__ import annotations

import os
from pathlib import Path

import re

from adir import Prior, TacticSource

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS = REPO_ROOT / "ml" / "models"
DEFAULT_PDK = "nangate45"


def declaration_features(declarations: dict) -> dict:
    """The feature counts of a declaration block: one key per (variable
    suffix, value), `family` for every `*.family` variable, counted over
    the variables that carry it. Only dotted variable names with scalar
    values count, so the line entries ADIR's seed ranker passes beside
    the VAR values are ignored. The block lists decisions alone, so a
    decision at its default is absent here at training and at prediction
    alike."""
    feats: dict = {}
    for name, v in (declarations or {}).items():
        if "." not in str(name) or v is None or isinstance(v, (list, dict, tuple)):
            continue
        suffix = str(name).rsplit(".", 1)[-1]
        key = (suffix, str(v))
        feats[key] = feats.get(key, 0) + 1
    return feats


def feature_vector(feats: dict, vocab: list) -> list:
    """The counts of `feats` in the order of `vocab`; a key outside the
    vocabulary is dropped."""
    idx = {tuple(k): i for i, k in enumerate(vocab)}
    x = [0.0] * len(vocab)
    for k, n in feats.items():
        i = idx.get(tuple(k))
        if i is not None:
            x[i] = float(n)
    return x


def model_pdk() -> str:
    """The PDK whose model the prior reads: CHIALU_SURROGATE_PDK when set,
    else the one PDK with a trained area model, else nangate45 (ADIR
    hands a prior the declarations alone, so the PDK cannot come from
    the run)."""
    env = os.environ.get("CHIALU_SURROGATE_PDK")
    if env:
        return env
    trained = sorted(p.name[: -len(".area_um2.pkl")] for p in MODELS.glob("*.area_um2.pkl"))
    return trained[0] if len(trained) == 1 else DEFAULT_PDK


_MODEL_CACHE: dict = {}


def load_model(pdk: str, target: str):
    """The trained bundle {model, vocab, ...} of ml/models/<pdk>.<target>.pkl,
    or None; re-read when the file changes."""
    path = MODELS / f"{pdk}.{target}.pkl"
    key = (str(path), path.stat().st_mtime if path.is_file() else None)
    if key not in _MODEL_CACHE:
        bundle = None
        if path.is_file():
            try:
                import pickle
                with path.open("rb") as f:
                    bundle = pickle.load(f)
            except Exception:  # noqa: BLE001
                bundle = None
        _MODEL_CACHE.clear()
        _MODEL_CACHE[key] = bundle
    return _MODEL_CACHE[key]


def predict(pdk: str, target: str, declarations: dict):
    """The surrogate's prediction of `target` for a declaration block, or
    None without a trained model for the PDK."""
    bundle = load_model(pdk, target)
    if bundle is None:
        return None
    x = feature_vector(declaration_features(declarations), bundle["vocab"])
    try:
        return float(bundle["model"].predict([x])[0])
    except Exception:  # noqa: BLE001
        return None


def _db_structure_area(declarations: dict):
    """The area of a declaration block priced from the synthesis database:
    per STRUCTURE line the row of the family the block declares for that
    structure's slot and index, at the line's width. Returns None when the
    block carries no STRUCTURE line or the database prices none of them."""
    from chialu import synthdb
    from chialu.lines import parse_structure
    from chialu.targets.rtl.structures import structure_index
    rows = declarations.get("STRUCTURE")
    if not isinstance(rows, list) or not rows:
        return None
    pdk = model_pdk()
    total, priced = 0.0, 0
    for tokens in rows:
        try:
            e = parse_structure(tokens)
        except Exception:  # noqa: BLE001 - a line the parser rejects is not priced
            continue
        kind = str(e.get("kind") or "")
        slot = str(e.get("slot") or kind)
        width = int(e.get("width") or 0)
        if not kind or width <= 0:
            continue
        sid = e["_"][0] if isinstance(e.get("_"), list) else str(e.get("id", ""))
        base = f"core.{slot}.{structure_index(sid, kind)}"
        family = declarations.get(base + ".family")
        if family is None:
            continue
        pins = {k.rsplit(".", 1)[-1]: v for k, v in declarations.items()
                if isinstance(k, str) and k.startswith(base + ".") and not k.endswith(".family")}
        got = synthdb.estimate_structure(pdk, kind, str(family), pins, width)
        if got:
            total += float(got.get("area_um2") or 0.0)
            priced += 1
    return (total, priced) if priced else None


def _predict_structure_area(declarations: dict):
    """The predicted area of a declaration block: the surrogate under
    ml/models where one is trained, else the synthesis database's own
    rows. The database path is what makes `rank` order the seeds at all:
    without a trained model the prior used to return the same value for
    every block, so the ranker kept the first `top` seeds in list order.
    A block the database cannot price keeps the wide interval."""
    v = predict(model_pdk(), "area_um2", declarations)
    if v is not None:
        return (v, v * 0.8, v * 1.25)
    got = _db_structure_area(declarations)
    if got is None:
        return (0.0, 0.0, float("inf"))
    area, priced = got
    # the interval widens with the structures the database could not price
    return (area, area * 0.7, area * 1.6 if priced else float("inf"))


STRUCTURE_AREA = Prior("chialu_structure_area", _predict_structure_area)


_SEG_RE = re.compile(r"([A-Za-z_][\w.()]*?)\((\d+), (\d+) ps\)")


def _units_of_summary(summary: str) -> list:
    """[(instance, area um2, out arrival ps)] from the unit table of
    synth_ppa.summary (the rows whose first field is an instance)."""
    out = []
    for line in (summary or "").splitlines():
        f = line.split()
        if len(f) >= 9 and f[0].startswith("u_"):
            try:
                out.append((f[0], float(f[-6]), float(f[-1])))
            except ValueError:
                continue
    return out


def _target(instance, archive, parent):
    """Two targets for the round, from the parent's synthesis report: the
    critical path (the units that own its segments, to shorten) and the
    logic off it (the largest units the path does not cross, to shrink
    without lengthening the path). The composer's UCB picks between
    them by child improvement; the operator says what kind of change,
    the target says where."""
    fb = (parent or {}).get("feedback") or {}
    path = str(fb.get("synth_ppa.critical_path") or "")
    if not path:
        return []
    on_path = [o for o, _c, _p in _SEG_RE.findall(path) if o.startswith("u_")]
    segs = sorted(((int(ps), o) for o, _c, ps in _SEG_RE.findall(path)), reverse=True)
    longest = ", ".join(f"{o} ({ps} ps)" for ps, o in segs[:3])
    on = (f"Target: the critical path. {path[:400]}. The longest segments: {longest}. Shorten the path: a decode "
          "or select net with a fanout above 20 wants duplication, a long run inside one unit a faster family or a "
          "shorter chain, two units in series a merged stage; a change off the path does not move the delay.")
    units = _units_of_summary(str(fb.get("synth_ppa.summary") or ""))
    off_units = [u for u in units if u[0] not in set(on_path)]
    off_units.sort(key=lambda u: -u[1])
    if not off_units:
        return [on]
    listed = ", ".join(f"{u[0]} ({u[1]:.0f} um2, out at {u[2]:.0f} ps)" for u in off_units[:4])
    off = (f"Target: the logic off the critical path. The largest units the path does not cross: {listed}. Reduce "
           "their area (a smaller family, a shared sub-structure, a narrower chain, dropped redundancy) without "
           "lengthening the path; their slack is the room.")
    return [on, off]


# structure slot -> the move library's domain (knowledge/moves/<id>.md `applies_to`)
SLOT_MOVE_DOMAIN = {"adder": "adder", "comparator": "adder", "multiplier": "mul", "divider": "div",
                    "shifter": "shift", "bitcount": "shift", "subword": "shift",
                    "fp_adder": "fp", "fp_multiplier": "fp", "fp_divider": "fp", "fp_comparator": "fp",
                    "converter": "fp", "rounder": "fp", "unpacker": "fp", "logic": "alu",
                    "posit_unit": "dsp", "checker": "checker"}


def move_domains(instance) -> set:
    """The move domains of a bound unit: the unit class, the domains of
    its structure slots, decimal for a BCD mode, redundant for a
    redundant or RNS core."""
    info = instance.elaboration.info or {}
    unit = info.get("unit") or "alu"
    out = {{"alu": "alu", "vec_sfu": "sfu", "vec_dot_acc": "dot"}.get(unit, "alu")}
    for slot in (info.get("families") or {}):
        d = SLOT_MOVE_DOMAIN.get(slot)
        if d:
            out.add(d)
    if info.get("checked"):
        out.add("checker")
    spec = info.get("spec") or {}
    if "bcd" in (spec.get("families") or []):
        out.add("decimal")
    b = instance.bindings.get("core.family")
    if b is not None and b.time == "fixed" and b.value in ("redundant_internal", "rns_internal"):
        out.add("redundant")
    return out


# the move cards (knowledge/moves) reach the agent through the knowledge index rather than as a sampled tactic
TARGET = TacticSource("target", _target)
