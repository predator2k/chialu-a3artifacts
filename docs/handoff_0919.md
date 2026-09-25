# 交接文档 2026-09-19：<host> 上的评测现状、本地模型链路与待办

本文档给接手 `chialu-a3eval` 评测的下一个会话（人或 AI）。它记录 2026-09-18 晚到 09-19 晚在 `<host>` 上做过的一切：环境怎么搭的、哪些实验已经出数、哪些被 Vertex 限流打断、本地模型链路怎么接的、还剩什么要跑、哪些事要用户拍板。原始运行手册是 `docs/handoff.md`（写给"新服务器从零开始"），本文档只讲它之外新增的事实与偏离；两份都读。逐步的原始记录在 `runs/notes.md`（不提交，gitignored），每条命令、每个数、每次事故都在里面，本文档是它的整理版。

## 0. 一句话现状

* 不花模型钱的部分全部完成：Table B 全部 12 行与手册记录逐位一致；Table A 的参考行（FPnew、HardFloat、TransDot，两种映射器各四个时钟目标）、第二层种子行、两个绑定点、`prune_best_delay` 参考点都已测出；综合数据库建到 17,891 行；目标套件 148 例全绿；TestFloat 台架 15 项全过。
* 花模型钱的部分只跑出两行（Gemini 3.1 Pro）：chiALU 完整行（run/fp_alu_cmp.full，20 迭代，5.59 USD）和 best_of_n（run/fp_alu_cmp.free_best_of_n，8.76 USD）。之后 Vertex 对 `gemini-3.1-pro-preview` 在这个项目上从 09-19 03:00 起对任何非平凡请求持续 429，到 20:06 仍未恢复。
* 用户转向本地模型：Mac Studio `<host>`（M3 Ultra，96 GB）上用 Ollama 0.34.2 跑 `qwen3.8:27b-mxfp8`，<host> 经 SSH 隧道调用。A/B 表明它在 `--effort low` 下一次 46 分钟的调用给出了可行、分数 1.059 的候选（所有模型中单候选最高）。所有运行文件已切到本地模型。
* 用户最后的指示（09-19 23:30 左右）："不用跑了，写 handoff"。本地模型上的 chiALU 完整行（run/fp_alu_cmp.local）在第 1 次调用后被停掉，可用 `--resume` 续跑。
* Vertex 累计花费约 32.7 USD（账号约 700 USD 额度，用户要求不超）。

## 1. 机器与环境（与 docs/handoff.md 的偏离）

### 1.1 <host>

AlmaLinux 8.10，128 线程（2 × EPYC 9374F），754 GB 内存，glibc 2.28，**共享机器**（其他用户跑 gem5/spike，另一位 CHIA 用户 s2chitni 的 Ray 集群占着 6379 端口）。

* **家目录有 5 GB 硬配额**，09-18 时已满；`/tmp` 所在根分区只剩 0.9 GB。因此 `docs/handoff.md` 里所有 `~` 下的东西都放在 `/data2/jwang710/chialu-home`（下称 `$CH`）：`miniconda3/envs/chia_env`、`tools/oss-cad-suite`（20260807）、`tools/sbt`、`tools/bin/sv2v`（发布二进制需要 glibc 2.34，改为源码编译 v0.0.13）、`.opencode/bin/opencode`（1.18.31）、`src/chia`（75300e5 加本地补丁，见 4.4）、`.cache/chialu`（Verilator 模型缓存，已 85 GB）、`tmp`、`ray_tmp`、`.config/{opencode,gcloud}`。
* 环境文件是 **`$CH/chialu-env.sh`**（不是 `~/chialu-env.sh`），每个 shell 先 `source` 它。它设置 PATH、gcc-toolset-11、`A3=/data2/jwang710/chialu-a3eval`、`CHIALU=$A3/3rdparty/chialu`、PYTHONPATH、`CHIALU_VERILATOR_JOBS=6`、所有 XDG/TMPDIR/RAY_TMPDIR/CLOUDSDK_CONFIG 重定向、`PYTHONNOUSERSITE=1`（`~/.local` 曾把 pip 装的包"借"走又被用户删掉，导致 mpmath 消失，见 4.1）、`THIS_MACHINE=<HEAD_IP>`。
* 检出在 `/data2/jwang710/chialu-a3eval`，子模块指针与手册一致（chialu `c1d0251`，adir `06f78b9`，cvfpu `7781163`，hardfloat `c1105e6`，transdot `7abd4c4`）。**两个工作树都有未提交改动**（见第 6 节）。
* 并行度（手册 1.3 规则算出）：J=6，pytest N=21（实际用 16），synthdb `--jobs 126`（实际用 100）、`--wide-jobs 94`，clock_sweep `--workers 64`，集群 `eda: 124`、`opencode_creds: 102`。**但机器共享**：09-18 21:00 同时跑数据库构建、两个时钟扫描、Table B 和自检把 1 分钟负载推到 11,870，自检因 Verilator 构建超时大面积失败。规则：数据库构建之外一次只跑一个重 CPU 批任务。
* Ray 集群：`chia up -y targets/eval/fp_alu_cmp.yaml`，端口 **6390**（模板与 7 个手写运行文件都改了），当前在线（eda 124，opencode_creds 102）。`chia down -y ...` 关。改过 CHIA 源码后要 `chia down`/`chia up` 让 worker 重新加载。

### 1.2 认证与 Vertex

* `CLOUDSDK_CONFIG=$CH/.config/gcloud`，账号 <email>，项目 `project-61ce0e88-8479-4f76-abc`（ADC 的 quota project，与老主机相同）。`gcloud auth application-default print-access-token` 正常。
* `gemini-3.1-pro-preview` 只在 `global` 端点存在（us-central1/us-east5/us-east1/europe-west1 都报模型不存在）。
* **限流状况**（关键）：09-18 22:48–09-19 03:05 单独运行时正常；03:00 起对任何 `--variant medium` 的请求或 2,000 token 以上的请求持续 429 `Resource exhausted`，10 token 的一字请求能过，15:39 有过一次 2k 探测通过但真实调用立刻又 429，到 20:06 的 24k 探测仍 429。gemini-2.5-pro 有容量但在 opencode 里不真正调用工具（两次调用都只叙述计划、不 edit）；gemini-3.8-flash 有容量但每次调用 2.85/1.53 USD 且首个候选语法错误。探测记录在 `runs/vertex_probe.log`。是否申请提额或换项目由用户决定。
* 费用：Pro 一次成功求解调用（朴素循环）1.07 USD，ADIR 求解调用 0.33–0.47 USD，失败调用也计费其已消耗轮次；首轮 429 不计费。

### 1.3 <host>（Mac Studio，本地模型）

* `ssh <email>` 从 <host> 免密可达。M3 Ultra，60 核 GPU，96 GB 统一内存，macOS 26.3，702 GB 空闲，没有 brew，系统 Python 3.9。
* 11434 端口上的 Ollama.app（0.24.0）属于另一位用户 <user>，跑了 77 天，**不要动**。我们的服务是独立二进制 `~/ollama-new/ollama`（0.34.2），以 orchard 身份在 **11435** 端口跑：
  ```
  cd ~/ollama-new && OLLAMA_HOST=127.0.0.1:11435 OLLAMA_CONTEXT_LENGTH=131072 OLLAMA_KEEP_ALIVE=-1 OLLAMA_NUM_PARALLEL=2 OLLAMA_FLASH_ATTENTION=1 nohup ./ollama serve > ~/ollama-serve.log 2>&1 &
  ```
  它不是 launch agent，sage 重启后要手动重起。检查：`OLLAMA_HOST=127.0.0.1:11435 ~/ollama-new/ollama ps`。
* 模型：`qwen3.8:27b-mxfp8`（MLX 8-bit，31 GB，加载后 49 GB 含 128K 上下文，100% GPU，keep-alive forever）。另有 `qwen3.6:35b-a3b-coding-mxfp8`（37 GB）。实测（18.9k token 提示）：27B prefill 294 tok/s、生成 27 tok/s；35B-A3B 1,875 / 74。
* <host> 侧：`$CH/tunnel_sage.sh` 维持 `ssh -N -L 127.0.0.1:11434:127.0.0.1:11435 orchard@sage`（日志 `$CH/tunnel_sage.log`）；`curl http://127.0.0.1:11434/api/version` 应回 0.34.2。隧道用 `setsid nohup $CH/tunnel_sage.sh > $CH/tunnel_sage.log 2>&1 < /dev/null &` 重起；杀它用 `pkill -f "^/bin/bash $CH/tunnel_sage.sh"; pkill -f "^ssh -N -o BatchMode=yes -o ServerAliveInterval=30"`（模式要锚定，否则 pkill 会杀到自己的 shell）。
* opencode provider：`$CH/.config/opencode/opencode.jsonc` 定义 `ollama`（`@ai-sdk/openai-compatible`，baseURL http://127.0.0.1:11434/v1），两个模型各带 none/low/medium/high 四个 variant（`reasoningEffort`）。调用形式 `--model ollama/qwen3.8:27b-mxfp8 --variant low`。CHIA 的每次调用配置文件与这个全局配置合并，不需要改 CHIA。
* 现在所有运行文件（`targets/*.yaml`、`targets/eval/*.yaml`）都指向 `provider: ollama`、`model: qwen3.8:27b-mxfp8`、`effort: low`、代理调用 `timeout_s: 7200`、审查 `timeout_s: 3600`（`targets/make_targets.py` 的 PROVIDER/MODEL/EFFORT/REVIEW_TIMEOUT_S 与代理块 timeout 改过，综合节点的 1200 未动）。要回到 Vertex：`git -C $CHIALU checkout targets/` 后重新做 `eda/opencode_creds/env/6390` 四处集群编辑（见 `runs/notes.md` 第 2 节）或把 make_targets.py 里四个常量改回 `google-vertex` / `gemini-3.1-pro-preview` / `medium` / 900 / 1200 再 `python3 targets/make_targets.py`，手写的 7 个文件要同步 sed。

## 2. 已完成的实验与数字

所有 PPA 都是 nangate45、medium effort。产物在 `$A3/runs/`（gitignored）。

### 2.1 参考设计一致性（手册 5.4）

| 设计 | 向量 | 失配 | 判定 |
| --- | --- | --- | --- |
| FPnew MERGED（runs/fpnew/classes.json） | 427,964 | 24，全是 `flags_only`（bf16 fmul 8、fp8e5m2 fmul 16，uf_after_round） | 与手册期望完全一致 |
| HardFloat（runs/hardfloat/classes.json） | 427,964 | 47,819，全在 fp8e5m2 fadd/fsub（value 42,894、nan_result 4,925） | 声明的 (5,3) 缺口 |
| TransDot ALU 级 no-DP（runs/transdot/classes.json） | 427,964 | 24，与 FPnew 同一组 flags_only | 手册第 9 节第 11 项待定 |
| TestFloat 台架（runs/testfloat） | 15 项 × 46,464 | 0 | 全 PASS |

`baselines/transdot/build.py` 加了两行 `pragma diagnostic ignore`（-Wrange-oob、-Windex-oob），否则它的文本在 `read_slang` 下综合失败；这是 a3eval 工作树里唯一的代码改动。

### 2.2 Table A 参考行与第二层（runs/sweeps/*.md）

&nf（chiALU 默认流程，一个设计一个点）；d_min = 2801 ps（HardFloat 紧目标）→ 目标 2800/3500/4200/7000 ps。面积 um2（延时 ps）：

| 设计 | 2800 | 3500 | 4200 | 7000 | 最小延时 |
| --- | --- | --- | --- | --- | --- |
| FPnew_MERGED | 4882.7 (3721) | 4882.7 (3721) | 4715.6 (4195) | 4705.0 (4519) | 3721 |
| FPnew_MERGED_bare | 5299.3 (3625) | 5299.3 (3625) | 5071.6 (4188) | 5065.4 (4472) | 3625 |
| FPnew_PARALLEL | 6307.4 (3713) | 6307.4 (3713) | 6215.1 (4246) | 6201.5 (4354) | 3713 |
| FPnew_PARALLEL_bare | 6525.0 (3774) | 6525.0 (3774) | 6400.5 (4185) | 6389.3 (4436) | 3774 |
| HardFloat | 5419.5 (2801) | 5342.1 (3358) | 5342.1 (3358) | 5342.1 (3358) | 2801 |
| TransDot_noDP | 4523.3 (4250) | 4523.3 (4250) | 4523.3 (4250) | 4398.0 (4850) | 4250 |
| chiALU baseline 种子 | 7283.6 (4319) | 7283.6 (4319) | 7283.6 (4319) | 6991.0 (5226) | 4319 |
| packed_banks / per_position | 与 baseline 相同（渲染成同一文本） | | | | |
| dedicated_speed | 8244.7 (4416) | 8244.7 (4416) | 8244.7 (4416) | 7946.0 (5002) | 4416 |
| fused_fma | 13077.6 (7554) ×4 | | | | 7554 |
| chialu_fpnew（绑定 FPnew 结构） | 6527.1 (5029) ×3 | | | 6375.0 (5906) | 5029 |
| chialu_hardfloat（绑定 HardFloat 结构） | 6133.2 (3340) | 6068.5 (3502) | 5983.4 (3988) | 5983.4 (3988) | 3340 |
| prune_best_delay（数据库最快族） | 7268.2 (3859) | 7268.2 (3859) | 7165.8 (4192) | 7146.6 (4637) | 3859 |

map -D 版本（目标 3100/3900/4700/7800，d_min = 3110）在 `refs.map.md`、`refs_bare.map.md`、`fp_alu_cmp.map.md`、`fp_alu_cmp_prune.map.md`，与手册所说一致：map 在浮点设计上延时更长。注意"包装开销"在 &nf 下是**负的**（FPnew MERGED 带译码 4882.7 < 裸 5299.3），因为包装把模式/操作拴死让综合剪得更多，表里应加脚注而不是报开销数。

### 2.3 Table B（runs/tableb，`sweeps/tableb.py --table --details`）

12 行全部与 `docs/handoff.md` 7.5 节的表逐位一致（transdot_dp fp16 6,045.9 / 6,621.1 / 5,270 FAIL 160；fp8 4,969.1 / 6,662.4 / 4,326 FAIL 1,621；no_dp fp16 8,052.4 / 9,802.5；fp8 11,764.9 / 19,360.0；hardfloat_dot fp16 7,797.0 / 8,821.6；fp8 11,009.2 / 16,153.3；chiALU 种子 fp16 15,771.9 / 9,639.6，fp8 13,284.6 / 7,942.2；_td fp16 21,925.8 / 12,047.4，fp8 25,735.0 / 11,740.1；_tdw fp16 11,484.0 / 10,834.0，fp8 12,400.9 / 10,704.9；chiALU 全部 PASS、ulp 0）。`tables/table_b.md` 无需改。

### 2.4 综合数据库（`$CHIALU/chialu/synth/nangate45/`，未提交）

`synthdb build --pdk nangate45 --seeds --jobs 100 --wide-jobs 94`（默认宽度 8,16,24,32,48,64 加种子宽度；第 9 节第 13 项的稠密网格未建）跑了 4 h 40 min，17,891 行（28 种类），在最后一个点上卡死后手动停止：`fp_divider` 的 `direct_polynomial` 族在 52 位有效数、kin=25 的种子点上要逐项算一张 2^25 项的多项式种子表（纯 Python Fraction，估计 8 小时），`--timeout` 管不到生成器。这是 chiALU c1d0251 的生成器问题。fp_alu_cmp 不用除法器。
* `sfu` 种类 2,973 行全部失败，原因是构建时 worker 里的 mpmath 还是 1.3.0（`TypeError: cannot create mpf from Fraction`）；VecSFU 目标需要时删掉 `chialu/synth/nangate45/sfu.jsonl` 后 `synthdb build --kinds sfu` 重建。
* 消费者验证通过：`synthdb status`（无 stale）、`query --kind adder --width 16`、`chialu.timing.render`（时序提示）、`chialu.prune --best delay`。**prune 的 bug**：它写出的 yaml 绑定了 15 个在所选族下不活跃的子引脚（`near_lz.split_string_select`、各种 `*.incrementer.topology`、`rounder.m2.exp_adder.log2_sparsity/fanout_cap`），`adir seeds` 逐个拒绝；已手工删除，可用版本在 `$CH/tmp/a3eval/fp_alu_cmp.best.yaml`（原件 `.orig`）。

### 2.5 方法行（模型调用）

| 运行 | 模型 | 迭代/调用 | 结果 | 费用 | 目录 |
| --- | --- | --- | --- | --- | --- |
| chiALU 探路 | 3.1-pro | 5 迭代，5 次求解调用，0 停滞 | 5 候选全可行，最好 6993.7 / 5030.6（1.039） | 1.65 | run/fp_alu_cmp |
| chiALU 完整行 | 3.1-pro | 20 迭代，12 次成功 / 37 次失败 | 11 记录 10 可行；前沿 (6923.2, 5543.8)、(6976.1, 5478.1)、(6990.5, 5335.8)、种子 (6991.0, 5225.6)、(7053.3, 5167.6)；最好分数 1.011 | 5.59 | run/fp_alu_cmp.full |
| best_of_n | 3.1-pro | 20 迭代，9 次成功 / 13 次失败 | 7 可行，无一超过种子（最好 7034.6 / 5252.2，0.995） | 8.76 | run/fp_alu_cmp.free_best_of_n |
| 朴素循环 | 3.1-pro | 冒烟 2 次 | 1 可行 7094.2 / 5365.1（0.974），1 失败 | 1.60 | runs/plain/smoke |
| 朴素循环 | 3.8-flash | 冒烟 2 次 | 1 语法错误，1 停滞（7062.0 / 5449.3 可行但被支配） | 4.38 | runs/plain/smoke_flash |
| 朴素循环 | 2.5-pro | 冒烟 2 次 | 两次都不写程序 | 0.14 | runs/plain/smoke_25pro |
| 朴素循环 | 本地 27B，effort medium | 1 次 | 停滞 3600 s，只读不改，一轮 32k token 被截断 | 0 | runs/plain/smoke_qwen38 |
| 朴素循环 | 本地 27B，effort low | 1 次 | **可行 7310.7 / 4934.5（1.059）**，46 min，22 轮 3 次 edit | 0 | runs/plain/ab_27b_low |
| 朴素循环 | 本地 35B-A3B，medium | 1 次 | 16 min，32 次 read，0 edit，无程序 | 0 | runs/plain/ab_35b_med |
| chiALU 完整行 | 本地 27B，low | 20 迭代，停在第 1 次调用后 | 2 记录（种子 + 1） | 0 | run/fp_alu_cmp.local（可 `--resume`） |

被中断的朴素循环尝试（全部 429，无有效候选）：`runs/plain/fp_alu_cmp.aborted_0142`、`.429_0306`、`.429_1244`。beam_search 三次启动都在首轮 429 上耗尽退避，已删目录。

失败原因分类（3.1-pro 运行）：Vertex 429（两个运行重叠时每分钟 token 撞限，单独跑时没有）；我的事故（00:29 自检孤儿进程占了 200 GB 内存触发 Ray 内存监视器杀任务）；AdaEvolve 的 "paradigm breakthrough" 指导调用 7 × 3 次全部瞬时 `opencode call failed (rc -1)`，不耗 token，是 CHIA/skydiscover 集成问题（`use_paradigm_breakthrough: true`）；2 个候选被评估器拒绝（`physical sharing is not implemented`、`explicit choices are inactive`）。

### 2.6 环境验证（手册第 5 节）

* 目标套件：`115 passed, 32 skipped, 1 xfailed`（148 例 = 37 个运行文件 × 4，含新增的 `fp_alu_cmp_plans.yaml`），0 失败，7 min 44 s。
* fptest：322/322，`--tight` 266/266。archdocs 干净（mpmath 1.4.1 后）。behavior_rules lint 0 unregistered 0 stale。
* 自检套件（`tests/test_selftests.py`）在这台机器上快集合 23 失败 / 54 通过，慢集合 2 失败 / 5 通过。绝大多数是 600 s 快限撞上冷缓存的 Verilator 构建（这台机器没有老主机那 26–32 GB 的模型缓存，单个模块直接跑 70 分钟还没完且写了 57 GB 临时文件）；确定性失败三个：`engine_selftest`（fp32 标志位黄金失配）、`rns_mod_add_selftest`（`lower_part_width=2 is outside 4..32 by 4` 引脚校验）、`seed_selection_selftest`（手册已记）。都不阻塞评测。日志 `runs/selftests3_fast.log`。

## 3. 怎么跑（现状下的命令）

```
source /data2/jwang710/chialu-home/chialu-env.sh      # 每个 shell
curl -s http://127.0.0.1:11434/api/version              # 隧道 + sage 上的 Ollama，应为 0.34.2
cd $CHIALU && chia status --chia-cluster targets/eval/fp_alu_cmp.yaml   # 集群
```

* ADIR 运行（本地模型，脱离终端）：`setsid nohup $CH/launch_adir.sh targets/eval/<文件>.yaml <运行目录名> <迭代数> > /dev/null 2>&1 < /dev/null &`，然后 `ps -u jwang710 -o pid=,args= | grep "[p]ython3.10.*adir run"` 拿 pid。续跑：`adir run <文件> --run-dir run/<名> --resume`。停：`adir stop <文件>`（迭代末）或 kill。
* 朴素循环：`$CH/launch_ab.sh <模型> <effort> <输出名> <超时秒>` 只跑 1 次调用；正式行用 `python3 harness/plain_loop.py targets/eval/fp_alu_cmp.yaml --agent opencode --provider ollama --model qwen3.8:27b-mxfp8 --effort low --calls 100 --timeout-s 7200 --out runs/plain/fp_alu_cmp`（在 `$A3` 下，setsid nohup）。
* **一次只跑一个调模型的运行**：Vertex 上两个运行并行会互相触发 429；本地模型上 GPU 只有一块（Ollama `NUM_PARALLEL=2` 能并发两路但吞吐分摊）。
* 记录 pid 时不要用 `pgrep -f`/`pkill -f` 匹配自己命令行里也有的字符串（本会话多次把自己的 shell 杀掉，exit 144）；用 `ps -o pid=,args= | grep "[p]ython3.10.*adir run"` 这种括号技巧，或锚定 `^`。
* 自检/目标套件之后清孤儿：`ps -u jwang710 -o pid=,ppid=,args= | awk '$2==1 && /-m chialu\.(verify|targets)/ {print $1}' | xargs -r kill`（pytest 超时只杀直接子进程，模块自己的进程池会变孤儿并吃掉几百 GB 内存）。
* 磁盘：`$CH/.cache/chialu/sim_build`（85 GB，越大后续越快，别删）；`$CH/tmp` 里 `pytest-of-*`、`chialu_fptest_*`、`yosys-abc-*`、`a3eval/st_*` 用完可删；`/data2` 09-19 22:00 剩 ~640 GB。

## 4. 事故与改动（接手者必须知道）

### 4.1 `~/.local` 事件
第一次 pip 安装时 60 多个包（numpy、scipy、mpmath 1.3.0 ……）被判定为"已满足"于 `~/.local/lib/python3.10`；用户为腾家目录配额删了 `~/.local`，这些包随之消失（自检大面积 FileNotFound、朴素循环 `No module named mpmath`）。修复：`PYTHONNOUSERSITE=1` 进环境文件、全部 pip 步骤重装、`mpmath==1.4.1` 固定。**综合数据库的 sfu 行在此之前建成，全部失败（见 2.4）。**

### 4.2 负载与内存
见 1.1。另：09-19 00:29 21 个自检孤儿进程（`families.selftest` 的进程池）合计 200 GB，MemAvailable 跌到 12 GB、用了 35 GB swap，Ray 内存监视器杀掉了 best_of_n 的 3 个迭代。

### 4.3 Vertex 429
见 1.2。首次重叠两个运行时的 429 是并发所致；03:00 之后是项目级持续限流，与并发无关。

### 4.4 CHIA 本地补丁（未提交，在 `$CH/src/chia/chia/models/opencode.py`，基于 75300e5）
`OpenCodeLLM.prompt` 原来对 `RateLimitError` 立即抛出（每次 429 浪费一次尝试并计费已消耗轮次）；补丁让同一次尝试退避 30/60/120/240/300/300 s 再试（环境变量 `CHIA_RATE_LIMIT_RETRIES`，默认 6 次）。`git -C $CH/src/chia diff` 可看。副作用：一次尝试可能因等待超过 `timeout_s`；本地模型不会 429，此补丁无影响。

### 4.5 chiALU / a3eval 代码层面的发现（报告给作者）
1. `synthdb build` 在 `fp_divider direct_polynomial` 52 位种子点上生成器跑 8 小时（2.4）。
2. `chialu.prune --best delay` 写出不活跃绑定（2.4）。
3. AdaEvolve paradigm-breakthrough 指导调用经 opencode 瞬时失败 rc -1（2.5）。
4. `baselines/transdot/build.py` 缺 slang pragma（已修）。
5. `baselines/hardfloat/build.sh <相对路径>` 会把输出写进子模块目录（它先 `cd` 到 hardfloat 再调 sbt），传绝对路径。
6. `sweeps/tableb.py` 如果 PATH 里 `/usr/bin` 在 chia_env 之前会用系统 python（第一次 Table B 就这样失败）；sbt 用 PATH 里 Synopsys 自带的 Java 8 即可，不要 `export PATH=/usr/bin:$PATH`。
7. 自检里 `engine_selftest`、`rns_mod_add_selftest` 在 c1d0251 上确定性失败（2.6）。

## 5. 待办与用户决定

### 5.1 还没跑的行（当前配置：本地 27B，effort low，一次一个）
按每次调用约 46 分钟估：20 迭代 ADIR 运行约 30 h，100 次朴素循环约 77 h。
1. chiALU 完整行 `run/fp_alu_cmp.local`（`--resume` 或重来）。
2. `fp_alu_cmp.free_best_of_n`、`.free_beam_search`、`.free_adaevolve`（本地模型；已有的 3.1-pro best_of_n 与本地行不是同一模型，表里注明或以本地版为准）。
3. 朴素循环 fp_alu_cmp（100 次或用户定的数）。
4. Table B fp16 行集的方法行：`vec_dot_acc_cmp_fp16.yaml` 的 chiALU 与朴素循环（点积程序更大，单次更慢）。
5. 表格：`eval/tables/make_table.py`（chiALU 仓库）算 Table A 方法行，再补四个时钟列、综合分钟、token 列，写 `$A3/tables/table_a.md`，末尾列归档路径与命令（同 `table_b.md` 式样）。参考行与第二层行的数已在 2.2。
6. 综合数据库：稠密网格（决定 13）与 sfu 重建视需要。

### 5.2 用户决定（手册第 9 节 13 项之外的新项）
* 规模：用户最后说"先跑着"随后改为"不用跑了"，天数没有定。11 天（原缩减计划）或 5–6 天（每行减半）。
* 模型一致性：已用 3.1-pro 跑出的两行是否用本地模型重跑。
* Vertex：是否去 Console 查/申请 `gemini-3.1-pro-preview` 的 token 配额，或换到账号下另一个项目 `project-bfe4cbb6-5f7c-4b1c-b17`。
* 手册第 9 节未决项 3、4、5、6、7、8、9、10、11、12、13 仍未决；本会话按"计划默认"执行：映射器两列并列（4）、HardFloat fp8 行上声明（5）、TransDot ALU 级点已测未入表（11）、asap7 不做（12）、默认网格先建（13）。第 10 项（FPnew RTL 为种子的 ADIR 行）未起草。

## 6. 文件清单

* `runs/notes.md`：逐步记录（最重要）。`runs/*.log`：各步日志。`runs/memlog.txt`：5 s 一次的 MemAvailable/负载采样。`runs/vertex_probe.log`。
* `runs/fpnew/`、`runs/hardfloat/`、`runs/transdot/`：包装文本、综合 json、classes.json。`runs/tableb/`：13 个 json 与 summary。`runs/sweeps/`：16 个 json/md。`runs/testfloat/`。`runs/plain/`：所有朴素循环目录。
* `$CHIALU/run/`：ADIR 运行目录（fp_alu_cmp、fp_alu_cmp.full、fp_alu_cmp.free_best_of_n、fp_alu_cmp.local 有内容；其余是 `adir check` 生成的空骨架）。`$CHIALU/run/synthdb/build.log`。
* `$CH/tmp/a3eval/`：`fpc/seeds`（五个共享方案种子）、`fpc_fpnew`、`fpc_hardfloat`、`fpc_best`（prune 参考种子）、`fp_alu_cmp.best.yaml`。这些是扫描的输入，别清。
* 未提交改动：a3eval 工作树 `baselines/transdot/build.py`（pragma）、`docs/handoff_0919.md`（本文）；chialu 工作树 `targets/make_targets.py` 与 35 个 yaml（集群四处 + 端口 6390 + 本地模型）、新文件 `targets/eval/fp_alu_cmp_plans.yaml`、`chialu/synth/seed_widths.json`（重新收集）、未跟踪 `chialu/synth/nangate45/`（数据库）；transdot 子模块 `src/transdot_fp4_fp8_fp16_fp32_fma.sv` 被 `tdot_comb.py` 打过补丁（`.orig` 在旁边）；berkeley-hardfloat 子模块内有 SoftFloat/TestFloat 的构建产物；CHIA 检出 `$CH/src/chia` 有 4.4 的补丁。提交与否由用户定；手册规定不改子模块指针。
* 记忆文件（Claude 会话用，`~/.claude/projects/-data2-jwang710-chialu-a3eval/memory/`）：<host> 布局、并发限制、预算、规模决定、sage 本地模型。
