"""
Explanation Builder — Tạo giải thích cho quá trình suy luận.

Hai loại:
  1. short_explanation(question, near_fire_rules) → 1 câu ngắn gọn inline
  2. full_explanation(session) → dict đầy đủ cho modal/panel
"""

from __future__ import annotations
from typing import Optional


SEVERITY_LABELS = {
    "CRITICAL": "🔴 Nghiêm trọng — cần kỹ thuật viên",
    "HIGH": "🟠 Cao — cần xử lý ngay",
    "MEDIUM": "🟡 Trung bình — có thể tự xử lý",
    "LOW": "🟢 Thấp — dễ tự khắc phục",
    "UNKNOWN": "⚪ Chưa xác định",
}


def build_short_explanation(
    question: dict,
    near_fire_rules: list[dict],
    current_group: Optional[str] = None,
) -> str:
    """
    Tạo giải thích ngắn (1–2 câu) về lý do hỏi câu này.
    Hiển thị inline dưới câu hỏi trong chat UI.
    """
    purpose = question.get("purpose", "")
    if purpose:
        return f"💡 {purpose}"

    if not near_fire_rules:
        return ""

    # Lấy tên rules gần fire nhất
    rule_names = []
    for nf in near_fire_rules[:2]:
        rule = nf.get("rule")
        if rule:
            name = rule.name if hasattr(rule, "name") else rule.get("name", "")
            if name:
                rule_names.append(name)

    if rule_names:
        return f"💡 Câu hỏi này giúp kiểm tra: {' và '.join(rule_names)}"

    return "💡 Câu hỏi giúp thu hẹp nguyên nhân lỗi"


def build_full_explanation(session) -> dict:
    """
    Tạo explanation đầy đủ từ một DiagnosticSession.

    Returns dict với:
    - question_path: danh sách Q&A
    - facts_collected: tất cả facts trong WM
    - rules_fired: rules đã kích hoạt
    - diagnoses: kết quả chẩn đoán
    - narration: giải thích bằng ngôn ngữ tự nhiên
    """
    # Q&A path
    question_path = []
    for step in session.history:
        question_path.append({
            "step": len(question_path) + 1,
            "question_id": step["question_id"],
            "question": step["question_text"],
            "answers": step.get("answer_labels", step["answers"]),
        })

    # Facts collected
    facts = sorted(session.engine.wm.facts)
    fact_history = [
        {"fact": f, "source": s}
        for f, s in session.engine.wm.history
    ]

    # Rules fired
    rules_fired = []
    for log in session.engine.fired_rules_trace:
        rules_fired.append({
            "rule_id": log["rule_id"],
            "rule_name": log["rule_name"],
            "added_facts": log["new_facts"],
            "triggered_diagnosis": log["triggers_diagnosis"],
            "certainty": round(log["cf"], 2),
            "certainty_percent": round(log["cf"] * 100),
        })

    # Top diagnoses
    top_diagnoses = session.engine.get_top_diagnoses(3)
    for d in top_diagnoses:
        d["severity_label"] = SEVERITY_LABELS.get(d.get("severity", ""), "")

    # Narration (ngôn ngữ tự nhiên tiếng Việt)
    narration = _build_narration(question_path, rules_fired, top_diagnoses)

    return {
        "question_path": question_path,
        "facts_collected": facts,
        "fact_history": fact_history,
        "rules_fired": rules_fired,
        "diagnoses": session.final_diagnoses,
        "top_diagnoses": top_diagnoses,
        "narration": narration,
        "summary": {
            "questions_asked": len(question_path),
            "facts_collected": len(facts),
            "rules_fired": len(rules_fired),
            "diagnoses_found": len(top_diagnoses),
        }
    }


def _build_narration(
    question_path: list[dict],
    rules_fired: list[dict],
    top_diagnoses: list[dict],
) -> list[str]:
    """Tạo danh sách câu giải thích bằng tiếng Việt."""
    lines = []

    lines.append("📋 **Quá trình chẩn đoán:**")
    for step in question_path:
        ans_text = ", ".join(step["answers"]) if step["answers"] else "—"
        lines.append(f"  {step['step']}. {step['question']} → *{ans_text}*")

    if rules_fired:
        lines.append("")
        lines.append("🔍 **Luật đã kích hoạt:**")
        for r in rules_fired:
            if r["added_facts"]:
                lines.append(f"  • {r['rule_name']}: thêm facts `{', '.join(r['added_facts'])}`")
            if r["triggered_diagnosis"]:
                lines.append(
                    f"  • {r['rule_name']}: → **{r['triggered_diagnosis']}** "
                    f"(CF={r['certainty_percent']}%)"
                )

    if top_diagnoses:
        lines.append("")
        lines.append("✅ **Kết quả chẩn đoán:**")
        for i, d in enumerate(top_diagnoses):
            marker = "🥇" if i == 0 else ("🥈" if i == 1 else "🥉")
            lines.append(f"  {marker} **{d['name']}** — Độ tin cậy: {d['cf_percent']}%")
            severity_label = SEVERITY_LABELS.get(d.get("severity", ""), "")
            if severity_label:
                lines.append(f"     Mức độ: {severity_label}")
            steps = d.get("solution_steps", [])
            if steps:
                lines.append("     Cách xử lý:")
                for s in steps[:3]:
                    lines.append(f"       • {s}")
            if d.get("warning"):
                lines.append(f"     ⚠️ {d['warning']}")

    return lines
