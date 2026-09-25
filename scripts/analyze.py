"""exp10 interim/final results: per target and method, the designs found within the first K iterations
(records with iteration <= K; seeds excluded from "found"), metrics relative to each run's own starting point.

    python3 analyze.py [K]      (default: the smallest iteration count reached by every run)

Per run: best delay among designs with area <= start area, best area among designs with delay <= start delay,
hypervolume of (start front + found) minus hypervolume of the start front, both w.r.t. the reference point
(1.1 x max start area, 1.1 x max start delay) of that target's common baseline. Reported as mean ± std over
the 3 repetitions. Differences below the synthesis noise floor (delay < 5 %) are not improvements."""
import glob, json, os, sys, statistics as st, collections

RUN = "$A3EVAL/3rdparty/chialu/run"


def records(d):
    out = []
    for l in open(os.path.join(d, "results_db.jsonl")):
        try:
            out.append(json.loads(l))
        except ValueError:
            pass
    return out


def pts(rs):
    return [tuple(r["goal_values"]) for r in rs
            if r.get("feasible") and r.get("goal_values") and None not in r["goal_values"]]


def hv(points, ref):
    ps = sorted({p for p in points if p[0] < ref[0] and p[1] < ref[1]})
    front, best = [], float("inf")
    for a, d in ps:
        if d < best:
            front.append((a, d)); best = d
    area, prev_d = 0.0, ref[1]
    for a, d in front:
        area += (ref[0] - a) * (prev_d - d); prev_d = d
    return area


def iters(d):
    f = os.path.join(d, "iteration.txt")
    if os.path.exists(f):
        return int(open(f).read().strip() or 0)
    return max([r.get("iteration") or 0 for r in records(d)] + [0])


runs = [d for d in sorted(glob.glob(f"{RUN}/exp10.*")) if os.path.isdir(d)]
K = int(sys.argv[1]) if len(sys.argv) > 1 else min(iters(d) for d in runs)
groups = collections.defaultdict(list)
for d in runs:
    parts = os.path.basename(d).split(".")
    groups[(parts[1], parts[2])].append(d)

print(f"# exp10 results within the first K={K} iterations (runs keep going; min iterations over all runs = "
      f"{min(iters(d) for d in runs)})\n")
print("| target | method | runs | start (area/delay) | best delay @ area<=start | best area @ delay<=start | "
      "ΔHV vs start (%) | designs dominating start |")
print("|---|---|---|---|---|---|---|---|")
for (t, m), ds in sorted(groups.items()):
    bd, ba, dhv, ndom, starts = [], [], [], [], []
    for d in ds:
        rs = records(d)
        seed = pts([r for r in rs if r.get("is_seed")])
        found = pts([r for r in rs if not r.get("is_seed") and (r.get("iteration") or 0) <= K])
        if not seed:
            continue
        sa = min(p[0] for p in seed); sd = min(p[1] for p in seed)
        s0 = min(seed, key=lambda p: p[1])          # the fastest start point
        starts.append(s0)
        ref = (1.1 * max(p[0] for p in seed), 1.1 * max(p[1] for p in seed))
        h0 = hv(seed, ref); h1 = hv(seed + found, ref)
        dhv.append(100 * (h1 - h0) / h0 if h0 else 0.0)
        bd.append(min([p[1] for p in found if p[0] <= s0[0]] + [s0[1]]) / s0[1] - 1)
        ba.append(min([p[0] for p in found if p[1] <= s0[1]] + [s0[0]]) / s0[0] - 1)
        ndom.append(sum(1 for p in found if any(p[0] <= q[0] and p[1] <= q[1] and p != q for q in seed)))
    f = lambda v: f"{100 * st.mean(v):+.1f}% ± {100 * (st.pstdev(v) if len(v) > 1 else 0):.1f}"
    s0 = starts[0] if starts else (0, 0)
    print(f"| {t} | {m} | {len(ds)} | {s0[0]:.0f}/{s0[1]:.0f} | {f(bd)} | {f(ba)} | "
          f"{st.mean(dhv):+.1f} ± {st.pstdev(dhv) if len(dhv) > 1 else 0:.1f} | {st.mean(ndom):.1f} |")
