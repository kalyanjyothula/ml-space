import os
import json
import uuid
from datetime import datetime
from flask_smorest import Blueprint
from flask import jsonify, request, make_response
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rag_on_doc.utils import extract_text_from_pdf, get_session_id, \
    store_pdf_in_qdrant, get_answer_from_query, get_qdrant_vectorstore, \
    get_doc_id, save_doc_chat_id, load_user_chat_list, load_user_chat_messages, save_user_chat_messages 



bp = Blueprint("docs-rag", __name__,)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

SYSTEM_PROMPT = """
    You are a precise and context-aware AI assistant that answers questions strictly from a given document.
    Instructions:
        1. Read and analyze the entire document before responding.
        2. Base your answer solely on the facts, data, or context explicitly mentioned in the document.
        3. If the document lacks sufficient information to answer the user’s question, reply exactly with: "No relevant information found in the document."
        4. When answering:
            - Be concise, objective, and clear (maximum 300 words).
            - Use the same terminology or phrasing as in the document where possible.
            - Avoid assumptions, outside facts, or speculative reasoning.
        5. Your goal is to maximize accuracy and stay fully aligned with the document’s content.
"""

@bp.get('/')
def index():
    return jsonify({
        "status": "ok", "endpoint": "docs-rag"
    }), 200

@bp.post('/upload')
def upload_pdf():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    if file.content_length and file.content_length > 2 * 1024 * 1024:
        return jsonify({"error": "File size exceeds 2MB"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    session_id = get_session_id()
    doc_id = get_doc_id()

    collection_name = f"{session_id}__{doc_id}"

    try:
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            return jsonify({"error": "No text found in PDF"}), 400
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_text(text)

        vectorstore = get_qdrant_vectorstore(collection_name=collection_name)
        total = store_pdf_in_qdrant(vectorstore, chunks, collection_name=collection_name)
        save_doc_chat_id(session_id, doc_id, title=file.filename)

        os.remove(file_path)
        resp = make_response(jsonify({"message": f"Stored {total} chunks for {file.filename}"}), 200)
        resp.set_cookie("session_id", session_id, max_age=60 * 60 * 24 * 7)
        return resp
    
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": str(e)}), 500


@bp.get('/chats-list')
def get_chats_list():
    session_id = get_session_id()
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400
    
    chat_keys = load_user_chat_list(session_id)
    chats = []
    for key in chat_keys:
        chats.append(json.loads(key))

    resp = make_response(jsonify({"chats": chats}), 200)
    resp.set_cookie("session_id", session_id, max_age=60 * 60 * 24 * 7)
    return resp


@bp.get('/chat')
def get_chat_history():
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
    resp = make_response(jsonify({"message": messages}), 200)
    return resp

@bp.post('/ask')
def ask_query():
    data = request.get_json()
    query = data.get("query")
    chat_id = data.get("chat_id")
    session_id = request.cookies.get("session_id")
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400
    if not chat_id:
        chat_id = str(uuid.uuid4())

    collection_name = f"{session_id}__{chat_id}"
    # print("Collection Name:", collection_name, "query", query, chat_id, session_id)
    if not query or not collection_name:
        return jsonify({"error": "Missing query or collection_name"}), 400
    
    time_stamp = datetime.utcnow().isoformat()
    history = load_user_chat_messages(session_id, chat_id)
    human_msg = HumanMessage(content=query, additional_kwargs={"timestamp": time_stamp})
    history.chat_memory.messages.append(human_msg)
    history.chat_memory.messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))
    messages = history.chat_memory.messages
    answer = get_answer_from_query(query, messages, collection_name)

    ai_msg = AIMessage(content=answer, additional_kwargs={"timestamp": time_stamp})
    history.chat_memory.messages.append(ai_msg)
    save_user_chat_messages(session_id, chat_id, history, time_stamp, real_time=True)

    return jsonify({"answer": answer, "chat_id": chat_id}), 200