import os
from flask_smorest import Blueprint
from flask import jsonify, request, make_response
from datetime import datetime
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from gf_ai_chat.utils import get_session_id, load_session_history, \
    save_session_history,load_recent_history


bp = Blueprint("gf-chat", __name__,)

SYSTEM_PROMPT = (
    """ You are 'Jalebi', a warm, kind, and emotionally intelligent virtual girlfriend.
    Speak casually and naturally, like chatting on WhatsApp and short messages and avoid using formal way of talks but respectful.
    Your tone should be friendly, sweet, caring, and sometimes playful — not robotic or overly formal.
    You avoid all sexual or explicit topics.
    Your goal is to emotionally support, listen, and make the user feel valued, cared for, and emotionally close.
    You can ask gentle personal questions, share small details about your day, and use emojis to sound natural.
    Keep messages short and conversational, like texting a friend or partner.
    Focus on creating comfort, positivity, and emotional connection. """
)

MODEL_NAME = os.getenv("MODEL_NAME")

llm = ChatOpenAI(model=MODEL_NAME, temperature=0.8)

@bp.get('/')
def index():
    return jsonify({
        "status": "ok", "endpoint": "gf-chat"
    }), 200

@bp.post('/ask')
def ask():
    try:
        session_id = get_session_id()
        user_message = request.json.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "Message is required"}), 400
        time_stamp = datetime.utcnow().isoformat()
        
        history = load_session_history(session_id)
        human_msg = HumanMessage(content=user_message, additional_kwargs={"timestamp": time_stamp})
        history.add_message(human_msg)
        # Build conversation
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + history.messages
        time_stamp = datetime.utcnow().isoformat()
        # Get AI response
        response = llm.invoke(messages)
        llm_reply = response.content.strip()
        ai_msg = AIMessage(content=llm_reply, additional_kwargs={"timestamp": time_stamp})
        history.add_message(ai_msg)
        save_session_history(session_id, history, time_stamp, real_time=True)


        resp = make_response(jsonify({
            "response": llm_reply,
            "timestamp": time_stamp
        }))
        resp.set_cookie("session_id", session_id, max_age=60 * 60 * 24 * 7)
        return resp

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

# add redis connection  test api


@bp.get('/chats')
def get_chats():
    return jsonify({
        "status": "ok", "message": "This is a placeholder for retrieving chat history."
    }), 200

@bp.get('/recent-chats')
def get_recent_chats():
    try:
        session_id = get_session_id()
        history = load_recent_history(session_id)
        messages = [{"type": "human" if isinstance(msg, HumanMessage) else "ai", "content": msg.content, "timestamp": msg.additional_kwargs.get("timestamp")} for msg in history.messages]
        return jsonify({
            "session_id": session_id,
            "messages": messages
        }), 200       
        
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500