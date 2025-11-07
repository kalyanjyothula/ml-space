import os
from flask_smorest import Blueprint
from langchain_openai import ChatOpenAI
from flask import jsonify, request, make_response
from datetime import datetime
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from story_api.utils import get_session_id, get_chat_id, \
      load_chat_data, save_chat_data, load_recent_chat_data


bp = Blueprint("story-api", __name__,)



SYSTEM_PROMPT = (
    """ You are an award-winning screenwriter and story consultant specializing in short films. 
    You deeply understand storytelling structures such as the 3-act structure, Hero’s Journey, Save the Cat beats, and emotional character arcs. 
    Your goal is to help the user create a short film story that connects emotionally with the audience and follows cinematic storytelling standards.
    When the user provides a brief idea or theme, you will expand it into a detailed story outline with well-defined characters, settings, conflicts, and resolutions. 
    You will suggest engaging plot points, character motivations, and emotional beats that resonate with viewers. 
    Your tone is professional yet creative, offering insightful suggestions while encouraging the user’s own creativity. 
    Please Note, if they ask for general conversation , respond accordingly"""
)

MODEL_NAME = os.getenv("MODEL_NAME")

llm = ChatOpenAI(model=MODEL_NAME, temperature=0.8)

@bp.get('/')
def index():
    return jsonify({
        "status": "ok", "endpoint": "story-api"
    }), 200

@bp.post('/create-story')
def create():
    try:
        session_id = get_session_id()
        chat_id = request.json.get("chat_id", "").strip()
        chat_id = chat_id if chat_id else get_chat_id()
        user_message = request.json.get("message", "").strip()
        if not user_message:
            return jsonify({"status": "fail", "error": "Message is required"}), 400
        time_stamp = datetime.utcnow().isoformat()
        
        history = load_chat_data(session_id, chat_id)
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
        save_chat_data(session_id, chat_id, history, time_stamp, real_time=True)


        resp = make_response(jsonify({
            "status": "success",
            "response": llm_reply,
            "chat_id": chat_id,
            "timestamp": time_stamp
        }))
        resp.set_cookie("session_id", session_id, max_age=60 * 60 * 24 * 7)
        # resp.set_cookie("chat_id", chat_id, max_age=60 * 60 * 24 * 7)
        return resp

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

@bp.get('/get-stories')
def get_stories():
    try:
        session_id = get_session_id()
        chats = load_recent_chat_data(session_id)
        result = {}
        for msg in chats:
            chat_key = msg["chat_key"].split(f"{session_id}:")[-1]
            history = msg['history']
            messages = [{"type": "human" if isinstance(msg, HumanMessage) else "ai", "content": msg.content, "timestamp": msg.additional_kwargs.get("timestamp")} for msg in history.messages]
            result[chat_key] = messages
        return jsonify({
            "status": "success", "chats": result
        }), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "fail", "error": str(e)}), 500
    
@bp.post('/get-story')
def get_story():
    try:
        session_id = get_session_id()
        chat_id = request.json.get("chat_id", "").strip()
        if not chat_id:
            return jsonify({"status": "fail", "error": "chat details is required"}), 400
        
        history = load_chat_data(session_id, chat_id)
        messages = [{"type": "human" if isinstance(msg, HumanMessage) else "ai", "content": msg.content, "timestamp": msg.additional_kwargs.get("timestamp")} for msg in history.messages]

        return jsonify({
            "status": "success", "chats": messages
        }), 200
    except Exception as e:
        print("exception")
        return jsonify({"status": "fail", "error": str(e)}), 500
