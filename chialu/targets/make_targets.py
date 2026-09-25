"""The target run files of this directory, written from one skeleton:
`python3 targets/make_targets.py` rewrites every `<name>.yaml`. Edit a
target here rather than in its yaml, so the shared parts (the cluster,
the graph, the search settings) stay identical across targets. The task
statement of the prompt is rendered by `chialu/task.py` from the bound
unit and the role text is `targets/prompts/role.md`; a run file names
both under `role:` and `task:`."""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent

CLUSTER = """# ---- CHIA cluster (read by `chia up`) ---------------------------------
# Two machines are registered: <host> (the head, also an EDA worker) and
# <host>.  Neither shares a filesystem with the other, so each node type
# sources its own environment file; those files move HOME onto the large
# volume (/data2 on <host>, /mnt/ssd on <host>) so that nothing this
# cluster runs writes to a home quota or to /tmp.
cluster_name: {name}

provider:
  head_ip: ${{THIS_MACHINE}}

auth:
  ssh_user: ${{USER}}
  overrides:
    <IP>:                        # <host>; a literal IP, chia expands ${{VAR}} in values only
      tunnel:                            # <host>'s and <host>'s firewalls pass only port 22, so Ray rides an SSH tunnel
        gcs_tunnel_port: 6395            # the worker dials $RAY_HEAD_IP:<this>, so it must equal the head port above
        # chia pins the HEAD's ray worker ports as soon as any worker is tunnelled, and its
        # default range is 100 wide.  Ray keeps idle workers alive, so on a 344-CPU cluster the
        # range runs out and every later driver hangs in cache.start_cache() with no error.
        # The range is also bounded from above: chia reverse-tunnels every one of these ports,
        # each listener costs two sockets (v4 and v6) on <host>, and <host>'s sshd hands sessions
        # RLIMIT_NOFILE=1024 -- the forward fails at offset 483 every time, and
        # ExitOnForwardFailure then kills the whole tunnel.  chia's default fix for this raises
        # sshd's LimitNOFILE, which needs root we do not have, so the range stays under ~450.
        # It sits below the ephemeral range (32768-60999) as well, so an outgoing connection on
        # <host> cannot transiently steal one of these ports.
        head_worker_port_min: 21000
        head_worker_port_max: 21399
        # The worker's range does cost: chia emits one ssh -L per port.  200 is far more than
        # <host>'s 84 eda slots can occupy and still keeps the ssh command manageable.
        ray_worker_port_min: 30000
        ray_worker_port_max: 30199
        pre_tunnel_commands:             # chia's default here needs sudo; we have no root on either machine
          - bash $REMOTE_HOME/chialu-home/start_relay.sh

available_node_types:
  eda:                                   # <host>: verilator, yosys, ABC; the opencode login
    resources:
      eda: 124                           # tool slots: a simulation node takes CHIALU_VERILATOR_JOBS of them, a synthesis one CHIALU_EDA_SYNTH_WEIGHT
      opencode_creds: {creds}                 # concurrent agent calls; one per run in flight, so this bounds how many runs share the host
    num_workers: 1
    compatible_ips: ["${{THIS_MACHINE}}"]
    worker_env_commands:
      - source $CHIALU_HOME/chialu-env.sh
      - export RAY_num_workers_soft_limit=150
      - export VERTEX_LOCATION=global       # the region {model} answers on through opencode
  eda_<host>:                             # <host>: EDA only, no agent calls (no credentials staged there)
    resources:
      eda: 84
      opencode_creds: 0
    num_workers: 1
    compatible_ips: ["${{<host>_MACHINE}}"]
    worker_env_commands:
      - source $REMOTE_HOME/chialu-home/chialu-env.sh

head_env_commands:
  - source $CHIALU_HOME/chialu-env.sh
  - export VERTEX_LOCATION=global
  - export RAY_num_workers_soft_limit=150   # ray keeps one idle worker per CPU by default; on 344
                                            # CPUs that outruns the pinned worker-port range above

head_start_ray_commands:
  - ray stop
  - ray start --head --port=${{CHIA_RAY_PORT}} --include-dashboard=false --dashboard-agent-listen-port=0

worker_start_ray_commands:
  - ray stop
  - ray start --address=$RAY_HEAD_IP:${{CHIA_RAY_PORT}} --dashboard-agent-listen-port=0

cache:
  conformance:
    cache: true
  fault:
    cache: true
  synth_unit:
    cache: true
  synth_ppa:
    cache: true
"""

# the conventions every template shares (chialu/modules/common.py), at the defaults
CONVENTIONS = [("nan_payload", "canonical"), ("invalid_result", "saturate"), ("nan_to_int", "zero"),
               ("minmax_nan", "propagate"), ("tininess", "after"), ("int_div_zero", "riscv"),
               ("zero_sign", "positive"), ("quire_overflow", "wrap"), ("block_scale_rounding", "nearest"),
               ("block_element_overflow", "saturate"), ("sr_compare", "gt")]

SYNTH_REPEATS = 3                            # ABC mappings per synthesis, per-metric median (2026-09-24: 3, for time)
PROVIDER = "deepseek"                      # opencode's provider id (the setting opencode takes beyond claude's and codex's model)
MODEL = "deepseek-flash"                  # the provider's model id. Chosen on a five-model comparison over the
                                         # fp16 ALU: the widest Pareto front, zero call failures, and $0.37-0.69
                                         # a run against $6.46 for gemini-3.1-pro at no better quality.
                                             # credentials, and VERTEX_LOCATION=global is the endpoint verified under opencode's
                                             # API version. gemini-3.8-flash was tried first and dropped: it answers a direct
                                             # call but returns 429 RESOURCE_EXHAUSTED on the first request of a session in
                                             # global, us-central1 and us-east5 alike, and the project's Cloud Quotas listing
                                             # carries no requests-per-minute entry for it at all, only token-per-minute and
                                             # token-per-day ones. gemini-3.1-pro-preview carries 250 requests per minute
REVIEW_AGENT = "opencode"                    # the review's coding agent: opencode | claude | codex (the node's name, and the worker credential it takes)
REVIEW_MODEL = MODEL                         # the review's model; claude and codex take a model alone, opencode a provider beside it
REVIEW_TIMEOUT_S = 900                       # one review call's wall limit
MAX_OUTPUT_TOKENS = 393216                   # a call's output cap, reasoning included: deepseek-v4.1-flash's whole output
                                             # limit in opencode's catalogue. It takes its size out of the 1,048,576-token
                                             # context (openrouter refuses input + max_tokens beyond it, and opencode compacts
                                             # a session at the context less the cap: about 105k tokens here, 786k at 262,144)
MIN_DELAY_PS = 300                           # the synthesis target of a min_delay target: below any design's reach, so every
                                             # synthesis maps for its least delay. `&nf -D` is inert in this ABC build and the
                                             # target binds only through the one buffering pass (buffer; upsize -D; dnsize -D),
                                             # which at a reachable target switches between two mappings rather than tracking
                                             # the clock (tier 2, 2026-09-22): one delay-driven mapping per design is the
                                             # comparison, area reported beside it
# random vectors per mode of the conformance testbench, on top of its directed ones: the count the reference
# designs were judged at (fp_alu_cmp: 427,964 vectors, 12 s of simulation a candidate, against 4 s at 300)
N_RANDOM = 20000
EFFORT = "high"                            # the agent's reasoning effort: opencode passes it as --variant,
                                             # claude as --effort, codex as its reasoning effort
OPENCODE_CREDS = 100                         # concurrent opencode calls the worker admits: the cross-run serializer,
                                             # since one run issues one call at a time; each process costs a few hundred MB


def yaml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return "[" + ", ".join(yaml_value(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{k}: {yaml_value(x)}" for k, x in v.items()) + "}"
    raise TypeError(v)


def variables_block(entries: list) -> str:
    """entries: (name, binding, value, comment): binding is fixed | runtime |
    search | preset | block; a value list under runtime/search renders
    inline; `block` takes pre-rendered lines under `<name>:`."""
    L = []
    for name, binding, value, comment in entries:
        head = f"    {name}:"
        if comment:
            head = f"{head:38s} # {comment}"
        L.append(head)
        if binding == "block":
            L += value
        elif binding == "runtime" and isinstance(value, list) and value and isinstance(value[0], dict):
            L.append("      runtime:")
            for m in value:
                L.append(f"        - {yaml_value(m)}")
        else:
            L.append(f"      {binding}: {yaml_value(value)}")
    return "\n".join(L)


def check_block(t: dict) -> list:
    """The `check` block of a checked ALU target (docs/checker-spec-plan.md):
    one rule over every mode format and every op, the target's checker
    family and pins as its one entry, a replica for the ops the code does
    not cover, no detection bound (the run file's fault constraint gates
    the alias); the search chooses the pins the entry leaves open."""
    family = t.get("checker", "residue")
    entry = {"family": family}
    if family in ("residue", "inverse_residue"):
        entry["modulus"] = t.get("modulus", 15)
    if family == "residue":
        entry["generator_style"] = "csa_tree"
    if family == "inverse_residue":
        entry["inverse_on"] = "check_channel"
    if family == "multi_residue":
        entry.update({"moduli_count": 2, "moduli_set": "low_cost_2a_minus_1"})
    entry["comparator.family"] = "direct_compare"
    formats = sorted({m["format"] for m in t["modes"]}, key=[m["format"] for m in t["modes"]].index)
    return ["      fixed:",
            "        default: {detect: none}        # a pair no rule selects is unchecked",
            "        fallback: duplicate            # an op the code does not cover gets a replica of the datapath",
            "        rules:",
            "          - name: all                  # one rule over every format and op: the one-rule spelling as a table",
            f"            formats: {yaml_value(formats)}",
            f"            ops: {yaml_value(t['ops'])}",
            "            choices:                   # the checker families and pins in play; an omitted pin is open to the search",
            f"              - {yaml_value(entry)}"]


def alu_variables(t: dict) -> list:
    v = [("modes", "runtime", t["modes"], "a mode port over the formats"),
         ("ops", "runtime", t["ops"], "an opcode port over the ops"),
         ("accuracy", "fixed", t.get("accuracy", "exact"), None)]
    if t.get("accuracy") == "approximate":
        v.append(("error_budget", "fixed", t["error_budget"], "the bound the conformance judge applies"))
        v.append(("accuracy_ctl", "fixed", t.get("accuracy_ctl", "static"),
                  "static: one operating point per approximate structure; runtime: a mode port selects it"))
        if t.get("accuracy_ctl") == "runtime":
            v.append(("accuracy_modes", "fixed", t.get("accuracy_modes", 2),
                      "the operating modes the port selects, mode 0 the coarsest"))
    checked = t.get("check_en", True) and t.get("accuracy") != "approximate"
    if checked:
        v.append(("check", "block", check_block(t),
                  "the check specification per format and op (docs/checker-spec-plan.md); the search picks check.<rule>.*"))
    else:
        v.append(("check_en", "fixed", False, "no concurrent checker beside the datapath"))
    v += [("clock_ps", "fixed", MIN_DELAY_PS if t.get("min_delay") else t["clock_ps"],
           "the synthesis target, below any design's reach: every synthesis maps for its least delay (MIN_DELAY_PS)"
           if t.get("min_delay") else "the synthesis timing target: the mapper optimizes area under it; the Pareto front is taken at it"),
          ("rounding", *t.get("rounding", ("fixed", "RNE")), None),
          ("daz_in", "fixed", False, None), ("ftz_out", "fixed", t.get("ftz_out", False), None),
          ("flags", "fixed", t.get("flags", []), "the flag bits the unit reports"),
          ("sr_bits", "fixed", t.get("sr_bits", 8), None),
          ("unary_dual", "fixed", t.get("unary_dual", False), "a unary op on both operands at once"),
          ("check_sr", "fixed", t.get("check_sr", True), None)]
    v += [(k, "fixed", t.get(k, d), None) for k, d in CONVENTIONS]
    v.append(("flag_scope", "fixed", t.get("flag_scope", "per_result"),
              "one flag word per result, or one for the whole operation" if t.get("flag_scope") else None))
    if {"fmadd", "fmsub", "fnmsub", "fnmadd"} & set(t["ops"]):
        v.append(("fma_contract", "fixed", t.get("fma_contract", "fused"),
                  "the fused ops round the exact product plus addend once (a fused fp_fma family), or round the "
                  "product first (sequential: the separate multiplier then adder)"))
    if "quotient_semantics" in t:
        v.append(("quotient_semantics", "runtime", t["quotient_semantics"], None))
    v += [("check_flags", "fixed", t.get("check_flags", False), None),
          ("verify.n_random", "fixed", t.get("n_random", N_RANDOM), "random vectors of the conformance testbench"),
          ("verify.seed", "fixed", 655366, None)]
    if checked:
        v.append(("verify.n_random_masks", "fixed", 2000, "fault masks of the checker gate"))
    if t.get("search_x_form"):
        v.append(("x_form", "search", "all", "internal float representation; exact preserves the baseline"))
    v += [("core.family", "fixed", "unit_per_class", "the core's architecture: one unit per op class, its structures shared by plan"),
          ("core.*", "search", "all", "every structure family and choice; undeclared ones stand at their defaults")]
    for name, dom in t.get("narrow", []):
        v.append((name, "search", dom, None))
    for name, preset in t.get("presets", []):
        v.append((name, "preset", preset, "a named design from chialu/papers.py"))
    for name, value, comment in t.get("fixed", []):
        v.append((name, "fixed", value, comment))
    return v


def dot_variables(t: dict) -> list:
    checked = t.get("check_en", True)
    one = len(t["modes"]) == 1
    v = [("modes", "fixed" if one else "runtime", t["modes"][0] if one else t["modes"],
          t.get("mode_comment", "one mode") if one else "the reductions the datapath serves; a mode port selects"),
         ("accumulate", "fixed", True, "d = c + a . b (false ties c to 0)"),
         ("check_en", "fixed", checked, "the residue checker" if checked else "no checker: the comparison target keeps the fault gate out of the loop"),
         ("clock_ps", "fixed", MIN_DELAY_PS if t.get("min_delay") else t["clock_ps"],
          "the synthesis target, below any design's reach: every synthesis maps for its least delay (MIN_DELAY_PS)"
          if t.get("min_delay") else "the synthesis timing target"),
         ("rounding", "fixed", "RNE", None), ("daz_in", "fixed", False, None), ("ftz_out", "fixed", False, None),
         ("flags", "fixed", [], None), ("sr_bits", "fixed", 8, None), ("check_sr", "fixed", True, None),
         ("overflow", "fixed", "saturate", "integer and fixed-point d results"),
         ("dot_contract", "fixed", "fused", "one rounding of the exact dot product (spec section 6)")]
    v += [(k, "fixed", d, None) for k, d in CONVENTIONS]
    v += [("check_flags", "fixed", False, None), ("verify.n_random", "fixed", N_RANDOM, None), ("verify.seed", "fixed", 655366, None)]
    if checked:
        v += [("verify.n_random_masks", "fixed", 2000, None),
              ("checker.family", "fixed", "residue", "the dot unit's checker: the residue family"),
              ("checker.modulus", "fixed", 15, None),
              ("checker.generator_style", "fixed", "csa_tree", "the residue generator over the chunks")]
    v += [("core.family", "search", "all", "the dot-accumulate architecture (fma_dot_spaces)"),
          ("core.*", "search", "all", "its choices and component families")]
    return v


def sfu_variables(t: dict) -> list:
    v = [("modes", "fixed" if len(t["modes"]) == 1 else "runtime", t["modes"][0] if len(t["modes"]) == 1 else t["modes"],
          "the lanes and formats" + ("" if len(t["modes"]) == 1 else "; a mode port selects")),
         ("functions", "runtime", t["functions"], "an fn_sel port over the functions"),
         ("reconfig_slots", "fixed", 0, "writable-table slots (none)"),
         ("error_budget", "fixed", t["error_budget"], "the accuracy contract the conformance judge applies"),
         ("clock_ps", "fixed", MIN_DELAY_PS if t.get("min_delay") else t["clock_ps"],
          "the synthesis target, below any design's reach: every synthesis maps for its least delay (MIN_DELAY_PS)"
          if t.get("min_delay") else "the synthesis timing target"),
         ("rounding", "fixed", "RNE", None), ("daz_in", "fixed", False, None), ("ftz_out", "fixed", False, None),
         ("flags", "fixed", [], None), ("sr_bits", "fixed", 8, None)]
    v += [(k, "fixed", d, None) for k, d in CONVENTIONS]
    v += [("verify.n_random", "fixed", 400, None), ("verify.seed", "fixed", 655366, None),
          ("core.family", "search", "all", "the approximation method (sfu_spaces)"),
          ("core.*", "search", "all", "its choices and component families")]
    return v


def alu_graph(t: dict, effort: str = "medium") -> str:
    checked = t.get("check_en", True) and t.get("accuracy") != "approximate"
    L = ["  artifacts:",
         "    core:", "      role: seed", "      kind: text", "      source: generated", "      language: systemverilog",
         "      indexed_by: rtl_members           # one member (file) per structure, plus packages, top and library",
         "      declaration_member: top            # the VAR / STRUCTURE block sits in the top's region",
         '      evolve: [alu_core, "alu_core_u_*"]  # the top and every unit module: one region each']
    if checked:
        L += ["    checker:", "      role: fixed", "      kind: text", "      source: generated", "      language: systemverilog"]
    L += ["    verify_bundle:", "      role: fixed", "      kind: text", "      source: generated", "      indexed_by: verify_files", "",
          "  evaluate:", "    nodes:",
          "      declaration:", "        node: adir.declaration",
          "      lint:", "        node: chialu.eda.lint", "        inputs:", "          rtl_text: candidate.core",
          "      conformance:", "        node: chialu.eda.conformance", "        inputs:",
          "          rtl_text: candidate.core", "          files: artifacts.verify_bundle"]
    if checked:
        L += ["      checker_gen:                       # the checker under the candidate's declared check.<rule>.* choices",
              "        node: chialu.eda.checker_gen", "        inputs:", "          files: artifacts.verify_bundle",
              "          decl: decl.check",
              "      fault:", "        node: chialu.eda.fault", "        inputs:", "          rtl_text: candidate.core",
              "          files: artifacts.verify_bundle", "          checker_rtl: checker_gen.rtl_text"]
    review_provider = ([f"          provider: \"'{PROVIDER}'\""] if REVIEW_AGENT == "opencode" else [])
    L += ["      review:                            # a coding agent reads the modules the candidate wrote itself: does the text realize the declared family?",
          f"        node: chialu.review.{REVIEW_AGENT}       # opencode | claude | codex; the node takes that agent's worker credential",
          "        inputs:", "          rtl_text: candidate.core",
          "          structures: decl.STRUCTURE",
          "          declaration: decl.core           # the completed declaration: a structure at its slot's default family is reviewed too"] + review_provider + [
          f"          model: \"'{REVIEW_MODEL}'\"",
          f"          timeout_s: {REVIEW_TIMEOUT_S}",
          f"          effort: {EFFORT}",
          f"          max_output_tokens: {MAX_OUTPUT_TOKENS}",
          "          only: candidate.touched          # the members whose text differs from the parent's; a re-rendered unit needs no review",
          "          work_dir: run.agent_dir           # the review calls' directories (prompt, files, transcript) beside the solution calls'",
          "        when:", "          - conformance.pass",
          "      yosys_stat:                        # a gate count after techmap: the screen before synthesis",
          "        node: chialu.eda.yosys_stat", "        inputs:", "          rtl_text: candidate.core", "          top: alu_core",
          "      synth_unit:                        # ABC map of every unit module alone: the attribution per structure",
          "        node: chialu.eda.synth_unit", "        inputs:", "          rtl_text: candidate.core",
          "          structures: decl.STRUCTURE", "          pdk: nangate45", "          clock_ps: vars.clock_ps",
          f"          repeats: {SYNTH_REPEATS}", f"          effort: {effort}", "        when:", "          - conformance.pass",
          "          - yosys_stat.cells le 2.0 * seed.yosys_stat.cells",
          "      synth_ppa:", "        node: chialu.eda.synth_ppa", "        inputs:", "          rtl_text: candidate.core",
          "          top: alu_core", "          pdk: nangate45", "          clock_ps: vars.clock_ps", f"          repeats: {SYNTH_REPEATS}", f"          effort: {effort}",
          "          timeout_s: 1200",
          "          report: true                   # the critical path, paths and area by hierarchy as feedback, whatever CHIALU_SYNTH_REPORT says",
          "        when:", "          - conformance.pass",
          "          - synth_unit.area_um2 le 1.2 * seed.synth_unit.area_um2",
          "    feedback: [conformance.detail, " + ("checker_gen.detail, fault.detail, " if checked else "") + "review.detail, synth_unit.attribution, synth_ppa.detail, synth_ppa.summary, synth_ppa.critical_path, synth_ppa.paths, synth_ppa.area_by_hierarchy]",
          "", "  constraints:",
          "    - {metric: declaration.ok, eq: true, hard: true}",
          "    - {metric: lint.ok, eq: true, hard: true}"]
    if t.get("accuracy") == "approximate":
        L.append("    - {metric: conformance.pass, eq: true, hard: true, satisfies: error_bound}   # the judge applies error_budget")
    else:
        L.append("    - {metric: conformance.pass, eq: true, hard: true}")
    if checked:
        L += ["    - {metric: fault.pass, eq: true, hard: true}",
              "    - {metric: fault.alias_rate, le: 0.09, hard: true}",
              "    # alias_rate is the seam campaign's: an XOR mask on y_core before the checker, so for a",
              "    # conformant core it gates the checker declaration rather than this candidate. escape_max is",
              "    # the grouped campaign's worst group: the fraction of one-bit corruptions of a unit's own",
              "    # internal nets the checker misses, which does depend on the datapath. Measured 2026-09-17 on",
              "    # the baseline seeds: int_subword 0.0126, mixed_cvt 0.0020, posit 0.0199.",
              "    - {metric: fault.escape_max, le: 0.05, hard: true}"]
    if not t.get("min_delay"):
        L += ["    - {metric: synth_ppa.abc_delay_ps, le: vars.clock_ps}   # a violation is infeasible, kept with its measurements"]
    L += ["    - {metric: review.dissent, le: 1}           # modules whose text does not realize the family they declare;",
          "                                               # one is tolerated because a rewrite often lands on a structure the",
          "                                               # declaration no longer names, two says the declaration is fiction.",
          "                                               # A count, not a ratio: it means the same for two structures or twelve,",
          "                                               # and a review whose call failed reports no dissent rather than total dissent.",
          "", "  goal:", "    pareto:                              # the front over area and delay" +
          (" of the delay-driven mapping" if t.get("min_delay") else " at the clock"),
          "      - minimize: synth_ppa.area_um2", "      - minimize: synth_ppa.abc_delay_ps",
          "    score:", "      rule: ratio_to_seed", "      infeasible: slack"]
    return "\n".join(L)


def free_graph(t: dict) -> str:
    """The ALU graph without the library's machinery, for the runs that edit one plain program (the
    generic-evolution controls and the hand seed): the whole program is one region, and the review,
    the per-unit synthesis and its area screen (all three read a declaration) are gone. What stays
    is every gate of the unit itself: the declaration check of an empty block, lint, conformance,
    the checker and its fault campaign where the target has one, the gate-count screen and the
    synthesis, so a candidate here is judged as the chiALU run judges one."""
    L = alu_graph(t).split("\n")
    out, skip = [], None
    for line in L:
        if skip == "review":             # the comment lines under the review constraint
            if line.strip().startswith("#"):
                continue
            skip = None
        if line.startswith("      indexed_by: rtl_members") or line.startswith("      declaration_member: top"):
            continue
        if line.startswith("      evolve: [alu_core"):
            out.append('      evolve: ["*"]                     # the whole program, the library\'s text included')
            continue
        if line.startswith("      review:") or line.startswith("      synth_unit:"):
            skip = True
            continue
        if skip and (line.startswith("      yosys_stat:") or line.startswith("      synth_ppa:")):
            skip = None
        if skip:
            continue
        if line.startswith("          - synth_unit.area_um2 le"):
            out.append("          - yosys_stat.cells le 2.0 * seed.yosys_stat.cells")
            continue
        if line.startswith("    feedback: ["):
            line = line.replace("review.detail, ", "").replace("synth_unit.attribution, ", "")
        if line.startswith("    - {metric: review.dissent"):
            skip = "review"
            continue
        out.append(line)
    return "\n".join(out)


# the plain baseline program of each ALU target (targets/make_plain_seeds.py): the generic controls' seed,
# the library's modules kept as text and no declaration to edit
FREE_SEEDS = {"int_subword_alu": "seeds/int_subword_alu.baseline.sv",
              "fp_alu_cmp": "../seeds/fp_alu_cmp.baseline.sv",
              "fp_alu_cmp_hf": "../seeds/fp_alu_cmp_hf.baseline.sv",
              "vec_dot_acc_cmp_fp16": "../seeds/vec_dot_acc_cmp_fp16.baseline.sv",
              "vec_dot_acc_cmp_fp8": "../seeds/vec_dot_acc_cmp_fp8.baseline.sv",
              "vec_dot_acc_cmp": "../seeds/vec_dot_acc_cmp.baseline.sv"}
NO_REPLAN = "  search:\n    replan: false                        # no library: a VAR line re-renders nothing\n"


def plain_graph(top: str, checked: bool, effort: str = "medium", min_delay: bool = False) -> str:
    """The graph of a unit without structures (VecDotAcc, VecSFU): no review, no per-unit synthesis."""
    L = ["  artifacts:",
         "    core:", "      role: seed", "      kind: text", "      source: generated", "      language: systemverilog",
         f"      evolve: [{top}]                   # one region: the whole module"]
    if checked:
        L += ["    checker:", "      role: fixed", "      kind: text", "      source: generated", "      language: systemverilog"]
    L += ["    verify_bundle:", "      role: fixed", "      kind: text", "      source: generated", "      indexed_by: verify_files", "",
          "  evaluate:", "    nodes:",
          "      declaration:", "        node: adir.declaration",
          "      lint:", "        node: chialu.eda.lint", "        inputs:", "          rtl_text: candidate.core",
          "      conformance:", "        node: chialu.eda.conformance", "        inputs:",
          "          rtl_text: candidate.core", "          files: artifacts.verify_bundle"]
    if checked:
        L += ["      fault:", "        node: chialu.eda.fault", "        inputs:", "          rtl_text: candidate.core",
              "          files: artifacts.verify_bundle", "          checker_rtl: artifacts.checker"]
    L += ["      yosys_stat:", "        node: chialu.eda.yosys_stat", "        inputs:", "          rtl_text: candidate.core", f"          top: {top}",
          "      synth_ppa:", "        node: chialu.eda.synth_ppa", "        inputs:", "          rtl_text: candidate.core",
          f"          top: {top}", "          pdk: nangate45", "          clock_ps: vars.clock_ps", f"          repeats: {SYNTH_REPEATS}", f"          effort: {effort}",
          "          timeout_s: 1200",
          "          report: true                   # the critical path, paths and area by hierarchy as feedback, whatever CHIALU_SYNTH_REPORT says",
          "        when:", "          - conformance.pass",
          "          - yosys_stat.cells le 2.0 * seed.yosys_stat.cells",
          "    feedback: [conformance.detail, " + ("fault.detail, " if checked else "") + "synth_ppa.detail, synth_ppa.summary, synth_ppa.critical_path, synth_ppa.paths, synth_ppa.area_by_hierarchy]",
          "", "  constraints:",
          "    - {metric: declaration.ok, eq: true, hard: true}",
          "    - {metric: lint.ok, eq: true, hard: true}",
          "    - {metric: conformance.pass, eq: true, hard: true}"]
    if checked:
        L += ["    - {metric: fault.pass, eq: true, hard: true}",
              "    - {metric: fault.alias_rate, le: 0.09, hard: true}",
              "    # alias_rate is the seam campaign's: an XOR mask on y_core before the checker, so for a",
              "    # conformant core it gates the checker declaration rather than this candidate. escape_max is",
              "    # the grouped campaign's worst group: the fraction of one-bit corruptions of a unit's own",
              "    # internal nets the checker misses, which does depend on the datapath. Measured 2026-09-17 on",
              "    # the baseline seeds: int_subword 0.0126, mixed_cvt 0.0020, posit 0.0199.",
              "    - {metric: fault.escape_max, le: 0.05, hard: true}"]
    if not min_delay:
        L += ["    - {metric: synth_ppa.abc_delay_ps, le: vars.clock_ps}"]
    L += ["", "  goal:", "    pareto:" + ("                              # the front over area and delay of the delay-driven mapping" if min_delay else ""),
          "      - minimize: synth_ppa.area_um2", "      - minimize: synth_ppa.abc_delay_ps",
          "    score:", "      rule: ratio_to_seed", "      infeasible: slack"]
    return "\n".join(L)


def calibration_model_block() -> str:
    """One source for model/noise defaults, including stored calibrated variants."""
    return """        model: xgboost             # gnn selects the packaged whole-design graph model
        min_delay_gap_pct: 5       # smaller true differences are synthesis noise
        min_area_gap_pct: 2
        gnn:
          config: G5              # G1..G8, or full experiment names; G5 omits estimate globals
          hyperparameters: {}     # optional architecture/optimizer overrides
          ensemble_size: 3
          epochs: 250
          patience: 40
          device: cpu             # cuda for a configured GPU worker
          python: python          # interpreter with numpy and torch
          host: null              # optional SSH host, e.g. <host>
          workdir: null           # required remote scratch directory when host is set
          threads: 2
"""


def search_block(alu: bool, iterations: int = 20, seeds: str | None = None,
                 provider: str = PROVIDER, model: str = MODEL,
                 max_output_tokens: int = MAX_OUTPUT_TOKENS) -> str:
    # Provider/model knobs are opt-in; existing targets keep their exact text.
    if provider == "deepseek":
        max_output_tokens = min(max_output_tokens, 393216)
    # An ALU's seeds are the numeric stage's front alone (chialu.pipeline writes them into
    # `<run>/discovered.json`, which ADIR reads beside this list): the baseline program and the named
    # plans are what the front is measured against, not what the search starts from. The front's first
    # point is the fastest, which is the score reference and the reference of the area screens below.
    # `adir seeds` on a run directory without that file has nothing to start from and says so; the
    # pipeline's numeric stage writes it (`python3 -m chialu.pipeline <target> --run-dir <dir>`).
    seeds = seeds if seeds is not None else (
        "      generated: []                      # the numeric stage's front (chialu.pipeline), fastest point first"
        if alu else "      generated: [baseline]")
    sources = "[chialu_interface, chialu_families, chialu_structures, chialu_timing]" if alu else "[chialu_interface]"
    # the tactic names the round's target: the critical path (delay) or the logic off it (area), from the parent's
    # synthesis report; the operator says what kind of change, the target where
    # `target` offered exactly two tactics -- aim at the critical path, or at the logic off it
    # (chialu/priors.py:_target) -- and the UCB chose between them. The choice carried no
    # information the agent did not already have: the path, its longest segments and the area by
    # hierarchy all reach the call as feedback artifacts, which this file already lists.
    tactics = "[]" if alu else "[worst_constraint]"
    discover = ""
    return f"""  search:
    backend: adaevolve
    iterations: {iterations}
    parallel: 2
    parallel_nodes: 6
    eval_timeout_s: 3600
    diff_mode: true
    max_solution_bytes: 400000
    attempts: 1                          # one candidate per iteration for every backend (no re-prompt on a failed one)
    retries: 0
    database:
      use_migration: true
      migration_interval: 10
      use_paradigm_breakthrough: true
      diversity_strategy: metric
    seeds:
{seeds}
    context:
      programs: 1                        # the program reaches the agent as a file path in the call's directory
    prompts:
      variants:
        operator: [structural, local, free]
        ambition: [conservative, moderate, aggressive]   # how far one round's change reaches; sampled like the rest
        member_focus: [one]              # one region per round
        feedback_depth: [files]          # every feedback artifact as a file of the call directory, indexed in the prompt
        knowledge_depth: [path]          # the directory's layout in one line; the agent lists it and reads the cards it needs
      sample: ucb
      sources: {sources}
      log: true
    tactics:
      sources: {tactics}
      select: ucb
      window: 20
    models:
      solution:
        agent: opencode
        provider: {provider}               # opencode's provider id; the model id is the provider's own
        model: {model}
        effort: {EFFORT}               # opencode passes it as --variant, the provider's reasoning effort
        max_output_tokens: {max_output_tokens}   # the model's whole output limit (MAX_OUTPUT_TOKENS in make_targets.py)
        timeout_s: 1200                # one attempt, as the plain loop's call: a stalled call is recorded, not repeated
        retries: 1
      guide:
        agent: opencode
        provider: {provider}
        model: {model}
        effort: {EFFORT}
        max_output_tokens: {max_output_tokens}
        timeout_s: 1200                # one attempt, as the plain loop's call: a stalled call is recorded, not repeated
        retries: 1
{discover}    budget:
      wall_hours: 48                     # a stop only a hung run reaches: 20 iterations take a few hours
      node_runs: 2000
      llm_calls: 2000                    # likewise: the iterations bound the run, not the call count
    history:
      entries: 7                         # entries of a region's history the prompt summarizes
    extensions:                    # ADIR passes this through without reading it
      calibration:
{calibration_model_block()}        # A plan is a sharing scheme over a fixed structure set, and inside one plan the search ranks
        # micro-architectures rather than prices them: the Pareto front is five to eleven designs out
        # of thousands and can span as little as 4% in area. A calibration coefficient is a monotone
        # transform of the estimate, so it moves the level and leaves that ordering untouched -- the
        # numeric model's own rank correlation against synthesis was measured at 0.00 to 0.61 on
        # delay. So what a plan declares here is the ranking accuracy it requires, and how much
        # synthesis it will spend to certify it.
        exhaustive_below: 2000     # a plan with no more admissible designs than this is synthesized
                                   # whole: ranking by measurement beats ranking by any model, and
                                   # the heavily shared plans really are this small (8, for fmt-all)
        ranking:
          metric: delay            # the objective the target is stated against
          target_rho: 0.90         # required gap-filtered rank correlation on held-out designs
          margin: 0.03             # size the test set to certify the target when the truth is this
                                   # much above it. This, not the size of the space, is what drives
                                   # the number: the standard error of a correlation depends on the
                                   # sample alone, so 500 designs certify a space of 1e11 exactly as
                                   # well as one of 1e6. At 99% confidence a 0.90 target needs 160
                                   # designs against a true 0.93, and 1773 against a true 0.91.
          confidence: 0.99         # one-sided, for the lower bound the certificate is taken on
          rows_per_column: 10      # the initial TRAINING set is sized per one-hot family column
                                   # instead, because it is a learning curve and not an inference:
                                   # an int_subword plan has ~102 columns, so 100 designs is
                                   # underdetermined and ~1000 is where the measured curve flattens
          test_size: null          # null derives it from target_rho, margin and confidence
          initial_train: null      # null derives it from rows_per_column
          increment: null          # designs added after a failed round; null reuses the test size
          max_rounds: 6            # after this many failures the plan falls back to exhaustive
          max_error_ratio: 0.5     # the holdout RMSE over the spread (std) of all measured designs: the
                                   # model's error must stay well inside the differences between designs
          cv_floor_pct: 3.0        # a metric whose coefficient of variation over the measured points is
                                   # below this needs no ranking (the designs are about equal on it):
                                   # a low rho there is the synthesizer's jitter, not a model failure
    stop:
      plateau_iterations: 0              # off: every method runs its full iteration count (the plain loop has no such stop)

  archive:
    store: jsonl
    path: results_db.jsonl
    keep_transcripts: true
    report:
      front_only: false
"""


TARGETS = {
    "int_subword_alu": dict(
        kind="alu", title="An integer subword ALU",
        header="""# An integer subword ALU of chiALU on nangate45: int16, uint16 and 2 x int8
# modes on a 16-bit datapath with the add, multiply, compare, shift, logic
# and bit-count classes, the carry and overflow flags, a residue-15
# checker; the Pareto front of area and delay of the delay-driven mapping. Every
# integer family the library realizes is in play, so the seeds and the
# discovered plans synthesize by construction.""",
        modes=[{"count": 1, "format": "int16"}, {"count": 1, "format": "uint16"}, {"count": 2, "format": "int8"}],
        ops=["add", "sub", "adc", "neg", "abs", "add_sat", "mul", "mul_high", "min", "max", "cmp",
             "shl", "shr_arith", "rol", "and", "or", "xor", "not", "popcount", "clz", "ctz"],
        flags=["carry", "int_overflow"], clock_ps=3000, min_delay=True,
        narrow=[("core.subword.family", ["partitioned_carry_chain", "replicated_lanes"])],),
    "fp_alu": dict(
        kind="alu", title="A floating-point ALU",
        header="""# A floating-point ALU of chiALU on nangate45: fp16, bf16 and 2 x fp8e4m3
# modes on a 16-bit datapath with add, sub, mul, min, max and compare,
# two runtime rounding modes and the IEEE flags, an inverse-residue
# checker; the Pareto front of area and delay at a 20 ns target. The
# float structures (unpacker, significand adder and multiplier, rounder)
# are behavioral in the seed: the rewrite realizes their families.""",
        modes=[{"count": 1, "format": "fp16"}, {"count": 1, "format": "bf16"}, {"count": 2, "format": "fp8e4m3"}],
        ops=["fadd", "fsub", "fmul", "fmin", "fmax", "fcmp"], rounding=("runtime", ["RNE", "RTZ"]),
        flags=["invalid", "overflow", "underflow", "inexact"], checker="inverse_residue", clock_ps=20000,),
    "fp_fma_alu": dict(
        kind="alu", title="A fused multiply-add floating-point ALU",
        header="""# A floating-point ALU of chiALU on nangate45 whose float modes compute
# through the fp_fma slot's fused families: fp16 and bf16 share one
# classic_fma datapath across the formats, fp8e5m2 takes a three-path
# multipath_fma and fp8e4m3 a reduced_latency_fma; add, sub, mul,
# the four RISC-V fused multiply-add ops (fmadd, fmsub, fnmsub, fnmadd on
# a third operand c, rounded once under the fused contract), min, max and
# compare on a 16-bit datapath, the four IEEE rounding modes at run time,
# the IEEE flags, a duplication checker; the Pareto front of area and
# delay at a 20 ns target. The fused families are bound, and the slots
# under them (multiplier, align, lza, cpa, norm_shifter) and the rounder
# and unpacker are the search's. Every mode has one lane: the fault
# campaign's bench injects one site per net of the core, and a second
# lane of each fp8 mode is a second fused datapath, which took the bench
# past the 900 s build the flow allows it.""",
        modes=[{"count": 1, "format": "fp16"}, {"count": 1, "format": "bf16"}, {"count": 1, "format": "fp8e5m2"},
               {"count": 1, "format": "fp8e4m3"}],
        ops=["fadd", "fsub", "fmul", "fmadd", "fmsub", "fnmsub", "fnmadd", "fmin", "fmax", "fcmp"],
        rounding=("runtime", ["RNE", "RTZ", "RDN", "RUP"]), n_random=5000,
        flags=["invalid", "overflow", "underflow", "inexact"], checker="duplication", clock_ps=20000,
        fixed=[("core.fp_fma.m0.family", "classic_fma", "fp16: one fused datapath for fadd, fsub and fmul"),
               ("core.fp_fma.m0.sharing", "shared_across_formats", "shared with the bf16 mode: one datapath per lane at the wider geometry"),
               ("core.fp_fma.m1.family", "classic_fma", "bf16: the same fused datapath"),
               ("core.fp_fma.m1.sharing", "shared_across_formats", None),
               ("core.fp_fma.m2.family", "multipath_fma", "fp8e5m2: the close, far and product-shifted paths"),
               ("core.fp_fma.m2.path_count", 3, None),
               ("core.fp_fma.m3.family", "reduced_latency_fma", "fp8e4m3: the anticipator before the add"),
               ("core.fp_fma.m3.rounding_position", "fused_with_cpa_dual_sum", "the rounding fused into the window adder's compound sum")],),
    "fp_alu_cmp": dict(
        kind="alu", dir="eval", title="The fp16-class comparison ALU",
        header="""# The comparison target of docs/evaluation-plan.md (section 2): fp16, bf16
# and 2 x fp8e5m2 modes on a 16-bit datapath with add, sub, mul, min, max
# and compare, the four IEEE rounding modes at run time, min/max as
# minimumNumber/maximumNumber, the four flags, no checker; the Pareto
# front of area and delay of the delay-driven mapping. The comparison
# target of the FPnew rows (fp_alu_cmp_hf is HardFloat's), whose wrappers
# present the same interface.""",
        modes=[{"count": 1, "format": "fp16"}, {"count": 1, "format": "bf16"}, {"count": 2, "format": "fp8e5m2"}],
        ops=["fadd", "fsub", "fmul", "fmin", "fmax", "fcmp"], rounding=("runtime", ["RNE", "RTZ", "RDN", "RUP"]),
        flags=["invalid", "overflow", "underflow", "inexact"], check_en=False, minmax_nan="number",
        flag_scope="per_operation", clock_ps=8000, min_delay=True, search_x_form=True,),
    "fp_alu_cmp_hf": dict(
        kind="alu", dir="eval", title="The fp16-class comparison ALU in HardFloat's op set",
        header="""# fp_alu_cmp with the op set HardFloat realizes: fp16 and bf16 with add, sub,
# mul, min, max and compare, and 2 x fp8e5m2 with mul, min, max and compare
# (HardFloat's wrapper has no fp8 adder). The comparison target of the
# HardFloat row, as fp_alu_cmp is FPnew's: each reference is measured
# against a chiALU unit of its own function. The four IEEE rounding modes
# at run time, min/max as minimumNumber/maximumNumber, the four flags, no
# checker; every synthesis maps for its least delay.""",
        modes=[{"count": 1, "format": "fp16"}, {"count": 1, "format": "bf16"},
               {"count": 2, "format": "fp8e5m2", "ops": ["fmul", "fmin", "fmax", "fcmp"]}],
        ops=["fadd", "fsub", "fmul", "fmin", "fmax", "fcmp"], rounding=("runtime", ["RNE", "RTZ", "RDN", "RUP"]),
        flags=["invalid", "overflow", "underflow", "inexact"], check_en=False, minmax_nan="number",
        flag_scope="per_operation", clock_ps=8000, min_delay=True, search_x_form=True,),
    "mixed_cvt_alu": dict(
        kind="alu", title="A mixed integer, float and fixed-point ALU with conversions",
        header="""# A mixed ALU of chiALU on nangate45: fp16, int16, 2 x int8 and a
# fixed-point mode on a 16-bit datapath with add, mul and min in every
# mode and the conversions among the formats, a two-modulus residue
# checker; the Pareto front of area and delay at a 14 ns target. The
# converters and the sharing between the integer and the float
# arithmetic are what the search explores.""",
        modes=[{"count": 1, "format": "fp16"}, {"count": 1, "format": "int16"}, {"count": 2, "format": "int8"},
               {"count": 1, "format": "fxs1i7f8"}],
        ops=["add", "mul", "min", "fadd", "fmul", "cvt(int8)", "cvt(fp16)", "cvt(fxs1i7f8)"],
        checker="multi_residue", clock_ps=14000,
        narrow=[("core.subword.family", ["partitioned_carry_chain", "replicated_lanes"])],),
    "approx_alu": dict(
        kind="alu", title="An approximate integer ALU",
        header="""# An approximate integer ALU of chiALU on nangate45: int16 and 2 x int8
# modes with add, mul and mul_wide under a mean relative error budget
# (2% MRED, 60% error rate) and no checker; the Pareto front of area and
# delay at a 3 ns target. The approximate adder and multiplier families
# (truncation, speculative segments, inexact compressors, Mitchell's
# logarithm) are behavioral in the seed and open to the rewrite.""",
        modes=[{"count": 1, "format": "int16"}, {"count": 2, "format": "int8"}],
        ops=["add", "mul", "mul_wide"], accuracy="approximate", error_budget={"mred": 0.02, "error_rate": 0.6},
        check_en=False, clock_ps=3000,),
    "posit_alu": dict(
        kind="alu", title="A posit and integer ALU",
        header="""# A posit ALU of chiALU on nangate45: one posit16 (es = 1) mode beside
# 2 x int8, with integer add, mul and min and posit add, mul and min, a
# residue-15 checker; the Pareto front of area and delay at a 30 ns
# target. The posit decode and encode are realized inline in the top;
# the significand arithmetic can share the integer structures.""",
        modes=[{"count": 1, "format": "posit16_1"}, {"count": 2, "format": "int8"}],
        ops=["add", "mul", "min", "fadd", "fmul", "fmin"], clock_ps=30000,),
    "block_alu": dict(
        kind="alu", title="A block-format ALU",
        header="""# A block-format ALU of chiALU on nangate45: one MXFP4 block of eight
# elements (a shared e8m0 scale) beside eight fp8e4m3 lanes, elementwise
# add and mul in both, a residue-31 checker; the Pareto front of area
# and delay at a 16 ns target. The block scale handling and the sharing
# of the eight narrow lanes are what the search explores.""",
        modes=[{"count": 1, "format": "blksfps0e8m0Nefp4e2m1s8"}, {"count": 8, "format": "fp8e4m3"}],
        ops=["fadd", "fmul"], modulus=31, ftz_out=False, clock_ps=16000,),
    "vec_dot_acc": dict(
        kind="dot", title="A vector dot-product accumulator",
        header="""# A vector dot-product accumulator of chiALU on nangate45 (unit class 3:
# vecD = vecC + vecA . vecB): four fp16 products accumulated into fp32
# under one rounding (the fused contract), and four int8 products into
# int32 with saturation, a residue checker; the Pareto front of area and
# delay at a 40 ns target (the behavioral seed's fused reduction). The
# multiplier array, the adder tree and the
# accumulator's alignment are the structures a rewrite reshapes.""",
        modes=[{"elements": 4, "format_ab": "fp16", "format_c": "fp32", "format_d": "fp32"},
               {"elements": 4, "format_ab": "int8", "format_c": "int32", "format_d": "int32"}],
        clock_ps=40000,),
    "vec_dot_acc_cmp": dict(
        kind="dot", dir="eval", title="The dot-product comparison unit",
        header="""# The dot-product comparison target of docs/evaluation-plan.md (section 2):
# two fp16 products with an fp32 addend into fp32, and four fp8e5m2
# products with an fp32 addend into fp32, one rounding of the exact dot
# product (the fused contract), no checker; the reference designs are
# TransDot's DP mode and its no-DP SIMD FMA variant and a HardFloat
# MulAddRecFN cascade under the sequential contract. Table B is not
# frozen until TransDot's DP contract is confirmed by simulation.""",
        modes=[{"elements": 2, "format_ab": "fp16", "format_c": "fp32", "format_d": "fp32"},
               {"elements": 4, "format_ab": "fp8e5m2", "format_c": "fp32", "format_d": "fp32"}],
        check_en=False, clock_ps=40000, min_delay=True,),
    "vec_dot_acc_cmp_fp16": dict(
        kind="dot", dir="eval", title="The fp16 dot-product comparison unit",
        header="""# The fp16 row of Table B (docs/evaluation-plan.md, section 4): two fp16
# products with an fp32 addend into fp32 under one rounding of the exact
# dot product (the fused contract), no checker. TransDot's DP mode computes
# this function out of a 76-bit window (2 of 3,156 vectors differ); the
# no-DP SIMD FMA cascade and the HardFloat MulAddRecFN cascade compute it
# under the sequential contract and carry an ulp column. The slot defaults
# keep the exact 281-bit frame; vec_dot_acc_cmp_fp16_td.yaml binds
# TransDot's slot choices and _tdw adds its window.""",
        modes=[{"elements": 2, "format_ab": "fp16", "format_c": "fp32", "format_d": "fp32"}],
        mode_comment="one mode: the fp16 pair TransDot's DP mode computes fused",
        check_en=False, clock_ps=40000, min_delay=True,),
    "vec_dot_acc_cmp_fp8": dict(
        kind="dot", dir="eval", title="The fp8e5m2 dot-product comparison unit",
        header="""# The fp8e5m2 row of Table B (docs/evaluation-plan.md, section 4): four
# fp8e5m2 products with an fp32 addend into fp32 under one rounding of the
# exact dot product (the fused contract), no checker. TransDot's DP mode
# accumulates this function in a window that is not exact (1,113 of about
# 3,150 vectors differ), so the row carries the ulp column beside area and
# delay; the two FMA cascades compute it under the sequential contract.
# The slot defaults keep the exact frame, so this seed is exact and its
# ulp column is 0.""",
        modes=[{"elements": 4, "format_ab": "fp8e5m2", "format_c": "fp32", "format_d": "fp32"}],
        mode_comment="one mode: the four fp8e5m2 products TransDot's DP mode accumulates windowed",
        check_en=False, clock_ps=40000, min_delay=True,),
    "vec_sfu": dict(
        kind="sfu", title="A vector special-function unit",
        header="""# A vector special-function unit of chiALU on nangate45 (unit class 2:
# vecC = sfu(vecA)): four fp8e4m3 lanes with exp2, reciprocal, reciprocal
# square root and the sigmoid selected at run time, one ulp of error
# allowed; the Pareto front of area and delay at a 4 ns target. The seed
# is a bit-exact ROM per function and lane (the format has 256 patterns);
# the rewrite replaces the tables by shared arithmetic within the budget.
# (At fp16 the seed is a piecewise-linear evaluator that misses the one-ulp
# contract by design, so a wider target needs a soft accuracy constraint.)""",
        modes=[{"count": 4, "format": "fp8e4m3"}], functions=["exp2", "recip", "rsqrt", "sigmoid"],
        error_budget={"max_ulp": 1.0}, clock_ps=4000,),
}


NUMERIC_GRAPH = """  artifacts:
    verify_bundle:                       # the spec the estimate reads its structure manifest from
      role: fixed
      kind: text
      source: generated
      indexed_by: verify_files

  evaluate:
    nodes:
      declaration:
        node: adir.declaration
      estimate:                          # the synthesis database's area and delay of the declared structures
        node: chialu.eda.estimate
        inputs:
          files: artifacts.verify_bundle
          decl: decl.core
          pdk: nangate45
          effort: medium
          area_scale: 1.0                # the pipeline's calibrate stage writes the baseline's measured/estimated
          delay_scale: 1.0               # ratios into <name>.numeric.cal.yaml
          glue_json: ""                  # and the glue the top adds around the structures (the OR of a mode's
                                         # unit buses, the mode mux, the flags), which no row of a module alone has
          context_json: ""               # and the factor a (kind, family) costs in place against its row, from
                                         # the same profile: a unit overlapping its producer is cheaper than alone
    feedback: [estimate.detail]

  constraints:
    - {metric: declaration.ok, eq: true, hard: true}
    - {metric: estimate.ok, eq: true, hard: true}
    - {metric: estimate.coverage, ge: 0.8}          # a declaration the database mostly lacks is not ranked
@CLOCK_CONSTRAINT@
  goal:
    pareto:                              # the front over the estimated area and delay
      - minimize: estimate.area_um2
      - minimize: estimate.delay_ps
    score:
      rule: ratio_to_seed
      infeasible: slack
"""


def numeric_search(iterations: int = 400) -> str:
    return f"""  search:
    backend: nsga2                       # the database-driven stage (docs/demo-plan.md); smac by --backend
    iterations: {iterations}
    numeric:
      seed: 1
    seeds:
      generated: [baseline, packed_banks, per_position, dedicated_speed]   # the initial designs' declarations
    stop:
      plateau_iterations: 120

  archive:
    store: jsonl
    path: results_db.jsonl
    report:
      front_only: false
"""


def render_numeric(name: str, t: dict) -> tuple:
    """The numeric run file of an ALU target: the same variables, the
    estimate node in place of the RTL graph, no seed artifact (a numeric
    backend mutates declarations alone)."""
    up = "../.." if t.get("dir") else ".."
    vars_ = alu_variables(t)
    # These per-mode choices require a coordinated STRUCTURE plan. The
    # numeric stage draws independent mode variables and crosses them with
    # every sharing scheme; the full RTL target retains the explicit choices.
    if name in ("fp_alu_cmp", "fp_alu_cmp_hf"):
        vars_ += [("search_geometry", "fixed", "independent_modes", "sample components at the independent mode widths"),
                  ("core.rounder.*.family", "search", ["dedicated_per_op", "shared_per_lane"], "cross-format sharing is selected by the plan"),
                  ("core.unpacker.*.family", "search", ["per_unit_unpack", "shared_per_lane"], "cross-format sharing is selected by the plan"),
                  ("core.fp_multiplier.*.family", "search", ["sig_mul_then_round"], "an internally rounded multiplier cannot serve cross-format arithmetic sharing"),
                  ("core.fp_fma.*.sharing", "search", ["dedicated_per_mode"], "cross-format FMA sharing requires coordinated per-mode selections")]
    if name == "int_subword_alu":
        vars_ += [("core.logic.*.family", "search", ["lane_replicated_gates", "wide_gate_row"], "PG fusion requires a coordinated adder/logic partition")]
    yaml = (f"# The numeric stage of {name} (docs/demo-plan.md, stage 2): NSGA-II or SMAC over the\n"
            f"# declared families and choices, scored by the synthesis database's estimate; its front\n"
            f"# becomes seeds of the search run (chialu.front_seeds). Written by targets/make_targets.py.\n\n"
            "# ---- ADIR instance (read by `adir`) -----------------------------------\n"
            f"adir:\n  module: chialu.ALU\n  run_dir: run/{name}.numeric\n\n  variables:\n"
            + variables_block(vars_) + "\n\n"
            + NUMERIC_GRAPH.replace("@CLOCK_CONSTRAINT@", "" if t.get("min_delay") else "    - {metric: estimate.delay_ps, le: vars.clock_ps}\n") + "\n"
            f"  knowledge: {up}/chialu/knowledge\n  role:\n    file: {up}/targets/prompts/role.md   # who the model is: the system text's first section\n  task:\n    script: {up}/chialu/task.py          # the task statement, rendered from the bound unit\n\n" + numeric_search())
    return yaml


# the generic backends the host's SkyDiscover 0.1.0 runs: best_of_n and beam_search (its evox search type fails on a
# prompt file the package lacks, evox_search_sys_prompt.txt; openevolve and shinkaevolve need their own packages)
FREE_BACKENDS = ("best_of_n", "beam_search", "adaevolve")


def render_free(name: str, t: dict, backend: str) -> str:
    """The generic-code-evolution copy of a comparison target (docs/evaluation-plan.md,
    section 4): the same unit, evaluator, model and budget, the backend
    named, no prompt sources, no knowledge (an empty directory at
    `knowledge_depth: path`), the free operator alone, the baseline seed
    alone and no discover role. What stays is the seed program, the
    graph and the constraints."""
    up = "../.." if t.get("dir") else ".."
    kind = t["kind"]
    alu = kind == "alu"
    if alu:
        vars_, graph, module = alu_variables(t), free_graph(t), "chialu.ALU"
    elif kind == "dot":
        vars_, graph, module = dot_variables(t), plain_graph("dot_core", t.get("check_en", True), min_delay=bool(t.get("min_delay"))), "chialu.VecDotAcc"
    else:
        vars_, graph, module = sfu_variables(t), plain_graph("sfu_core", False), "chialu.VecSFU"
    # the control starts from the baseline program: it has no numeric stage, so it has no front. An ALU's is the
    # plain text of it (FREE_SEEDS): the library's modules as text, no declaration, no re-render
    search = search_block(alu, seeds=f"      files: [{FREE_SEEDS[name]}]   # the plain baseline program (FREE_SEEDS)\n"
                                     "      discovered: false                  # no numeric-front plan, whatever the run directory holds")
    if alu:
        search = search.replace("  search:\n", NO_REPLAN, 1)
    search = search.replace("backend: adaevolve", f"backend: {backend}")
    search = search.replace("        operator: [structural, local, free]\n"
                            "        ambition: [conservative, moderate, aggressive]   # how far one round's change reaches; sampled like the rest\n"
                            "        member_focus: [one]              # one region per round\n"
                            "        feedback_depth: [files]          # every feedback artifact as a file of the call directory, indexed in the prompt\n"
                            "        knowledge_depth: [path]          # the directory's layout in one line; the agent lists it and reads the cards it needs\n",
                            "        operator: [free]                 # the free rewrite alone\n"
                            "        ambition: [conservative, moderate, aggressive]\n"
                            "        member_focus: [none]\n"
                            "        feedback_depth: [files]\n"
                            "        knowledge_depth: [path]          # an empty knowledge directory\n")
    search = search.replace("      sources: [chialu_interface, chialu_families, chialu_structures, chialu_timing]",
                            "      sources: []                        # no domain sources")
    search = search.replace("      sources: [chialu_interface]",
                            "      sources: []                        # no domain sources")
    search = search.replace("      sources: [target, worst_constraint]", "      sources: []")
    search = search.replace("      sources: [target]", "      sources: []")
    yaml = (f"# The generic code evolution control of {name} (docs/evaluation-plan.md, section 4): the\n"
            f"# {backend} backend over the baseline program as plain text, the unit's own gates, the model and\n"
            f"# the budget, with no library (no declaration, no re-render, no review, no per-unit synthesis),\n"
            f"# no prompt sources, no knowledge and the free operator alone.\n"
            "# Written by targets/make_targets.py.\n\n"
            + CLUSTER.format(name=f"{name}-free-{backend}", creds=OPENCODE_CREDS, model=MODEL) + "\n"
            "# ---- ADIR instance (read by `adir`) -----------------------------------\n"
            f"adir:\n  module: {module}\n  run_dir: run/{name}.free_{backend}\n\n  variables:\n"
            + variables_block(vars_) + "\n\n" + graph + "\n\n"
            f"  knowledge: {up}/eval/empty_knowledge\n  role:\n    file: {up}/targets/prompts/role.md   # who the model is: the system text's first section\n  task:\n    script: {up}/chialu/task.py          # the task statement, rendered from the bound unit\n\n" + search)
    return _undeclared(yaml)


# the second experiment of docs/evaluation-plan.md (section 4): every method starts from a hand design, FPnew's
# PARALLEL point behind the target's interface (bit-exact against fp_alu_cmp; MERGED differs in 24 underflow
# flags and would start infeasible). The joined text is chialu-a3eval's, written by baselines/fpnew/build.py
# under runs/fpnew/, which this tree sits four levels under (3rdparty/chialu/targets/eval).
HAND_SEEDS = {
    "fp_alu_cmp": dict(file="../../../../runs/fpnew/fpnew_parallel_hand_seed.sv", label="FPnew PARALLEL"),
    "fp_alu_cmp_fpnew": dict(base="fp_alu_cmp", reference="fpnew", label="FPnew PARALLEL",
                             file="$A3EVAL/runs/fpnew/fpnew_parallel_hand_seed.sv"),
    "fp_alu_cmp_hardfloat": dict(base="fp_alu_cmp_hf", reference="hardfloat", label="HardFloat",
                                 file="$A3EVAL/runs/hardfloat/hardfloat_hand_seed.sv"),
    "fp_alu_cmp_transdot": dict(base="fp_alu_cmp", reference="transdot", label="TransDot MERGED",
                                file="$A3EVAL/runs/transdot/transdot_merged_hand_seed.sv",
                                max_solution_bytes=600000),
    # TransDot MERGED ran under `underflow_contract: fpnew_merged_16` until 2026-09-25 (24 flag-only mismatches,
    # bf16/fp8 fmul underflow). TransDot's UF tininess-index fix (upstream pncel/develop cd3d062) makes it
    # bit-exact under the standard contract, so the comparison is fp_alu_cmp's own (docs/codex/handseeds.md).
}
HAND_PROVIDER = "deepseek"
HAND_MODEL = "deepseek-flash"
HAND_MAX_OUTPUT_TOKENS = 393216


def write_hand_comparisons():
    """Keep the stored architecture pins of the old comparison files.

    HardFloat's stored architecture variant predates the restricted fp8 op
    set. Refresh that functional binding from fp_alu_cmp_hf and remove
    the now-absent fp8 adder's pins. New hand variants have no such pins.
    """
    import re
    for name, hand in HAND_SEEDS.items():
        if "base" not in hand:
            continue
        target = dict(TARGETS[hand["base"]])
        if hand.get("underflow_contract"):
            target["fixed"] = [("underflow_contract", hand["underflow_contract"],
                                "reference bug compatibility; docs/formats-and-options.md")]
        path = HERE / "eval" / f"{name}.yaml"
        if hand["reference"] == "transdot":
            target["header"] = ("# TransDot MERGED 16-bit no-DP comparison: FPnew's ALU interface under fp_alu_cmp's\n"
                                "# standard contract (IEEE after-rounding tininess). The former\n"
                                "# underflow_contract: fpnew_merged_16 workaround is retired: TransDot's UF tininess\n"
                                "# index fix makes MERGED bit-exact (docs/codex/handseeds.md, 2026-09-25).")
            path.write_text(render(name, target))
        elif hand["reference"] == "hardfloat":
            text = path.read_text()
            modes = variables_block(alu_variables(target)[:1]) + "\n"
            text = re.sub(r"    modes:.*?(?=    ops:)", modes, text, count=1, flags=re.S)
            text = re.sub(r"^    core\.fp_adder\.m2\.[^\n]*\n(?:      [^\n]*\n)*", "", text, flags=re.M)
            path.write_text(text)
        (HERE / "eval" / f"{name}.hand_adaevolve.yaml").write_text(render_hand(name, target, "adaevolve"))
HAND_VARIANTS = ("chialu",) + FREE_BACKENDS


def render_hand(name: str, t: dict, variant: str) -> str:
    """A comparison target started from its hand seed (HAND_SEEDS): the reference design, its
    wrapper and every source module it pulls in, as one text the rewrite may change
    anywhere. No structures stand behind it, so the graph is free_graph's over `alu_core`
    (lint, conformance, the gate-count screen, synthesis) rather than the ALU's per-member
    one, whose review and per-unit synthesis read a declaration the hand design lacks, and
    whose `rtl_members` family admits no single-file seed. `chialu` keeps the interface,
    the families and the timing among the domain sources and the knowledge cards under
    the free operator; a generic backend is render_free's control on the same seed."""
    up = "../.." if t.get("dir") else ".."
    hand = HAND_SEEDS[name]
    seed, label = hand["file"], hand["label"]
    model_options = (dict(provider=HAND_PROVIDER, model=HAND_MODEL, max_output_tokens=HAND_MAX_OUTPUT_TOKENS)
                     if "reference" in hand else {})
    vars_ = alu_variables(t)
    graph = free_graph(t)
    if "reference" in hand:
        graph = graph.replace("  constraints:\n", "  constraints:\n    - {metric: synth_ppa.ok, eq: true, hard: true}\n", 1)
    search = search_block(True, seeds=f"      files: [{seed}]   # {label} (HAND_SEEDS)\n"
                                      "      discovered: false                  # the hand design alone", **model_options)
    if hand.get("max_solution_bytes"):
        search = search.replace("max_solution_bytes: 400000", f"max_solution_bytes: {hand['max_solution_bytes']}")
    search = search.replace("  search:\n", NO_REPLAN, 1)
    if variant == "chialu":
        search = search.replace("        operator: [structural, local, free]\n",
                                "        operator: [free]                 # a hand design declares no structures to edit\n")
        search = search.replace("      sources: [chialu_interface, chialu_families, chialu_structures, chialu_timing]",
                                "      sources: [chialu_interface, chialu_families, chialu_timing]   # no structures to list")
        knowledge = f"{up}/chialu/knowledge"
        what = "chiALU's free operator with the knowledge cards and the timing source"
    else:
        search = search.replace("backend: adaevolve", f"backend: {variant}")
        search = search.replace("        operator: [structural, local, free]\n"
                                "        ambition: [conservative, moderate, aggressive]   # how far one round's change reaches; sampled like the rest\n"
                                "        member_focus: [one]              # one region per round\n"
                                "        feedback_depth: [files]          # every feedback artifact as a file of the call directory, indexed in the prompt\n"
                                "        knowledge_depth: [path]          # the directory's layout in one line; the agent lists it and reads the cards it needs\n",
                                "        operator: [free]                 # the free rewrite alone\n"
                                "        ambition: [conservative, moderate, aggressive]\n"
                                "        member_focus: [none]\n"
                                "        feedback_depth: [files]\n"
                                "        knowledge_depth: [path]          # an empty knowledge directory\n")
        search = search.replace("      sources: [chialu_interface, chialu_families, chialu_structures, chialu_timing]",
                                "      sources: []                        # no domain sources")
        knowledge = f"{up}/eval/empty_knowledge"
        what = f"the {variant} generic control"
    return _undeclared(f"# The hand-seed experiment of {name} (docs/evaluation-plan.md, section 4): {what},\n"
            f"# started from {label} rather than a generated seed. Written by targets/make_targets.py.\n\n"
            + CLUSTER.format(name=f"{name}-hand-{variant}", creds=OPENCODE_CREDS, model=model_options.get("model", MODEL)) + "\n"
            "# ---- ADIR instance (read by `adir`) -----------------------------------\n"
            f"adir:\n  module: chialu.ALU\n  run_dir: run/{name}.hand_{variant}\n\n  variables:\n"
            + variables_block(vars_) + "\n\n" + graph + "\n\n"
            f"  knowledge: {knowledge}\n  role:\n    file: {up}/targets/prompts/role.md   # who the model is: the system text's first section\n"
            f"  task:\n    script: {up}/chialu/task.py          # the task statement, rendered from the bound unit\n\n" + search)


def _undeclared(yaml: str) -> str:
    """A run over a program with no declaration behind it (the generic rows, the hand-seed runs). The
    bindings stay as the template needs them (it renders the verify bundle and requires the declaration
    node), but the prompt names none of it (ADIR `prompts.declarations: false`: no decision menu, no
    declaration grammar, no declared choice; `omit_vars`: the realization and the structure choices are
    not listed as options), and the checker the fault gate uses is the target's frozen one rather than one
    a `check.*` line could re-declare."""
    out = []
    for line in yaml.split("\n"):
        if line.strip() == "decl: decl.check":
            continue                                 # checker_gen without a declaration: the frozen rules
        out.append(line)
        if line == "    prompts:":
            out += ["      declarations: false              # nothing to declare: the prompt names no decision or block",
                    "      omit_vars: [realization, \"core.*\", behavior_rules]  # the library's options and menu are not the control's to see"]
    return "\n".join(out)


def _drop_review(yaml: str) -> str:
    """The review gone entirely: its node, its feedback and its constraint (removing the constraint alone
    would leave the review's calls and its verdicts in the model's feedback)."""
    out, skip = [], None
    for line in yaml.split("\n"):
        if skip == "constraint":
            if line.strip().startswith("#"):
                continue
            skip = None
        if skip == "node":
            if line.startswith("       ") or not line.strip():
                continue                         # the review node's own body (deeper than the 6-space node key)
            skip = None
        if line.startswith("      review:"):
            skip = "node"
            continue
        if line.startswith("    - {metric: review.dissent"):
            skip = "constraint"
            continue
        if line.startswith("    feedback: ["):
            line = line.replace("review.detail, ", "")
        out.append(line)
    return "\n".join(out)


# the ablations of docs/evaluation-plan.md (section 6): each removes one practice from the chiALU run file.
# key -> (practice number, what it removes, [(old, new)] text edits on the rendered run file); an edit whose
# `old` text a target lacks leaves that target without the ablation (the practice does not apply there).
ABLATION_SEEDS_BASELINE = ("      generated: [baseline]              # the baseline alone: no numeric front, no sharing schemes\n"
                           "      discovered: false                  # and no discovered.json plan, whatever the run directory holds")
ABLATIONS = {
    # the library off cannot render the numeric front's plans (a lane-partitioned adder, a unit shared across
    # formats are library constructions), so this ablation starts from the baseline with the replicated subword
    # layout, as chialu-a3eval's switch test did; its comparison is `nofront`, the baseline with the library on
    "behavioral": (1, "the library: every structure rendered as behavioral text, from the baseline",
                   [("  variables:\n", "  variables:\n    realization:                       # ablation: the library off, every structure behavioral\n      fixed: behavioral\n"),
                    ("    core.subword.family:\n      search: [partitioned_carry_chain, replicated_lanes]",
                     "    core.subword.family:               # ablation: the replicated layout, a partitioned carry chain being a library construction\n      fixed: replicated_lanes"),
                    ("      generated: []                      # the numeric stage's front (chialu.pipeline), fastest point first",
                     ABLATION_SEEDS_BASELINE)]),
    "cards": (2, "knowledge at depth cards", [("        knowledge_depth: [path]", "        knowledge_depth: [cards]")]),
    "index": (2, "knowledge at depth index", [("        knowledge_depth: [path]", "        knowledge_depth: [index]")]),
    "noknowledge": (2, "no knowledge: an empty directory and no family source",
                    [("  knowledge: ../../chialu/knowledge", "  knowledge: ../../eval/empty_knowledge"),
                     ("  knowledge: ../chialu/knowledge", "  knowledge: ../eval/empty_knowledge"),
                     ("chialu_interface, chialu_families, ", "chialu_interface, ")]),
    "notiming": (3, "the database's timing source", [(", chialu_timing]", "]")]),
    # behavioral's control on int_subword_alu: the baseline with the library on and the same replicated subword
    # layout, so the pair differs in the library alone
    "nofront_replicated": (1, "the baseline alone with the replicated subword layout (behavioral's control)",
                           [("    core.subword.family:\n      search: [partitioned_carry_chain, replicated_lanes]",
                             "    core.subword.family:               # ablation control: the layout behavioral has to take\n      fixed: replicated_lanes"),
                            ("      generated: []                      # the numeric stage's front (chialu.pipeline), fastest point first",
                             ABLATION_SEEDS_BASELINE)]),
    "nofront": (4, "the numeric front and the sharing schemes as seeds: the baseline alone",
                [("      generated: []                      # the numeric stage's front (chialu.pipeline), fastest point first",
                  ABLATION_SEEDS_BASELINE)]),
    # the free operator alone, and no re-render: a VAR line the model still writes then changes nothing, so the
    # declarations carry no structure (the seed keeps its block, which the free rewrite may leave as it is)
    "opfree": (5, "structured declarations: the free operator alone, no re-render",
               [("        operator: [structural, local, free]", "        operator: [free]"),
                ("  search:\n", "  search:\n    replan: false                        # ablation: a VAR line re-renders nothing\n")]),
    "noreplan": (5, "replan: a family change is not re-rendered", [("  search:\n", "  search:\n    replan: false                        # ablation: no re-render on a family change\n")]),
    "noreview": (6, "the review: its node, its feedback and its gate", [_drop_review]),
    "noscreens": (7, "the gate-level screens before synthesis",
                  [("          - yosys_stat.cells le 2.0 * seed.yosys_stat.cells\n", ""),
                   ("          - synth_unit.area_um2 le 1.2 * seed.synth_unit.area_um2\n", "")]),
    "opstructural": (8, "one operator: structural", [("        operator: [structural, local, free]", "        operator: [structural]")]),
    "oplocal": (8, "one operator: local", [("        operator: [structural, local, free]", "        operator: [local]")]),
    "nofocus": (8, "member focus: none", [("        member_focus: [one]", "        member_focus: [none]")]),
}
# practices 1-5 on the three comparison targets, 6-8 on fp_alu_cmp alone (section 6's run counts)
ABLATION_TARGETS = {"fp_alu_cmp": None, "int_subword_alu": 5, "vec_dot_acc_cmp_fp16": 5}


def render_ablation(name: str, t: dict, key: str) -> str | None:
    """The chiALU run file of `name` with ABLATIONS[key] applied, or None where
    none of its edits applies to the target (a source or a knob it does not have)."""
    practice, what, edits = ABLATIONS[key]
    yaml = render(name, t)
    applied = 0
    for edit in edits:
        if callable(edit):
            new_yaml = edit(yaml)
            applied += new_yaml != yaml
            yaml = new_yaml
            continue
        old, new = edit
        if old in yaml:
            yaml = yaml.replace(old, new)
            applied += 1
    if not applied:
        return None
    yaml = yaml.replace(f"  run_dir: run/{name}\n", f"  run_dir: run/{name}.abl_{key}\n", 1)
    yaml = yaml.replace(f"cluster_name: {name}\n", f"cluster_name: {name}-abl-{key}\n", 1)
    return (f"# Ablation {practice} of {name} (docs/evaluation-plan.md, section 6): {what}. Every other\n"
            f"# setting is the chiALU run file's. Written by targets/make_targets.py.\n" + yaml)


def render(name: str, t: dict) -> tuple:
    kind = t["kind"]
    up = "../.." if t.get("dir") else ".."           # the run file's directory relative to the repository
    if kind == "alu":
        vars_ = alu_variables(t)
        graph = alu_graph(t)
        module = "chialu.ALU"
    elif kind == "dot":
        vars_ = dot_variables(t)
        graph = plain_graph("dot_core", t.get("check_en", True), min_delay=bool(t.get("min_delay")))
        module = "chialu.VecDotAcc"
    else:
        vars_ = sfu_variables(t)
        graph = plain_graph("sfu_core", False)
        module = "chialu.VecSFU"
    yaml = (t["header"] + f"\n# Every model call is opencode on {MODEL} through {PROVIDER}; every prompt\n"
            "# and reply is logged under the run directory. Written by targets/make_targets.py.\n\n"
            + CLUSTER.format(name=name, creds=OPENCODE_CREDS, model=MODEL) + "\n"
            "# ---- ADIR instance (read by `adir`) -----------------------------------\n"
            f"adir:\n  module: {module}\n  run_dir: run/{name}\n\n  variables:\n"
            + variables_block(vars_) + "\n\n" + graph + "\n\n"
            f"  knowledge: {up}/chialu/knowledge\n  role:\n    file: {up}/targets/prompts/role.md   # who the model is: the system text's first section\n  task:\n    script: {up}/chialu/task.py          # the task statement, rendered from the bound unit\n\n" + search_block(kind == "alu"))
    return yaml


def refresh_synthesis_policy() -> None:
    """Refresh stored variants as well as primary templates without losing their pins.

    Calibrated, hand-bound and Table B variants carry choices outside TARGETS;
    their graphs still obey the same explicit synthesis policy as generated runs.
    """
    import re
    for path in HERE.rglob("*.yaml"):
        text = path.read_text()
        pattern = r"(node: chialu\.eda\.synth_(?:ppa|unit)\n( +)inputs:\n)((?:\2  [^\n]*\n)*)"

        def update(match):
            body = match[3]
            if re.search(r"^ +repeats:", body, re.M):
                return match[0]
            return match[1] + match[2] + f"  repeats: {SYNTH_REPEATS}\n" + body

        text = re.sub(pattern, update, text)
        # Stored variants carry pins outside TARGETS; insert only absent defaults.
        cal = r"(      calibration:\n)(.*?)(?=^      [^ ]|^    [^ ]|\Z)"
        def model_defaults(match):
            body = match[2]
            defaults = calibration_model_block()
            import yaml
            existing = yaml.safe_load(body) or {}
            blocks = []
            for line in defaults.splitlines(keepends=True):
                if line.startswith("        ") and not line.startswith("         "):
                    blocks.append(line)
                else:
                    blocks[-1] += line
            return match[1] + "".join(b for b in blocks if b.strip().split(":", 1)[0] not in existing) + body
        path.write_text(re.sub(cal, model_defaults, text, flags=re.M | re.S))


def main() -> int:
    for name, t in TARGETS.items():
        yaml = render(name, t)
        out = HERE / t["dir"] if t.get("dir") else HERE
        out.mkdir(exist_ok=True)
        (out / f"{name}.yaml").write_text(yaml)
        print(f"wrote {out.relative_to(HERE.parent)}/{name}.yaml")
        if t["kind"] == "alu" and name in NUMERIC_TARGETS:
            (out / f"{name}.numeric.yaml").write_text(render_numeric(name, t))
            print(f"wrote {out.relative_to(HERE.parent)}/{name}.numeric.yaml")
        if name in FREE_TARGETS:
            for backend in FREE_BACKENDS:
                (out / f"{name}.free_{backend}.yaml").write_text(render_free(name, t, backend))
            print(f"wrote {out.relative_to(HERE.parent)}/{name}.free_<backend>.yaml for {', '.join(FREE_BACKENDS)}")
        if name in ABLATION_TARGETS:
            wrote = []
            for key, (practice, _what, _edits) in ABLATIONS.items():
                limit = ABLATION_TARGETS[name]
                if limit is not None and practice > limit:
                    continue
                if key in ("behavioral", "noreplan", "nofront_replicated") and t["kind"] != "alu":
                    continue                     # realization, replan and the subword layout are chialu.ALU's; VecDotAcc has none
                if key == "nofront_replicated" and name != "int_subword_alu":
                    continue                     # only int_subword_alu has a subword layout to choose
                text = render_ablation(name, t, key)
                if text is not None:
                    (out / f"{name}.abl_{key}.yaml").write_text(text)
                    wrote.append(key)
            print(f"wrote {out.relative_to(HERE.parent)}/{name}.abl_<key>.yaml for {', '.join(wrote)}")
        if name in HAND_SEEDS:
            for variant in HAND_VARIANTS:
                (out / f"{name}.hand_{variant}.yaml").write_text(render_hand(name, t, variant))
            print(f"wrote {out.relative_to(HERE.parent)}/{name}.hand_<variant>.yaml for {', '.join(HAND_VARIANTS)}")
    write_hand_comparisons()
    refresh_synthesis_policy()
    return 0


# the targets whose numeric stage is written beside them (the demo's two)
NUMERIC_TARGETS = ("int_subword_alu", "fp_alu_cmp", "fp_alu_cmp_hf")

# the three comparison targets of docs/evaluation-plan.md section 6 (the ALU, the dot
# unit and the integer control) and the two one-mode seeds of Table B (section 4); each
# carries a generic-evolution copy per backend
FREE_TARGETS = ("int_subword_alu", "fp_alu_cmp", "fp_alu_cmp_hf", "vec_dot_acc_cmp", "vec_dot_acc_cmp_fp16", "vec_dot_acc_cmp_fp8")


if __name__ == "__main__":
    raise SystemExit(main())
