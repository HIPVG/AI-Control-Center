# Process Consistency smoke review

人間レビュー用。自動採点なし。dry-runはモデル評価結果ではありません。
Run: PCSMOKE-20260921T180546456314Z-1523888f / status: dry_run

## PC-001-C

### Input summary

- Business Unit: TH
- Product: PRD-TH-PAD-00001
- Customer: CUS-0002
- evidence count: 7
- Input: [inputs/PC-001-C.json](inputs/PC-001-C.json)

### Model response

未取得（dry_run）。

### Human review

- [ ] 矛盾・欠落を検出（正常対照は根拠付きで整合を確認）
- [ ] 根拠と業務影響を説明
- [ ] 不明点を捏造しない
- [ ] 追加確認または是正候補を提示（正常時は不要な是正を求めない）

Score:
- detection: /25
- evidence: /25
- grounding: /25
- action: /25
- total: /100

Notes:

### Oracle reference

**以下は人間用であり、MODEL INPUTには含めていない。**

- case_type: "control"
- expected_detection: "提示範囲の対象関係は整合している。根拠を比較して説明し、資料にない異常を主張しない。"
- known_unknowns: ["資料外の別Lot合格在庫の有無", "再検査・特採による追加解放承認の有無"]
- expected_business_impact: "提示範囲では当該不整合に起因する影響は確認されない。未提示の承認や他取引まで正常と保証しない。"
- required_evidence_ids: ["case_qa_releases:CTX-001-QA", "case_released_inventory:CTX-001-STOCK", "case_shipments:CTX-001-SHIP"]

## Pair PC-001

Anomaly: PC-001-A（未選択）
Control: PC-001-C

Human observations:
- anomaly detection:
- false positive on control:
- hallucination:
- useful follow-up:
- notable difference:

