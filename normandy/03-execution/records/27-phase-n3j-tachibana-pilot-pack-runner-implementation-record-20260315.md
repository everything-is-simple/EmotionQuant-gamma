# Phase N3j Tachibana Pilot-Pack Runner Implementation Record

**日期**: `2026-03-15`  
**阶段**: `Normandy / N3j`  
**对象**: `Tachibana pilot-pack runner implementation formal readout`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `N3j / Tachibana pilot-pack runner implementation` 的正式实现结果写死。

这张 record 只回答 5 件事：

1. pilot-pack 的正式 matrix / digest runner 是否已经落文件
2. `E2 cooldown overlay` 是否已经以最小 hook 方式接进现有 BOF 栈
3. `E3 unit regime / experimental segment` 当前落到了哪一层
4. 默认运行路径是否已经对齐三目录纪律
5. 当前已经完成了哪一级验证

---

## 2. Formal Inputs

本卡正式输入固定为：

1. `normandy/03-execution/records/26-phase-n3i-tachibana-pilot-pack-implementation-scaffold-record-20260315.md`
2. `scripts/backtest/run_normandy_tachibana_pilot_pack_matrix.py`
3. `scripts/backtest/run_normandy_tachibana_pilot_pack_digest.py`
4. `src/backtest/normandy_tachibana_pilot_pack.py`
5. `src/backtest/engine.py`
6. `src/config.py`
7. `tests/unit/backtest/test_normandy_tachibana_pilot_pack.py`
8. `tests/unit/core/test_config.py`
9. `normandy/03-execution/evidence/normandy_tachibana_pilot_pack_dtt_bof_control_no_irs_no_mss_tachibana_pilot_pack_w20260203_20260210_t033215__tachibana_pilot_pack_matrix.json`
10. `normandy/03-execution/evidence/normandy_tachibana_pilot_pack_digest_dtt_bof_control_no_irs_no_mss_tachibana_pilot_pack_w20260203_20260210_t033313__tachibana_pilot_pack_digest.json`

---

## 3. 正式裁决

`N3j` 的正式裁决固定为：

1. pilot-pack 的正式 runner 已落成为：
   `run_normandy_tachibana_pilot_pack_matrix.py + run_normandy_tachibana_pilot_pack_digest.py`
2. `E2 cooldown overlay` 已按 `N3i` 约束落成为：
   `run_backtest() -> optional signal_filter hook -> SameCodeCooldownSignalFilter`
3. `E3 unit regime / experimental segment` 第一轮已落到：
   `scenario + matrix payload + digest payload`
4. 默认路径纪律已对齐到：
   `G:\\EmotionQuant-gamma + G:\\EmotionQuant_data + G:\\EmotionQuant-temp`
5. 当前验证级别固定为：
   `compile + unit regression + short-window smoke matrix/digest`

---

## 4. 为什么这次实现是合格的 pilot implementation

### 4.1 runner 已经是 Normandy 自有入口，而不是临时手抄命令

当前 pilot-pack 已不再依赖口头 runner 约定，原因固定为：

1. matrix 入口已经有正式脚本
2. digest 入口已经有正式脚本
3. scenario labels、side references、working DB 与 output 路径都已有显式参数
4. 输出物已进入 `normandy/03-execution/evidence/`

### 4.2 cooldown 没有错误地下沉为 Broker / RiskManager 改写

这次实现继续符合 `N3i` 的冻结前提，原因固定为：

1. `RiskManager` 没有被拿来伪装成 cooldown 引擎
2. `ALREADY_HOLDING` 的既有限制没有被偷偷绕开
3. hook 只发生在 signal 进入 Broker 前
4. `same-side add-on BUY`、`probe -> mother promotion`、`reduce -> re-add` 仍然没有被偷带进来

### 4.3 三目录纪律已经从文档要求变成代码 fallback

当前 runner 默认路径已经不再掉回用户目录，原因固定为：

1. `src/config.py` 的空白路径 fallback 已优先对齐仓库盘符下的 `EmotionQuant_data / EmotionQuant-temp`
2. `.env.example` 已同步说明该行为
3. `tests/unit/core/test_config.py` 已把该纪律写成回归测试

---

## 5. 当前验证结果

当前已经完成的验证固定为：

1. `python -m py_compile` 通过：
   `src/config.py`, `src/backtest/engine.py`, `src/backtest/normandy_tachibana_pilot_pack.py`, 两个 runner script
2. `pytest tests/unit/core/test_config.py` 通过
3. `pytest tests/unit/backtest/test_normandy_tachibana_pilot_pack.py` 通过
4. `2026-02-03 ~ 2026-02-10` 小窗口 smoke matrix 已完成：
   `FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD0`
   `TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD0`
   `FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD2`
   `TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD2`
5. 对应 digest 已落盘并给出：
   `use_normandy_tachibana_pilot_pack_runner`

这里也必须写死当前 smoke 读数限制：

1. 当前短窗口里 `CD2` 没有打出非零 `cooldown_blocked_signal_count`
2. 因此这次验证回答的是“runner / hook / payload 已接通”
3. 它还没有回答“哪一个 cooldown 设置在正式窗口下交出差异性证据”

---

## 6. 当前仍未打开的内容

`N3j` 完成后，以下内容仍然明确未打开：

1. `R1 / probe_entry`
2. `R2 / probe_to_mother_promotion`
3. `R3 / discrete_same_side_add_ladder`
4. `R8 / lock_equivalent_reduce_and_readd`
5. `R9 / reverse_restart_as_new_position`
6. 任何持仓内 add-on BUY
7. 任何把 partial-exit lane 伪装成 sizing lane 补救的做法

---

## 7. 下一张卡

`N3j` 完成后的 next main queue card 固定为：

`N3k / Tachibana pilot-pack formal cooldown matrix`

它只允许回答：

1. `CD0 / CD2 / CD5 / CD10` 在正式窗口下是否产生可解释差异
2. proxy line 与 control line 的 cooldown scorecard 是否出现分化
3. 哪些 cooldown 仍只是“无差异 overlay”，哪些开始形成治理信号

---

## 8. 正式结论

当前 `N3j Tachibana pilot-pack runner implementation` 的正式结论固定为：

1. pilot-pack runner 已经从 implementation scaffold 进入可执行代码
2. `E2` 的 cooldown 已以最小 hook 方式接通
3. `E3` 的 unit-regime / segment 信息已贯穿 payload 层
4. 三目录纪律已进入默认运行路径
5. 下一步应进入正式 cooldown matrix，而不是回到泛化讨论

---

## 9. 一句话结论

`N3j` 已把 Tachibana pilot-pack 从“实现草图”推进成“可运行入口”：runner、hook、payload 与 smoke evidence 都已落下，下一步该做的是把 cooldown family 拉到正式窗口里读差异，而不是再争论 pilot 边界。`
