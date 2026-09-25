# 交接文档：在新服务器上准备环境、构建综合数据库并运行全部评测实验

本文档给在 `<host>` 或 `<host>` 上运行的 Claude Code 会话一份可以直接照做的操作说明：量机器、取仓库、装环境、完成认证、验证环境、构建综合数据库、运行 `3rdparty/chialu/docs/evaluation-plan.md` 规定的每一个实验、记录结果、并把需要用户拍板的事项列出来。本文档不引用其他文档；凡来自仓库文件的事实都已在此复述。

## 0. 版本锚点与约定

本文档依据下列提交写成。

| 仓库 | 分支 | 提交 | 说明 |
| --- | --- | --- | --- |
| `predator2k/chialu-a3eval` | `main` | `0f42523` 之后加入本文档的合并提交 | 本仓库；加入本文档的提交把子模块 `3rdparty/chialu` 的指针更新到 `c1d0251` |
| `predator2k/chiALU`（子模块 `3rdparty/chialu`） | `accuracy-ctl` | `c1d0251` | a3eval `main` 记录的子模块指针；第 2.3 节核对它 |
| `predator2k/adir`（chiALU 的子模块 `third_party/adir`） | `main` | `06f78b9` | chiALU `c1d0251` 记录的指针 |

约定如下。

* `$A3` 指 chialu-a3eval 的检出目录，`$CHIALU` 指 `$A3/3rdparty/chialu`。所有命令在 bash 中运行。
* 会话把每一步的命令、关键输出和选定的数值记到 `$A3/runs/notes.md`。`runs/` 在 a3eval 的 `.gitignore` 中（`/runs/`、`/work/`、`*.log`），不会被提交。
* 会话在四处停下并询问用户：第 4 节的认证；第 3.4 节找不到 gcc 10 或更新版本时；第 5.3 节目标套件不是绿色时；第 9 节的每一项决定。
* 会话不读取、不打印任何凭据文件，不把凭据复制进任何仓库。
* 会话不使用不带参数的 `git stash`。

## 1. 先量机器

### 1.1 记录命令

会话在做任何事之前运行下列命令，并把输出原样写到 `runs/notes.md` 的顶部。

```
hostname; cat /etc/os-release | head -4
nproc
free -g
df -h ~ /tmp
lscpu | head -25
gcc --version | head -1; ls /opt/rh/ 2>/dev/null
```

从中读出四个数并写下：核数 `C`（`nproc`）、内存 `M`（`free -g` 的 `total`，GB）、家目录可用空间 `D_home`、`/tmp` 可用空间 `D_tmp`。

### 1.2 校准数据：老主机 `<IP>`

老主机是 RHEL 8.10 的 VMware 虚拟机，AMD Ryzen 9 3900X，`nproc` 20（每核一线程），内存 23 GB，交换 15 GB，磁盘 327 GB（2026-09-19 检查时已用 88%）。下表是老主机上的实测经验，作为新机器取数的校准。

| 项目 | 老主机实测 |
| --- | --- |
| `python3 -m chialu.profile --jobs 6` 对 281 位点积设计做切分综合 | 内存达到 23 GB 中的 22 GB |
| `pytest tests/test_targets.py -n 3` 配 `CHIALU_VERILATOR_JOBS=4` | 全绿，25 到 60 分钟 |
| `pytest tests/test_targets.py -n 4` 配 `CHIALU_VERILATOR_JOBS=2` | `mixed_cvt_alu` 的故障注入台构建超过 900 s 限制而失败 |
| pytest 默认的 `tmp_path_retention_policy`（仓库 `pytest.ini` 设为 `failed`，`count 1`） | 失败用例的临时树累计 39 GB；改用 `-o tmp_path_retention_policy=none` |
| `~/.cache/chialu/sim_build`（Verilator 模型缓存，从不淘汰） | 涨到 26 到 32 GB；检查时 `~/.cache/chialu` 共 13 GB |
| 一次 281 位点积种子的综合 | 66 到 318 s，2 到 4 GB；`tests/test_selftests.py` 记录一次 `vec_dot_acc` 种子综合峰值 8.78 GB |
| 一次 opencode 求解调用（gemini-3.1-pro-preview） | 12 到 18 分钟；约三分之一在 1,200 s 限制处停滞（实测两轮迭代 8 次尝试中 6 次停滞） |
| Vertex 的 429 响应 | 在调用间轮转出现，不是配额耗尽；`gemini-3.1-pro-preview` 的配额是每分钟 250 次请求 |
| 综合数据库 `synthdb build --widths dense --seeds --jobs 16` | 1,757 s 内完成 8,450 行（共 28,563 个点），最差采样时仍有 13.5 GB 可用；`--jobs 10` 且无宽模块闸门的旧构建在约 5,750 行处被 Ray 的内存监视器杀掉 20 个 worker |
| 综合数据库 `--jobs 4 --wide-jobs 1` | 161 s 内 1,750 行 |
| CHIA 集群资源（运行文件） | `eda: 8`，`opencode_creds: 16`，每个运行 `parallel: 2`，`parallel_nodes: 6` |

### 1.3 推导规则

下表给出每个并行度参数的起始取值规则、老主机的对应值和写入位置。规则是起始值；第一次运行时会话每 5 s 采样一次 `MemAvailable`（`awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo`），若低于 4,096 MB 就把对应参数减一档并记录。

| 参数 | 规则 | 老主机 | 写入位置 |
| --- | --- | --- | --- |
| `CHIALU_VERILATOR_JOBS`（记 `J`） | `C <= 24` 取 4；`C >= 32` 取 6 | 4 | 环境文件 `~/chialu-env.sh`（第 3.10 节） |
| pytest `-n`（记 `N`） | `min(floor((C - 2) / J), floor((M + 4) / 8))` | 3 | 第 5.3 节的命令行 |
| `synthdb build --jobs` | `min(C - 2, floor(M / 1.5))` | 15（老主机用 16 通过） | 第 6 节的命令行 |
| `synthdb build --wide-jobs` | `max(1, floor(M / 8))` | 2 | 第 6 节的命令行 |
| 同时运行的 yosys 数（`sweeps/clock_sweep.py --workers`） | `min(floor(M / 4), floor(C / 2))` | 5（老主机用 3 到 4） | 第 7.3 节的命令行 |
| 运行文件 `available_node_types.eda.resources.eda` | `min(C - 4, floor((M - 4) / 2))` | 9（老主机用 8） | `targets/make_targets.py` 的 `CLUSTER` 模板中 `eda: 8` 一行，再重新生成运行文件 |
| 同时在飞的运行数（记 `R`） | `min(8 * C / 20, floor((M + 1) / 3))`，向下取整 | 8 | `runs/notes.md`；第 7.7 节 |
| 运行文件 `opencode_creds` | `2 * R` | 16 | `targets/make_targets.py` 的 `OPENCODE_CREDS`，再重新生成运行文件 |

`eda` 池的含义来自 `chialu/eda.py`：一个仿真节点占 `CHIALU_VERILATOR_JOBS` 个槽（`SIM_RESOURCE`），一个综合节点占 `CHIALU_EDA_SYNTH_WEIGHT` 个槽（默认 2），所以 `eda: 8` 配 `J = 4` 同时容纳两个 Verilator 构建或四个综合。`opencode_creds` 的含义是同时进行的 opencode 调用数，每个 opencode 进程占几百 MB 内存。

### 1.4 写下选择

会话把 `C`、`M`、`D_home`、`D_tmp`、`J`、`N`、`--jobs`、`--wide-jobs`、`--workers`、`eda`、`R`、`opencode_creds` 十二个数写进 `runs/notes.md`，之后每处命令行都引用这些数。`D_home` 低于 150 GB 时会话在开始前告诉用户：老主机在一轮评测中被 Verilator 缓存、pytest 临时树和运行目录用掉了超过 100 GB。

## 2. 仓库

### 2.1 仓库与分支

| 仓库 | 地址 | 分支 | 作用 |
| --- | --- | --- | --- |
| chialu-a3eval | `git@github.com:predator2k/chialu-a3eval.git`（私有） | `main` | 评测仓库：参考设计的包装、数值模型、时钟扫描、TestFloat 台架、朴素代理循环、表格 |
| `3rdparty/chialu` | `https://github.com/predator2k/chiALU.git` | `accuracy-ctl` | chiALU：所有流程（渲染、一致性、综合、搜索）从这里运行 |
| `3rdparty/chialu/third_party/adir` | `https://github.com/predator2k/adir.git`（私有） | `main` | ADIR：变量绑定、评估图、归档、搜索后端、`adir` 命令 |
| `3rdparty/cvfpu` | `https://github.com/openhwgroup/cvfpu.git` | `develop` | FPnew / CVFPU |
| `3rdparty/berkeley-hardfloat` | `https://github.com/ucb-bar/berkeley-hardfloat.git` | 默认分支 | Berkeley HardFloat（Chisel），嵌套子模块 `berkeley-softfloat-3`、`berkeley-testfloat-3` |
| `3rdparty/transdot` | `git@github.com:predator2k/SafeDot.git`（私有 fork） | `noregs` | TransDot；a3eval `README.md` 写的 `develop` 是上游名字，`.gitmodules` 绑定的是 fork 的 `noregs` |

a3eval `main` 记录的子模块指针：`berkeley-hardfloat c1105e6`、`chialu c1d0251`、`cvfpu 7781163`、`transdot 7abd4c4`。`berkeley-hardfloat` 的嵌套指针：`berkeley-softfloat-3 5c06db3`、`berkeley-testfloat-3 06b2007`。`cvfpu` 的嵌套指针：`src/common_cells 6aeee85`、`src/fpu_div_sqrt_mvp 86e1f55`、`tb/flexfloat 28be2d4`。

### 2.2 克隆

1. 确认到 GitHub 的 ssh 可用：`ssh -T git@github.com` 回答 `Hi <user>! You've successfully authenticated`。不可用时停下让用户放置 ssh 密钥。
2. 让 https 形式的子模块地址也走 ssh，避免私有仓库要密码：`git config --global url."git@github.com:".insteadOf https://github.com/`。
3. 克隆：`cd ~ && git clone --recurse-submodules --shallow-submodules git@github.com:predator2k/chialu-a3eval.git && cd chialu-a3eval && export A3=$PWD CHIALU=$PWD/3rdparty/chialu`。
4. 初始化嵌套子模块：`git submodule update --init --recursive --depth 1 3rdparty/cvfpu 3rdparty/berkeley-hardfloat 3rdparty/chialu`。`3rdparty/transdot` 没有嵌套子模块。

### 2.3 检查指针

1. `git submodule status --recursive` 列出每个子模块的提交；与第 2.1 节的指针逐一核对，前缀 `-` 表示未初始化，前缀 `+` 表示检出与记录不同。
2. `3rdparty/chialu` 不在 `c1d0251` 时切过去：`git -C $CHIALU fetch --depth 200 origin accuracy-ctl && git -C $CHIALU checkout c1d0251 && git -C $CHIALU submodule update --init --depth 50`。`fetch` 找不到该提交时改用 `git -C $CHIALU fetch --unshallow origin`。
3. 核对：`git -C $CHIALU log --oneline -1` 打印 `c1d0251 The plan names the plain agent loop's script and its smoke test`；`git -C $CHIALU/third_party/adir log --oneline -1` 打印 `06f78b9 Merge member-when: ...`。
4. 会话不改动 a3eval 的子模块指针，除非用户要求提交一个指针更新。

### 2.4 目录布局

a3eval 的目录（来自其 `README.md`）如下。

* `3rdparty/`：四个子模块。
* `baselines/<name>/`：每个参考设计一个目录，放呈现 chiALU `alu_core` 或 `dot_core` 接口的包装、文件列表、重新生成它的脚本、数值模型和一致性判决。目录有 `fpnew/`、`hardfloat/`、`hardfloat_dot/`、`transdot/`、`transdot_no_dp/`；`baselines/conform.py`、`classify.py`、`classify_dot.py`、`conform_clocked.py`、`ulp_error.py` 是共用工具。
* `sweeps/`：`clock_sweep.py`（第二层的时钟扫描）、`tableb.py`（Table B 的流水线）、`lint_rtl.py`、`verify_ieee.sh`（老主机上一次验证批处理的记录）。
* `harness/`：`testfloat_harness.py`（TestFloat 台架）、`tb_testfloat.sv`、`plain_loop.py`（Table A 的朴素代理循环）、`README.md`。
* `tables/`：`table_b.md` 与 `table_b/*.json`；没有 Table A 的产出。
* `docs/plan.md`：前置工作清单与每项的发现；`docs/handoff.md`：本文档。
* `env.sh`：把 `$A3/3rdparty/chialu/third_party/adir:$A3/3rdparty/chialu` 放到 `PYTHONPATH` 前面，并设 `CHIALU_SYNTH_REPORT=0`。

chiALU 的目录（来自其 `README.md`）如下。

* `third_party/adir/`：ADIR 子模块，`docs/design.md` 是其规范。
* `chialu/`：域库。`domain.py` 注册模板；`modules/` 是三个模板（ALU、VecSFU、VecDotAcc）；`spaces/` 是 14 个族空间文件；`eda.py` 是 CHIA 节点 `lint`、`conformance`、`fault`、`equivalence`、`yosys_stat`、`synth_unit`、`synth_ppa`、`estimate`；`review.py` 是声明审查节点；`plans.py` 是共享方案 `baseline`、`packed_banks`、`per_position`、`dedicated_speed`、`fused_fma`；`prompts.py` 是提示源（含 `chialu_timing`）；`synthdb.py`、`timing.py`、`prune.py` 是综合数据库及其消费者；`profile.py` 是切分综合；`extract.py` 是知识库抽取；`synth/` 放数据库文件；`knowledge/` 是知识卡；`verify/` 是黄金验证层与自检；`targets/rtl/` 是 SystemVerilog 生成器。
* `targets/`：运行文件；`targets/eval/` 是评测用运行文件；`targets/make_targets.py` 从一个骨架重写全部运行文件；`targets/prompts/role.md` 是角色文本。
* `eval/`：`empty_knowledge/`（空目录，含 `.gitkeep`，`*.free_*.yaml` 指向它）、`tables/make_table.py`（Table A 的表格脚本）、`plain_loop/loop.py`（早期版本，评测用的是 a3eval 的 `harness/plain_loop.py`）。
* `pdk/`：`nangate45.yaml`、`asap7.yaml`、`sky130hd.yaml` 描述符；liberty 文件首次使用时下载到 `~/pdk/`。
* `run/`：每个运行一个子目录，gitignored。
* `tests/`：`test_selftests.py`、`test_targets.py`；`pytest.ini` 设 `testpaths = tests`、`tmp_path_retention_policy = failed`、`addopts = -q --strict-markers`。
* `ops/hostctl.sh`：老主机的部署脚本（推送到裸仓库再检出，`chia up`，tmux 中 `adir run`）；新机器上不需要。

## 3. 环境

### 3.0 目录约定

运行文件的 `worker_env_commands` 把下列路径写死：`$HOME/.opencode/bin`、`$HOME/miniconda3/envs/chia_env/bin`、`$HOME/tools/bin`、`$HOME/tools/oss-cad-suite/bin`。新机器镜像老主机的布局：miniconda 装在 `~/miniconda3`，conda 环境名为 `chia_env`，工具装在 `~/tools/`，opencode 装在 `~/.opencode/bin`。不镜像时会话修改 `targets/make_targets.py` 的 `CLUSTER` 模板并重新生成运行文件（第 7.2 节）。所有安装都不需要 root；老主机唯一以 root 安装的是 `gcloud`（RPM），第 3.9 节给出免 root 的替代。

### 3.1 miniconda 与 `chia_env`

老主机：conda 26.7.1，环境 `chia_env` 由 `conda create -y -n chia_env -c conda-forge --override-channels python=3.10` 创建（2026-09-04），Python 3.10.21。CHIA 的 `README.md` 要求 Python 3.10。

1. `curl -fsSL -o /tmp/miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && bash /tmp/miniconda.sh -b -p ~/miniconda3`。
2. `~/miniconda3/bin/conda create -y -n chia_env -c conda-forge --override-channels python=3.10`。
3. 不依赖 `conda activate`：所有脚本把 `~/miniconda3/envs/chia_env/bin` 放到 `PATH` 前面（第 3.10 节）。检查：`~/miniconda3/envs/chia_env/bin/python --version` 打印 `Python 3.10.x`。

### 3.2 CHIA、ray、skydiscover、adir 与 chiALU 的依赖

老主机 `chia_env` 中的来源（`pip show`、`direct_url.json`）如下。

| 包 | 版本 | 来源 |
| --- | --- | --- |
| `chialoops`（CHIA） | 0.1.0 | 可编辑安装自 `~/src/chia`，即 `https://github.com/predator2k/chia.git`（fork 自 ucb-bar/chia；分支 `rate-limit-backoff` 带 429 退避与识别，见 `docs/handoff_0920.md` 第 8 节），老主机检出提交 `75300e5` |
| `ray` | 2.54.0 | CHIA 的 `pyproject.toml` 固定 `ray[default]==2.54.0` |
| `skydiscover` | 0.1.0 | PyPI（无 `direct_url.json`；`pip index versions skydiscover` 列出 0.1.0） |
| `adir` | 0.1.0 | 可编辑安装自 chiALU 的 `third_party/adir` |
| `pytest`、`pytest-xdist`、`pytest-timeout` | 9.1.1、3.8.0、2.4.0 | PyPI |
| `mpmath`、`PyYAML`、`numpy`、`pypdf`、`xgboost`、`scikit-learn` | 1.4.1、6.0.3、2.2.6、6.16.2、3.2.0、1.7.2 | chiALU `requirements.txt` |
| `smac`、`pymoo` | 2.4.0、0.6.2 | 数值阶段（`*.numeric.yaml` 的 `nsga2` / `smac` 后端） |
| `openai`、`google-genai` | 3.10.0、2.8.0 | skydiscover 与 CHIA 的依赖 |

安装步骤（`PIP=~/miniconda3/envs/chia_env/bin/pip`）如下。

1. `mkdir -p ~/src && git clone https://github.com/predator2k/chia.git ~/src/chia && git -C ~/src/chia checkout rate-limit-backoff`。（fork 自 ucb-bar/chia，基于 `75300e5`。）
2. `$PIP install -e ~/src/chia`。这一步装入 `ray[default]==2.54.0`、`mcp==1.27.1`、`pydantic==2.12.4`、`fastapi==0.121.0`、`pyyaml==6.0.3`、`graphviz==0.21`、`google-genai`、`boto3`、`google-cloud-compute`、`requests`。
3. `$PIP install skydiscover==0.1.0`。
4. `$PIP install -e $CHIALU/third_party/adir`。
5. `$PIP install -r $CHIALU/requirements.txt`。
6. `$PIP install pytest==9.1.1 pytest-xdist==3.8.0 pytest-timeout==2.4.0 smac==2.4.0 pymoo==0.6.2`。
7. 检查：`~/miniconda3/envs/chia_env/bin/python -c "import chia, ray, skydiscover, adir; print(ray.__version__)"` 打印 `2.54.0`；`~/miniconda3/envs/chia_env/bin/chia --help` 列出 `up`、`down`、`status`、`job`、`ray` 等子命令；`~/miniconda3/envs/chia_env/bin/adir --help` 列出 `check,cluster,seeds,run,status,stop,report`。

chiALU 本身不安装，靠 `PYTHONPATH` 找到（第 3.10 节）。

### 3.3 OSS CAD Suite：yosys、`slang` 插件、ABC、Verilator

老主机的 `~/tools/oss-cad-suite` 来自 `https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-08-07/oss-cad-suite-linux-x64-20260807.tgz`（737 MB，`VERSION` 文件内容 `20260807`）。它提供 `Yosys 0.68+36 (git sha1 17d51a330-dirty, Release, Clang ...)`、`share/yosys/plugins/slang.so`（`read_slang`，`chialu/eda.py` 记录 yosys 0.68+36 内建该前端）、`yosys-abc`、`Verilator 5.051 devel rev v5.050-148-g1a4bcac66`、`slang`、`iverilog`。

1. `mkdir -p ~/tools && cd ~/tools && curl -fL -O https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-08-07/oss-cad-suite-linux-x64-20260807.tgz && tar xzf oss-cad-suite-linux-x64-20260807.tgz`。解压得到 `~/tools/oss-cad-suite/`。
2. 检查：`~/tools/oss-cad-suite/bin/yosys -V` 打印 `Yosys 0.68+36 ...`；`~/tools/oss-cad-suite/bin/yosys -q -p 'help read_slang' >/dev/null && echo slang-ok` 打印 `slang-ok`；`~/tools/oss-cad-suite/bin/verilator --version` 打印 `Verilator 5.051 ...`；`ls ~/tools/oss-cad-suite/share/yosys/plugins/slang.so` 存在。
3. 同一发布日期的 tarball 已下架时，取最近的一个日期，并把 `yosys -V`、`verilator --version` 的输出记到 `runs/notes.md`：综合数据库的 `tool_hash` 含这两个版本，换版本意味着数据库整体重建。

### 3.4 Verilator 与 gcc-toolset-11

Verilator 来自上一节的 tarball，老主机没有单独构建它。chiALU 的台架用 `#1` 延时驱动组合电路，Verilator 以 `--timing` 运行（`chialu/verify/simulate.py` 的 `VERILATOR_FLAGS`），生成的 `verilated.mk` 设 `CFG_CXXFLAGS_COROUTINES = -fcoroutines`，所以模型编译需要 GCC 10 或更新版本和 `libatomic`。RHEL 8 的系统 gcc 是 8.5.0，老主机每个运行 EDA 流程的 shell 都先 `source /opt/rh/gcc-toolset-11/enable`（gcc 11.2.1）。

1. 查系统 gcc：`gcc --version | head -1`。10 或更新则不需要 toolset。
2. 否则查 toolset：`ls /opt/rh/`。有 `gcc-toolset-11`（或 12、13）就在环境文件里 `source /opt/rh/gcc-toolset-<n>/enable`，检查 `g++ --version | head -1` 是 11 或更新。
3. 两者都没有时停下并询问用户，附上 `gcc --version` 与 `ls /opt/rh` 的输出。备选是让管理员安装 `gcc-toolset-11`。
4. `libatomic` 检查：`ldconfig -p | grep libatomic` 有输出。

老主机的登录 shell 不 source 该 toolset（`.bashrc`、`.bash_profile` 都没有），运行文件的 `worker_env_commands` 也没有；老主机上每次 `chia up` 与 `adir run` 都从一个先 `source /opt/rh/gcc-toolset-11/enable` 的 shell 启动（本地的远程运行脚本），Ray 进程继承了这个环境。新机器上会话不依赖继承，把 `source /opt/rh/gcc-toolset-11/enable` 明确写进环境文件和运行文件的 `head_env_commands`、`worker_env_commands`（第 7.2 节），并在第 5.3 节用一次集群上的 `adir seeds` 验证。

### 3.5 sv2v

`harness/testfloat_harness.py` 在编译前对设计运行 `sv2v`；其余流程自 2026-09-17 起走 `read_slang`，不再用 sv2v。老主机的 `~/tools/bin/sv2v` 是 `sv2v v0.0.13`，来自 zachjs/sv2v 发布页的 `sv2v-Linux.zip`。

1. `mkdir -p ~/tools/bin && cd /tmp && curl -fL -o sv2v-Linux.zip https://github.com/zachjs/sv2v/releases/download/v0.0.13/sv2v-Linux.zip && unzip -o sv2v-Linux.zip && cp sv2v-Linux/sv2v ~/tools/bin/ && chmod +x ~/tools/bin/sv2v`。
2. 检查：`~/tools/bin/sv2v --version` 打印 `sv2v v0.0.13`。

### 3.6 sbt 与 Java 8

HardFloat 的 Chisel 包装由仓库自带的 sbt 流程生成（`baselines/hardfloat/build.sh`、`baselines/hardfloat_dot/build.sh`：Chisel 3.5.6、Scala 2.13、`project/build.properties` 固定 `sbt.version=1.8.2`）。老主机用 `~/tools/sbt/bin/sbt`（sbt 1.10.7 的启动器，`sbt-launch.jar` 的 `sbt.boot.properties` 默认 `1.10.7`）配系统 OpenJDK 1.8.0_422；启动器首次运行时从 Maven Central 下载 sbt 1.8.2 与 Scala 2.12.17，`sbt_compile.log` 记录首次编译 37 s。

1. `cd ~/tools && curl -fL -O https://github.com/sbt/sbt/releases/download/v1.10.7/sbt-1.10.7.tgz && tar xzf sbt-1.10.7.tgz`。解压得到 `~/tools/sbt/bin/sbt`。
2. Java：`java -version` 打印 `1.8.0_xxx` 即可。系统没有 Java 8 且无 root 时，下载 Temurin 8 的 Linux x64 JDK tarball 解压到 `~/tools/jdk8`，在环境文件里 `export JAVA_HOME=~/tools/jdk8; export PATH=$JAVA_HOME/bin:$PATH`。
3. 检查：`cd $A3/3rdparty/berkeley-hardfloat && ~/tools/sbt/bin/sbt -batch compile 2>&1 | tail -3` 以 `[success]` 结尾。第一次需要网络，`~/.sbt`、`~/.ivy2` 会被写入。
4. 脚本通过 `SBT=$HOME/tools/sbt/bin/sbt` 找到它。

### 3.7 SoftFloat 与 TestFloat

TestFloat 台架需要 `3rdparty/berkeley-hardfloat/berkeley-testfloat-3/build/Linux-x86_64-GCC/testfloat_gen`。

1. `make -C $A3/3rdparty/berkeley-hardfloat/berkeley-softfloat-3/build/Linux-x86_64-GCC`，产出 `softfloat.a`。
2. `make -C $A3/3rdparty/berkeley-hardfloat/berkeley-testfloat-3/build/Linux-x86_64-GCC`，产出 `testfloat_gen`、`testfloat_ver`、`testfloat`、`testsoftfloat`、`timesoftfloat`。
3. 检查：`$A3/3rdparty/berkeley-hardfloat/berkeley-testfloat-3/build/Linux-x86_64-GCC/testfloat_gen -level 1 f16_add | head -2` 打印两行十六进制向量。

`pdftotext` 不需要。

### 3.8 opencode

老主机：`~/.opencode/bin/opencode`，版本 1.18.31，由 opencode 官方安装脚本装入。

1. `curl -fsSL https://opencode.ai/install | bash`。安装到 `~/.opencode/bin/opencode`。
2. 检查：`~/.opencode/bin/opencode --version` 打印版本号。会话把版本记到 `runs/notes.md`；版本不同于 1.18.31 时，第 4 节的测试调用和第 5.3 节的运行会暴露 `opencode run --format json` 事件格式的变化。
3. 配置目录 `~/.config/opencode/` 在老主机上有三个文件和 `node_modules/`：
   * `opencode.jsonc`（273 字节）：把 `model` 和 `small_model` 都设为 `openrouter/z-ai/glm-5.3-flash`，注释说明 chiALU 运行时 opencode 自己的标题与摘要调用留在运行模型上。ADIR 的每次调用都显式传 `--model google-vertex/gemini-3.1-pro-preview`，所以这个文件只决定裸 `opencode run` 的默认模型。新机器上会话写一个只含 `"$schema"` 的 `opencode.jsonc`，或复制同样两行；不写任何密钥。
   * `package.json`（依赖 `@opencode-ai/plugin 1.18.30`）、`package-lock.json`、`.gitignore`：opencode 首次运行自己生成。
4. 名为 `chia` 的代理不是 `~/.config/opencode/` 下的文件。CHIA 的 `chia/models/opencode.py` 在每次调用前写一个临时配置文件并以 `OPENCODE_CONFIG` 指向它：文件定义代理 `chia`（`mode: primary`，`prompt` 是本次调用的系统文本），`permission` 块把 `edit`、`bash`、`webfetch`、`external_directory` 设为 `allow`；命令行是 `opencode run --format json --agent chia --dangerously-skip-permissions --model <provider>/<model> --dir <调用目录> [--variant <effort>] <消息>`。ADIR 再在调用目录之外拒绝一切路径（`harness/README.md` 记录朴素循环唯一的差异是允许在调用目录内编辑文件）。
5. opencode 自己的登录状态在 `~/.local/share/opencode/auth.json`（老主机上权限 `-rw-------`，125 字节），保存 openrouter 等提供商的密钥；Vertex 不走它，走第 4 节的 gcloud 应用默认凭据。会话不打印、不复制这个文件。opencode 的会话库在同目录的 `opencode.db`（老主机 83 MB）、`snapshot/`、`log/`。

### 3.9 gcloud

老主机：Google Cloud SDK 583.0.0，RPM `google-cloud-cli-583.0.0-1.x86_64`，yum 源 `https://packages.cloud.google.com/yum/repos/cloud-sdk-el9-x86_64`（需要 sudo）。免 root 的安装如下。

1. `cd ~/tools && curl -fL -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz && tar xzf google-cloud-cli-linux-x86_64.tar.gz && ./google-cloud-sdk/install.sh --quiet --path-update false`。
2. 环境文件加 `export PATH=$HOME/tools/google-cloud-sdk/bin:$PATH`。
3. 检查：`gcloud --version | head -1` 打印 `Google Cloud SDK <版本>`。
4. gcloud 的状态目录是 `~/.config/gcloud/`；应用默认凭据在其中的 `application_default_credentials.json`（老主机权限 `-rw-------`）。会话不读它。

### 3.10 环境文件与运行文件里的环境行

运行文件（`targets/make_targets.py` 的 `CLUSTER` 模板）为 Ray worker 设置：

```
export PATH=$HOME/.opencode/bin:$HOME/miniconda3/envs/chia_env/bin:$HOME/tools/bin:$HOME/tools/oss-cad-suite/bin:$PATH
export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null)
export VERTEX_LOCATION=global
```

为 head 设置 `export PATH=$HOME/.opencode/bin:$HOME/miniconda3/envs/chia_env/bin:$PATH` 和同样的两个变量。`VERTEX_LOCATION=global` 是 `gemini-3.1-pro-preview` 经 opencode 应答的区域。老主机上脚本用的环境（`~/chialu-verification/runs/env-issues.sh`）还加 `source /opt/rh/gcc-toolset-11/enable`、`PYTHONPATH=<chialu>:<chialu>/third_party/adir`、`CHIALU_VERILATOR_JOBS=4`；`ops/hostctl.sh` 还设 `THIS_MACHINE`、`PYTHONUNBUFFERED=1`、`GOOGLE_VERTEX_LOCATION=global`、`GOOGLE_VERTEX_PROJECT`，并 `ulimit -n 65536`。

会话把下面的内容写成 `~/chialu-env.sh`，把 `<J>` 换成第 1.3 节的值，把 `<ip>` 换成本机对外的 IPv4 地址（`hostname -I | awk '{print $1}'`），之后每个 shell 先 `source ~/chialu-env.sh`。

```
export PATH=$HOME/.opencode/bin:$HOME/miniconda3/envs/chia_env/bin:$HOME/tools/bin:$HOME/tools/oss-cad-suite/bin:$HOME/.local/bin:$PATH
[ -f /opt/rh/gcc-toolset-11/enable ] && source /opt/rh/gcc-toolset-11/enable
export A3=$HOME/chialu-a3eval
export CHIALU=$A3/3rdparty/chialu
export PYTHONPATH=$CHIALU/third_party/adir:$CHIALU
export CHIALU_VERILATOR_JOBS=<J>
export CHIALU_SYNTH_REPORT=0
export THIS_MACHINE=<ip>
export PYTHONUNBUFFERED=1
export RAY_DISABLE_IMPORT_WARNING=1
export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null)
export VERTEX_LOCATION=global
export GOOGLE_VERTEX_LOCATION=global
export GOOGLE_VERTEX_PROJECT=$GOOGLE_CLOUD_PROJECT
export SBT=$HOME/tools/sbt/bin/sbt
ulimit -n 65536
```

`CHIALU_SYNTH_REPORT=0` 只对 a3eval 的脚本有意义（关掉综合报告文本，`plain_loop.py` 自己按 `--no-synth-report` 设置它）；ADIR 运行的 `feedback` 列表包含 `synth_ppa.summary` 等报告，不受它影响。

## 4. 认证：停止点

Vertex 通过 gcloud 的应用默认凭据（ADC）访问，不用 API 密钥。CHIA 的 `chia/models/vertex.py` 与 opencode 的 `google-vertex` 提供商都从 `~/.config/gcloud/application_default_credentials.json` 取凭据，从 `GOOGLE_CLOUD_PROJECT` 取项目，从 `VERTEX_LOCATION`（opencode）或 `GOOGLE_CLOUD_LOCATION`（google-genai）取区域。

装好 gcloud 后会话停下，提醒用户亲自、交互地运行下面三条命令（它们会打开浏览器登录，会话不能替用户完成）：

1. `gcloud auth login`
2. `gcloud auth application-default login`
3. `gcloud config set project <项目 id>`。老主机上运行文件解析到的项目是 `project-61ce0e88-8479-4f76-abc`；新机器用哪个项目由用户决定。

用户回来后会话按顺序验证：

1. `gcloud auth application-default print-access-token >/dev/null && echo ok` 打印 `ok`。
2. `gcloud config get-value project` 打印用户设定的项目 id。
3. 一次小的 opencode 调用：`source ~/chialu-env.sh && opencode run --model google-vertex/gemini-3.1-pro-preview "Reply with the single word ok."`。正常应答是一行 `ok`（模型可能带句号）。应答中出现 `UNAUTHENTICATED`、`401`、`PERMISSION_DENIED`、`Model not found` 或 `Selected model is not supported in the selected location` 时，把原文交给用户；出现 `429 RESOURCE_EXHAUSTED` 时隔 30 s 重试一次再判断。
4. 确认 `~/.config/gcloud/application_default_credentials.json` 与 `~/.local/share/opencode/auth.json`（若存在）的权限都是 `-rw-------`：`stat -c '%A %n' ~/.config/gcloud/application_default_credentials.json ~/.local/share/opencode/auth.json 2>/dev/null`。会话只看权限位，不看内容。

四步都通过后再继续。凭据不进入任何仓库、任何 `runs/` 记录。

## 5. 实验前的环境验证

所有命令在 `source ~/chialu-env.sh && cd $CHIALU` 之后运行。每一项的末行与退出码记到 `runs/notes.md`。

### 5.1 chiALU 自检

| 命令 | 期望末行 |
| --- | --- |
| `python3 -m chialu.verify.selftest` | `[selftest] all 30 cases pass`（`README.md` 记为 30 个规格；格式是 `[selftest] all <N> cases pass`） |
| `python3 -m chialu.verify.formats_selftest` | `[formats_selftest] 35 groups pass` |
| `python3 -m chialu.verify.domain_selftest`（需要 `read_slang` 与 Verilator） | `[domain_selftest] all pass (<临时目录>)`，其前一行是六个方案的 area、delay、score 的 JSON |
| `python3 -m chialu.verify.float_seed_selftest` | `PASS 8 float seeds against Python golden, including negative zero (<目录>)` |
| `python3 -m chialu.verify.alu_fidelity_selftest` | `PASS ALU family fidelity simulation regressions: <目录>` |
| `python3 -m chialu.verify.fp_cpa_selftest` | 以若干 `... PASS 950` 结尾 |
| `python3 -m chialu.verify.mode_ops_selftest` | `PASS mode masks, converter-only generation, Python golden and template preservation: <目录>` |
| `python3 -m chialu.verify.module_collector_selftest` | `PASS strict collectors, module identity and three unit simulations <目录>` |
| `python3 -m chialu.verify.dot_structural_selftest` | `PASS 41/41 structural cases, 3 inactive rejections; <目录>` |
| `python3 -m chialu.verify.family_space_selftest` | `PASS 2360 enumerated points; deterministic samples retain every family baseline` |
| `python3 -m chialu.verify.check_rules_selftest` | `PASS check rules through adir <目录>` |
| `python3 -m chialu.verify.exponent_rounder_selftest` | 两行 `{"format": "e8m0", ..., "pass": true, ...}` |

全部自检模块由 `python3 -m chialu.selftests --list` 列出（`chialu/verify/*_selftest.py` 与 `chialu/targets/rtl/families/selftest.py`）。整套用 pytest 跑：`pytest tests/test_selftests.py -n 8 -m "not slow" -o tmp_path_retention_policy=none` 与 `pytest tests/test_selftests.py -n 2 -m slow -o tmp_path_retention_policy=none`；慢集合（`domain_selftest`、`check_rules_selftest`、`combinational_sim_selftest`、`combinational_sim_check_selftest`、`checkers_selftest`、`simulate_selftest`、`prompt_selftest`、`families.selftest`）用 `-n 2`，因为一次 `vec_dot_acc` 种子综合峰值 8.78 GB。已知失败只有一个：`seed_selection_selftest`（第 8 节），其余失败都要报告给用户。

### 5.2 知识 lint、行为规则 lint 与浮点族测试

| 命令 | 期望 |
| --- | --- |
| `python3 -m chialu.archdocs` | 退出码 0；输出里没有 `ORPHAN doc`、`BAD REF`、`BAD VARIANT`、`missing doc` 行 |
| `python3 -m chialu.behavior_rules lint` | 末行以 `0 unregistered, 0 stale` 结尾 |
| `python3 -m chialu.targets.rtl.families.fptest --formats fp16,bf16,fp8e5m2,fp8e4m3` | 末行 `[fptest] <N>/<N> pass (<目录>)`，退出码 0 |
| `python3 -m chialu.targets.rtl.families.fptest --formats fp16,bf16,fp8e5m2,fp8e4m3 --tight` | 同上；`--tight` 是单元选项 `x_form: guard_round_sticky` 的几何 |

`fptest` 默认格式 `fp16,bf16,fp8e4m3` 在老主机上是 `322/322 pass`。老主机 2026-09-18 的 `--tight` 日志是 `260/266 pass`，6 个失败都是 `fp8e4m3` 的 `fam_fp_round_*` 舍入器（`x=07070 ref=01800 lib=01870`）；提交 `aa4a73e`（2026-09-19，"The rounder's kept-bit shift stops at the word width"）修的就是它，`c1d0251` 含该修复，期望全过。macOS 上有一个已知的 Verilator 内部错误，Linux 上没有。`fptest --jobs` 默认 8，每个台架一个 Verilator 构建，按第 1.3 节的 `N * J` 上限调整。

### 5.3 目标套件

```
cd $CHIALU && CHIALU_VERILATOR_JOBS=<J> pytest tests/test_targets.py -n <N> -o tmp_path_retention_policy=none 2>&1 | tee $A3/runs/test_targets.log
```

每个运行文件四个用例：加载、种子 lint、种子一致性、种子故障注入；跳过的是没有校验器的目标和数值阶段文件；xfail 是 `approx_alu`。记录在案的期望末行是 `85 passed, 22 skipped, 1 xfailed in <秒>s`，它对应 2026-09-18 的 26 个运行文件；`c1d0251` 有 36 个运行文件（`targets/` 13 个、`targets/eval/` 23 个，2026-09-19 新增的 10 个 `vec_dot_acc_cmp_fp8*` 与 `vec_dot_acc_cmp_fp16*` 文件在 Table B 的那次运行中以 51 passed、17 skipped 通过），所以用例总数是 144，验收条件是 `0 failed`、恰好 `1 xfailed`，其余为 passed 或 skipped。会话把实际的末行记到 `runs/notes.md`。老主机 `-n 3`、`J = 4` 用 25 到 60 分钟。输出开头的两行 `bringing up nodes...` 是 xdist 的。任何 `FAILED` 都停下报告用户，附失败用例名和 `tee` 到的日志。

一次集群上的验证（确认 Ray worker 里的 Verilator 找得到 gcc 11）：

```
cd $CHIALU && adir check targets/eval/fp_alu_cmp.yaml && chia up -y targets/eval/fp_alu_cmp.yaml && adir seeds targets/eval/fp_alu_cmp.yaml && chia down -y targets/eval/fp_alu_cmp.yaml
```

期望 `adir seeds` 打印 `[adir seeds] baseline: feasible, goal [<area>, <delay>], score 1.000`；worker 上的构建失败会以 `conformance` 的 `detail` 里的编译错误（`-fcoroutines` 未识别）出现。`chia up` 用 `bash --login` 经 ssh 连到 `${THIS_MACHINE}`，所以本机到自己的免密 ssh 必须可用：`ssh -o BatchMode=yes $USER@$THIS_MACHINE true && echo self-ssh-ok`；不通时把本机公钥追加到 `~/.ssh/authorized_keys`。

### 5.4 参考设计包装的一致性

三个包装的判决已记录在 `docs/plan.md` 与 `3rdparty/chialu/docs/evaluation-plan.md` 第 8 节；新机器上重跑一遍以确认环境。命令在 `$A3` 下运行，`PYTHONPATH` 已由环境文件设置。

FPnew：

1. `python3 baselines/fpnew/build.py --point MERGED --out runs/fpnew` 产出 `runs/fpnew/fpnew_merged_alu_core.sv`（带译码的包装，进表格的数）与 `fpnew_merged_bare.sv`（裸 FPU），并把两者在 `--tight`（默认 300 ps）与每个 `--clocks` 目标下综合，结果写到 `runs/fpnew/fpnew_synth.json`。`baselines/fpnew/files.txt` 列出 CVFPU 的 15 个源文件（含 `src/fpnew_cast_multi.sv`，缺它会少一个被引用的模块）。
2. `python3 baselines/classify.py --target targets/eval/fp_alu_cmp.yaml --rtl runs/fpnew/fpnew_merged_alu_core.sv --n-random 20000 --out runs/fpnew/classes.json`。`--target` 相对 `$CHIALU` 解析（`classify.py`、`conform.py`、`classify_dot.py` 都读环境变量 `CHIALU`，缺省 `3rdparty/chialu`），`--rtl` 相对当前目录。
3. 期望：约 428k 个向量（`evaluation-plan.md` 8.4 记 427,964）中 24 个不一致，全部是 `flags_only` 类的 `uf_after_round`：bf16 `fmul`，次正规数乘接近 1 的数，`flags expected 0x8 got 0xc`，即 FPnew 在两种 tininess 规则下都不该报的 underflow。这 24 个是声明在行上的合同差异，不是失配。其余类别（老主机 2026-09-16 曾见 `lane_flags` 25,412、`snan_flags` 4,630、`qnan_invalid` 4,212）已被 `flag_scope: per_operation` 与 IEEE 的 sNaN 规则关闭，再出现就是回归。

HardFloat：

1. `SBT=$HOME/tools/sbt/bin/sbt bash baselines/hardfloat/build.sh runs/hardfloat` 产出 `runs/hardfloat/alu_core.v`（每个（格式，op）一个模块，`recFNFromFN` / `fNFromRecFN` 在边界，min/max 由 `CompareRecFN` 加多路器构成）。
2. `python3 baselines/classify.py --target targets/eval/fp_alu_cmp.yaml --rtl runs/hardfloat/alu_core.v --n-random 20000 --out runs/hardfloat/classes.json`。
3. 期望：失配只出现在 `mode fp8e5m2` 的 `fadd`、`fsub`（`value` 与 `nan_result` 类，老主机 38,423 加 4,135）：HardFloat 的 `AddRecFN` 与 `MulAddRecFN` 在 (5, 3) 上不能例化（`baselines/hardfloat/ProbeFormats.scala`），包装让 fp8 的 fadd/fsub 返回零。这是行上声明的差异。其他任何类别都要报告。

TransDot：

* Table B 的 DP 包装：`python3 baselines/transdot/tdot_comb.py`（对 `3rdparty/transdot/src/transdot_fp4_fp8_fp16_fp32_fma.sv` 打一次补丁，保留 `.orig`），再 `python3 baselines/transdot/build_dp.py --row fp16 fp8 --no-synth --out runs/tableb/transdot_dp`，然后 `python3 baselines/classify_dot.py --target targets/eval/vec_dot_acc_cmp_fp16.yaml --rtl runs/tableb/transdot_dp/transdot_dp_dot_core_fp16.sv --n-random 3000`。期望 fp16 行 3,156 个向量中 160 个失配：2 个 `value`（负乘积被整个移出 36 位对齐字且无 sticky，舍入器当成平局）与 158 个 `nan_expected`（上层 lane 的特殊值被丢弃：只有 lane 0 与加数进入特殊值检测）。fp8 行 3,153 个中 1,621 个（1,092 `value`、409 `nan_expected`、120 `inf_expected`），fp8 的累加是窗口式的。这些都是行上声明的合同差异。
* Table A 的 ALU 级 no-DP 点：`python3 baselines/transdot/build.py --point MERGED --out runs/transdot`；它在 `read_slang` 下需要 `-Wno-range-oob -Wno-index-oob`（脚本自带）。`docs/plan.md` 第 8 项记录它在 `read_slang` 下能展平，但其 Table A 行尚未测量，一致性判决也没有记录；会话跑 `classify.py` 并把类别写进 `runs/notes.md`。

TestFloat 台架（chiALU 的 fp16 单元对 Berkeley TestFloat 一级向量）：

1. `cd $CHIALU && adir check targets/eval/fp_alu_cmp.yaml --run-dir /tmp/a3eval/fpc && adir seeds targets/eval/fp_alu_cmp.yaml --run-dir /tmp/a3eval/fpc --local` 渲染种子到 `/tmp/a3eval/fpc/seeds/<方案>/program.sv`。
2. `cd $A3 && python3 harness/testfloat_harness.py --rtl /tmp/a3eval/fpc/seeds/baseline/program.sv --testfloat 3rdparty/berkeley-hardfloat/berkeley-testfloat-3/build/Linux-x86_64-GCC --out runs/testfloat`。
3. 期望每行 `TESTFLOAT <fn> rnd=<r> vectors=46464 mismatches=0 ... PASS`：`add`、`sub`、`mul` 各四种舍入模式，`eq`、`lt`、`le`（对 SoftFloat 的 quiet 谓词 `f16_eq`、`f16_lt_quiet`、`f16_le_quiet`）各一种。IEEE 规则之前每个算术函数有 2,447 个失配，现在为 0。

## 6. 综合数据库

### 6.1 命令与选项

数据库是族库的综合测量表：每行是一个族在一个几何、一个流程、一个 PDK 下的设计点。构建命令（`chialu/synthdb.py` 的 `build` 子命令）：

```
cd $CHIALU && export RAY_TMPDIR=$HOME/.ray_synthdb && mkdir -p $RAY_TMPDIR run/synthdb && \
nohup python3 -u -m chialu.synthdb build --pdk nangate45 --widths dense --seeds --jobs <jobs> --wide-jobs <wide> --timeout 900 > run/synthdb/build.log 2>&1 &
```

| 选项 | 默认 | 含义 |
| --- | --- | --- |
| `--pdk` | `nangate45` | `pdk/` 下的描述符名或描述符文件 |
| `--liberty`、`--name` | 无 | 用 liberty 文件列表代替描述符 |
| `--kinds`、`--families` | 全部有点的种类 | 只建某些种类或族 |
| `--widths` | `8,16,24,32,48,64` | 宽度列表，或 `dense` 即 `4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512` |
| `--seeds` | 关 | 加上运行文件结构所用的宽度（281 位累加帧、22 位乘积、9 位移位量等），缓存于 `chialu/synth/seed_widths.json` |
| `--effort` | `medium` | ABC 脚本档位 |
| `--jobs` | `max(2, cpu - 2)` | 同时运行的综合数（线程池，每个一个 yosys 进程） |
| `--wide-jobs` | 0 | 模块文本超过 200 KB 的点同时运行的上限；每个只在有 6,144 MB 空闲内存时启动（`CHIALU_MEM_FLOOR_MB`）；0 表示只受内存下限约束 |
| `--timeout` | 900 | 一次综合的秒数上限 |
| `--limit` | 0 | 只建前 N 个点，用于计时 |
| `--host` | 无 | 在 EDA 主机上跑并取回；新机器上不用 |

其他子命令：`status [--pdk] [--seeds]`（每种类的行数、已建宽度、过期的生成器）、`query --kind <kind> --width <w> [--family] [--smallest]`、`verify --sample 20`（重综合抽样比对）、`merge <目录>`、`fetch --host`、`prune [--apply]`（丢掉没有命名子结构的行）、`slots`。

`seed_widths.json` 由 `synthdb.seed_widths()` 从 `targets/*.yaml`（不含 `targets/eval/`）的结构清单收集，仓库里的一份写于 2026-09-13。构建前删掉它让 `--seeds` 重新收集：`rm -f chialu/synth/seed_widths.json`；收集要加载每个运行文件，费几分钟。`targets/eval/` 的评测目标与 `targets/fp_alu.yaml`、`targets/vec_dot_acc.yaml` 共用格式与 281 位帧，所以稠密网格加这些宽度覆盖它们；会话用 `python3 -m chialu.synthdb status --seeds` 确认。

### 6.2 输出布局与失效规则

* 文件在 `chialu/synth/<pdk>/<kind>.jsonl`；一个文件超过 10 MB 时拆成 `<kind>/<family>.jsonl`；每个 PDK 一个 `manifest.json`，记 `schema`（2）、`pdk`、`descriptor_hash`、`liberty_hash`、`tool_hash`、`tools`（yosys 与前端的版本）、每种类的行数、每个生成器模块的内容哈希、日期。
* 一行有五部分，键是前三部分：`point`（`kind`、`family`、`choices`、`slots` 递归、`point_id`）、`geometry`（`width` 与派生量）、`flow`（`pdk`、`liberty_hash`、`effort`、`clock_ps`、`tool_hash`）、`result`（`status`、`area_um2`、`cells`、`delay_ps`、`seconds`、`detail`）、`provenance`（`gen_hash`、`module`、`date`、`tags`、`label`）。
* 增量与可恢复：已有行在 `gen_hash`（生成文本）与 `tool_hash`（yosys、前端、ABC 的版本与脚本）都相同时保留，否则重综合；每行落地即追加，中断后重跑同一命令继续。
* 失效条件：生成器改变（`status` 报 `stale generators since the build: ...`）、工具版本改变（行的 `tool_hash` 与当前不同，`status` 报 `measured under other tools`）、liberty 文件改变（`liberty_hash`）。三者任一都意味着相应行重建。
* liberty：`pdk/nangate45.yaml` 指向 `pdk/lib/NangateOpenCellLibrary_typical.lib`，缺失时从 `https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/master/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib` 下载到 `~/pdk/`（首次需要网络），解析结果缓存在 `~/pdk/*.pkl` 与 `~/.cache/chialu/liberty`。
* ABC 脚本（`medium`）：`+strash;&get -n;&dc2;&dch -f;&nf -C 32 -F 8 -p -D {clock_ps};&put;buffer;upsize -D {clock_ps};dnsize -D {clock_ps};topo;stime`。`&nf -D` 在这个 ABC 里不生效，一个设计只有一个（面积，延时）点；缓冲尾部 `buffer;upsize;dnsize` 是 2026-09-17 加入的。

### 6.3 并行度与内存

`--jobs`、`--wide-jobs` 按第 1.3 节取。老主机的经验：`--jobs 16` 稠密构建下最差采样仍有 13.5 GB 可用，最大的 mapper 0.8 GB；`--jobs 10` 且没有宽模块闸门的旧构建在 4,907 s、约 5,750 行处被 Ray 内存监视器杀掉 20 个 worker 后终止。`RAY_TMPDIR` 放到家目录，避免 Ray 的会话文件填满小的 `/tmp`。构建期间会话用第 1.3 节的采样循环记录 `MemAvailable`。

### 6.4 耗时

老主机没有一次完整构建的时长记录：三次构建日志（`~/chiALU/run/synthdb*/run.log`）都以 SIGTERM 结束。已知的速率是 16 个作业时 1,757 s 完成 8,450 行（点总数 28,563），4 个作业时 161 s 完成 1,750 行；宽模块（点积、FMA 的 281 位帧）在后段，单个 66 到 318 s。会话先计时一个小种类：`python3 -m chialu.synthdb build --pdk nangate45 --kinds adder --widths 16 --limit 50 --jobs <jobs>`，记下每行秒数，再启动完整构建，并每小时把 `tail -2 run/synthdb/build.log` 的进度行（格式 `<n> rows (<ok> ok, <synth> synthesized, <skip> unchanged), <秒>s`）记到 `runs/notes.md`。

### 6.5 确认消费者读到它

1. `python3 -m chialu.synthdb status --pdk nangate45`：每种类的行数与宽度，没有 `stale generators` 行。
2. `python3 -m chialu.synthdb query --pdk nangate45 --kind adder --width 16`：打印每个族最快的行。
3. 提示源 `chialu_timing`（`chialu/prompts.py` 的 `TIMING`，调用 `chialu.timing.render(instance)`）：`python3 -c "from adir.instance import load; from chialu.timing import render; print(render(load('targets/eval/fp_alu_cmp.yaml', run_dir_override='/tmp/a3eval/timing')))"` 打印每个结构种类在运行时钟下的族延时与面积表；没有数据库时为空。
4. `python3 -m chialu.prune targets/eval/fp_alu_cmp.yaml --best delay --out /tmp/a3eval/fp_alu_cmp.best.yaml`：打印 `[prune] nangate45, the database's best family per structure by delay` 与每个结构的族、延时、面积，末行 `[prune] wrote /tmp/a3eval/fp_alu_cmp.best.yaml`；没有数据库时退出并打印 `prune: no database for nangate45`。

### 6.6 数据库的用途，以及老主机上的那份不复制

用途有四个：第二层的 `prune --best delay` 无模型参考点（第 7.3.4 节）；提示里的时序先验（`prompts.sources` 中的 `chialu_timing`）；数值阶段（`*.numeric.yaml` 的 `chialu.eda.estimate` 节点，约束 `estimate.coverage ge 0.8`）；消融中的 `chialu.prune --threshold 0.10`。

老主机 `~/chiALU` 停在提交 `1f07497`（"the nangate45 database is discarded"），`~/chiALU/chialu/synth/nangate45/` 为空；`~/chiALU-eval/chialu/synth/` 只有 `seed_widths.json`。那份数据库建于 `fp_fma` 槽、`negation_handling` 选择与 `x_form` 选项之前，也在 slang 前端与缓冲尾部之前，不复制。

## 7. 实验

### 7.1 一次 chiALU 运行：启动、目录、停止与恢复、进度

所有 ADIR 运行从 `$CHIALU` 启动，运行目录是运行文件 `adir.run_dir` 指定的 `run/<名字>/`。

1. `source ~/chialu-env.sh && cd $CHIALU`。
2. `adir check targets/eval/<文件>.yaml`：绑定时检查，写 `run/<名字>/contract.json`、`problem.md`、`space.json`、`graph.json`、`evaluator.py`、`skydiscover.yaml`、`prompt_templates/`。
3. 集群只起一次：`chia up -y targets/eval/fp_alu_cmp.yaml`。每个运行文件的集群段只有 `cluster_name` 不同；`adir run` 用 `ray.init(address="auto")` 加入当时在跑的 Ray 集群，所以同一台机器上所有运行共用一个集群，`eda` 与 `opencode_creds` 两个资源池在它们之间共享。`chia status --chia-cluster targets/eval/fp_alu_cmp.yaml` 看节点；`ray status` 看资源。
4. 种子：`adir seeds targets/eval/<文件>.yaml`（在集群上评估；`--local` 在本进程）。写 `run/<名字>/seeds/<方案>/{program.sv, record.json}` 与 `seeds/seed_values.json`。`adir run` 在 `seeds/` 不存在时自己先跑这一步。
5. 搜索：在 tmux 窗口里 `adir run targets/eval/<文件>.yaml --iterations 20 2>&1 | tee -a run/<名字>/run.log`。`--iterations` 覆盖 `search.iterations`。
6. 停止：另一个终端 `adir stop targets/eval/<文件>.yaml` 写下 `stop` 文件，当前迭代结束后运行停止并把 `stopped_by` 写进 `summary.json`。预算 `budget.wall_hours`（12）、`budget.llm_calls`（200）、`budget.node_runs`（2000）与 `stop.plateau_iterations`（30）由同一个每 5 s 检查一次的监视线程执行。
7. 恢复：`adir run targets/eval/<文件>.yaml --resume` 从最新的 `run/<名字>/skydiscover/checkpoints/checkpoint_<n>` 继续；运行文件的 `cache:` 段把 `conformance`、`fault`、`synth_unit`、`synth_ppa` 设为 `cache: true`，重评估的节点命中 `run/<名字>/chia_cache`。
8. 报告：`adir report targets/eval/<文件>.yaml` 写 `summary.json` 与 `report.md`。
9. 结束：`chia down -y targets/eval/fp_alu_cmp.yaml`。残留的 Ray 用 `ray stop` 清掉。

运行目录（ADIR `docs/design.md` 1.3 与 7.7）：

| 路径 | 内容 |
| --- | --- |
| `results_db.jsonl` | 归档：每个候选一行 JSON（字段见第 7.8 节），种子在前 |
| `programs/<candidate_id>.sv` | 每个评估过的程序 |
| `prompts/<时间戳>_<角色>_<父>.md` | 每个角色每次调用的提示，应答附在后面（`prompts.log: true`） |
| `agent/<时间戳>-<id>-<父或角色>/` | 每次模型调用的工作目录：`knowledge/`（知识库副本）、`program.sv`（父程序副本）、`members/`、`context/`（上下文程序、`parent.md`、`unit.md`、`decisions.md`、`seeds.md`）、反馈文件 |
| `seeds/`、`calls/`、`instructions.jsonl`、`prompt_sample.md` | 种子、在飞调用的边车、指令行、第一个种子的示例提示 |
| `cache/`、`chia_cache/`、`chia_eval_log.jsonl` | 节点缓存、CHIA 缓存、每次评估一行 |
| `skydiscover/{db, checkpoints/, best/}` | 后端的数据库、检查点、最优 |
| `summary.json`、`status.json`、`report.md` | 计数器（`llm_calls`、`llm_calls.solution`、`llm_failures`、`input_tokens`、`output_tokens`、`reasoning_tokens`、`cost_microusd`、`stopped_by`）、状态、报告 |

读进度：`wc -l run/<名字>/results_db.jsonl`（候选数）；`tail -f run/<名字>/run.log`；`python3 -c "import json;print(json.load(open('run/<名字>/summary.json')))"`；`adir status targets/eval/<文件>.yaml`。一次求解调用 12 到 18 分钟，一个迭代最多两次求解调用、两次指导调用、两次审查（每次审查最多 `chialu.review.MAX_CALLS = 3` 次模型调用），所以一个迭代最多 10 次调用，200 次调用覆盖 20 个迭代。

### 7.2 运行文件族与开关

`targets/eval/` 的评测运行文件由 `targets/make_targets.py` 生成；改运行文件要改 `make_targets.py` 再 `python3 targets/make_targets.py`，然后 `git -C $CHIALU diff --stat targets/` 确认只有预期的行变了。会话在第一次生成前把这些改动做完：`CLUSTER` 模板中 `eda: 8` 改成第 1.3 节的值；`OPENCODE_CREDS = 16` 改成 `2 * R`；`head_env_commands` 与 `worker_env_commands` 各加一行 `- source /opt/rh/gcc-toolset-11/enable`（需要 toolset 的机器）；不镜像老主机目录布局时改 `PATH` 行。`PROVIDER = "google-vertex"`、`MODEL = "gemini-3.1-pro-preview"`、`EFFORT = "medium"`、`REVIEW_TIMEOUT_S = 900` 不动。

| 运行文件 | 用途 | 与 `fp_alu_cmp.yaml` 的差别 |
| --- | --- | --- |
| `fp_alu_cmp.yaml` | Table A 的 chiALU 完整行 | 基准：`adaevolve`，20 迭代，`parallel: 2`，`operator: [structural, local, free]`，`ambition: [conservative, moderate, aggressive]`，`member_focus: [one]`，`feedback_depth: [files]`，`knowledge_depth: [path]`，`prompts.sources: [chialu_interface, chialu_families, chialu_structures, chialu_timing]`，`tactics.sources: [target]`，`seeds.generated: [baseline]` 加 `rank.prior: chialu_structure_area, top: 8`，审查节点 `chialu.review.opencode`，约束 `review.agree ge 1.0`，`clock_ps 8000`，`verify.n_random 300` |
| `fp_alu_cmp.free_{best_of_n,beam_search,adaevolve}.yaml` | 通用代码进化对照 | `backend` 换成对应后端；`knowledge: ../../eval/empty_knowledge`；`operator: [free]`；`member_focus: [none]`；`prompts.sources: []`；`tactics.sources: []`；无 `rank` |
| `fp_alu_cmp.numeric.yaml` | 数值阶段 | `nsga2`（`--backend smac` 可换）400 迭代，节点只有 `declaration` 与 `chialu.eda.estimate`，种子 `[baseline, packed_banks, per_position, dedicated_speed]` |
| `fp_alu_cmp_fpnew.yaml`、`fp_alu_cmp_hardfloat.yaml` | chiALU 绑定到参考设计的结构选择（`fp_fma.m*.family: classic_fma` 等 / `fp_adder.m*.family: two_path` 等），加 `x_form: guard_round_sticky` | 只多出固定的 `core.*` 绑定 |
| `vec_dot_acc_cmp_fp16.yaml`、`vec_dot_acc_cmp_fp8.yaml` 及各自的 `.free_*` | Table B 的两个行集的种子 | `chialu.VecDotAcc`，一个模式，`dot_contract: fused`，`clock_ps 40000`，`prompts.sources: [chialu_interface]`，`tactics.sources: [target, worst_constraint]`，没有审查节点与 `synth_unit` |
| `vec_dot_acc_cmp_fp16_td.yaml`、`_fp8_td`、`_fp16_tdw`、`_fp8_tdw` | chiALU 绑定到 TransDot 的槽选择（`core.family: multi_term_fused_dot` 等）；`_tdw` 再加 `core.window_bits: 76`，`verify.n_random 3000` | 只多出固定绑定 |
| `vec_dot_acc_cmp.yaml` 及 `.free_*` | 双模式的混合文件，留给内部层次 | `modes` 为两个 |
| `int_subword_alu.yaml` 及 `.free_*`、`.numeric`（在 `targets/`） | 整数对照 | 同结构 |

消融用的开关（第 7.6 节）也都改在 `make_targets.py` 里，或复制一个运行文件到 `targets/eval/abl/<名字>.yaml` 改动后单独加载（`knowledge`、`role`、`task` 的相对路径 `../../` 要随目录深度调整为 `../../../`）。

### 7.3 Table A：`fp_alu_cmp` 的行

Table A 的方法行列：相对种子的（面积，延时）前沿超体积、每个时钟目标下最佳可行面积、最小延时、可行比例、达到最终超体积 95% 所需的模型调用数、综合分钟数、token 数。参考行与第二层行的列：四个时钟目标下的面积、最小延时、cell 数、包装开销、一致性判决。

#### 7.3.1 chiALU 完整行

* 命令：第 7.1 节的流程，文件 `targets/eval/fp_alu_cmp.yaml`，`--iterations 20`。
* 运行目录 `run/fp_alu_cmp/`；产物 `results_db.jsonl`、`prompts/`、`agent/`、`summary.json`。
* 验收：`summary.json` 的 `llm_calls` 达到 200 或 `stopped_by` 有值；`results_db.jsonl` 每行 `feasible`、`goal_values`、`score` 齐全；至少一个候选 `feasible: true`。老主机两次迭代 2.7 小时的记录：子代 1 通过全部门槛，6744.7 um2 / 6546 ps（基准 6838.6 / 7032），子代 2 位精确但被审查以 `agree` 0.909 拒绝。
* 表格格：方法行 "chiALU"。
* 重复三次（第 7.7 节）：每次换 `run_dir`（`--run-dir run/fp_alu_cmp.r2`）。

#### 7.3.2 通用代码进化行

* 命令：同上，文件 `targets/eval/fp_alu_cmp.free_best_of_n.yaml`、`.free_beam_search.yaml`、`.free_adaevolve.yaml`。SkyDiscover 的 `evox`、`openevolve`、`shinkaevolve` 后端在老主机上缺包，不在表中。
* 运行目录 `run/fp_alu_cmp.free_<后端>/`。
* 验收：同 7.3.1；`prompts/*.md` 里没有声明块与知识索引。
* 表格格：方法行 "generic code evolution"，每个后端一行。

#### 7.3.3 朴素代理循环

* 命令（在 `$A3`）：`python3 harness/plain_loop.py targets/eval/fp_alu_cmp.yaml --agent opencode --provider google-vertex --model gemini-3.1-pro-preview --effort medium --calls 200 --out runs/plain/fp_alu_cmp`。运行文件路径相对 `PYTHONPATH` 上的 chiALU 树解析。脚本需要 CHIA（`chia.models.*`），不需要 Ray 集群（它自己起一个本地 Ray 实例）。
* 每次调用一次 opencode 调用，一次尝试，`--timeout-s 1200`；停滞的调用计入 `--calls`，其 token 从 opencode 会话库恢复（`call.json` 的 `recovered: true`）。
* 输出 `runs/plain/fp_alu_cmp/`：`target.json`、`seed/`、`call_<k>/{prompt.md, program.sv, candidate.sv, feedback/, reply.md, transcript.md, usage.json, call.json, evaluation.json}`、`programs/`、`results_db.jsonl`、`best.sv`、`summary.json`、`run.log`。
* 验收：`summary.json` 的 `calls` 等于 200，`stalled` 与 `failed` 有计数；`results_db.jsonl` 每行有 `call`、`status`、`cost.input_tokens`。老主机的冒烟：两次调用（1,200.6 s 与 658.1 s）都应答，两个候选可行且被种子支配（7,175.1 um2 / 5,368.8 ps 与 7,031.4 / 5,422.5，种子 6,991.0 / 5,225.6），659k 输入 token、17k 输出 token。
* 表格格：方法行 "plain agent loop"。
* 评估器差异（`harness/README.md`）：没有 `synth_unit` 与 `review` 节点，`retries` 为 1，允许在调用目录内编辑；其余（种子、评估器函数、门控、约束、评分规则、模型构造）与 chiALU 行相同。

#### 7.3.4 第二层：共享方案种子与无模型参考

1. 渲染种子。老主机扫描过的种子目录（`/tmp/pipe_fpc4/seeds`：`baseline`、`packed_banks`、`per_position`、`dedicated_speed`、`front_1` 到 `front_4`）由 `chialu.pipeline` 产生。两条路：
   * 四个共享方案：把 `targets/eval/fp_alu_cmp.yaml` 复制为 `targets/eval/fp_alu_cmp_plans.yaml`，`search.seeds.generated` 改成 `[baseline, packed_banks, per_position, dedicated_speed, fused_fma]`（`chialu/plans.py` 的 `PLANS`；`fp_alu_cmp.numeric.yaml` 已列前四个），然后 `cd $CHIALU && adir check targets/eval/fp_alu_cmp_plans.yaml --run-dir /tmp/a3eval/fpc && adir seeds targets/eval/fp_alu_cmp_plans.yaml --run-dir /tmp/a3eval/fpc --local`。种子在 `/tmp/a3eval/fpc/seeds/<方案>/program.sv`。
   * 数值前沿点（需要第 6 节的数据库）：`python3 -m chialu.pipeline targets/eval/fp_alu_cmp.yaml --run-dir /tmp/a3eval/pipe_fpc --stage calibrate --stage numeric --stage seeds --local --no-llm [--schemes 6] [--top 6]`。`calibrate` 用基准种子校准估计节点的 `area_scale`、`delay_scale`（写到 `fp_alu_cmp.numeric.cal.yaml`），`numeric` 在每个共享方案下跑 `fp_alu_cmp.numeric.yaml` 并由 `chialu.front_seeds` 取前沿写 `discovered.json`，`seeds` 渲染并评估基准与前沿方案到 `/tmp/a3eval/pipe_fpc/seeds/`。`--schemes 0` 是消融"共享方案与数值前沿作为种子"的开关。
2. 无模型参考：`python3 -m chialu.prune targets/eval/fp_alu_cmp.yaml --best delay --out /tmp/a3eval/fp_alu_cmp.best.yaml && adir seeds /tmp/a3eval/fp_alu_cmp.best.yaml --run-dir /tmp/a3eval/fpc_best --local`，得到 `/tmp/a3eval/fpc_best/seeds/baseline/program.sv`。
3. 时钟扫描（在 `$A3`）：`python3 sweeps/clock_sweep.py --seeds /tmp/a3eval/fpc/seeds --top alu_core --name fp_alu_cmp --out runs/sweeps --workers <workers> --extra prune_best_delay=/tmp/a3eval/fpc_best/seeds/baseline/program.sv --abc map --dmin <d_min>`。`--dmin` 是参考设计的最小延时（ps），目标是它的 1.0、1.25、1.5、2.5 倍取整到 100 ps；不给 `--dmin` 也不给 `--clocks` 时用集合在紧目标（`--tight 300`）下达到的最小延时。`--abc map` 用经典映射器 `+strash;dch -f;map -D {clock_ps};topo;stime`，它对目标有响应；默认 `nf` 是流程自己的 `&nf` 加缓冲尾部，对目标无响应（一个设计一个点）。老主机上 fp_alu_cmp 一次扫描 411 s（`nf`）、562 s（`map`）。
4. 产物：`runs/sweeps/fp_alu_cmp.json` 与 `.md`（`--abc map` 时为 `fp_alu_cmp.map.json` / `.md`）。
5. 验收：每个种子在每个目标下有 `area_um2`、`abc_delay_ps`、`cells`，紧目标一列给出最小延时。
6. 表格格：第二层行（每个方案一行、`prune_best_delay` 一行）的四个时钟列与最小延时列。

#### 7.3.5 参考行：FPnew、HardFloat、TransDot 的时钟扫描

1. 文本：第 5.4 节的 `runs/fpnew/fpnew_merged_alu_core.sv`、`fpnew_merged_bare.sv`（再以 `--point PARALLEL` 得 `fpnew_parallel_*`）、`runs/hardfloat/alu_core.v`、`runs/transdot/transdot_merged_alu_core.sv`。
2. 最小延时：`python3 baselines/fpnew/build.py --point MERGED PARALLEL --tight 300 --out runs/fpnew` 在紧目标下综合；HardFloat 与 TransDot 用 `clock_sweep.py` 的 `--extra`。四个 `d_min` 中最小的一个定四个目标（第 7.3.4 节第 3 步）。
3. 四个目标下的面积：`python3 sweeps/clock_sweep.py --seeds /tmp/a3eval/fpc/seeds --only baseline --top alu_core --name refs --out runs/sweeps --workers <workers> --abc map --dmin <d_min> --extra FPnew_MERGED=runs/fpnew/fpnew_merged_alu_core.sv FPnew_MERGED_bare=runs/fpnew/fpnew_merged_bare.sv FPnew_PARALLEL=runs/fpnew/fpnew_parallel_alu_core.sv FPnew_PARALLEL_bare=runs/fpnew/fpnew_parallel_bare.sv HardFloat=runs/hardfloat/alu_core.v TransDot_noDP=runs/transdot/transdot_merged_alu_core.sv`。
4. 同一命令不带 `--abc map` 再跑一次得 `&nf` 的单点，两组数都进表并注明映射器（第 9 节的决定）。
5. 验收：每个设计四个目标各一个点加最小延时；包装开销列是带译码的包装与裸设计之差。
6. 表格格：表脚的参考行。2026-09-17 之前测得的数（`docs/plan.md` 表中 FPnew MERGED 4590.4 / 5650、HardFloat 5340.2 / 4087 等）在缓冲尾部与 slang 前端之前，不与新数同列。

#### 7.3.6 chiALU 绑定到参考结构的点

`targets/eval/fp_alu_cmp_fpnew.yaml` 与 `fp_alu_cmp_hardfloat.yaml` 的基准种子是 chiALU 按 FPnew、HardFloat 的槽选择渲染的单元，`docs/coverage-gap-plan.md` 在 8,000 ps 下记录 FPnew 绑定 6,510.9 ps / 6,544.7 um2、HardFloat 绑定 4,027.1 ps / 5,928.3 um2（`x_form: guard_round_sticky`）。它们以 `adir seeds --local` 渲染后放进 7.3.4 节的扫描（`--extra chialu_fpnew=<program.sv>`），在表中作为 chiALU 点而非方法行。

### 7.4 第二个实验：从 FPnew 的 RTL 出发

计划第 4 节：每个方法从手写设计而非生成种子出发，FPnew 包装的 RTL 是种子程序，声明为空，chiALU 以自由算子加知识卡与时序源运行，与通用后端和朴素循环同预算比较。

* 朴素循环行可以直接跑：`python3 harness/plain_loop.py targets/eval/fp_alu_cmp.yaml --seed baselines/fpnew/fpnew_alu_core.sv --fpnew-point MERGED --agent opencode --provider google-vertex --model gemini-3.1-pro-preview --effort medium --calls 200 --out runs/plain/fpnew`。种子由 `baselines/fpnew/build.py` 的 `joined` 与 CVFPU 源拼接。种子本身在 `uf_after_round` 类上失 16 个角向量，所以在第一个候选通过之前父程序一直是种子；`--synth-infeasible` 让不通过一致性的候选也综合（老主机种子 4,764.3 / 4,466.0）。老主机冒烟：一次调用在 1,207 s 停滞，留下一个失 51 个向量的部分编辑。
* ADIR 的行（chiALU 自由算子、三个通用后端）在 `c1d0251` 没有现成运行文件。ADIR 支持 `search.seeds.files: [<路径>]` 作为文件种子（`docs/design.md` 8.1）；会话起草 `targets/eval/fp_alu_cmp_fpnew_seed.yaml`（`seeds.generated: []`、`seeds.files: [../../../runs/fpnew/fpnew_merged_alu_core.sv]` 或绝对路径、`operator: [free]`、`declaration` 节点与 `review` 节点及其约束去掉、`synth_unit` 去掉），用 `adir check` 与 `adir seeds --local` 验证种子加载与评估，然后把草稿交给用户确认后再跑。这是第 9 节的待决事项。

### 7.5 Table B：点积单元

Table B 冻结为 TransDot DP 路径的每个模式一个行集（计划第 4 节，`tables/table_b.md`）。

| 行集 | 种子 | 函数 | 种子合同 | 参考行 |
| --- | --- | --- | --- | --- |
| fp16 | `targets/eval/vec_dot_acc_cmp_fp16.yaml`（加三个 `.free_*`） | 两个 fp16 乘积加 fp32 加数入 fp32 | `fused`（精确 281 位帧） | TransDot DP（`baselines/transdot/transdot_dot_core_fp16.sv`）、TransDot no-DP FMA 级联（`baselines/transdot_no_dp/transdot_no_dp_dot_core_fp16.sv`）、HardFloat `MulAddRecFN` 级联（`baselines/hardfloat_dot/`，两项） |
| fp8 | `targets/eval/vec_dot_acc_cmp_fp8.yaml`（加三个 `.free_*`） | 四个 fp8e5m2 乘积加 fp32 加数入 fp32 | `fused`，ulp 为 0 | 同上的 fp8 版本，HardFloat 四项 |

chiALU 的点：`_td` 绑定 TransDot 的槽选择（`multi_term_fused_dot`、`pairwise_difference_reuse`、`segmented_grid` 6 位 4 段乘法器、`lzc_after_add`、`barrel_mux_tree`、`increment_adder`），`_tdw` 再加 `core.window_bits: 76`（TransDot 的 `3p + 4` 归约字）。

参考行与 chiALU 点已在 2026-09-19 于 chiALU `aa4a73e` 测得（nangate45，medium，40,000 ps，`&nf` 单点）：

| 行集 | 设计 | 合同 | 面积 um2 | 延时 ps | cells | 一致性（fused） | max ulp | mean ulp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fp16 | TransDot DP | fused，76 位窗口 | 6,045.9 | 6,621.1 | 5,270 | FAIL 160/3,156（2 `value`，158 `nan_expected`） | 1.0 | 0.0007 |
| fp16 | TransDot no-DP FMA 级联 | sequential | 8,052.4 | 9,802.5 | 6,950 | FAIL 96/3,156 | 6.0 | 0.0326 |
| fp16 | HardFloat 级联 | sequential | 7,797.0 | 8,821.6 | 6,726 | FAIL 96/3,156 | 6.0 | 0.0326 |
| fp16 | chiALU 种子 | fused | 15,771.9 | 9,639.6 | 14,037 | PASS | 0 | 0 |
| fp16 | chiALU `_td` | fused | 21,925.8 | 12,047.4 | 19,267 | PASS | 0 | 0 |
| fp16 | chiALU `_tdw` | fused，76 位窗口带 sticky | 11,484.0 | 10,834.0 | 10,377 | PASS | 0 | 0 |
| fp8 | TransDot DP | window | 4,969.1 | 6,662.4 | 4,326 | FAIL 1,621/3,153 | 83,886,080 | 384,882 |
| fp8 | TransDot no-DP FMA 级联 | sequential | 11,764.9 | 19,360.0 | 9,912 | FAIL 87/3,153 | 8,388,608 | 5,362.6 |
| fp8 | HardFloat 级联 | sequential | 11,009.2 | 16,153.3 | 9,487 | FAIL 87/3,153 | 8,388,608 | 5,362.6 |
| fp8 | chiALU 种子 | fused | 13,284.6 | 7,942.3 | 10,908 | PASS | 0 | 0 |
| fp8 | chiALU `_td` | fused | 25,735.0 | 11,740.1 | 22,588 | PASS | 0 | 0 |
| fp8 | chiALU `_tdw` | fused，76 位窗口带 sticky | 12,400.9 | 10,704.9 | 11,217 | PASS | 0 | 0 |

重现参考行（在 `$A3`，需要第 5.4 节的 `tdot_comb.py` 补丁已打）：

```
python3 baselines/transdot/build_dp.py --row fp16 fp8 --no-synth --out runs/tableb/transdot_dp
python3 baselines/transdot_no_dp/build.py --no-synth --out runs/tableb/transdot_no_dp
SBT=$HOME/tools/sbt/bin/sbt bash baselines/hardfloat_dot/build.sh runs/tableb/hardfloat_dot
python3 sweeps/tableb.py --out runs/tableb --n-random 3000 --clock 40000
python3 sweeps/tableb.py --out runs/tableb --table --details
```

`sweeps/tableb.py` 对每个（设计，行）跑 `chialu.eda.lint`、种子自己的一致性门（`verify.n_random` 3000 加角集）、`baselines/ulp_error.py`、`synth_ppa`，每个（设计，行）写一个 JSON（键 `chars`、`conformance`、`contract`、`design`, `lint`、`modules`、`row`、`seconds`、`synth`、`ulp`）与 `summary.json`；`--table` 打印 markdown 行。验收：与上表一致（chiALU 的数在 `c1d0251` 可能与 `aa4a73e` 略有不同，记录差异）。单个设计的 ulp 列：`python3 baselines/ulp_error.py --target $CHIALU/targets/eval/vec_dot_acc_cmp_fp16.yaml --rtl runs/tableb/transdot_dp/transdot_dp_dot_core_fp16.sv --n-random 3000`。

ulp 列的定义（`baselines/ulp_error.py`）：正规参考值的 ulp 是 `2^(e - 23)`，零或次正规参考值取 `2^-149`；误差是 `|got - ref| / ulp`；特殊结果归类（`nan_expected`、`inf_expected`、`nan_got`、`inf_got`），`zero_sign` 是误差 0 的单独类；正确舍入的设计每个向量得 0；`ulp_vs_exact` 是对精确有理点积的误差，正确舍入的设计至多 0.5。

方法行：对 `vec_dot_acc_cmp_fp16.yaml`、`vec_dot_acc_cmp_fp8.yaml` 各自重复第 7.3.1 到 7.3.3 节（chiALU 完整、三个 `.free_*`、朴素循环 `harness/plain_loop.py targets/eval/vec_dot_acc_cmp_fp16.yaml ...`），表格格是每个行集的方法行。点积行只用 `&nf`（经典映射器在这个种子上慢两到三倍且更紧的目标更差）。

行上声明的两个差异不计为失配：TransDot 两个 DP 模式丢上层 lane 的特殊值（158 与 529 个向量）；两个级联在精确抵消时给 +0 而 chiALU 的顺序参考保留首项符号（1 与 3 个向量，`zero_sign`）。

### 7.6 消融矩阵

每个消融从比较目标的完整配置去掉一个做法。开关列是运行文件键（改在 `make_targets.py` 或复制的运行文件里）。

| 做法 | 开关 | 观测量 | 目标与重复 |
| --- | --- | --- | --- |
| 族库按构造实现声明的族 | `realization: {fixed: behavioral}`（种子全部渲染成行为文本，菜单去掉 `[library]`；`docs/plan.md` 第 10 项记录 int_subword_alu 的行为基准 5087.8 um2 / 1446 ps，比库基准 5544.5 / 1949 两轴都小；该运行同时固定 `core.subword.family: replicated_lanes`；`review.agree` 约束去留由设计决定，见第 9 节） | 可行比例、`review.agree`、达到第二层前沿的调用数 | 三个比较目标，各三次 |
| 提示中的知识卡 | `knowledge_depth: cards` / `index` / `path`；第四档：空知识目录并从 `prompts.sources` 去掉 `chialu_families` | 声明族的分布、超体积 | 三个比较目标，各三次 |
| 综合数据库作为时序模型 | 从 `prompts.sources` 去掉 `chialu_timing`；`chialu.prune --threshold 0.10` 用与不用 | 超过 `clock_ps` 的候选比例、到最终超体积的调用数 | 三个比较目标，各三次 |
| 共享方案与数值前沿作为种子 | `--schemes 0`（只有未共享的结构集）与仅 baseline 种子；去掉 `rank.prior` | 超体积、前沿上不同方案数 | 三个比较目标，各三次 |
| 结构化声明与重规划 | `operator: [free]` 且无 `VAR` / `STRUCTURE` 行；`search.replan: false`（ADIR `7b2f2e5` 起支持）使族变化不重渲染 | 改族的候选中通过一致性的比例 | 三个比较目标，各三次 |
| 审查节点 | 去掉约束 `review.agree >= 1.0` | 文本未实现声明族的比例，搜索是否利用它 | `fp_alu_cmp`，两次 |
| 门级筛选 | 去掉 `synth_unit` 的 `when`（`yosys_stat.cells le 2.0 * seed`）与 `synth_ppa` 的 `when`（`synth_unit.area_um2 le 1.2 * seed`） | 每个可行候选的综合分钟数 | `fp_alu_cmp`，两次 |
| 提示算子与战术 | 一次一个 `operator` 值；`tactics.sources: []`；`member_focus: none` | 每次模型调用的改进 | `fp_alu_cmp`，两次 |

三个比较目标是 ALU（`fp_alu_cmp`）、点积单元、`int_subword_alu`（整数对照）；点积用混合文件还是两个单模式种子见第 9 节。研究的核心是二乘二：库开、模型关是 `smac` 或 `random` 后端在声明空间上（`adir run <文件> --backend smac`）；库关、模型开是通用代码进化行；两者都关是第二层种子；第四个点 `chialu.prune --best delay` 不需要搜索。每条曲线对模型调用数而非迭代数作图。

### 7.7 预算与重复次数

计划第 7 节给出的数如下。

* 模型：每个方法行、每个消融都用 `gemini-3.1-pro-preview`，opencode 的 `google-vertex` 提供商，`effort: medium`（opencode 的 `--variant`）。
* 每次运行 200 次调用（`budget.llm_calls`），20 个迭代；求解与指导调用 `timeout_s: 1200`、`retries: 2`（一次 ADIR 调用最多两次尝试；协议按尝试计数）；审查每候选至多 3 次调用；`budget.wall_hours: 12`。
* 并行：运行内 `parallel: 2`，同时在飞至多八个运行；`opencode_creds: 16` 是这个上限的来源。
* 规模：第 4 到 6 节约 30 个配置，三次重复，约 90 次运行，约 18,000 次模型调用（RTLScout 对不在内）。
* 重复：方法行与前五个消融各三次，后三个消融各两次；表格给中位数与范围，配置间的差按目标与种子配对。
* 风险：停滞的求解尝试计入预算，完成率接近实测值时墙钟时间约乘四。第一次全预算运行报告每个配置的完成率。

`docs/plan.md` 第 14 项把"模型、每次运行的调用数、跨运行并行度"记为 open；本文档按计划第 7 节的数执行，用户可在第 9 节改。

### 7.8 每次运行的记录与表格装配

每次运行结束后会话在 `runs/notes.md` 记：运行文件路径与其 sha256、chiALU 提交、数据库 `manifest.json` 的 `tool_hash` 与 `liberty_hash`、模型 id、预算、开始与结束时间、`summary.json` 的全部计数器、停滞次数（ADIR 运行从 `run.log` 里的 `Timeout on attempt` 行数；朴素循环从 `summary.json` 的 `stalled`）、`results_db.jsonl` 行数、可行比例、前沿点、当时的机器参数。

归档记录的字段（`harness/README.md`，两种归档同形）如下。

| 字段 | ADIR 归档 | 朴素循环 |
| --- | --- | --- |
| `run`、`candidate_id`、`parent_id`、`seed_name`、`is_seed` | 运行名、`seed:<名>` 或 12 位十六进制 id、父 id | 相同 |
| `iteration` | 后端的迭代 | 调用序号；种子为 `null` |
| `unit_id`、`space_hash`、`evaluator_hash`、`search_hash` | 实例哈希 | 前三个相同；`search_hash` 是代理规格、预算、阶段的哈希 |
| `model`、`operator`、`prompt_config`、`tactic_id`、`instruction_id` | 组合器的边车 | 模型 id、`plain_loop`、`{agent, provider, effort, loop: plain}`、`null`、`null` |
| `declarations` | `VAR` 行与 `STRUCTURE` 行 | `{vars: {}, lines: [], verified: null}` |
| `constraints` | 每个运行文件约束一行 | 三行（`lint.ok`、`conformance.pass`、`synth_ppa.abc_delay_ps`） |
| `measurements` | `{节点: {value, node_hash}}` | 相同，`node_hash` 为 `null` |
| `skipped`、`hard_fail`、`feasible`、`goal_values`、`fidelity_level`、`score` | 来自 `adir.metrics` | 相同函数 |
| `touched`、`sub`、`decision` | 组合器的 | `[]`、`[]`、`pending` |
| `source_sha256`、`source_path` | 程序 | 相同 |
| `cost.seconds`、`cost.node_calls`、`cost.cache_hits` | 评估 | 相同 |
| `cost.synth_seconds`、`cost.llm_calls`、`cost.llm_wall_s`、`cost.stalled`、`cost.input_tokens`、`cost.output_tokens`、`cost.reasoning_tokens`、`cost.cache_read`、`cost.cache_write`、`cost.cost_usd`、`cost.num_turns` | 无（token 总数在 `summary.json`） | 每候选一份 |
| `feedback`、`stderr` | 反馈表达式 | 相同 |
| `call`、`status`、`session_id` | 无 | 调用序号、`ok` / `stalled` / `failed` / `no_program`、会话 id |

Table A 从两种归档读 `feasible`、`goal_values[0]`（面积）、`goal_values[1]`（延时）、`measurements.synth_ppa.value.cells`、`call`、`cost.synth_seconds`、`cost.*_tokens`；chiALU 运行的调用序号来自 `prompts/` 的时间戳顺序，token 来自 `summary.json`。

表格脚本：a3eval 的 `tables/` 只有 `table_b.md` 与 `table_b/*.json`，没有 Table A 的产出。chiALU 的 `eval/tables/make_table.py` 计算 Table A 的方法行与图（`python3 eval/tables/make_table.py --out eval/tables/out --method chiALU=run/fp_alu_cmp/results_db.jsonl --method best_of_n=run/fp_alu_cmp.free_best_of_n/results_db.jsonl --method plain_loop=$A3/runs/plain/fp_alu_cmp/results_db.jsonl [--seeds <归档>] [--reference FPnew=<面积>,<延时>] [--clock 8000]`）：方法行的前沿、相对种子的超体积（参考点是种子面积与时钟围成的盒子，`docs/plan.md` 第 13 项的修正）、最佳可行面积、最小延时、可行比例、记录数、到 95% 超体积的调用数；`--seeds` 给第二层行，`--reference` 给参考行。会话先在一次冒烟运行的归档上跑它，确认每列都算出来，再补它没有的列（每个时钟目标下的最佳可行面积、综合分钟数、token 数、四个时钟列的 `map -D` 数），把结果写到 `$A3/tables/table_a.md`，并把用到的归档路径与命令写在文件末尾，与 `table_b.md` 同式。

## 8. 已知故障与处理

* 磁盘：`~/.cache/chialu/sim_build`（`CHIALU_SIM_BUILD_CACHE` 可改位置）从不淘汰，老主机涨到 26 到 32 GB；`df -h ~` 超过 90% 时 `rm -rf ~/.cache/chialu/sim_build`，下一次一致性构建重建它。pytest 的临时树用 `-o tmp_path_retention_policy=none`。Ray 的会话目录用 `RAY_TMPDIR` 放到家目录。运行目录 `run/<名字>/` 含每次调用的知识库副本，一次 200 调用的运行以 GB 计；结束后可删 `run/<名字>/agent/*/knowledge`。
* 内存：`chialu.profile --jobs 6` 在 281 位点积上到 22 GB；`synthdb build` 靠 `--wide-jobs` 与 `CHIALU_MEM_FLOOR_MB`（6,144）闸门；pytest 的 `-n` 按 8 GB 一个 worker 取；`MemAvailable` 低于 4 GB 时降一档。
* 在运行中的 pytest 下同步源码树：pytest 的 worker 在导入时读源码，之后再改文件会让后面的用例混用新旧代码（chiALU 的 `verification-decisions.md` 记录过导入旧代码却哈希到新文件的报告）。同步（`git pull`、`git checkout`、rsync）只在没有 pytest、`adir run`、`synthdb build` 在跑的时候做，做完重跑受影响的套件。
* `read_slang` 的严格性：slang 对超出操作数范围的选择比 sv2v 严格，TransDot 的多格式代码在 generate 条件永不取的分支里有这种选择。`baselines/transdot/build.py` 与 `build_dp.py` 给 `read_slang` 传 `-Wno-range-oob -Wno-index-oob`；`baselines/transdot_no_dp/build.py` 在拼接文本里用 `` `pragma diagnostic ignore="-Wrange-oob" `` 与 `-Windex-oob`。抑制只在包装目录里，不进参考设计，也不进 chiALU 的流程（`chialu/eda.py` 的 `read_slang` 不带 `-Wno`），且被抑制的网表必须先过一致性门。
* 故障注入台的构建上界：通用台架给核心的每个 net 注入一个位点，Verilator 构建随 net 数增长，`chialu/verify/simulate.py` 给构建 900 s（`compile_timeout`）；Verilator 的前端是单线程的，`CHIALU_VERILATOR_JOBS` 只加速 C++ 编译。约 6,600 个 net 以上的带校验器目标超时；`fp_fma_alu` 为此每个模式只留一个 lane（`docs/issues.md`）。目标套件里 `-n 4` 配两个作业让 `mixed_cvt_alu` 超时，`-n 3` 配四个通过。
* opencode 停滞：约三分之一的求解尝试在 1,200 s 处停滞，CHIA 的节点对超时的尝试不返回会话、应答与用量。朴素循环自己从会话库恢复（`opencode session list --format json` 按调用目录找会话，`opencode export <id>` 取消息、token 与转录，`call.json` 标 `recovered: true`）。ADIR 运行的 `summary.json` 不含停滞尝试的 token；需要精确 token 时会话按 `agent/` 目录名对 `opencode session list --format json` 的 `directory` 字段做同样的恢复，并把方法写进 `runs/notes.md`。停滞尝试按协议计入预算。
* Vertex 429：`RESOURCE_EXHAUSTED` 在调用间轮转出现，`gemini-3.1-pro-preview` 的配额是每分钟 250 次请求，不是耗尽；`retries: 2` 让 ADIR 重试一次。不因 429 换区域或模型（`gemini-3.8-flash` 曾因每个会话首个请求即 429 且项目配额里没有它的每分钟请求项而被弃用；`us-central1`、`us-east5` 与 `global` 一样）。
* `approx_alu` 的 xfail：`tests/test_targets.py` 把 `approx_alu` 的一致性标为 xfail（"the approximate baseline misses its own mred budget; pre-existing"）。
* `seed_selection_selftest` 的失败：整数补码模式选 `end_around_carry` 时 `validate_pins` 把族自己的 `modulus_value` 判为 inactive，`docs/issues.md` 记为 open、pre-existing（2026-09-18，在 `be62c54` 也复现）。它不阻塞评测。
* `&nf -D` 无效：流程的 `&nf` 在这个 ABC 里不响应延时目标，一个设计一个点；"每个时钟目标下的面积"列用 `clock_sweep.py --abc map`。两个映射器在同一设计上给出不同点（int_subword 基准 5,544.5 / 1,949 对 5,632.0 / 2,154），表格注明映射器。
* 老主机上 `ccache`：`CHIALU_OBJCACHE` 未设时 Verilator 构建不用对象缓存；设了 `ccache` 时 `simulate.py` 自己补 `CCACHE_SLOPPINESS`。不要在环境里设 `OBJCACHE=ccache`。
* `chia up` 需要本机到自己的免密 ssh（`bash --login` 经 ssh 到 `${THIS_MACHINE}`）；`ulimit -n 65536` 避免 Ray 的文件描述符耗尽。
* 数值阶段文件（`*.numeric.yaml`）的种子是声明块而非 RTL，目标套件对它们跳过 RTL 级用例，这是预期的 skip。
* TransDot DP 的三个 `_qq` 寄存器级不受 `NumPipeRegs` 控制；`baselines/transdot/tdot_comb.py` 把它们放到 `` `ifdef COMBINATIONAL `` 下。没打补丁时 DP 包装以拴住的时钟回答零。
* 2026-09-17 之前测得的所有 PPA 数（`docs/plan.md` 的大部分表）在缓冲尾部与 slang 前端之前，不与之后的数同列。

## 9. 需要用户决定的事项

每项给出计划或仓库文档中的选项；会话不替用户选。

1. 模型与每次运行的预算。计划第 7 节：`gemini-3.1-pro-preview` 经 `google-vertex`，每次运行 200 次调用、20 个迭代；`docs/plan.md` 第 14 项把它记为 open。选项：按计划；或减调用数（100）以换取更多重复；或换模型（运行文件与 `make_targets.py` 的 `MODEL` 同改）。
2. 重复次数。计划：方法行与前五个消融三次，后三个消融两次，约 90 次运行、18,000 次调用，停滞使墙钟约乘四。选项：按计划；或先每配置一次出第一版表格再补重复。
3. NaN 的 invalid 规则。`evaluation-plan.md` 第 8 节第 0 项把 IEEE 规则（仅 sNaN 操作数置 invalid）记为已冻结并绑定在 `fp_alu_cmp.yaml`（`minmax_nan: number`、`tininess: after`、`nan_payload: canonical`、`flag_scope: per_operation`）；TestFloat 台架在该规则下全部一致。仍要确认的是表格如何对待 FPnew 在 `fmin`/`fmax` 上对 sNaN 置 invalid 而 chiALU 的 `minmax_nan: number` 不置：作为行上声明的差异（计划第 7 节的规则），或改绑选项使两边一致。
4. "每个时钟目标下的面积"列的映射器。`&nf` 加缓冲尾部一个设计一个点，是流程与数据库的映射器；`map -D` 对目标有响应但在浮点种子上多 3 到 23% 延时、少 3 到 8% 面积，会翻转 `front_3` 在 8,000 ps 下的可行性，在点积种子上慢两到三倍。计划第 3 节：两个数都进表并注明映射器，点积行只用 `&nf`；`docs/plan.md` 的结论是"没有支持切换的证据"。选项：按计划两列并列；或只报 `&nf` 单点并去掉四个时钟列。
5. HardFloat 的 fp8 加法器缺口。`AddRecFN` 与 `MulAddRecFN` 在 (5, 3) 不能例化，包装让 fp8 的 fadd/fsub 返回零，面积不是完整单元的。选项：按计划在行上声明并保留其面积；或把 HardFloat 行的 fp8 列标为不适用；或从 fp16 的 `AddRecFN` 在边界上做 fp8 到 fp16 的转换补一个 fp8 加法器并把转换计入包装开销。
6. `fma_contract: sequential` 下的级联。`bridge_fma` 的 `composition_style: cascade_mul_then_add` 在 `fused` 下被拒绝（它先舍入乘积），在 `sequential` 下也被拒绝（`docs/coverage-gap-plan.md`：它的乘积舍入是一个固定模式而非模式自己的舍入），顺序合同由分离的乘法器加加法器计算。选项：维持拒绝；或让级联在 `sequential` 下接受模式的舍入并进入槽。这影响消融中 `fp_fma` 槽的菜单。
7. `chialu/extract.py` 的词表是否加入 `fp_fma_space`。`render_vocab` 列出 `_named_spaces()` 的空间（`cpa_space`、`incrementer_space`、`comparator_space`、`mul_space`、`div_space`、`fp_add_space`、`fp_mul_space` 等），没有 `fp_spaces.fp_fma_space`；加入后每个抽取提示的前缀都变，语料的缓存前缀失效。选项：加入并重跑抽取；或维持现状直到下一轮语料更新。
8. 消融的点积目标。计划第 6 节说三个比较目标是 ALU、点积单元与 `int_subword_alu`；Table B 冻结后点积有混合文件 `vec_dot_acc_cmp.yaml` 与两个单模式种子。选项：消融在混合文件上跑；或在两个单模式种子上各跑（运行数翻倍）；或只在 fp16 行集上跑。
9. 行为文本消融中的 `review.agree` 约束。`realization: {fixed: behavioral}` 下审查只看文本，计划说"去留由设计决定"。选项：保留（审查判断行为文本是否实现声明族）；或去掉（与"审查节点"消融合并观察）。
10. 第二个实验的 ADIR 行。`c1d0251` 没有以 FPnew RTL 为文件种子的运行文件（第 7.4 节）；会话起草后由用户确认字段（`seeds.files`、去掉声明与审查、`operator: [free]`）与是否保留 `synth_unit`。
11. TransDot 的 ALU 级 no-DP 点。`docs/plan.md` 第 8 项：它在 `read_slang` 下能展平，Table A 行尚未测量，一致性判决未记录。选项：测量并按其失配类别决定入表；或只在 Table B 保留 TransDot。
12. RTLScout 与 asap7。任务把 RTLScout 排除；`docs/plan.md` 记 asap7 因此未配置。确认排除保持不变，则计划第 5 节与 `pdk/asap7.yaml` 都不在本轮工作中。
13. `synthdb build` 的宽度集合。老主机最后一次完整尝试用 `--widths dense --seeds`（28,563 个点），`dbbuild.sh` 用 `--widths 8,16,32 --seeds`。选项：稠密网格（覆盖 `prune` 与时序提示的插值需求，耗时未知）；或默认网格 `8,16,24,32,48,64` 加 `--seeds`（先出可用数据库）后再补稠密。
