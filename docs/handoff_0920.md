# 交接文档 2026-09-20：<host> + <host> 的环境重建、集群、数据库与模型选型

上一轮见 `docs/handoff_0919.md`（在 jwang710 的目录下，与本轮无共享文件）；
原始运行手册是 `docs/handoff.md`。本文件记录本轮所有不在代码里的事实。


## 0. 本轮与上一轮的根本差异

* 用户是 **<user>**，不是 jwang710；两份 handoff 里所有 `/data2/jwang710/...` 路径都不适用。
* 子模块 `3rdparty/chialu` 已从 `c1d0251`（accuracy-ctl）**推进到 `c9262c8`（main）**，提交 `8fc3167`。
  adir 指针不变（`06f78b9`）。两份 handoff 的版本锚点因此全部过期。
* 用户宣布**此前测得的全部数据作废**，数据库从零重建。

## 1. 机器

### <host>（head）
AlmaLinux 8.10，`nproc` 128，内存 754 GB，交换 192 GB，IP <HEAD_IP>。
gcc 8.5 + gcc-toolset-{9,11,14}（用 11）。glibc 2.28。Java 1.8.0_442。

**磁盘是本机最硬的约束**：`$HOME` 配额 5120 MB（会话开始时已用 2646 MB），
`/`（承载 `/tmp`）只剩约 5 GB，`/data2` 7 TB、剩 1 TB。

### <host>（第二个 EDA 节点）
AlmaLinux 8.10，`nproc` 88，内存 251 GB，IP <IP>。
gcc 8.5 + gcc-toolset-{12,14}（用 12）。Java 1.8.0_302。
`/mnt/ssd` 7 TB、剩约 236 GB。**与 <host> 不共享任何文件系统**（各自本地 home，无 /data2）。

### 并行度（按 handoff §1.3 的规则算出，实际取值见括号）
| 参数 | <host> | <host> |
| --- | --- | --- |
| `CHIALU_VERILATOR_JOBS` (J) | 6 | 6 |
| `synthdb --jobs` | 126（分片后每片 16–20） | 126（每片 14–16） |
| `--wide-jobs` | 94（分片后每片 4–6） | 每片 4–5 |
| 集群 `eda` | 124 | 84 |
| `opencode_creds` | 102 | 0（无凭据，不发模型调用） |

## 2. 目录与环境

```
<host>: $CH=$CHIALU_HOME   $A3=$A3EVAL   $CHIALU=$A3/3rdparty/chialu
<host>:  $CH=$REMOTE_HOME/chialu-home $A3=$REMOTE_HOME/chialu-a3eval     $CHIALU=$A3/3rdparty/chialu
```

每个 shell 先 `source $CH/chialu-env.sh`。该文件的核心做法是**把 HOME 整个搬到大盘**，
再叠加显式重定向（TMPDIR / XDG_* / RAY_TMPDIR / CLOUDSDK_CONFIG / PIP / CONDA / npm / bun /
sbt / coursier / ccache / CHIALU_SIM_BUILD_CACHE / CHIALU_SYNTH_CACHE / CHIALU_LIBERTY_CACHE）。
`.ssh` 软链回真实 home 以免 ssh 失效；`.gitconfig` 是副本（不是软链），这样
`git config --global url."git@github.com:".insteadOf https://github.com/` 只影响本项目。

### 磁盘泄漏（两处，都已堵住）
1. **opencode 的 npm 步骤**往 `$HOME/.local/lib` 和 `.npm` 写了 770 MB。npm 读绝对
   prefix，无视 HOME。更麻烦的是 opencode 是 Bun 写的，`os.homedir()` 读 passwd，
   **`HOME` 和 `XDG_DATA_HOME` 都不认**——清掉后跑一次 `opencode --version` 它又装回来了。
   最终把 `.local/lib`、`.local/share/opencode`、`.config/opencode` 三个目录软链到 /data2，
   并在环境文件里设 `npm_config_prefix` / `NPM_CONFIG_CACHE` / `BUN_INSTALL`。
   `~/.local/bin/opencode` 保留为指向 /data2 副本的软链，用户其他 session 照常可用。
2. 子代理在 `/tmp` 下解了 916 MB 的旧版源码树做 diff 对比，已删。

看门狗 `$CH/diskwatch.sh` 每 60 秒记一行到 `$CH/logs/watch_disk.log`，主目录读 XFS 配额
（不是 du——du 要遍历 4.8 万个文件）。会话结束时主目录 2583/5120 MB，**低于开始时的 2646**。

### 版本
yosys 0.68+36（含 slang 插件）、Verilator 5.051、gcloud 585.0.0、opencode 1.18.31、
sbt 1.10.7、sv2v v0.0.13（**源码编译**：发布二进制要 glibc 2.29，这两台是 2.28）、
CHIA 75300e5（本地补丁见 §4）、ray 2.54.0、mpmath 1.4.1、Python 3.10。
liberty 文件放在 `$CHIALU/pdk/lib/`，这样 `chialu/eda.py:108` 的 `~/pdk` 兜底永不触发。

## 3. 环境验证（全绿）
`selftest` 30/30、`formats_selftest` 35 组、`float_seed_selftest`、`exponent_rounder_selftest`、
`module_collector_selftest`（这条证明 Verilator + gcc-toolset-11 的 `-fcoroutines` 通了）、
`alu_fidelity_selftest`、`archdocs` rc=0、`behavior_rules lint` 0 unregistered 0 stale、
`fptest` 322/322、`fptest --tight` 266/266。
目标套件 `pytest tests/test_targets.py` **尚未跑**（等数据库建完，避免抢 CPU）。

## 4. CHIA 集群：两台注册，以及三个必须知道的坑

两台机器的防火墙**只放行 22 端口**（实测 <host> 连 <host> 的 6395/21000/30000/8265 全部
`No route to host`），所以 Ray 走 chia 的 SSH 隧道模式。head 是 <host>，GCS 端口 **6395**
（6379/6390 属于其他用户）。运行文件的 `auth.overrides` 段配置隧道。

### 4.1 无特权回环中继 `$CH/loopback_relay.py`
<host> 的 sshd 是默认 `GatewayPorts no`，所以 head 发起的 `ssh -R <addr>:PORT` **静默降级**
绑到 `127.0.0.1:PORT`，而不是 chia 要求的地址。两处因此落空：worker 拨 `<IP>:6395` 找
GCS；chia 的 iptables DNAT 把 `<head ip>:21000-21399` 和 29800/29801 重定向到 `<IP>`。
中继监听这些地址、转发到 `127.0.0.1`，共 414 个端口。由 `pre_tunnel_commands` 调
`$CH/start_relay.sh` 拉起。绑 127.x 别名不需要权限；改 sshd 需要 root 且要重启唯一的登录服务。
**实测**：修之前 <host> 上的任务调用 head 的 actor 报 `ActorUnavailableError`；修之后通过。
这条是 load-bearing 的——chia 的 cache actor 就在 head 上，`adir` 每次连接都要 `start_cache()`。

### 4.2 Ray worker 端口（两次踩坑）
* chia 只要有 worker 走隧道就**把 head 的 Ray worker 端口钉死**，默认只有 100 个
  （`chia/cluster/config.py:35-41`）。Ray 会保留空闲 worker，344 核集群上很快攒到 105 个
  `ray::` 进程，端口耗尽后**任何新 driver 都注册不上**：`adir run` 无声挂在
  `cache.start_cache()` 的 `ray.get` 上，自己一个字都不报，只有 raylet 日志里一行
  `No available ports`。`py-spy dump --pid <pid>` 能直接看到。
* 放宽到 5000 个端口更糟：chia 给**每个**端口建反向隧道，每个监听占 v4+v6 两个 socket，
  而 <host> 的 sshd 给会话的 `RLIMIT_NOFILE` 是 1024，**每次都在偏移 483 处失败**，
  `ExitOnForwardFailure=yes` 再把整条隧道杀掉。chia 默认的修法是 sudo 抬 sshd 的
  `LimitNOFILE`，需要 root 并重启 sshd。
* 最终取值：`head_worker_port_min/max = 21000/21399`（400 个，远低于 ~480 的上限，
  且低于临时端口范围 32768-60999），`ray_worker_port_min/max = 30000/30199`，
  并在 head 与 worker 环境里设 `RAY_num_workers_soft_limit=150` 让 Ray 不囤空闲 worker。

### 4.3 模型调用跑在 Ray worker 上，不在启动 run 的 shell 里
chia 把求解调用派给 Ray 任务 `OpenCodeLLM.prompt`，worker 的环境来自
`worker_env_commands`。把 OpenRouter key 只 export 在启动 shell 里 → 每次调用都失败。
而 chia 报出来的是 **`opencode call failed (rc -1)`**，`rc -1` 是它自己的哨兵值
（"所有 attempt 都失败"），**不是 opencode 的退出码**，真实错误只在
`$CH/ray_tmp/ray/session_latest/logs/worker-*.err` 里写着 `opencode run exited 1`。
这正是 `docs/handoff_0919.md` §2.5/§4.5-3 记的"瞬时 rc -1"，上一轮归因为 CHIA/skydiscover
集成问题，实际是凭据没传到 worker。
修法：`chialu-env.sh` 从 600 权限的 `$CH/.secrets/openrouter.env` 读取，worker 自然继承；
key 不进任何 repo 文件、不进集群配置。

### 4.4 CHIA 本地补丁（未提交，在 `$CH/src/chia`）
`chia/models/opencode.py`：上游对 `RateLimitError` 立即抛出，会吃掉一次 attempt
（ADIR 记账并计费），在 Vertex 项目级限流窗口里等于整个运行报废。补丁让 429 走**独立预算**
30/60/120/240/300/300 秒（认 `Retry-After` 取较大值），**不消耗** attempt；
`CHIA_RATE_LIMIT_RETRIES=0` 退回上游行为。原件在 `$CH/opencode.py.orig`。

### 4.5 <host> 尚未承担评测计算
它的 Verilator sim-build 缓存与 synth_unit 缓存都是 0 条。这是 Ray 的正常行为（驱动在
<host>，<host> 的 124 个 eda 槽放得下就不外派），不是故障——强制调度过去的任务能跑完并
回传结果。正式评测同时在飞 8 个运行时才会外溢。

## 5. 综合数据库重建

### 5.1 `synthdb build` 的并行是假的
`chialu/synthdb.py:1154` 用 `ThreadPoolExecutor`，只有 yosys 子进程调用释放 GIL，
**模块生成被 GIL 串死**。实测 `--jobs 100`：0.50 行/秒、采样时 yosys 进程数恒为 0、
128 核机器负载只有 7、估计全量 14.2 小时。

止血办法是按**进程**切分：`DB_DIR` 从包路径推导（`synthdb.py:74`），所以每个 git worktree
天然写自己的 `chialu/synth/nangate45/`，点数大的单个种类再用 `--families` 二次切分，
最后 `synthdb merge` 合并。切成 13 个分片后：**~23 行/秒、负载 132**。
对照：`adder`（2404 点）串行时跑了几分钟才到两个宽度，独立分片 **1870 行 / 62 秒**跑完；
`fp_adder` 2496 行 / 265 秒。
脚本：`$CH/build_shard.sh`（单片）、`$CH/merge_db.sh`（合并）。
**根治方案由子代理在 `$CH/fixdb` worktree 里做，未采纳前不要动 `$CHIALU`。**

### 5.2 两个必须记住的操作陷阱
* `synthdb merge` 会先 `unlink` 目标目录下所有 `.jsonl` 再重写。**绝不能在主检出正被某个
  build 追加写入时合并**，否则丢数据。
* `synthdb build` 把所有种类的点提交进同一个池子、按提交顺序完成。中途 kill 掉它，
  **每个种类都只建了前面的宽度**，而 `synthdb status` 只打印"有哪些宽度"、不打印
  "应该有哪些宽度"，所以一个被打断的构建在它眼里是完整的。第一次串行构建就这样留下了
  `adder` 只有 8/16 的残缺数据。写了 `$CH/db_coverage.py` 做逐 (种类, 宽度) 的覆盖度审计，
  **每次构建后都该跑一遍**。

### 5.3 有意的缺口
`fp_divider` 的 64 位（fp64）被 `CHIALU_FP_FORMATS` 排除：`direct_polynomial` 生成器在
52 位有效数上要逐项算 2^25 项的多项式种子表，纯 Python `Fraction`，估计 8 小时，
且 `--timeout` 够不到生成器内部（上一轮的构建就死在这里）。`fp_alu_cmp` 与 Table B 都不用
除法器，不影响当前评测；要补必须先让作者修生成器。

## 6. 运行文件的改动（`$CHIALU/targets/`，未提交）

`targets/make_targets.py` 的 `CLUSTER` 模板重写为两节点 + 隧道 + 端口范围 + 凭据；
`OPENCODE_CREDS` 16 → 102。重新生成后 29 个文件更新，另有 6 个手写文件
（`fp_alu_cmp_{fpnew,hardfloat}`、`vec_dot_acc_cmp_fp{8,16}_{td,tdw}`）用脚本同步了集群段。
`PROVIDER` / `MODEL` / `EFFORT` **未动**（用户尚未决定正式评测用哪个模型）。

新增两个未跟踪文件：
* `targets/eval/fp_alu_cmp_plans.yaml`：`fp_alu_cmp.yaml` 的副本，`seeds.generated` 显式列出
  五个共享方案。main 把八个 ALU 运行文件的 `seeds.generated` 改成了 `[]`（种子改由
  `chialu.pipeline` 数值阶段产生，需要数据库），在数据库建好之前 `adir seeds` 会报
  `search.seeds: no seeds listed`。这个文件是不依赖数据库的取种子路径。
* `targets/eval/fp_alu_simple.yaml`：给模型对比用的小 ALU——fp16 单模式、fadd/fsub/fmul、
  RNE、`n_random 200`、`clock_ps 8000`、`parallel: 1`、10 轮、baseline 种子、
  去掉会读数据库的 `chialu_timing` 提示源。**种子 25 秒出数：2912.966 um² / 5175.72 ps**。

### 6.1 `adir seeds` 与 `clock_sweep` 对同一方案会给出不同结果
`fused_fma` 在 `adir seeds` 下是 infeasible、`goal_values` 为 `[None, None]`，
原因是被门级筛选挡在综合之前：`skipped: {'synth_ppa': 'when synth_unit.area_um2 le 1.2 *
seed.synth_unit.area_um2 is False'}`，它的 `synth_unit.area_um2` 是 15035.9、种子是 3940.5。
它的 lint、一致性（逐位精确）、审查全部通过——设计没错，只是大。
手册 §7.3.4 里 Table A 第二层那些数出自 `sweeps/clock_sweep.py`（无条件综合每个种子），
**不是** `adir seeds`。交接文档必须写明哪一列出自哪条路径。

## 7. 待办

1. 数据库：等分片跑完 → `$CH/merge_db.sh` → `$CH/db_coverage.py` 复查 → `synthdb status`
   确认无 stale generators → 消费者验证（`query`、`chialu.timing.render`、`chialu.prune`）。
2. 目标套件 `pytest tests/test_targets.py`（数据库建完后跑；注意八个 ALU 目标在
   `seeds.generated: []` 下的 RTL 级用例会 ERROR，除非先跑 `chialu.pipeline`）。
3. 模型选型：五模型 × 10 轮的对比由子代理在跑，结果决定 `make_targets.py` 的
   `PROVIDER`/`MODEL`/`EFFORT`。
4. 用户未决：正式评测的模型与预算；`docs/handoff.md` §9 的 13 项仍未决。
5. 报给作者的问题：`opencode call failed (rc -1)` 掩盖真实错误；chia 隧道模式下 head
   worker 端口默认过窄且落在临时端口范围内；`synthdb` 的线程池并行；`synthdb status`
   不报缺失宽度；`chialu/timing.py` 取行不区分浮点格式（子代理读码发现，未复核）。


## 8. 推上去的分支

| 仓库 | 分支 | 内容 |
| --- | --- | --- |
| `predator2k/chiALU` | `<host>-eval-2026-09-20` | `4859acd` 评审门修复（可单独采纳）；`cf02c77` 双机集群配置与两个新运行文件 |
| `predator2k/chialu-a3eval` | `<host>-eval-2026-09-20` | `8fc3167` 子模块 accuracy-ctl→main；`934516d` 指针移到上面那个分支并同步 `.gitmodules` |
| `predator2k/chia`（**fork 自 ucb-bar/chia**） | `rate-limit-backoff` | 429 退避 + 429 识别 |

**CHIA 不是任何仓库的子模块**，它是 pip 可编辑安装自 `$CH/src/chia`。所以"指向 fork"落实在两个
引导脚本里（`$CH/install_python.sh`、`$CH/<host>-bootstrap.sh`）：clone 地址改成 fork，
并 checkout `rate-limit-backoff`。`docs/handoff.md` 第 151、162 行仍写着 ucb-bar 的地址，
按下面第 9 节一并更正。

未提交的：综合数据库 `chialu/synth/nangate45/`（32 MB，未跟踪）、`pdk/lib/*.lib`（已在 .gitignore）。

## 9. 模型选型结论

简单 ALU（`targets/eval/fp_alu_simple.yaml`），10 轮迭代，effort 全部 high，种子
2912.966 um² / 5175.72 ps。

| | deepseek-v4.1-flash | glm-5.3 | glm-5.3-flash | gemini-3.1-pro | gemini-3.8-flash |
| --- | --- | --- | --- | --- | --- |
| 可行候选 | 8 | 5 | 4 | 9 | 2（修复前） |
| 调用失败 | 0 | 1 | 0 | 0 | 4 |
| 最好面积 | **2828.6** | 2885.8 | 2893.5 | 2838.0 | 2840.6 |
| 最好延时 | **4874.0** | 5045.9 | 5175.7（=种子） | 4915.6 | 5152.6 |
| 总花费 | **$0.45** | $2.51 | $0.19 | $7.36 | $3.31 |
| 1800 次迭代外推 | **$81** | $501 | $42（无改进） | $1,324 | $1,987 |

**推荐 deepseek-v4.1-flash**：花费是 gemini-3.1-pro 的 1/16，前沿更宽、两轴都更好，且它是唯一
在负载 65 的机器上跑出这个成绩的。glm-5.3-flash 的 $42 是假便宜——10 轮之后最优解仍是种子本身。

gemini-3.8-flash 产出了**全场最好的单个设计**（2754.164 / 4602.68，面积 −5.45%、延时 −11.07%，
支配所有其他候选），但被评审崩溃判成不可行。修好后重测中。

**每次迭代实测 1.3–2.0 次模型调用**，不是手册假设的 10 次；1800 次迭代对应约 2,400–3,600 次调用。
adir 自己的成本计数器只统计 solution 调用、不含 review，**低估 5–34%**，预算要按 opencode 的
会话库实测值算。

## 10. 必须知道的其余坑（本轮实测）

* **模型调用与重 CPU 批任务不能并发。** 负载 57 时 GLM 每次调用都撞 1200 s 超时、50 分钟只出 2 个
  候选；负载 17.6 时同样的模型 2439 s 跑完 10 条记录。opencode 要 CPU 解析和落盘流式响应，被饿死就
  表现为调用超时，而 chia 报的 `rc -1` 里完全看不出原因。手册 §1.1 只写了"数据库构建之外一次只跑
  一个重 CPU 批任务"，要补上这一条。
* **`pgrep yosys` 恒为 0 是计数陷阱**：oss-cad-suite 的 `yosys` 是 bash wrapper，最后 exec
  `ld-linux-x86-64.so.2 ... libexec/yosys`，进程 comm 不叫 yosys。要数用
  `ps -u <user> -o args= | grep "[l]ibexec/yosys"`。
* **`search.parallel` 不约束并发模型调用**，只约束并发评估（`skydiscover.py:138`
  `"parallel_evaluations"`）。想靠它压 429 无效。
* **`report.py:59` 在 run 结束时整体覆写 `summary.json`**，抹掉 `llm_calls`/token/成本。要拿这些
  数必须在运行中轮询快照。
* **归档会整段丢迭代**（glm-5.3 缺第 5 轮，glm-5.3-flash 缺第 2、7 轮），`summary.json` 无任何字段
  提示；另有候选 `parent_id` 为 `None`，谱系断掉。
* **`review.agree` 在"无可评审对象"时返回 1.0 免检**——把改动放进 `top` 就能完全绕开架构评审，
  36 次评审里命中 8 次。本轮加了 `unreviewed` 标记使其可测，但洞仍在。
* 观测工具：`$CH/watch_opencode.sh`（区分 opencode 挂死与正常工作，四个信号 cpu/net/wrote/sess）、
  `$CH/db_coverage.py`（逐 (种类,宽度) 覆盖度审计）、`$CH/diskwatch.sh`（配额看门狗）。

## 11. 报给作者的问题清单

1. `chialu/review.py` 评审调用失败被记成 `agree=0.0`，等于判候选不合格（本轮已修，见分支）。
2. `review.agree` 在无可评审对象时返回 1.0，与上一条方向相反的漏洞（未修）。
3. `chia/models/opencode.py` 只按 `statusCode == 429` 识别限流，漏掉 Vertex 与 OpenRouter 的
   文字形式；且 `rc -1` 是"所有 attempt 失败"的哨兵值，掩盖真实错误（本轮已修，见 fork）。
4. `chialu/synthdb.py` 的 `ThreadPoolExecutor` 使生成阶段被 GIL 串行化（子代理已给出多进程补丁，
   在 `$CH/fixdb`，未采纳）。
5. `synthdb status` 不报缺失宽度，被打断的构建在它眼里是完整的。
6. `chialu/targets/rtl/families/div.py` 与 `sfu.py` 的 `Fraction` 表生成器在若干 (族, 宽度) 上
   耗时爆炸，`--timeout` 够不到生成器内部。
7. `adir/report.py:59` 覆写 `summary.json` 丢失计数器；`adir/composer.py:1441` 秒级时间戳导致
   同秒两次 compose 互相覆盖 prompt 文件。
8. `chialu/timing.py` 取行只按 kind+width、不区分浮点 format（子代理读码发现，未复核）。

## 12. plan 层与微架构层的边界（2026-09-21 调查，未修改代码）

正式探索要先穷举 plan、再在每个 plan 内搜索微架构，所以边界划在哪里决定了两层各自的大小。
实测（`fp_alu_cmp`，plan `fmt-none`，266 个活跃选择）：

* **不能用"是否影响 slot 存在性"划线。** 探测 120 次嵌套 family 翻转，**75 次（62%）改变了
  它下面有哪些选择存在**——`fp_adder.m0.lz.family=lzc_after_add` 改动 13 个，
  `align.tzc.lzd.family=prefix_lzc` 改动 11 个。条件性是空间的普遍性质（一个 plan 的
  space.json 里 25,109 个超参数有 25,076 个是条件变量），按这条线划，几乎每个 family 都得
  进 plan 层，分层失去意义。
* **可用的判据是"是否改变 `synth_unit.attribution` 的键集合"**，即估计器求和的那组物理结构。
  plan 改变模型的**形式**（Σ 有几项、关键路径穿过谁），微架构只改变各项的**值**。
  数据库的行记录的正是结构边界上的面积延时，内部嵌套什么并不影响组合。

### 现在 plan 的增殖来源不完整

plan 应当枚举的是 **op → 物理结构的分配**，例如"用一个 fma 单元承担 fma/fadd/fmul"或
"用 fp_adder 承担 fcmp/fadd/fsub"。但现在：

* `sharing_schemes` 只枚举**同类结构之间的数据通路共享**（add/mul/log 分组 × pair × fmt × intfp）。
* op → 结构的分配是**硬编码的纯函数**：`chialu/targets/rtl/alu_float.py:571` 的
  `register_op` 是结构集合的唯一入口，它只读模式的格式族和 op 名字——
  `if op in ("fadd","fsub","fmul"): structure(kind="fp_fma")`、
  `if op in A.FUSED_OPS: structure(kind="fp_adder"); structure(kind="fp_multiplier")`——
  **函数体里没有任何 binding 或 family 选择**，所以结构集合是 (模式格式, op 集合) 的函数，
  没有可搜索的输入。（`alu_float.py:449` 的 `if ops & {"fcmp","fmin","fmax"}` 是渲染时
  要不要例化比较器模块，不是结构注册。）
* 这同时证明了上面那条判据不必实测：微架构决策根本不进入 `register_op`，因而不可能改变
  attribution 的键集合；代码层面 `register_op`（建结构集合）、`partition_of_plan`/`plan_vars`
  （分组）、`families_of`（填内部实现）三者是物理隔离的。
* 唯一的例外是 fma 融合（`partition.py:fuse_multiply_add`），它通过 partition 表达，所以要求
  adder/multiplier/fma 分在同一组。

因此"让 fp_adder 顺带承担 fcmp/fmin/fmax"（对齐段已经算出指数差和大小关系，可省掉整个比较器）
这类经典做法，搜索**碰不到**。要补需要两处改动：生成器里加一个 op 宿主决策，以及
`sharing_schemes` 增加一条对应的轴。

**本轮不修改**，因为它会改变所有方法行的搜索空间、使已测数据作废；而且已有的 fma 融合这条路
本身还没跑通——`fused_fma` 方案被门级筛选挡在综合之前（`synth_unit.area_um2 ≤ 1.2×seed`，
实测 14945.7 / 10864.2 = 1.375）。**那个门是按"结构面积之和"比的，而融合恰恰让单个结构变大、
总数变少，门的形式对融合天然不利**，应先查这个。
