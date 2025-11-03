import uuid
import json
import os
from flask import request
from datetime import datetime
from excel_companion.config import redis as redis_client
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.chains import ConversationalRetrievalChain
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from qdrant_client import QdrantClient
from langchain.memory import ConversationBufferMemory

session_memories = {}

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

def get_session_id():
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

def get_chat_id():
    chat_id = str(uuid.uuid4())
    return chat_id


def save_chat_id(session_id, chat_id, title="Untitled Document"):
    key = f"excel_user_chat_list:{session_id}"
    message = {"chat_id": chat_id, "title": title, "timestamp": datetime.utcnow().isoformat()}
    redis_client.rpush(key, json.dumps(message))
    redis_client.expire(key, 60 * 60 * 24 * 7)

def load_user_chat_list(session_id):
    pattern = f"excel_user_chat_list:{session_id}"
    chat_keys = redis_client.lrange(pattern,-20, -1)
    return chat_keys

# to load the message history of user chat 
def load_user_chat_messages(session_id, chat_id):
    """Load message history from Redis"""
    data = redis_client.lrange(f"excel_user_chat:{session_id}:{chat_id}", -20, -1)
    messages = []
    if data:
        for msg in data:
            msg = json.loads(msg)
            if msg["type"] == "human":
                messages.append(HumanMessage(content=msg["content"], additional_kwargs={"timestamp": msg["timestamp"]}))
            elif msg["type"] == "ai":
                messages.append(AIMessage(content=msg["content"], additional_kwargs={"timestamp": msg["timestamp"]}))
            elif msg["type"] == "system":
                messages.append(SystemMessage(content=msg["content"], additional_kwargs={"timestamp": msg["timestamp"]}))
    history = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    history.chat_memory.messages.extend(messages)
    return history

def save_user_chat_messages(session_id, chat_id, history, timestamp, real_time=False):
    """Save LangChain message history to Redis"""
    serialized = []
    key = f"excel_user_chat:{session_id}:{chat_id}"
    message_list = history.chat_memory.messages if not real_time else history.chat_memory.messages[-2:]
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



def get_answer_from_query(query, history, collection_name="pdf_docs", top_k=3):
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

    model=os.getenv("MODEL_NAME")

    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

    llm = ChatOpenAI(model=model, temperature=0.5)

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=history,
        return_source_documents=False
    )

    answer = qa_chain.invoke({"question": query})
    return answer["answer"]
