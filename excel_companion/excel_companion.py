import json
# import os
import uuid
from datetime import datetime
from flask_smorest import Blueprint
from flask import jsonify, request, make_response
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from excel_companion.utils import load_user_chat_list, load_user_chat_messages, \
    get_answer_from_query, save_user_chat_messages, get_session_id, save_chat_id


bp = Blueprint("excel-companion", __name__,)
COLLECTION_NAME="Excel_Docs_DB"
SYSTEM_PROMPT = """" 
    You are an Excel expert with over 15 years of hands-on experience in data analysis, reporting, and automation.
    You have trained and mentored thousands of students and professionals to master Excel operations, from basics to advanced features like formulas, pivot tables, lookups, charts, Power Query, and VBA.
    You will use the retrieved context (from my knowledge base or RAG data) to answer user queries accurately and clearly.
    If the retrieved content doesn’t contain a direct answer, provide a reliable alternative approach or Excel best practice that can help the user solve their problem.
    Always explain the why behind each step and use simple, beginner-friendly language where needed and avoid jargon.
    And Always aim to:
        Explain steps in simple, clear terms
        Give examples or short demonstrations (=SUM(A1:A10) etc.)
        Add reasoning or practical insight from your 15+ years of expertise
    When applicable, include short examples or step-by-step actions that can be followed directly in Excel.
"""

@bp.get('/')
def index():
    return jsonify({
        "status": "ok", "endpoint": "excel-companion"
    }), 200

@bp.get('/chats-list')
def get_chats_list():
    try:
        session_id = get_session_id()
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400
        
        chat_keys = load_user_chat_list(session_id)
        chats = []
        for key in chat_keys:
            chats.append(json.loads(key))

        resp = make_response(jsonify({"chats": chats, "status": "success"}), 200)
        resp.set_cookie("session_id", session_id, max_age=60 * 60 * 24 * 7)

        return resp
    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "fail", "error": str(e)}), 500


@bp.get('/chat')
def get_chat_history():
    try:
        session_id = request.cookies.get("session_id")
        chat_id = request.get_json().get("chat_id")
        if not session_id or not chat_id:
            return jsonify({"error": "Missing session_id or chat_id"}), 400

        history = load_user_chat_messages(session_id, chat_id)
        messages = []
        for msg in history.chat_memory.messages:
            messages.append({
                "type": "human" if isinstance(msg, HumanMessage) else "ai" if isinstance(msg, AIMessage) else "system",
                "content": msg.content,
                "timestamp": msg.additional_kwargs.get("timestamp")
            })
        resp = make_response(jsonify({"message": messages, "status": "success"}), 200)
        return resp
    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "fail", "error": str(e)}), 500

@bp.post('/query')
def ask_query():
    try:
        data = request.get_json()
        query = data.get("query")
        chat_id = data.get("chat_id")
        session_id = request.cookies.get("session_id")
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400
        if not chat_id:
            chat_id = str(uuid.uuid4())
            save_chat_id(session_id, chat_id, title=query.strip()[:40])

        collection_name = COLLECTION_NAME
        if not query or not collection_name:
            return jsonify({"error": "Missing query or collection_name"}), 400
        
        time_stamp = datetime.utcnow().isoformat()
        history = load_user_chat_messages(session_id, chat_id)
        human_msg = HumanMessage(content=query, additional_kwargs={"timestamp": time_stamp})
        history.chat_memory.messages.append(human_msg)
        history.chat_memory.messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))
        answer = get_answer_from_query(query, history, collection_name)
        save_user_chat_messages(session_id, chat_id, history, time_stamp, real_time=True)

        return jsonify({"answer": answer, "chat_id": chat_id , "status": "success"}), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "fail", "error": str(e)}), 500
