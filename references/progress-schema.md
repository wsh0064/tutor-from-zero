# Progress Schema

`.tutor/progress.json` is the only durable learning-state authority. Extraction cache and
rendered outputs are replaceable.

## Top-Level Shape

```json
{
  "schema_version": 2,
  "course_name": "数据结构",
  "started_at": "2026-06-07",
  "updated_at": "2026-06-07T12:00:00+00:00",
  "exam_date": "2026-06-20",
  "mode": "full",
  "material_quality": {
    "overall": "partial",
    "weak_sections": ["第7章"],
    "notes": "缺少真题"
  },
  "chapters": {},
  "wrong_questions": [],
  "user_preferences": {
    "onboarding_status": "complete",
    "teaching_entry": "example-first",
    "interaction_cadence": "balanced",
    "guidance_style": "step-by-step",
    "detail_level": "normal",
    "visual_density": "core-concept",
    "formula_style": "rendered",
    "confirmed_at": "2026-06-07T12:00:00+00:00",
    "notes": ""
  },
  "last_session": {
    "summary": "",
    "next_action": ""
  }
}
```

Valid preference values:

- `onboarding_status`: `pending` or `complete`;
- `teaching_entry`: `unknown`, `example-first`, `map-first`, or `intuition-first`;
- `interaction_cadence`: `frequent-checks`, `balanced`, or `complete-chunk`;
- `guidance_style`: `step-by-step`, `independent-first`, or `demonstrate-then-vary`;
- `detail_level`: `concise`, `normal`, or `detailed`;
- `visual_density`: `essential`, `core-concept`, or `visual-rich`;
- `formula_style`: `rendered`.

The first three choices are required for onboarding. Change later preferences only after
the user confirms the proposed adjustment.

## Chapter Record

Use a stable chapter identifier as the key:

```json
{
  "status": "in_progress",
  "mastered_concepts": ["栈的后进先出"],
  "weak_concepts": ["合法出栈序列"],
  "practice_level": 1,
  "attempted": 5,
  "correct": 4,
  "last_reviewed_at": "2026-06-07",
  "notes": ""
}
```

Valid statuses are `not_started`, `in_progress`, and `completed`. Practice level is 0-3.
Completion requires both explanation and practice evidence; do not mark a chapter complete
because a guide was generated.

## Wrong Question Record

```json
{
  "id": "stable-id",
  "chapter": "第3章",
  "question": "题目或题目文件引用",
  "student_answer": "C",
  "correct_answer": "D",
  "error_type": "method-selection",
  "cause": "没有模拟栈顶约束",
  "repair_action": "完成两道合法序列变式",
  "reviewed": false,
  "next_review_date": "2026-06-09"
}
```

## Writing Rules

- Load before changing; preserve unknown fields for forward compatibility.
- Automatically migrate schema v1 records to v2, retaining legacy and unknown fields.
- Use `scripts/progress.py` for atomic writes and backup creation.
- Update only after observed learning activity.
- Recompute mode from `exam_date`.
- Keep concise summaries; long teaching content belongs in `outputs/`.
- Do not store secrets, raw chat exports, recordings, or full private documents.

## Recovery

If `progress.json` is malformed, `load_progress` attempts `progress.json.bak`. After
recovery, inspect the cause before saving again. Extraction failure must not erase learning
progress.
