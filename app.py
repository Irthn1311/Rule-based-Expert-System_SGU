"""
app.py — Flask Web Expert System: PC Diagnostic Chat

Routes:
  GET  /              → Render chat UI
  POST /start         → Tạo session mới, trả Q01
  POST /message       → Nhận text user, NLU → facts → inference
  POST /select        → User click option (single_choice / yes_no)
  POST /submit        → User submit multi_choice
  GET  /explanation   → Trả full explanation của session
  POST /reset         → Reset / restart session
  GET  /status        → Health check + KB stats

Port: 5000 (Flask default)
"""

import os
import sys
from pathlib import Path

# Đảm bảo import từ project root
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, request, jsonify, render_template, abort

from engine.diagnostic_session import KnowledgeBaseLoader
from engine.question_selector import QuestionSelector
from engine.explanation_builder import build_short_explanation, build_full_explanation
from engine.tree_builder import DecisionTreeBuilder
from nlu.intent_classifier import IntentClassifier
from nlu.fact_extractor import FactExtractor
from nlu.patterns import (
    GREETING_MESSAGE, UNDERSTOOD_TEMPLATES,
    UNCERTAIN_MESSAGE, FACTS_UNDERSTOOD_PREFIX
)
from services.session_store import SessionStore

# ─────────────────────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False  # Giữ tiếng Việt trong JSON response
app.config["JSONIFY_MIMETYPE"] = "application/json; charset=utf-8"

# Paths
DATA_DIR = PROJECT_ROOT / "data"
QUESTIONS_PATH = DATA_DIR / "06_questions.json"
RULES_PATH = DATA_DIR / "07_rules_and_diagnoses.json"

# Global singletons (init khi startup)
kb: KnowledgeBaseLoader = None
store: SessionStore = None
question_selector: QuestionSelector = None
intent_clf: IntentClassifier = None
fact_extractor: FactExtractor = None
tree_builder: DecisionTreeBuilder = None


def init_app():
    """Khởi tạo Knowledge Base và các services."""
    global kb, store, question_selector, intent_clf, fact_extractor, tree_builder

    print("⏳ Loading Knowledge Base...")
    kb = KnowledgeBaseLoader(str(QUESTIONS_PATH), str(RULES_PATH))
    print(f"✅ KB loaded: {kb.stats}")

    store = SessionStore(kb)
    question_selector = QuestionSelector(kb.questions, kb.diagnoses)
    intent_clf = IntentClassifier()
    fact_extractor = FactExtractor()
    tree_builder = DecisionTreeBuilder(kb.questions, kb.diagnoses)
    print("✅ All services initialized")


# ─────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────

def _format_question(q: dict) -> dict:
    """Format câu hỏi để gửi về frontend."""
    if not q:
        return None
    return {
        "id": q["id"],
        "text": q["text"],
        "type": q.get("type", "single_choice"),
        "options": [
            {
                "value": opt["value"],
                "label": opt["label"],
            }
            for opt in q.get("options", [])
        ],
        "purpose": q.get("purpose", ""),
    }


def _build_bot_message(
    question: dict,
    prefix: str = "",
    understood_msg: str = "",
    short_explanation: str = "",
) -> str:
    """Xây dựng bot message từ các thành phần."""
    parts = []
    if prefix:
        parts.append(prefix)
    if understood_msg:
        parts.append(understood_msg)
    if question:
        q_text = question.get("text", "")
        if q_text:
            parts.append(q_text)
    if short_explanation:
        parts.append(short_explanation)
    return "\n\n".join(filter(None, parts))


def _get_ext_session_or_404(session_id: str):
    """Lấy ExtendedSession hoặc trả lỗi 404."""
    ext = store.get(session_id)
    if not ext:
        abort(404, description="Phiên chẩn đoán không tồn tại hoặc đã hết hạn.")
    return ext


def _match_text_to_option(text: str, question: dict, extracted_facts: list[str]) -> str | None:
    """
    Cố gắng map text người dùng → value của một option trong câu hỏi hiện tại.

    Chiến lược (theo thứ tự ưu tiên):
    1. Nếu extracted_facts giao với adds_facts của option → match
    2. Nếu label của option xuất hiện trong text (case-insensitive) → match
    3. Nếu value của option (A/B/C...) xuất hiện độc lập trong text → match

    Return: option value ('A', 'B', ...) hoặc None
    """
    text_lower = text.lower().strip()
    best_match = None
    best_score = 0

    for opt in question.get("options", []):
        val = opt.get("value", "")
        if val == "SUBMIT":
            continue
        score = 0

        # Chiến lược 1: fact overlap (ưu tiên cao nhất)
        opt_facts = set(opt.get("adds_facts", []))
        if opt_facts and extracted_facts:
            overlap = opt_facts & set(extracted_facts)
            if overlap:
                score += len(overlap) * 10

        # Chiến lược 2: label match
        label = opt.get("label", "").lower()
        if label and len(label) > 1:
            # Tách các từ chốt trong label và kiểm tra xuất hiện trong text
            label_words = [w for w in label.split() if len(w) > 2]
            hits = sum(1 for w in label_words if w in text_lower)
            if hits > 0:
                score += hits * 2

        # Chiến lược 3: option value letter (e.g. user types 'A' or 'B')
        import re
        if re.fullmatch(r'[a-zA-Z]', text.strip()) and text.strip().upper() == val:
            score += 5

        if score > best_score:
            best_score = score
            best_match = val

    return best_match if best_score >= 2 else None


def _make_question_response(ext, prefix="", understood_msg="", facts_added=None):
    """
    Tạo response chuẩn khi gửi câu hỏi tiếp theo.
    Bao gồm short_explanation từ dynamic questioning.
    """
    ds = ext.ds
    q = ds.get_current_question()

    # Dynamic questioning: lấy near-fire rules để tính explanation
    near_fire = ds.engine.get_near_fire_rules(3)

    short_exp = ""
    if q:
        short_exp = build_short_explanation(q, near_fire, ds.current_group)

    bot_msg = _build_bot_message(
        q,
        prefix=prefix,
        understood_msg=understood_msg,
        short_explanation=short_exp,
    )

    return jsonify({
        "session_id": ext.session_id,
        "session_complete": ds.is_complete,
        "bot_message": bot_msg,
        "question": _format_question(q) if q else None,
        "input_mode": ds.expected_input_mode if not ds.is_complete else None,
        "facts_added": facts_added or [],
        "current_group": ds.current_group,
        "top_diagnoses": ds.engine.get_top_diagnoses(3),
        "wm_size": len(ds.engine.wm.facts),
    })


def _make_diagnosis_response(ext, result: dict):
    """Tạo response khi session hoàn tất → hiển thị diagnosis card."""
    ds = ext.ds
    top = ds.engine.get_top_diagnoses(3)

    # Primary diagnosis
    primary = top[0] if top else None
    if not primary and ds.final_diagnoses:
        primary = ds.final_diagnoses[0]

    return jsonify({
        "session_id": ext.session_id,
        "session_complete": True,
        "bot_message": _build_completion_message(primary),
        "question": None,
        "input_mode": None,
        "diagnoses": top,
        "primary_diagnosis": primary,
        "facts_added": result.get("new_facts", []),
        "current_group": ds.current_group,
        "wm_size": len(ds.engine.wm.facts),
    })


def _build_completion_message(primary: dict | None) -> str:
    if not primary:
        return "✅ Phân tích hoàn tất. Không xác định được nguyên nhân cụ thể — vui lòng mang đến kỹ thuật viên."

    name = primary.get("name", "Lỗi không xác định")
    cf = primary.get("cf_percent", 0)
    severity = primary.get("severity", "UNKNOWN")

    severity_emoji = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢",
    }.get(severity, "⚪")

    msg = f"✅ **Chẩn đoán hoàn tất!**\n\n"
    msg += f"{severity_emoji} **{name}** (Độ tin cậy: {cf}%)\n\n"

    steps = primary.get("solution_steps", [])
    if steps:
        msg += "**Hướng xử lý:**\n"
        for s in steps[:3]:
            msg += f"• {s}\n"

    if primary.get("needs_technician"):
        msg += "\n⚠️ Nên mang máy đến kỹ thuật viên."
    elif primary.get("warning"):
        msg += f"\n⚠️ {primary['warning']}"

    return msg.strip()


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Render chat UI."""
    return render_template("chat.html", kb_stats=kb.stats if kb else {})


@app.route("/start", methods=["POST"])
def start_session():
    """
    Tạo phiên chẩn đoán mới.
    Response: session_id + câu hỏi đầu tiên (Q01)
    """
    ext = store.create()
    ds = ext.ds

    q = ds.get_current_question()
    bot_msg = GREETING_MESSAGE

    return jsonify({
        "session_id": ext.session_id,
        "session_complete": False,
        "bot_message": bot_msg,
        "question": _format_question(q),
        "input_mode": ds.expected_input_mode,
        "facts_added": [],
        "current_group": None,
        "top_diagnoses": [],
        "wm_size": 0,
    })


@app.route("/message", methods=["POST"])
def handle_message():
    """
    Nhận text tự do từ người dùng.

    Flow:
      1. NLU: classify intent + extract facts từ text
      2. Thử match text/facts → option của câu hỏi hiện tại
         → Nếu match: gọi ds.answer() để advance question (giống /select)
         → Nếu không match nhưng có facts: add facts vào WM, giữ câu hỏi
         → Nếu có intent: skip đến group
         → Fallback: hiển thị clarification message
    """
    data = request.get_json(force=True)
    session_id = data.get("session_id", "")
    text = data.get("text", "").strip()

    if not session_id or not text:
        return jsonify({"error": "session_id và text là bắt buộc"}), 400

    ext = _get_ext_session_or_404(session_id)
    ds = ext.ds

    if ds.is_complete:
        return _make_diagnosis_response(ext, {})

    # NLU: classify intent + extract facts
    intent_result = intent_clf.classify(text)
    nlu_result = fact_extractor.extract_and_classify(text, intent_result)
    extracted_facts = nlu_result.get("facts", [])

    # ── Bước 1: Thử match text/facts với options của câu hỏi hiện tại ──
    # Đây là fix cốt lõi: nếu tìm được match → gọi ds.answer() để câu hỏi ADVANCE
    current_q = ds.get_current_question()
    matched_value = None
    if current_q:
        matched_value = _match_text_to_option(text, current_q, extracted_facts)

    if matched_value:
        # Tìm được match → xử lý như /select (advance question)
        result = ds.answer([matched_value])
        if result.get("session_complete") or ds.is_complete:
            return _make_diagnosis_response(ext, result)
        # Thêm confirmed message lên trên
        confirmed_label = next(
            (opt["label"] for opt in current_q.get("options", []) if opt["value"] == matched_value),
            text
        )
        return _make_question_response(
            ext,
            facts_added=result.get("new_facts", []),
        )

    # ── Bước 2: Không match option → xử lý NLU thuần ──
    facts_added = []
    understood_msg = ""
    prefix = ""

    if extracted_facts:
        # Có facts cụ thể → add vào WM và chạy inference (không advance question)
        new_facts = ds.engine.add_facts(extracted_facts, source="nlu")
        facts_added = new_facts
        understood_msg = nlu_result.get("understood_message", "")

        # Chạy forward chaining với facts mới
        new_diags = ds.engine.run_until_stable()
        for d in new_diags:
            formatted = ds.flow._format_diag(d, ds.engine)
            if formatted not in ds.final_diagnoses:
                ds.final_diagnoses.append(formatted)

        # Nếu Q01 và intent rõ → skip đến group
        if nlu_result.get("skip_to_group") and ds.current_question_id == "Q01":
            skip_qid = nlu_result["skip_to_group"]
            if skip_qid:
                ds.current_question_id = skip_qid
                if intent_result.get("intent"):
                    ds.current_group = intent_result["intent"]
                    prefix = UNDERSTOOD_TEMPLATES.get(intent_result["intent"], "")

    elif nlu_result.get("intent") and nlu_result.get("skip_to_group"):
        # Intent rõ nhưng không có facts cụ thể → skip đến nhóm
        intent = nlu_result["intent"]
        skip_qid = nlu_result["skip_to_group"]
        if skip_qid and ds.current_question_id == "Q01":
            ds.current_question_id = skip_qid
            ds.current_group = intent
            prefix = UNDERSTOOD_TEMPLATES.get(intent, "")

    else:
        # Không hiểu được gì → gợi ý dùng buttons
        prefix = "Tôi chưa hiểu rõ. Hãy chọn một trong các lựa chọn bên dưới, hoặc mô tả cụ thể hơn:"

    if ds.is_complete:
        return _make_diagnosis_response(ext, {"new_facts": facts_added})

    return _make_question_response(ext, prefix=prefix, understood_msg=understood_msg, facts_added=facts_added)


@app.route("/select", methods=["POST"])
def handle_select():
    """
    Xử lý khi user click option (single_choice / yes_no).
    Body: { session_id, question_id, value }
    """
    data = request.get_json(force=True)
    session_id = data.get("session_id", "")
    question_id = data.get("question_id", "")
    value = data.get("value", "")

    if not all([session_id, question_id, value]):
        return jsonify({"error": "session_id, question_id và value là bắt buộc"}), 400

    ext = _get_ext_session_or_404(session_id)
    ds = ext.ds

    if ds.is_complete:
        return _make_diagnosis_response(ext, {})

    # Validate question
    if ds.current_question_id != question_id:
        return jsonify({
            "error": f"Question mismatch: expected {ds.current_question_id}, got {question_id}"
        }), 400

    # Process answer
    result = ds.answer([value])

    if result.get("session_complete") or ds.is_complete:
        return _make_diagnosis_response(ext, result)

    return _make_question_response(ext, facts_added=result.get("new_facts", []))


@app.route("/submit", methods=["POST"])
def handle_submit():
    """
    Xử lý khi user submit multi_choice (checkbox).
    Body: { session_id, question_id, values: [list] }
    """
    data = request.get_json(force=True)
    session_id = data.get("session_id", "")
    question_id = data.get("question_id", "")
    values = data.get("values", [])

    if not all([session_id, question_id]):
        return jsonify({"error": "session_id và question_id là bắt buộc"}), 400

    if not isinstance(values, list):
        return jsonify({"error": "values phải là list"}), 400

    ext = _get_ext_session_or_404(session_id)
    ds = ext.ds

    if ds.is_complete:
        return _make_diagnosis_response(ext, {})

    if ds.current_question_id != question_id:
        return jsonify({
            "error": f"Question mismatch: expected {ds.current_question_id}, got {question_id}"
        }), 400

    # Multi-choice: thêm SUBMIT nếu chưa có
    if "SUBMIT" not in values and values:
        values = values + ["SUBMIT"]

    result = ds.answer(values)

    if result.get("session_complete") or ds.is_complete:
        return _make_diagnosis_response(ext, result)

    return _make_question_response(ext, facts_added=result.get("new_facts", []))


@app.route("/explanation", methods=["GET"])
def get_explanation():
    """
    Trả full explanation của session.
    Query param: session_id
    """
    session_id = request.args.get("session_id", "")
    if not session_id:
        return jsonify({"error": "session_id là bắt buộc"}), 400

    ext = _get_ext_session_or_404(session_id)
    explanation = build_full_explanation(ext.ds)

    return jsonify(explanation)


@app.route("/reset", methods=["POST"])
def reset_session():
    """
    Reset / restart một session.
    Body: { session_id } — xóa session cũ, tạo mới
    Response: new session_id + Q01
    """
    data = request.get_json(force=True)
    old_sid = data.get("session_id", "")

    # Xóa session cũ nếu có
    if old_sid:
        store.delete(old_sid)

    # Tạo session mới
    ext = store.create()
    ds = ext.ds
    q = ds.get_current_question()

    return jsonify({
        "session_id": ext.session_id,
        "session_complete": False,
        "bot_message": GREETING_MESSAGE,
        "question": _format_question(q),
        "input_mode": ds.expected_input_mode,
        "facts_added": [],
        "current_group": None,
        "top_diagnoses": [],
        "wm_size": 0,
    })


# ─────────────────────────────────────────────────────────────
# Tree Routes
# ─────────────────────────────────────────────────────────────

@app.route("/tree")
def tree_page():
    """Render trang cây suy luận (mở từ diagnosis modal)."""
    return render_template("tree.html", kb_stats=kb.stats if kb else {})


@app.route("/api/tree", methods=["GET"])
def api_tree():
    """
    Trả full DAG tree JSON (cached sau lần đầu).
    Frontend dùng để render cây.
    """
    if not tree_builder:
        return jsonify({"error": "Tree builder chưa được khởi tạo"}), 503
    dag = tree_builder.build_dag()
    return jsonify(dag)


@app.route("/api/tree-path", methods=["GET"])
def api_tree_path():
    """
    Trả path của session → {node_ids, edge_keys, primary_group}.
    Frontend dùng để highlight nhánh đã đi.
    Query param: session_id
    """
    session_id = request.args.get("session_id", "")
    if not session_id:
        return jsonify({"node_ids": [], "edge_keys": [], "primary_group": None})

    ext = store.get(session_id)
    if not ext:
        return jsonify({"node_ids": [], "edge_keys": [], "primary_group": None})

    path = tree_builder.get_session_path(ext.ds)
    return jsonify(path)


@app.route("/status", methods=["GET"])
def status():
    """Health check + KB stats."""
    if not kb:
        return jsonify({"status": "degraded", "reason": "KB not loaded"}), 503

    return jsonify({
        "status": "ok",
        "kb": kb.stats,
        "sessions": store.stats() if store else {},
        "version": "1.0.0",
    })


# ─────────────────────────────────────────────────────────────
# Error Handlers
# ─────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": str(e.description)}), 404


@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": str(e.description)}), 400


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Lỗi server nội bộ", "detail": str(e)}), 500


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_app()
    print("\n🚀 PC Expert System đang chạy tại http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
