"""After the OpenRouter credit ran out (2026-09-23 17:37): the resume command of every Table A run that
brings it to 70 real iterations. An ADIR iteration whose solution call was refused for billing produced
nothing (no program entered the database), so the run resumes to 70 + that count; a plain-loop call
refused for billing is deleted (its directory and archive line) and the loop resumes to 70.
Prints the commands, one per line: `<job> <command>`; --apply also deletes the plain loop's refused calls."""
import json, glob, shutil, sys
from pathlib import Path
R = Path("$A3EVAL/3rdparty/chialu/run")
N = 70
apply = "--apply" in sys.argv
def billing(t): t = (t or "").lower(); return "billingerror" in t or "billing_error" in t or "available credits" in t
for d in sorted(R.glob("exp.*")):
    name = d.name[len("exp."):]
    t, m, rep = name.rsplit(".", 2)
    k = rep[1:]
    tf = {"int_subword_alu": "int_subword_alu", "fp_alu_cmp": "eval/fp_alu_cmp", "fp_alu_cmp_hf": "eval/fp_alu_cmp_hf"}[t]
    if m == "plain":
        calls = sorted(d.glob("call_*"), key=lambda p: int(p.name.split("_")[1]))
        bad = [c for c in calls if (c / "call.json").is_file() and billing(json.loads((c / "call.json").read_text()).get("stderr"))]
        if apply and bad:
            for c in bad:
                shutil.rmtree(c, ignore_errors=True)
            # the archive lines of those calls go too (the resume also trims every call past the first gap)
            gone = {int(c.name.split("_")[1]) for c in bad}
            db = d / "results_db.jsonl"
            lines = [l for l in db.read_text().splitlines() if l.strip() and (json.loads(l).get("call") or 0) not in gone]
            db.write_text("".join(l + "\n" for l in lines))
        print(f"{name} python3 ../../harness/plain_loop.py targets/{tf}.yaml --calls {N} --out run/exp.{name} --resume   # {len(bad)} refused calls removed")
        continue
    bill = 0
    for l in (d / "llm_calls.jsonl").read_text().splitlines() if (d / "llm_calls.jsonl").is_file() else []:
        try: r = json.loads(l)
        except ValueError: continue
        if r.get("role") == "solution" and billing(r.get("error")): bill += 1
    total = N + bill
    if m == "chialu":
        print(f"{name} python3 -m chialu.pipeline targets/{tf}.yaml --run-dir run/exp.{name} --resume --search-iterations {total}   # {bill} refused")
    else:
        print(f"{name} python3 -m adir.cli run targets/{tf}.free_{m}.yaml --run-dir run/exp.{name} --resume --iterations {total}   # {bill} refused")
