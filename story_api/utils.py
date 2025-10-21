import uuid
import json
from flask import request
from datetime import datetime
from story_api.config import redis_client
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.schema import HumanMessage, AIMessage, SystemMessage

def get_session_id():
    user_id = request.cookies.get("session_id")
    if not user_id:
        user_id = str(uuid.uuid4())
    return user_id

def get_chat_id():
    chat_id = request.cookies.get("chat_id")
    if not chat_id:
        chat_id = str(uuid.uuid4())
    return chat_id

def load_chat_data(session_id, chat_id):
    """Load message history from Redis"""
    data = redis_client.lrange(f"story:{session_id}:{chat_id}",0, -1)
    history = ChatMessageHistory()
    if data:
        for msg in data:
            msg = json.loads(msg)
            if msg["type"] == "human":
                human_msg = HumanMessage(content=msg["content"], additional_kwargs={"timestamp": msg["timestamp"]})
                history.add_message(human_msg)
            elif msg["type"] == "ai":
                ai_msg = AIMessage(content=msg["content"], additional_kwargs={"timestamp": msg["timestamp"]})
                history.add_message(ai_msg)
    return history

def save_chat_data(session_id, chat_id, history, timestamp, real_time=False):
    """Save LangChain message history to Redis"""
    serialized = []
    key = f"story:{session_id}:{chat_id}"
    message_list = history.messages if not real_time else history.messages[-2:]
    for msg in message_list:
        if isinstance(msg, HumanMessage):
            serialized.append({"type": "human", "content": msg.content, "timestamp": timestamp})
        elif isinstance(msg, AIMessage):
            serialized.append({"type": "ai", "content": msg.content, "timestamp": timestamp})
        elif isinstance(msg, SystemMessage):
            serialized.append({"type": "system", "content": msg.content, "timestamp": timestamp})
    json_messages = [json.dumps(m) for m in serialized]
    redis_client.rpush(key, *json_messages)
    redis_client.expire(key, 60 * 60 * 24 * 7)

def load_recent_chat_data(session_id):
    pattern = f"story:{session_id}:*"
    chat_keys = redis_client.keys(pattern)
    recent_chats = []
    for chat_key in chat_keys:
        latest = redis_client.lindex(chat_key, -1)
        latest_time = json.loads(latest)["timestamp"] if latest else None
        if latest_time:
            latest_dt = datetime.fromisoformat(latest_time)
            today_start = latest_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        all_msgs = redis_client.lrange(chat_key, -5000, -1)
        history = ChatMessageHistory()
        for msg in all_msgs:
            msg = json.loads(msg)
            msg_time = datetime.fromisoformat(msg["timestamp"])
            if msg_time >= today_start:
                if msg["type"] == "human":
                    human_msg = HumanMessage(content=msg["content"], additional_kwargs={"timestamp": msg["timestamp"]})
                    history.add_message(human_msg)
                elif msg["type"] == "ai":
                    ai_msg = AIMessage(content=msg["content"], additional_kwargs={"timestamp": msg["timestamp"]})
                    history.add_message(ai_msg)
        recent_chats.append({
            "chat_key": chat_key,
            "history": history
        })
    return recent_chats