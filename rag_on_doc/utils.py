import fitz 
import os
import uuid
import json
from datetime import datetime
from langchain.chains import ConversationalRetrievalChain
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams
from flask import request
from rag_on_doc.config import redis as redis_client
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.schema import HumanMessage, AIMessage, SystemMessage


def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

def get_session_id():
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

def get_doc_id():
    doc_id = str(uuid.uuid4())
    return doc_id
# to save the chat ids associated with the document uploads
def save_doc_chat_id(session_id, doc_id, title="Untitled Document"):
    key = f"doc_chat:{session_id}"
    message = {"doc_id": doc_id, "title": title, "timestamp": datetime.utcnow().isoformat()}
    redis_client.rpush(key, message)
    redis_client.expire(key, 60 * 60 * 24 * 7)

# to load the chat ids associated with the document uploads
def load_user_chat_list(session_id):
    pattern = f"doc_chat:{session_id}"
    chat_keys = redis_client.lrange(pattern,-20, -1)
    return chat_keys

# to load the message history of user chat associated with document uploads
def load_user_chat_messages(session_id, chat_id):
    """Load message history from Redis"""
    data = redis_client.lrange(f"doc_user_chat:{session_id}:{chat_id}",-20, -1)
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

def save_user_chat_messages(session_id, chat_id, history, timestamp, real_time=False):
    """Save LangChain message history to Redis"""
    serialized = []
    key = f"doc_user_chat:{session_id}:{chat_id}"
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


def get_qdrant_vectorstore(collection_name="pdf_docs"):
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance="Cosine") 
        )

    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    return vectorstore


def store_pdf_in_qdrant(vectorstore, chunks, collection_name="pdf_docs"):

    vectorstore = get_qdrant_vectorstore(collection_name)
    ids = vectorstore.add_texts(chunks)
    return len(ids)



def get_answer_from_query(query, history, collection_name="pdf_docs", top_k=3):
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

    model=os.getenv("MODEL_NAME")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

    llm = ChatOpenAI(model=model, temperature=0.3)

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=False
    )

    answer = qa_chain({"question": query, "chat_history": history})
    return answer["answer"]
    return answer

