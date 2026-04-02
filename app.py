"""
Computer Expert System - Flask Application (Hybrid)

Supports TWO modes:
1. GUIDED MODE (/diagnose) — Original QuestionFlow with yes/no buttons
2. HYBRID MODE (/chat)    — NLP + backward chaining + chatbot-style UI

Flask routes contain NO inference logic — all delegated to InferenceService.
"""

import os
import sys
import time
import json
import logging

from flask import (
    Flask, render_template, request, session,
    redirect, url_for, jsonify
)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.question_controller import QuestionController
from engine.inference_service import InferenceService
from engine.state_manager import StateManager
from utils.nlp_parser import parse_input, get_nlp_summary
from utils.answer_interpreter import interpret_answer
from utils.response_generator import get_natural_acknowledgment, get_nlp_natural_summary

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    template_folder='web/templates',
    static_folder='web/static'
)
app.secret_key = 'computer_expert_system_secret_key_2024'

# Initialize shared components
question_controller = QuestionController()
inference_service = InferenceService()


# ═══════════════════════════════════════════════════════
#  HOME
# ═══════════════════════════════════════════════════════

@app.route('/')
def index():
    """Homepage - choose between guided and hybrid mode."""
    session.clear()
    return render_template('index.html')


# ═══════════════════════════════════════════════════════
#  GUIDED MODE (original, preserved)
# ═══════════════════════════════════════════════════════

@app.route('/diagnose', methods=['GET', 'POST'])
def diagnose():
    """Original guided question flow (backward-compatible)."""
    if request.method == 'GET':
        if 'current_step' not in session:
            session['current_step'] = question_controller.get_first_step()
            session['answers'] = {}
            session['start_time'] = time.time()
            session['question_count'] = 0
            session['pending_question'] = None
            session['pending_rule_id'] = None
            session['pending_missing'] = None

        pending_q = session.get('pending_question')
        if pending_q:
            question_number = session.get('question_count', 0) + 1
            return render_template('question.html',
                                   question=pending_q,
                                   question_number=question_number,
                                   answers=session.get('answers', {}))

        current_step = session['current_step']

        if current_step == 'END':
            return redirect(url_for('result'))

        if str(current_step).startswith('R'):
            session['flow_rule_id'] = current_step
            return redirect(url_for('result'))

        question_data = question_controller.get_question_for_step(current_step)
        if not question_data:
            return redirect(url_for('result'))

        question_number = session.get('question_count', 0) + 1
        return render_template('question.html',
                               question=question_data,
                               question_number=question_number,
                               answers=session.get('answers', {}))

    elif request.method == 'POST':
        answer_value = request.form.get('answer')
        if answer_value is None:
            return redirect(url_for('diagnose'))

        answer = (answer_value == 'yes')

        # Handle pending question
        pending_q = session.get('pending_question')
        pending_rule_id = session.get('pending_rule_id')
        pending_missing = session.get('pending_missing', [])

        if pending_q and pending_rule_id:
            answers = dict(session.get('answers', {}))
            answered_code = pending_q['question_code']
            answers[answered_code] = answer
            session['answers'] = answers
            session['question_count'] = session.get('question_count', 0) + 1

            remaining_missing = [c for c in pending_missing if c != answered_code]

            if remaining_missing:
                next_code = remaining_missing[0]
                next_q = question_controller._make_question_for_symptom(
                    next_code, pending_rule_id
                )
                session['pending_question'] = next_q
                session['pending_missing'] = remaining_missing
                return redirect(url_for('diagnose'))
            else:
                session['pending_question'] = None
                session['pending_missing'] = None
                session['flow_rule_id'] = pending_rule_id
                session['pending_rule_id'] = None
                return redirect(url_for('result'))

        # Normal flow
        current_step = session.get('current_step', '1')
        nav = question_controller.process_answer(
            current_step, answer, dict(session.get('answers', {}))
        )

        if nav is None:
            return redirect(url_for('result'))

        session['answers'] = nav['updated_answers']
        session['question_count'] = session.get('question_count', 0) + 1

        if nav.get('pending_question'):
            session['pending_question'] = nav['pending_question']
            session['pending_rule_id'] = nav['pending_rule_id']
            session['pending_missing'] = nav['pending_missing']
            return redirect(url_for('diagnose'))

        if nav['is_rule']:
            session['flow_rule_id'] = nav['rule_id']
            session['current_step'] = nav['next_step']
            return redirect(url_for('result'))
        elif nav['is_end']:
            session['current_step'] = 'END'
            return redirect(url_for('result'))
        else:
            session['current_step'] = nav['next_step']
            return redirect(url_for('diagnose'))


@app.route('/result')
def result():
    """Guided mode result page."""
    answers = session.get('answers', {})
    flow_rule_id = session.get('flow_rule_id')
    question_count = session.get('question_count', 0)
    start_time = session.get('start_time')

    if not answers:
        return redirect(url_for('index'))

    session_time_s = round(time.time() - start_time, 1) if start_time else 0

    diagnosis = inference_service.run_quick_diagnosis(
        answers, rule_id=flow_rule_id
    )

    debug_mode = request.args.get('debug', 'false').lower() == 'true'

    return render_template('result.html',
                           diagnosis=diagnosis,
                           answers=answers,
                           question_count=question_count,
                           session_time_s=session_time_s,
                           debug_mode=debug_mode)


# ═══════════════════════════════════════════════════════
#  HYBRID MODE (NEW — chatbot-style)
# ═══════════════════════════════════════════════════════

@app.route('/chat')
def chat():
    """Hybrid mode chat page."""
    session.clear()
    state = StateManager()
    session['hybrid_state'] = state.to_dict()
    session['chat_messages'] = []
    session['chat_mode'] = 'initial'  # initial | asking | done
    return render_template('chat.html')


@app.route('/chat/send', methods=['POST'])
def chat_send():
    """
    Handle chat input (text or yes/no button).
    Returns JSON for AJAX updates.

    Input processing pipeline (3-tier):
    1. Button click (answer + question_code) — direct fact
    2. Contextual answer interpreter (if current_question exists) — 'có'/'không'
    3. NLP free-text parser — keyword extraction
    4. Clarification fallback — ask user to rephrase
    """
    data = request.get_json() or {}
    user_input = data.get('message', '').strip()
    answer_value = data.get('answer')  # 'yes' or 'no' for button clicks
    current_question_code = data.get('question_code')

    # Restore state
    state_data = session.get('hybrid_state')
    if not state_data:
        return jsonify({'error': 'Session expired', 'redirect': url_for('chat')})

    state = StateManager.from_dict(state_data)
    messages = session.get('chat_messages', [])

    # Track how the input was resolved (for debug)
    input_source = None
    resolved_fact_code = None
    resolved_fact_value = None

    # ════════════════════════════════════════════
    #  TIER 1: Button click (yes/no)
    # ════════════════════════════════════════════
    if answer_value and current_question_code:
        fact_value = (answer_value == 'yes')
        state.add_fact(current_question_code, fact_value)
        state.mark_asked(current_question_code)
        state.clear_current_question()

        user_msg = "Có ✅" if fact_value else "Không ❌"
        messages.append({'role': 'user', 'text': user_msg})

        input_source = 'button_click'
        resolved_fact_code = current_question_code
        resolved_fact_value = fact_value

    elif user_input:
        messages.append({'role': 'user', 'text': user_input})

        # ════════════════════════════════════════
        #  TIER 2: Contextual answer interpreter
        #  (only if there's an active question)
        # ════════════════════════════════════════
        active_q = state.current_question
        interpretation = None

        if active_q:
            interpretation = interpret_answer(user_input, active_q)

        if interpretation is not None:
            # Successfully interpreted in context
            fact_value = interpretation['value']
            state.add_fact(active_q, fact_value)
            state.mark_asked(active_q)
            state.clear_current_question()

            ack_text = get_natural_acknowledgment(active_q, fact_value, is_contextual=True)
            messages.append({
                'role': 'system',
                'text': f'✅ {ack_text}'
            })

            input_source = f'contextual_answer ({interpretation["source"]})'
            resolved_fact_code = active_q
            resolved_fact_value = fact_value

        else:
            # ════════════════════════════════════
            #  TIER 3: NLP free-text parser
            # ════════════════════════════════════
            extracted = parse_input(user_input)

            if extracted:
                state.add_facts(extracted)
                for code in extracted:
                    state.mark_asked(code)

                # If the active question was answered by NLP, clear it
                if active_q and active_q in extracted:
                    state.clear_current_question()

                summary_text = get_nlp_natural_summary(extracted)
                messages.append({'role': 'system', 'text': summary_text})

                input_source = 'nlp_parser'
                # Report first extracted fact for debug
                first_code = list(extracted.keys())[0]
                resolved_fact_code = first_code
                resolved_fact_value = extracted[first_code]

            else:
                # ════════════════════════════════
                #  TIER 4: Clarification fallback
                # ════════════════════════════════
                if active_q:
                    messages.append({
                        'role': 'system',
                        'text': '🤔 Xin lỗi, tôi chưa hiểu rõ. '
                                'Bạn có thể trả lời bằng **"có"** hoặc **"không"**, '
                                'hoặc mô tả rõ hơn một chút.'
                    })
                    input_source = 'clarification_with_question'
                else:
                    messages.append({
                        'role': 'system',
                        'text': '🤔 Tôi chưa nhận diện được triệu chứng từ mô tả. '
                                'Hãy để tôi hỏi thêm một số câu hỏi.'
                    })
                    input_source = 'clarification_no_question'
    else:
        return jsonify({'error': 'No input provided'})

    # ══════════════════════════════════════════════
    #  Run Hybrid Step (forward → backward chain)
    # ══════════════════════════════════════════════
    step_result = inference_service.run_hybrid_step(state)

    # ── Build Response ──
    response = {'messages': []}

    if step_result['status'] == 'diagnosed':
        diagnosis = step_result['diagnosis']
        explanation = step_result['explanation']

        messages.append({
            'role': 'result',
            'text': f"🎯 Đã xác định nguyên nhân!",
            'diagnosis': {
                'rule_id': diagnosis['rule_id'],
                'cause': diagnosis['cause'],
                'solution': diagnosis['solution'],
                'diagnosis_time_ms': diagnosis['diagnosis_time_ms'],
                'questions_asked': diagnosis['questions_asked'],
                'all_matches_count': len(diagnosis['all_matches']),
                'decision_source': diagnosis['decision_source'],
            },
            'explanation': explanation
        })

        session['chat_mode'] = 'done'
        response['status'] = 'diagnosed'
        response['diagnosis'] = diagnosis
        response['explanation'] = explanation

    elif step_result['status'] == 'need_input':
        question = step_result['question']
        candidates = step_result['candidates_remaining']

        # ── Store current_question in state ──
        state.set_current_question(question['question_code'])

        messages.append({
            'role': 'question',
            'text': question['question_text'],
            'question_code': question['question_code'],
            'group': question['group'],
            'reason': question['reason'],
            'candidates_remaining': candidates
        })

        session['chat_mode'] = 'asking'
        response['status'] = 'need_input'
        response['question'] = question
        response['candidates_remaining'] = candidates

    else:  # no_more_questions
        diagnosis = step_result['diagnosis']
        messages.append({
            'role': 'result',
            'text': '🤔 ' + diagnosis['cause'],
            'diagnosis': {
                'rule_id': None,
                'cause': diagnosis['cause'],
                'solution': diagnosis['solution'],
                'diagnosis_time_ms': diagnosis['diagnosis_time_ms'],
                'questions_asked': diagnosis['questions_asked'],
                'all_matches_count': 0,
                'decision_source': 'fallback',
            }
        })

        session['chat_mode'] = 'done'
        response['status'] = 'no_match'
        response['diagnosis'] = diagnosis

    # Save state
    session['hybrid_state'] = state.to_dict()
    session['chat_messages'] = messages

    # Enhanced debug info
    response['debug'] = {
        'input_source': input_source,
        'resolved_fact': f'{resolved_fact_code} = {resolved_fact_value}' if resolved_fact_code else None,
        'current_question': state.current_question,
        'facts': state.facts,
        'candidates_count': len(state.candidate_rules),
        'asked_count': len(state.asked),
        'history': state.history[-5:]
    }

    response['messages'] = messages

    return jsonify(response)


@app.route('/chat/state')
def chat_state():
    """Get current chat state (for page reload)."""
    return jsonify({
        'messages': session.get('chat_messages', []),
        'mode': session.get('chat_mode', 'initial')
    })


# ═══════════════════════════════════════════════════════
#  COMMON
# ═══════════════════════════════════════════════════════

@app.route('/reset')
def reset():
    """Reset the session and go home."""
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
