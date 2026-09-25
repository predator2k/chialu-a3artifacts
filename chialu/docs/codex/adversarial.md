# RTL 生成器对抗测试报告

日期：2026-09-24。工作树：`wt/adv`，分支：`rtl-adversarial`；起点 `3508e24`。确认并修复 **6 个生成器缺陷**，每项独立提交。未修改 golden、精度预算、checker 判定或目标向量；未修改训练数据，未推送。

## 结果与边界

本次生成并检查声明的设计共 **2,100 个**，三个目标各 700 个。每个目标先用固定种子 `20260924` 生成 300 个方案，再通过 `Stage.coverage_items` 的 activation path 强制补充 400 个稀有成员方案。全部直接渲染成功、声明有效；未观察到 `realize` 丢弃选择或修复原始不可渲染方案。

从每组中按稀有变量值、父子选择及共享特征贪心选取 80 个，使用原始完整目标向量做整机 conformance，并做 Yosys 结构 lint：

| 目标 | 初始整机检查 | 原始结果 | 每个设计的向量数 |
|---|---:|---|---:|
| `int_subword_alu` | 80 | 75 通过；4 个数值失败；1 个编译超时 | 1,274,226 |
| `fp_alu_cmp` | 80 | 80 通过 | 427,964 |
| `fp_alu_cmp_hf` | 80 | 79 通过；1 个数值失败 | 380,140 |

5 个原始数值失败均已修复，且通过 `adir.cli seeds --local` 的 surrogate evaluation run file 复测声明、lint、conformance。这个本地 run file 只移除综合、review 等与数值复测无关的节点，保留原始验证约束。原始 240 个设计的 lint 均通过，说明这些数值缺陷不会被常规结构检查发现。

共享方案另补 15 个整机检查：整数 7 个、FP 5 个、HF 3 个，全部通过。纠正方案名解析中的 `per_lane` / `per_mode` 下划线后，已覆盖样本方案集合中全部 **112 / 144 / 144** 个共享轴值对；这不是所有深层参数的两两穷举。另复测 HF 的两个 Booth 易受影响路径、FP/HF 的其余融合舍入易受影响路径。九个额外小型整机用例覆盖混合整数/浮点共享及 FMA 合同，均通过。

最终自动测试：`tests/test_adversarial_rtl.py` 的 40 个回归和 `tests/test_mul_elaboration.py` 的 13 个既有 elaboration 用例，**53/53 通过**。此外完成 6 个小位宽 Yosys 等价证明。

## 已确认并修复的缺陷

### 1. 十进制内部 CPA 错把模加法当二进制加法

提交：`438037f` — `fix(rtl): decode modular CPA results in decimal arithmetic`。

`decimal.Mod.lib` 直接调用 `FAM.adder_module`。`bcd_direct_addition.digit_adder` 和 `speculative_decimal_addition.carry_network` 消费普通二进制和/进位，而 EAC 返回模编码。最小整机为两位 BCD 加法；例如旧实现可把 `1 + 9` 算成 `11`，generic-p=3 路径甚至在零输入下产生非法 BCD。两个父族 × 三种模数的 6 个整机用例修复前全失败，修复后全通过。组件入口对这种组合返回 `no_golden`。

修复改用已有 `binary_cpa.adder_module`，保留所选模加法器结构并正确解码。三个主目标没有 BCD 模式，700×3 样本与整数训练集均不涉及此路径；通用 BCD 目标受影响。300 个未涉及路径的完整整数 ALU 渲染逐字节一致。

证据：[`decimal_evidence.json`](measurements/adversarial/decimal_evidence.json)、[`decimal_compatibility.json`](measurements/adversarial/decimal_compatibility.json)。

### 2. Checker 的内部加法器产生大量无故报警

提交：`aa052b7` — `fix(rtl): preserve binary arithmetic in checker CPA slots`。

`alu_checker.slot_add` 同样直接使用模编码结果。`an_code.coded_adder`、`berger.carry_replica`、`parity_prediction_adder.carry_replica` 选择 EAC generic-p=3 时，在 512 个无故障样本中分别出现 **509、442、243** 次误报；同架构 ripple 对照均为零。

修复使用二进制 CPA 包装。整机数据 conformance 和 fault gate 均通过，误报降为零，受测单比特故障覆盖仍为 1.0；未放松 checker。测试显式补齐 checker 的静态库依赖。主整数目标固定 residue checker，另外两个目标不启用 checker，因此本次主目标/训练集无直接影响。300 个未涉及路径的 core/checker 渲染保持一致。

证据：[`checker_evidence.json`](measurements/adversarial/checker_evidence.json)、[`checker_compatibility.json`](measurements/adversarial/checker_compatibility.json)。

### 3. 奇数位宽的二位分组乘法器丢失最高组符号

提交：`fac16fe` — `fix(rtl): sign-extend odd-width grouped multiplier digits`。

`mul.pp_groups2` 用 `base + 1 == w - 1` 识别符号组。奇数位宽时，最后一组由符号位及其扩展位组成，原判断漏掉了这一组，负权系数变成正权。最小有符号 3 位乘法器，`(-1) × (-1)` 得到 `0x31`，应为 `0x01`。

`segmented_grid` 的内部有符号叶子可达 3、5、7 位，故即使目标顶层都是偶数位宽也会触发。原始整数整机 `c00135`、`r0150`、`r0181` 分别有 **15,884、15,869、9,905** 个错误，部分错误仅表现为 overflow flag 错误。修复符号组边界后，三者原始完整向量全部通过。

对 3、5、7 位有符号乘法完成 Yosys 等价证明；无符号及偶数位宽保留对照。400 个渲染中 389 个完全一致，11 个变化均落在受修路径。样本空间影响为整数 **17/700（2.43%）**，两个 FP 目标未检出对应生成路径。

证据：[`grouped_evidence.json`](measurements/adversarial/grouped_evidence.json)、[`grouped_equivalence.json`](measurements/adversarial/grouped_equivalence.json)、[`grouped_compatibility.json`](measurements/adversarial/grouped_compatibility.json)。

### 4. 冗余 Booth 硬倍数的最高分片符号扩展不足

提交：`4ece168` — `fix(rtl): preserve signed top tiles in redundant Booth multiples`。

`booth_recoded_parallel` 的 `partially_redundant` 硬倍数路径按四位分片。radix-8 的最高分片需要至少两位符号空间，radix-16 需要三位；最高残片太短时，3a 及其移位形成的 6a 等带错符号。例：radix-16 有符号 5 位/9 位，以及 radix-8 有符号 2 位/6 位均可触发。

修复只为这些残片补足符号位。`full_extension`、`prevention_constant`、`roorda_compact` 三种输出符号扩展机制均有回归。40 点组件矩阵修复后全通过，另对 radix-8/2 位、radix-16/5 位和 6 位作等价证明。原始整数整机 `c00088` 的 **2,365** 个错误全部消失。400 个完整渲染中 398 个一致，2 个变化对应受修路径。

生成路径命中整数 **4/700（0.57%）**、HF **2/700（0.29%）**、FP 0/700。HF 两个样本修复前后均通过原始向量：命中易受影响内部几何不等于该整机输入一定能激发错误，不能将这些比例当作数值失败率。

证据：[`booth_evidence.json`](measurements/adversarial/booth_evidence.json)、[`booth_equivalence.json`](measurements/adversarial/booth_equivalence.json)、[`booth_hf_evidence.json`](measurements/adversarial/booth_hf_evidence.json)。

### 5. SFU 固定点运算误用模加法结果

提交：`44c7ebc` — `fix(rtl): decode modular CPA results in SFU fixed-point arithmetic`。

`sfu.Net._addsub` 的 Python 求值是普通有符号/无符号定宽加减，RTL 却直接实例化原生模加法器。最小完整例为 fp8e4m3 `exp2`、PWL、EAC generic-p=3。与同一 Net 的逐位求值比较，旧 RTL 的 256 个输入全部失败；与 SFU 整机数学参考比较，最大误差为 **126 ULP**，正常 ripple 对照为 1 ULP。

改用二进制 CPA 后，256 点 Net 比较通过，整机回到与 ripple 相同的 1 ULP；原有 `max_ulp=1` 预算未改变。三种模数均通过回归。300 个不受影响的完整整数 ALU，以及另 300 个使用非模 CPA、不同宽度/符号的 SFU Net，加总 600 个渲染完全一致。

三个主目标均没有 SFU，此缺陷不影响所查整数训练集；通用使用该固定点加减路径的 SFU 架构受影响。另发现当前 Verilator 在 `$finish` 后输出尾行，`sfutest.simulate` 的返回字符串未必是 PASS/FAIL；本次探针重新执行所生成二进制并保留完整 stdout，按独立 PASS 行判定，未把尾行误当成功。

证据：[`sfu_evidence.json`](measurements/adversarial/sfu_evidence.json)、[`sfu_native_compatibility.json`](measurements/adversarial/sfu_native_compatibility.json)。

### 6. 融合 CPA 舍入没有消费 LZA 延迟的一位修正

提交：`74b047c` — `fix(rtl): correct deferred LZA count before fused CPA rounding`。

组合为 `reduced_latency_fma`、`rounding_position=fused_with_cpa_dual_sum`、`normalize_before_add=False`、LZA `compensation_in_rounding`。LZA 允许归一化少移一位，将修正留给舍入器；融合 CPA 已经按未修正位置截取 P 位并标记 ROUNDED，后续普通 rounder 无法恢复丢失精度。

原始 HF `c00354` 有 **239** 个错误。BF16 的 `1 + (-最小 subnormal)` 在 RTZ 下应为 `0x3f7f`，旧结果为 `0x3f7e`。独立简化 BF16 整机也复现 25 个错误。修复在融合舍入选边界之前，以现有归一化结果的最高位补上这一位计数；不替换所选 LZA，也不增加完整 LZC。

简化用例、原始 HF 全向量和官方 CLI 均通过。8 个回归覆盖四种格式、两种负数处理、四种舍入模式、DAZ/FTZ、异常标志及真正 fmadd。400 个未涉及路径的完整 HF 渲染逐字节一致。易受影响的选择组合命中 FP **3/700（0.43%）**、HF **2/700（0.29%）**；这些样本修复后均复测。整数目标及训练集没有浮点路径。

证据：[`fma_evidence.json`](measurements/adversarial/fma_evidence.json)、[`fma_minimal_evidence.json`](measurements/adversarial/fma_minimal_evidence.json)、[`fma_compatibility.json`](measurements/adversarial/fma_compatibility.json)。

## 组件 golden 的盲区与覆盖

[`component_gaps.json`](measurements/adversarial/component_gaps.json) 枚举了已能渲染整机中的组件合同空洞。整数有 **234/700** 个设计至少包含一个被跳过的选择，去重后 279 个模运算嵌套选择；两个 FP 目标的 700 个设计均包含空洞。FP 的主要去重计数为：rounder 1,581、模运算嵌套 1,003、FMA 485、FP multiplier 464、comparator 451、adder 435；HF 对应为 1,580、984、547、467、479、276。这些是槽级合同计数，不是失败数。

实际调用 `run_space_case` 的 40 个代表中，39 个返回 `no_golden`，一个 `separate_multiplier_and_adder` 返回 `unrealized`。因此“组件 selftest 无失败”不足以证明整机正确。本次用整机原始 oracle 覆盖这些组合，没有让 skipped 状态充当通过。

| 指标 | 整数 | FP | HF |
|---|---:|---:|---:|
| 渲染的自然共享方案数 | 144 | 40 | 40 |
| `Stage` 可达 family 变量/成员对覆盖 | 1,219/1,219 | 2,507/2,507 | 2,330/2,330 |
| 全部变量/成员对覆盖 | 7,990/11,268 | 15,720/293,579 | 14,549/291,790 |
| 初始 80 点涉及的不同共享方案数 | 21 | 10 | 14 |
| 补充后共享轴值对覆盖 | 112/112 | 144/144 | 144/144 |

这里“可达”是当前 `Stage` 的 activation/domain 枚举结果，不是全空间形式可达性证明。渲染覆盖不等于数值覆盖；宽整数域、三重以上深层参数组合仍远未穷尽。最初选择器曾把 `per_lane` 的下划线也当分隔，已修正并补测四个整数整机；归档保留原始 80 点选择，避免事后改写实验记录。

三个固定目标没有混合 int/FP 模式，FP 主目标也没有真正 fmadd。额外的九个小型整机用例分别覆盖：三个 intfp 共享边界机制；classic/bridge/独立乘加 × exact/GRS。独立乘加用 sequential 合同，其余用 fused 合同，并检查 DAZ/FTZ 和四种舍入/异常标志。详见归档的 `supplement/summary.json`。

静态审计从 [`direct_module_calls.txt`](measurements/adversarial/direct_module_calls.txt) 出发，追踪二进制、模数、冗余、BCD、符号与进位合同。其余重点路径包括：分区 carry chain 明确拒绝 EAC；`adder_ext` 的叶子域限制；冗余表示通过 `rns_cpa.raw_binary` 解码；整数 ones-complement 使用原生 EAC 的正确合同；FP/乘法/除法中的 CPA 包装。对动态嵌套实际生成的有符号宽度做追踪，而非仅搜索 JSON 中的族名。

## 训练数据与历史前沿

只读扫描：`run/int_subword_alu.surrogate2/surrogate/dataset.jsonl`，SHA-256 为 `7bd6dbc8efb45c19326427125d6f5e83d1a5f927f9a6b774267d922759676e05`。

9,704 条记录中先筛出 4,165 个潜在组合，包含所有 group_bits=2、分段、平方器和冗余硬倍数选择，再实际渲染并追踪内部乘法器的宽度、符号、radix 和分片；没有渲染异常。奇数分组缺陷命中 **145 条（1.49%）**，Booth 缺陷命中 **49 条（0.50%）**，两者不重叠，共 **194 条（2.00%）**。其余四项不涉及这个整数目标。完整名称与内部几何见 [`training_impact.json`](measurements/adversarial/training_impact.json)。这是结构上的易受影响数据，不表示已对每条记录跑过 conformance。

按记录中 feasible 且有面积/延迟的点重算非支配层，第一层 23 条、第二层 31 条，均未命中这两项缺陷。但内部错误 RTL 的 PPA 标签仍不应无条件作为修复后生成器的训练标签：建议将这 194 条隔离并重新生成、验证和测量；本任务没有改写它们。

另扫描 22 个 `discovered.json`，共 110 个记录种子（包括 `front_*`）。97 个能按当前接口重建，未命中六项缺陷相关路径；13 个旧声明不再被当前空间接受，涉及旧 `lane_cpa.block_width`、叶子 family 域和 LZC `output_form=binary_count` 等。**这 13 个是未完成验证，不是安全结论**；没有擅自修复历史计划。名单和源文件摘要见 [`recorded_impact.json`](measurements/adversarial/recorded_impact.json)。本次未扫描历史 LLM 改写后的全部 RTL 个体，故不对它们做无影响承诺。

## 综合、超时与残余风险

对四个完整整数 ALU 做 Nangate45、medium、`repeats=1` 的本地映射：

| 样本 | 面积（µm²） | ABC 延迟（ps） | cells |
|---|---:|---:|---:|
| r0000 | 9,714.852 | 2,271.56 | 8,746 |
| c00088 | 11,070.654 | 2,119.54 | 9,799 |
| c00135 | 7,148.218 | 1,732.82 | 6,241 |
| c00142 | 6,800.024 | 2,443.77 | 5,987 |

四者均成功；日志唯一警告是 ABC 对库中 multi-output cell 的提示，没有发现 undriven、多驱动或锁存器错误。没有出现接近空逻辑的面积坍缩，但四点不足以建立异常检测分布。面积较低的 c00142 仍需数值判定，不能据面积或综合成功推断正确。完整映射记录见 [`area_evidence.json`](measurements/adversarial/area_evidence.json)。

整数 `c00142` 在低并发独立重试中再次超过 Verilator 的 900 秒编译限时；它的声明、Yosys lint 和完整 Nangate45 综合均成功，但尚无数值结论。保留为 **编译性能/工具路径疑点**，没有证据把它定性为算术错误，也未通过增加超时或改变验证门槛来掩盖。原始 RTL 已归档，重试见 [`timeout_retry.json`](measurements/adversarial/timeout_retry.json)。

合并补充用例、修复后官方复测及重试，三个固定目标共涉及 **261 个不同整机设计**：260 个最终通过，1 个编译超时未决；按目标分别为整数 86/87、FP 88/88、HF 86/86。额外的小型 BCD/checker/SFU/FMA/混合模式回归不混入这个分母。

本次所有完成的验证/综合均在本地执行，Verilator 与综合每任务一个工作线程，未运行 LLM/OpenRouter、SSH 或远端任务。面积探针首轮误调带调度装饰器的入口，触发了现有 Ray 地址的连接尝试；连接失败后已终止该进程，改用 `underlying(synth_ppa)` 本地入口。这是执行过程中的偏离，未计作任何有效证据。综合固定 `repeats=1`，没有改动默认 median-of-five 行为。

尚未覆盖全空间，没有证明所有 reachable 组合正确。尤其是深层高阶组合、更多极端位宽、SR/非固定目标格式、历史失效声明，以及未逐条复测的受影响训练记录仍有风险。没有把 `no_golden`、`unrealized` 或超时归类为通过。多个原始失败的诊断文本优先列出 EAC 行为规则，但本次逐步归因表明真正根因也可能是乘法符号或融合舍入，不能仅凭该提示自动封禁族。

## 复现与交付

代码和测试使用英文；报告为中文。六个修复提交分别为 `438037f`、`aa052b7`、`fac16fe`、`4ece168`、`44c7ebc`、`74b047c`。审计脚本、基线计划/RTL/结果压缩归档、原始向量规格和摘要、工具版本、兼容性比较、训练集命中名单均在 [`measurements/adversarial`](measurements/adversarial/README.md)。完整 Verilator 构建留在被忽略的 `scratch/`，不提交大量可再生二进制。

```sh
source measurements/adversarial/env.sh
pytest -q tests/test_adversarial_rtl.py tests/test_mul_elaboration.py \
  --basetemp measurements/adversarial/scratch/pytest_replay
```

完整目标复现命令及归档说明见 [`README.md`](measurements/adversarial/README.md)。
