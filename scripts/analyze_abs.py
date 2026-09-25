"""exp10 absolute comparison within the first K iterations, one common reference per target:
baseline B (the library baseline seed; for hand runs the reference design itself). Per run (start + found designs):
best delay among designs with area <= B.area; best area among designs with delay <= B.delay; hypervolume w.r.t.
ref = 1.3 x B (area, delay). Mean ± std over 3 repetitions. Delay differences < 5 % are within synthesis noise."""
import glob, json, os, sys, statistics as st, collections
RUN = "$A3EVAL/3rdparty/chialu/run"
BASE = {"int_subword_alu": (5743.5, 1782.6), "fp_alu_cmp": (7283.6, 4385.4), "fp_alu_cmp_hf": (6350.2, 4520.7),
        "fpnew": (6194.1, 3681.8), "hardfloat": (5420.5, 2800.8), "transdot": (4475.5, 4135.5)}
def recs(d): return [json.loads(l) for l in open(os.path.join(d, "results_db.jsonl")) if l.strip()]
def pts(rs): return [tuple(r["goal_values"]) for r in rs if r.get("feasible") and r.get("goal_values") and None not in r["goal_values"]]
def hv(points, ref):
    ps = sorted({p for p in points if p[0] < ref[0] and p[1] < ref[1]}); front, best = [], float("inf")
    for a, d in ps:
        if d < best: front.append((a, d)); best = d
    s, pd = 0.0, ref[1]
    for a, d in front: s += (ref[0] - a) * (pd - d); pd = d
    return s
def iters(d):
    f = os.path.join(d, "iteration.txt")
    return int(open(f).read().strip() or 0) if os.path.exists(f) else max([r.get("iteration") or 0 for r in recs(d)] + [0])
runs = [d for d in sorted(glob.glob(f"{RUN}/exp10.*")) if os.path.isdir(d)]
K = int(sys.argv[1]) if len(sys.argv) > 1 else min(iters(d) for d in runs)
G = collections.defaultdict(list)
for d in runs:
    p = os.path.basename(d).split("."); G[(p[1], p[2])].append(d)
print(f"# exp10, first K={K} iterations (all runs reached >= {min(iters(d) for d in runs)}); common reference per target\n")
print("| target | method | best delay @ area<=B (ps) | best area @ delay<=B (µm²) | HV (norm. to B box) | min delay any | min area any |")
print("|---|---|---|---|---|---|---|")
for (t, m), ds in sorted(G.items()):
    B = BASE[t]; ref = (1.3 * B[0], 1.3 * B[1]); v = collections.defaultdict(list)
    for d in ds:
        rs = recs(d); P = pts([r for r in rs if r.get("is_seed") or (r.get("iteration") or 0) <= K])
        if not P: continue
        v["bd"].append(min([p[1] for p in P if p[0] <= B[0]] or [float("nan")]))
        v["ba"].append(min([p[0] for p in P if p[1] <= B[1]] or [float("nan")]))
        v["hv"].append(hv(P, ref) / (ref[0] * ref[1]))
        v["md"].append(min(p[1] for p in P)); v["ma"].append(min(p[0] for p in P))
    f = lambda x, n=0: (f"{st.mean(x):.{n}f} ± {st.pstdev(x):.{n}f}" if all(y == y for y in x) else "n/a (" + ", ".join(f"{y:.0f}" for y in x) + ")")
    print(f"| {t} | {m} | {f(v['bd'])} | {f(v['ba'])} | {f(v['hv'],3)} | {f(v['md'])} | {f(v['ma'])} |")
print("\nB (area/delay): " + "; ".join(f"{k} {a:.0f}/{d:.0f}" for k, (a, d) in BASE.items()))
