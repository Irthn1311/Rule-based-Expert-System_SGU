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
  GET  /webhook/meta  → Verify Meta webhook
  POST /webhook/meta  → Nhận message từ Facebook Messenger
  GET  /webhook/instagram  → Verify Instagram webhook
  POST /webhook/instagram  → Nhận/log Instagram API webhook
  GET  /privacy       → Privacy Policy tối thiểu cho Meta App
  GET  /terms         → Terms of Service tối thiểu cho Meta App
  GET  /data-deletion → Data Deletion Instructions tối thiểu

Stateless mode (Vercel-compatible):
  Mỗi response trả về `session_state` (JSON blob).
  Mỗi request có thể gửi `session_state` thay vì `session_id`.
  → Server không cần lưu state giữa các invocations.

Port: 5000 (Flask default)
"""

import os
import re
import sys
import threading
import unicodedata
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover - documented in requirements.txt
    requests = None

# Đảm bảo import từ project root
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, request, jsonify, render_template, abort

from engine.diagnostic_session import KnowledgeBaseLoader, DiagnosticSession
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

# Global singletons — lazy init (tránh double-init và Vercel cold start issues)
kb: KnowledgeBaseLoader = None
store: SessionStore = None
question_selector: QuestionSelector = None
intent_clf: IntentClassifier = None
fact_extractor: FactExtractor = None
tree_builder: DecisionTreeBuilder = None
_initialized = False

# Facebook PSID -> stateless DiagnosticSession snapshot.
fb_sessions: dict[str, dict] = {}
fb_sessions_lock = threading.Lock()

# Instagram API sender -> stateless DiagnosticSession snapshot.
instagram_api_sessions: dict[str, dict] = {}
instagram_api_sessions_lock = threading.Lock()


def init_app():
    """Khởi tạo Knowledge Base và các services."""
    global kb, store, question_selector, intent_clf, fact_extractor, tree_builder, _initialized

    if _initialized:
        return

    print("⏳ Loading Knowledge Base...")
    kb = KnowledgeBaseLoader(str(QUESTIONS_PATH), str(RULES_PATH))
    print(f"✅ KB loaded: {kb.stats}")

    store = SessionStore(kb)
    question_selector = QuestionSelector(kb.questions, kb.diagnoses)
    intent_clf = IntentClassifier()
    fact_extractor = FactExtractor()
    tree_builder = DecisionTreeBuilder(kb.questions, kb.diagnoses)
    _initialized = True
    print("✅ All services initialized")


@app.before_request
def ensure_initialized():
    """Lazy init — an toàn với Vercel cold starts và Flask debug reloader."""
    init_app()


# ─────────────────────────────────────────────────────────────
# Session Resolution — Stateless + Stateful hybrid
# ─────────────────────────────────────────────────────────────

def _resolve_session(data: dict):
    """
    Lấy DiagnosticSession từ request data.

    Ưu tiên:
    1. session_state (blob JSON từ client) → stateless mode, hoạt động trên Vercel
    2. session_id → stateful in-memory store (hoạt động khi server là persistent process)

    Return: (ds: DiagnosticSession, session_id: str) hoặc abort(404)
    """
    session_state = data.get("session_state")
    if session_state and isinstance(session_state, dict):
        # Stateless mode: restore từ blob client gửi lên
        try:
            ds = DiagnosticSession.from_dict(
                session_state,
                kb.questions,
                kb.rules,
                kb.diagnoses,
            )
            # Dùng session_id từ blob làm identifier (chỉ để response)
            session_id = session_state.get("_session_id", "stateless")
            return ds, session_id
        except Exception as e:
            abort(400, description=f"session_state không hợp lệ: {e}")

    # Fallback: stateful in-memory store
    session_id = data.get("session_id", "")
    if not session_id:
        abort(400, description="session_id hoặc session_state là bắt buộc")
    ext = store.get(session_id)
    if not ext:
        abort(404, description="Phiên chẩn đoán không tồn tại hoặc đã hết hạn.")
    return ext.ds, session_id


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


def _build_start_payload(ext) -> dict:
    """Tạo payload bắt đầu session dùng chung cho web và adapter."""
    ds = ext.ds
    q = ds.get_current_question()

    state_snapshot = ds.to_dict()
    state_snapshot["_session_id"] = ext.session_id

    return {
        "session_id": ext.session_id,
        "session_complete": False,
        "bot_message": GREETING_MESSAGE,
        "question": _format_question(q),
        "input_mode": ds.expected_input_mode,
        "facts_added": [],
        "current_group": None,
        "top_diagnoses": [],
        "wm_size": 0,
        "session_state": state_snapshot,
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


def _normalize_answer_values_for_question(question: dict, values: list[str]) -> list[str]:
    """Chuẩn hóa answer values trước khi đưa vào DiagnosticSession."""
    if question.get("type") == "multi_choice" and values and "SUBMIT" not in values:
        return values + ["SUBMIT"]
    return values


def _process_text_for_session(ds: DiagnosticSession, session_id: str, text: str) -> dict:
    """
    Xử lý text user bằng flow chẩn đoán hiện có và trả payload dict.
    Dùng chung cho route /message và Facebook Messenger adapter.
    """
    if ds.is_complete:
        return _build_diagnosis_payload(ds, session_id, {})

    # NLU: classify intent + extract facts
    intent_result = intent_clf.classify(text)
    nlu_result = fact_extractor.extract_and_classify(text, intent_result)
    extracted_facts = nlu_result.get("facts", [])

    # ── Bước 1: Thử match text/facts với options của câu hỏi hiện tại ──
    current_q = ds.get_current_question()
    matched_value = None
    if current_q:
        matched_value = _match_text_to_option(text, current_q, extracted_facts)

    if matched_value:
        # Tìm được match → xử lý như /select (advance question)
        answer_values = _normalize_answer_values_for_question(current_q, [matched_value])
        result = ds.answer(answer_values)
        if result.get("session_complete") or ds.is_complete:
            return _build_diagnosis_payload(ds, session_id, result)
        return _build_question_payload(
            ds, session_id,
            facts_added=result.get("new_facts", []),
        )

    # ── Bước 2: Không match option → xử lý NLU thuần ──
    facts_added = []
    understood_msg = ""
    prefix = ""

    if extracted_facts:
        new_facts = ds.engine.add_facts(extracted_facts, source="nlu")
        facts_added = new_facts
        understood_msg = nlu_result.get("understood_message", "")

        new_diags = ds.engine.run_until_stable()
        for d in new_diags:
            formatted = ds.flow._format_diag(d, ds.engine)
            if formatted not in ds.final_diagnoses:
                ds.final_diagnoses.append(formatted)

        if nlu_result.get("skip_to_group") and ds.current_question_id == "Q01":
            skip_qid = nlu_result["skip_to_group"]
            if skip_qid:
                ds.current_question_id = skip_qid
                if intent_result.get("intent"):
                    ds.current_group = intent_result["intent"]
                    prefix = UNDERSTOOD_TEMPLATES.get(intent_result["intent"], "")

    elif nlu_result.get("intent") and nlu_result.get("skip_to_group"):
        intent = nlu_result["intent"]
        skip_qid = nlu_result["skip_to_group"]
        if skip_qid and ds.current_question_id == "Q01":
            ds.current_question_id = skip_qid
            ds.current_group = intent
            prefix = UNDERSTOOD_TEMPLATES.get(intent, "")

    else:
        prefix = "Tôi chưa hiểu rõ. Hãy chọn một trong các lựa chọn bên dưới, hoặc mô tả cụ thể hơn:"

    if ds.is_complete:
        return _build_diagnosis_payload(ds, session_id, {"new_facts": facts_added})

    return _build_question_payload(ds, session_id, prefix=prefix, understood_msg=understood_msg, facts_added=facts_added)


def _strip_vietnamese_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt để nhận lệnh điều khiển đơn giản hơn."""
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _is_facebook_reset_message(text: str) -> bool:
    normalized = _strip_vietnamese_accents(text).lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized in {"reset", "restart", "bat dau lai", "lam lai", "start over"}


def _restore_facebook_session(sender_id: str) -> tuple[DiagnosticSession | None, str | None]:
    with fb_sessions_lock:
        saved = fb_sessions.get(sender_id)

    if not saved:
        return None, None

    try:
        session_state = saved["session_state"]
        ds = DiagnosticSession.from_dict(
            session_state,
            kb.questions,
            kb.rules,
            kb.diagnoses,
        )
        return ds, saved.get("session_id", session_state.get("_session_id", "facebook"))
    except Exception as exc:
        print(f"⚠️ Không restore được Facebook session sender_id={sender_id}: {exc}")
        return None, None


def _create_facebook_session(sender_id: str) -> tuple[DiagnosticSession, str, dict]:
    ext = store.create()
    payload = _build_start_payload(ext)
    _save_facebook_session(sender_id, payload)
    print(f"🆕 Tạo Facebook diagnostic session sender_id={sender_id}, session_id={ext.session_id}")
    return ext.ds, ext.session_id, payload


def _save_facebook_session(sender_id: str, payload: dict) -> None:
    session_state = payload.get("session_state")
    if not session_state:
        return

    with fb_sessions_lock:
        fb_sessions[sender_id] = {
            "session_id": payload.get("session_id", session_state.get("_session_id", "facebook")),
            "session_state": session_state,
        }


def _format_question_for_messenger(question: dict | None) -> str:
    """Format câu hỏi + options thành text phù hợp Facebook Messenger."""
    if not question:
        return ""

    lines = [question.get("text", "").strip()]
    option_lines = []
    for opt in question.get("options", []):
        value = opt.get("value", "")
        if value == "SUBMIT":
            continue
        label = opt.get("label", "")
        option_lines.append(f"{value}. {label}")

    if option_lines:
        lines.append("")
        lines.extend(option_lines)
        lines.append("")
        lines.append("Bạn có thể trả lời bằng chữ A, B, C hoặc mô tả tự nhiên.")

    return "\n".join(line for line in lines if line is not None).strip()


def _clean_messenger_markdown(text: str) -> str:
    """Messenger hiển thị text thuần; bỏ markdown đậm cơ bản cho dễ đọc."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    return text.strip()


def _format_payload_for_messenger(payload: dict) -> str:
    bot_message = payload.get("bot_message", "") or ""
    question = payload.get("question")
    question_text = question.get("text", "") if question else ""
    formatted_question = _format_question_for_messenger(question)

    if formatted_question:
        if question_text and question_text in bot_message:
            bot_message = bot_message.replace(question_text, formatted_question, 1)
        else:
            bot_message = "\n\n".join(part for part in [bot_message, formatted_question] if part)

    if not bot_message:
        bot_message = "Bot đã nhận tin nhắn của bạn. Hãy mô tả lỗi máy tính cần chẩn đoán."

    bot_message = _clean_messenger_markdown(bot_message)
    if len(bot_message) > 1900:
        bot_message = bot_message[:1897].rstrip() + "..."
    return bot_message


def handle_facebook_message(sender_id: str, text: str) -> str:
    """
    Adapter xử lý một message Facebook và trả text để gửi lại Messenger.
    State được lưu theo sender_id bằng snapshot DiagnosticSession.to_dict().
    """
    init_app()
    text = text.strip()

    if _is_facebook_reset_message(text):
        with fb_sessions_lock:
            old = fb_sessions.pop(sender_id, None)
        if old and old.get("session_id"):
            store.delete(old["session_id"])
        _, _, payload = _create_facebook_session(sender_id)
        return "Đã bắt đầu lại phiên chẩn đoán.\n\n" + _format_payload_for_messenger(payload)

    ds, session_id = _restore_facebook_session(sender_id)
    if not ds or not session_id:
        ds, session_id, _ = _create_facebook_session(sender_id)

    payload = _process_text_for_session(ds, session_id, text)
    _save_facebook_session(sender_id, payload)
    return _format_payload_for_messenger(payload)


def send_meta_message(psid: str, text: str) -> bool:
    """Gửi tin nhắn về Facebook Messenger bằng Meta Send API."""
    page_access_token = os.getenv("PAGE_ACCESS_TOKEN", "").strip()
    graph_version = os.getenv("META_GRAPH_VERSION", "v20.0").strip() or "v20.0"

    if not page_access_token:
        print("❌ Thiếu PAGE_ACCESS_TOKEN, không thể gửi reply về Meta.")
        return False

    if requests is None:
        print("❌ Chưa cài thư viện requests. Hãy chạy: pip install -r requirements.txt")
        return False

    url = f"https://graph.facebook.com/{graph_version}/me/messages"
    payload = {
        "recipient": {"id": psid},
        "message": {"text": text},
    }

    try:
        resp = requests.post(
            url,
            params={"access_token": page_access_token},
            json=payload,
            timeout=10,
        )
        print(f"📤 Meta Send API status={resp.status_code}, response={resp.text}")
        return resp.ok
    except requests.RequestException as exc:
        print(f"❌ Lỗi khi gửi message về Meta: {exc}")
        return False


def _instagram_api_session_key(sender_id: str) -> str:
    return f"instagram_api:{sender_id}"


def _restore_instagram_api_session(sender_id: str) -> tuple[DiagnosticSession | None, str | None]:
    session_key = _instagram_api_session_key(sender_id)
    with instagram_api_sessions_lock:
        saved = instagram_api_sessions.get(session_key)

    if not saved:
        return None, None

    try:
        session_state = saved["session_state"]
        ds = DiagnosticSession.from_dict(
            session_state,
            kb.questions,
            kb.rules,
            kb.diagnoses,
        )
        return ds, saved.get("session_id", session_state.get("_session_id", "instagram_api"))
    except Exception as exc:
        print(f"[IG API] Cannot restore session key={session_key}: {exc}")
        return None, None


def _save_instagram_api_session(sender_id: str, payload: dict) -> None:
    session_state = payload.get("session_state")
    if not session_state:
        return

    session_key = _instagram_api_session_key(sender_id)
    with instagram_api_sessions_lock:
        instagram_api_sessions[session_key] = {
            "session_id": payload.get("session_id", session_state.get("_session_id", "instagram_api")),
            "session_state": session_state,
        }


def _create_instagram_api_session(sender_id: str) -> tuple[DiagnosticSession, str, dict]:
    ext = store.create()
    payload = _build_start_payload(ext)
    _save_instagram_api_session(sender_id, payload)
    print(f"[IG API] Created diagnostic session key={_instagram_api_session_key(sender_id)}, session_id={ext.session_id}")
    return ext.ds, ext.session_id, payload


def handle_instagram_api_message(sender_id, text) -> str:
    """Adapter Instagram API dùng lại rule-based chatbot hiện có."""
    init_app()
    sender_id = str(sender_id).strip()
    text = str(text).strip()

    if _is_facebook_reset_message(text):
        session_key = _instagram_api_session_key(sender_id)
        with instagram_api_sessions_lock:
            old = instagram_api_sessions.pop(session_key, None)
        if old and old.get("session_id"):
            store.delete(old["session_id"])
        _, _, payload = _create_instagram_api_session(sender_id)
        return "Đã bắt đầu lại phiên chẩn đoán.\n\n" + _format_payload_for_messenger(payload)

    ds, session_id = _restore_instagram_api_session(sender_id)
    if not ds or not session_id:
        ds, session_id, _ = _create_instagram_api_session(sender_id)

    payload = _process_text_for_session(ds, session_id, text)
    _save_instagram_api_session(sender_id, payload)
    return _format_payload_for_messenger(payload)


def send_instagram_api_message(recipient_id, text) -> bool:
    """
    Placeholder gửi message Instagram API.
    Hiện ưu tiên verify webhook + nhận/log payload trước khi chốt endpoint gửi.
    """
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
    version = os.getenv("INSTAGRAM_API_VERSION", "v25.0").strip() or "v25.0"
    account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "").strip()

    if not token or not account_id:
        print("[IG API] Missing INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ACCOUNT_ID")
        print(f"[IG API] Reply placeholder recipient_id={recipient_id}: {text}")
        return False

    print(
        "[IG API] Send placeholder "
        f"version={version}, business_account_id={account_id}, recipient_id={recipient_id}: {text}"
    )
    return False


def _as_list(value) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


def _extract_text_value(value) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        for key in ("text", "body", "message"):
            text = _extract_text_value(value.get(key))
            if text:
                return text
    return None


def _extract_instagram_api_messages(payload) -> list[tuple[str, str]]:
    """
    Parse mềm các cấu trúc webhook Instagram phổ biến.
    Không raise exception để webhook luôn nhận/log được payload thật.
    """
    if not isinstance(payload, dict):
        return []

    parsed: list[tuple[str, str]] = []
    for entry in _as_list(payload.get("entry")):
        for event in _as_list(entry.get("messaging")):
            sender = event.get("sender") if isinstance(event, dict) else {}
            message = event.get("message") if isinstance(event, dict) else {}
            sender_id = sender.get("id") if isinstance(sender, dict) else None
            text = _extract_text_value(message)
            if sender_id and text:
                parsed.append((str(sender_id), text))

        for change in _as_list(entry.get("changes")):
            if not isinstance(change, dict):
                continue
            value = change.get("value") or {}
            if not isinstance(value, dict):
                continue

            for message in _as_list(value.get("messages")):
                sender = message.get("sender") if isinstance(message, dict) else {}
                sender_id = (
                    message.get("from")
                    or message.get("sender_id")
                    or (sender.get("id") if isinstance(sender, dict) else None)
                )
                text = _extract_text_value(message.get("text") if isinstance(message, dict) else None)
                if not text:
                    text = _extract_text_value(message)
                if sender_id and text:
                    parsed.append((str(sender_id), text))

            sender = value.get("sender") or value.get("from") or {}
            sender_id = (
                value.get("sender_id")
                or (sender.get("id") if isinstance(sender, dict) else None)
            )
            text = _extract_text_value(value.get("message")) or _extract_text_value(value.get("text"))
            if sender_id and text:
                parsed.append((str(sender_id), text))

    return parsed


def _build_question_payload(ds: DiagnosticSession, session_id: str, prefix="", understood_msg="", facts_added=None) -> dict:
    """
    Tạo payload chuẩn khi gửi câu hỏi tiếp theo.
    Luôn bao gồm session_state để client có thể dùng stateless mode.
    """
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

    # Serialize state để client giữ lại (stateless Vercel support)
    state_snapshot = ds.to_dict()
    state_snapshot["_session_id"] = session_id

    return {
        "session_id": session_id,
        "session_complete": ds.is_complete,
        "bot_message": bot_msg,
        "question": _format_question(q) if q else None,
        "input_mode": ds.expected_input_mode if not ds.is_complete else None,
        "facts_added": facts_added or [],
        "current_group": ds.current_group,
        "top_diagnoses": ds.engine.get_top_diagnoses(3),
        "wm_size": len(ds.engine.wm.facts),
        "session_state": state_snapshot,  # ← stateless Vercel support
    }


def _make_question_response(ds: DiagnosticSession, session_id: str, prefix="", understood_msg="", facts_added=None):
    """Tạo response chuẩn khi gửi câu hỏi tiếp theo."""
    return jsonify(_build_question_payload(ds, session_id, prefix, understood_msg, facts_added))


def _build_diagnosis_payload(ds: DiagnosticSession, session_id: str, result: dict) -> dict:
    """Tạo payload khi session hoàn tất → hiển thị diagnosis card."""
    top = ds.engine.get_top_diagnoses(3)

    # Primary diagnosis
    primary = top[0] if top else None
    if not primary and ds.final_diagnoses:
        primary = ds.final_diagnoses[0]

    state_snapshot = ds.to_dict()
    state_snapshot["_session_id"] = session_id

    return {
        "session_id": session_id,
        "session_complete": True,
        "bot_message": _build_completion_message(primary),
        "question": None,
        "input_mode": None,
        "diagnoses": top,
        "primary_diagnosis": primary,
        "facts_added": result.get("new_facts", []),
        "current_group": ds.current_group,
        "wm_size": len(ds.engine.wm.facts),
        "session_state": state_snapshot,  # ← stateless Vercel support
    }


def _make_diagnosis_response(ds: DiagnosticSession, session_id: str, result: dict):
    """Tạo response khi session hoàn tất → hiển thị diagnosis card."""
    return jsonify(_build_diagnosis_payload(ds, session_id, result))


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


def _render_static_policy_page(title: str, body_html: str):
    """Render trang pháp lý HTML đơn giản cho Meta Developer App."""
    html = f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} - Expert System</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      line-height: 1.6;
      max-width: 860px;
      margin: 40px auto;
      padding: 0 20px;
      color: #1f2937;
    }}
    h1 {{ color: #111827; }}
    a {{ color: #2563eb; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  {body_html}
</body>
</html>"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Render chat UI."""
    return render_template("chat.html", kb_stats=kb.stats if kb else {})


@app.route("/privacy", methods=["GET"])
def privacy_policy():
    """Privacy Policy tối thiểu cho Meta Developer App."""
    body = """
  <p><strong>Tên ứng dụng:</strong> Expert System.</p>
  <p>
    Expert System là hệ thống chatbot/hệ chuyên gia hỗ trợ chẩn đoán lỗi máy tính
    trong phạm vi học tập, thử nghiệm và demo kỹ thuật.
  </p>
  <h2>Dữ liệu có thể được xử lý</h2>
  <ul>
    <li>Nội dung tin nhắn người dùng gửi tới chatbot.</li>
    <li>Thông tin định danh nền tảng do Meta cung cấp như sender id hoặc user id.</li>
    <li>Log kỹ thuật phục vụ kiểm thử, vận hành và debug.</li>
  </ul>
  <h2>Mục đích sử dụng dữ liệu</h2>
  <p>
    Dữ liệu chỉ được dùng để vận hành chatbot, cải thiện phản hồi, kiểm thử và debug.
    Dữ liệu không được bán cho bên thứ ba.
  </p>
  <h2>Yêu cầu xóa dữ liệu</h2>
  <p>
    Người dùng có thể yêu cầu xóa dữ liệu bằng cách liên hệ email:
    <a href="mailto:nhuutri1311@gmail.com">nhuutri1311@gmail.com</a>.
  </p>
"""
    return _render_static_policy_page("Chính sách quyền riêng tư", body)


@app.route("/terms", methods=["GET"])
def terms_of_service():
    """Terms of Service tối thiểu cho Meta Developer App."""
    body = """
  <p>
    Expert System chỉ phục vụ mục đích học tập, thử nghiệm và demo kỹ thuật.
  </p>
  <ul>
    <li>Kết quả chẩn đoán lỗi máy tính chỉ mang tính tham khảo.</li>
    <li>Người dùng nên liên hệ kỹ thuật viên nếu lỗi nghiêm trọng hoặc có nguy cơ mất dữ liệu.</li>
    <li>Hệ thống không đảm bảo luôn chính xác tuyệt đối trong mọi tình huống.</li>
    <li>Người dùng không nên gửi thông tin nhạy cảm như mật khẩu, OTP hoặc thông tin ngân hàng.</li>
  </ul>
"""
    return _render_static_policy_page("Điều khoản sử dụng", body)


@app.route("/data-deletion", methods=["GET"])
def data_deletion():
    """Data Deletion Instructions tối thiểu cho Meta Developer App."""
    body = """
  <p>
    Người dùng có thể yêu cầu xóa dữ liệu liên quan đến quá trình tương tác với
    Expert System bằng cách gửi email tới:
    <a href="mailto:nhuutri1311@gmail.com">nhuutri1311@gmail.com</a>.
  </p>
  <p><strong>Tiêu đề email đề xuất:</strong> Data Deletion Request - Expert System</p>
  <p>Nội dung email nên bao gồm:</p>
  <ul>
    <li>Nền tảng đã sử dụng, ví dụ Facebook Messenger hoặc Instagram.</li>
    <li>Thời gian tương tác gần đúng.</li>
    <li>Thông tin nhận diện nếu có, ví dụ sender id hoặc user id do nền tảng cung cấp.</li>
  </ul>
  <p>
    Sau khi nhận yêu cầu, dữ liệu liên quan sẽ được kiểm tra và xóa nếu còn được
    lưu trong hệ thống thử nghiệm.
  </p>
"""
    return _render_static_policy_page("Hướng dẫn xóa dữ liệu", body)


@app.route("/start", methods=["POST"])
def start_session():
    """
    Tạo phiên chẩn đoán mới.
    Response: session_id + câu hỏi đầu tiên (Q01) + session_state
    """
    ext = store.create()
    return jsonify(_build_start_payload(ext))


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
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "text là bắt buộc"}), 400

    ds, session_id = _resolve_session(data)
    return jsonify(_process_text_for_session(ds, session_id, text))


@app.route("/select", methods=["POST"])
def handle_select():
    """
    Xử lý khi user click option (single_choice / yes_no).
    Body: { session_id | session_state, question_id, value }
    """
    data = request.get_json(force=True)
    question_id = data.get("question_id", "")
    value = data.get("value", "")

    if not all([question_id, value]):
        return jsonify({"error": "question_id và value là bắt buộc"}), 400

    ds, session_id = _resolve_session(data)

    if ds.is_complete:
        return _make_diagnosis_response(ds, session_id, {})

    # Fix Bug #3: Nếu question đã lỗi thời (stale click sau NLU skip)
    # → trả lại câu hỏi hiện tại thay vì 400 cứng
    if ds.current_question_id != question_id:
        return _make_question_response(
            ds, session_id,
            prefix="⚠️ Câu hỏi đó đã qua. Đây là câu hỏi hiện tại:",
        )

    # Process answer
    result = ds.answer([value])

    if result.get("session_complete") or ds.is_complete:
        return _make_diagnosis_response(ds, session_id, result)

    return _make_question_response(ds, session_id, facts_added=result.get("new_facts", []))


@app.route("/submit", methods=["POST"])
def handle_submit():
    """
    Xử lý khi user submit multi_choice (checkbox).
    Body: { session_id | session_state, question_id, values: [list] }
    """
    data = request.get_json(force=True)
    question_id = data.get("question_id", "")
    values = data.get("values", [])

    if not question_id:
        return jsonify({"error": "question_id là bắt buộc"}), 400

    if not isinstance(values, list):
        return jsonify({"error": "values phải là list"}), 400

    ds, session_id = _resolve_session(data)

    if ds.is_complete:
        return _make_diagnosis_response(ds, session_id, {})

    # Fix: soft-match cho stale multi-choice submit
    if ds.current_question_id != question_id:
        return _make_question_response(
            ds, session_id,
            prefix="⚠️ Câu hỏi đó đã qua. Đây là câu hỏi hiện tại:",
        )

    # Multi-choice: thêm SUBMIT nếu chưa có
    if "SUBMIT" not in values and values:
        values = values + ["SUBMIT"]

    result = ds.answer(values)

    if result.get("session_complete") or ds.is_complete:
        return _make_diagnosis_response(ds, session_id, result)

    return _make_question_response(ds, session_id, facts_added=result.get("new_facts", []))


@app.route("/explanation", methods=["GET"])
def get_explanation():
    """
    Trả full explanation của session.
    Query param: session_id
    Hoặc POST với session_state (stateless mode)
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
    Response: new session_id + Q01 + session_state
    """
    data = request.get_json(force=True)
    old_sid = data.get("session_id", "")

    # Xóa session cũ nếu có (không lỗi nếu không tìm thấy)
    if old_sid:
        store.delete(old_sid)

    # Tạo session mới
    ext = store.create()
    return jsonify(_build_start_payload(ext))


@app.route("/webhook/meta", methods=["GET"])
def verify_meta_webhook():
    """
    Verify webhook từ Meta Developer Console.
    Query: hub.mode, hub.verify_token, hub.challenge
    """
    mode = request.args.get("hub.mode", "")
    verify_token = request.args.get("hub.verify_token", "")
    challenge = request.args.get("hub.challenge", "")
    expected_token = os.getenv("VERIFY_TOKEN", "").strip()

    if mode == "subscribe" and expected_token and verify_token == expected_token:
        print("✅ Meta webhook verified thành công.")
        return challenge, 200

    print("❌ Meta webhook verify thất bại.")
    abort(403)


@app.route("/webhook/meta", methods=["POST"])
def receive_meta_webhook():
    """
    Nhận message event từ Meta Messenger webhook và gửi reply bằng Send API.
    """
    payload = request.get_json(silent=True) or {}
    print(f"📥 Nhận Meta webhook payload: {payload}")

    for entry in payload.get("entry", []):
        for event in entry.get("messaging", []):
            message = event.get("message") or {}
            if message.get("is_echo"):
                print("⏭️ Bỏ qua Meta message echo")
                continue

            sender_id = (event.get("sender") or {}).get("id")
            text = message.get("text")

            if not sender_id or not text:
                continue

            print(f"💬 Meta message sender_id={sender_id}: {text}")
            reply_text = handle_facebook_message(sender_id, text)
            print(f"🤖 Reply Meta sender_id={sender_id}: {reply_text}")
            send_meta_message(sender_id, reply_text)

    return jsonify({"status": "received"})


@app.route("/webhook/instagram", methods=["GET"])
def verify_instagram_webhook():
    """
    Verify webhook từ Instagram API.
    Dùng VERIFY_TOKEN chung với Meta/Facebook để cấu hình demo đơn giản.
    """
    mode = request.args.get("hub.mode", "")
    verify_token = request.args.get("hub.verify_token", "")
    challenge = request.args.get("hub.challenge", "")
    expected_token = os.getenv("VERIFY_TOKEN", "").strip()

    if mode == "subscribe" and expected_token and verify_token == expected_token:
        print("[IG API] Webhook verified successfully.")
        return challenge, 200

    print("[IG API] Webhook verify failed.")
    abort(403)


@app.route("/webhook/instagram", methods=["POST"])
def receive_instagram_webhook():
    """
    Nhận Instagram API webhook.
    Giai đoạn này ưu tiên log raw payload + parse mềm để học payload thật.
    """
    raw_body = request.get_data(as_text=True)
    print(f"[IG API] Raw body: {raw_body}")

    payload = request.get_json(silent=True)
    if payload is None:
        print("[IG API] Payload is not valid JSON or body is empty.")
        return jsonify({"status": "received", "parsed_messages": 0})

    parsed_messages = _extract_instagram_api_messages(payload)
    if not parsed_messages:
        print("[IG API] No sender_id/text message parsed from payload.")

    for sender_id, text in parsed_messages:
        print(f"[IG API] Parsed message sender_id={sender_id}: {text}")
        reply_text = handle_instagram_api_message(sender_id, text)
        print(f"[IG API] Reply text: {reply_text}")
        send_instagram_api_message(sender_id, reply_text)

    return jsonify({
        "status": "received",
        "parsed_messages": len(parsed_messages),
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


@app.errorhandler(403)
def forbidden(e):
    return jsonify({"error": "Forbidden"}), 403


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
