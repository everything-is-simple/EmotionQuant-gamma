# Phase 9 Gene Promotion Flowchart

**状态**: `Completed`  
**日期**: `2026-03-19`

---

## 1. 用途

这张图只做一件事：

`把 Phase 9A -> 9B -> 9C -> 9D -> 9E -> 9F 的真实推进路径画清楚，明确哪些字段已赢下 isolated round，哪些组合只被冻结未打开 replay，以及为什么当前包级结论是 defer 而不是已 promotion。`

---

## 2. Flowchart

```mermaid
flowchart TD
    A["Phase 9A<br/>Completed<br/>Freeze candidate surface"] --> B1["Phase 9B-1<br/>duration_percentile<br/>Winner<br/>negative filter only"]
    B1 --> B2["Phase 9B-2<br/>wave_role<br/>Completed<br/>retain_sidecar_only"]
    B2 --> B3["Phase 9B-3<br/>reversal_state<br/>Winner<br/>exit-preparation only"]
    B3 --> B4["Phase 9B-4<br/>context_trend_direction_before<br/>Winner<br/>parent-context negative guard"]

    B1 --> C
    B3 --> C
    B4 --> C
    B2 --> S["Sidecar only<br/>wave_role"]:::side

    C["Phase 9C<br/>Completed<br/>Formal combination freeze"]:::freeze

    subgraph P["Frozen Phase 9C Combination Surface"]
        C1["duration_percentile + reversal_state"]:::freeze
        C2["duration_percentile + context_trend_direction_before"]:::freeze
        C3["reversal_state + context_trend_direction_before"]:::freeze
        C4["duration_percentile + reversal_state + context_trend_direction_before"]:::freeze
        X["Explicitly forbidden<br/>wave_role / current_wave_age_band / mirror / conditioning / gene_score"]:::side
    end

    C --> C1
    C --> C2
    C --> C3
    C --> C4
    C --> X

    C --> D["Phase 9C ruling<br/>no combination replay opened<br/>no formal combination winner"]:::decision

    D --> E{"Phase 9D<br/>Current package ruling"}:::decision
    E -.-> F["promote narrow Gene subset"]:::decision
    E -.-> G["retain Gene as sidecar only"]:::decision
    E -->|"Chosen"| H["defer and open a smaller follow-up package"]:::chosen

    H --> I["Phase 9E<br/>duration threshold sweep<br/>Active<br/>p65~p95 step 5"]:::chosen
    I --> J["Freeze truthful duration candidate(s)<br/>or rule out duration runtime promotion"]:::freeze
    J --> K["Phase 9F<br/>frozen combination replay<br/>Planned / blocked-by-17.8"]:::decision
    K --> L["Return to later package ruling<br/>with new evidence"]:::decision

    H --> M["Current truthful runtime<br/>legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only"]:::freeze
    H --> N["Phase 10<br/>blocked-by-Phase-9"]:::side

    classDef win fill:#e8f7ea,stroke:#2d6a4f,color:#1b4332;
    classDef side fill:#fdeaea,stroke:#b42318,color:#7a271a;
    classDef freeze fill:#eaf2ff,stroke:#1d4ed8,color:#1e3a8a;
    classDef decision fill:#fff4e5,stroke:#c2410c,color:#9a3412;
    classDef chosen fill:#e6fffb,stroke:#0f766e,color:#134e4a;

    class B1,B3,B4 win;
```

---

## 3. 读图结论

这张图当前对应的正式结论是：

1. `duration_percentile`、`reversal_state`、`context_trend_direction_before` 都已赢下 isolated round
2. `wave_role` 已完成 isolated validation，但 ruling 是 `retain_sidecar_only`
3. `Phase 9C` 只冻结组合面，没有打开 combination replay
4. `Phase 9C has no formal combination winner`
5. `Phase 9D` 当前选择的是：
   `defer and open a smaller follow-up package`
6. 当前主线仍然是：
   `legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`
7. 当前真实下一步是：
   - `17.8 / duration threshold sweep`
   - 然后 `17.9 / frozen combination replay`
