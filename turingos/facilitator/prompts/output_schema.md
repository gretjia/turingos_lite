# Facilitator Turn JSON Schema

## clarify turn
```json
{
  "turn_type": "clarify",
  "summary": "2-4 line compressed understanding",
  "choices": [
    {"id": "explore", "label": "short label", "hint": "what happens if picked"},
    {"id": "submit", "label": "我理解对了，可以提交", "select_action": "propose"},
    {"id": "other", "label": "其他需求（自行输入）", "input_prompt": "你还有什么其他需求？", "select_action": "freeform"}
  ],
  "proposals": [],
  "facilitator_note": "optional one calm sentence",
  "skill_id": null
}
```

## propose turn
```json
{
  "turn_type": "propose",
  "summary": "final intent to execute",
  "choices": [],
  "proposals": [
    {"event_type": "IntentCaptured", "payload": {"task": "..."}},
    {"event_type": "WorkCapsuleBuilt", "payload": {"capsule_id": "wc_x", "visible_markdown": "# ..."}}
  ],
  "facilitator_note": ""
}
```

## enrich turn (after human approved proposals)
```json
{
  "turn_type": "enrich",
  "summary": "Recorded μ:.... Add external context?",
  "choices": [
    {"id": "url", "label": "粘贴 URL 抓取摘要", "select_action": "freeform"},
    {"id": "paste", "label": "粘贴文本/文档片段", "select_action": "freeform"},
    {"id": "config", "label": "配置 Meta AI / Worker", "skill_id": "setup-meta-ai-openai"},
    {"id": "skip", "label": "不需要，继续", "select_action": "skip"}
  ],
  "proposals": [],
  "facilitator_note": ""
}
```

Known event_types: IntentCaptured, WorkCapsuleBuilt, HumanDecision, WorkerDispatchPrepared,
MacroObservationImported, ProjectDiscovered, FailureNode.