import os
import traceback
from flask import request, jsonify
from flask_smorest import Blueprint
from langchain_core.prompts import PromptTemplate
from text_api.utils import connect_to_model, is_valid_url, transcribe_audio_file, \
    get_content, get_summarized_content, audio_to_text_content, get_summarized_content_audio
from langchain_core.documents import Document

bp = Blueprint("text-api", __name__,)

@bp.get('/')
def index():
    return {
        "status": "ok"
    }

@bp.post('/text-summarize')
def get_text_summarize():
    data = request.get_json()
    url = data.get("url")
    model_name = os.getenv("MODEL_NAME")  
    try:    
        prompt_template="""
            Provide a summary of the following content in 500 words and please use subtitles and bullet points whenever necessary.
            Make sure the summary is easy to understand and captures the main points effectively. Avoid using overly technical language or jargon, and aim for clarity and conciseness.:
            Content:{page_content}
            """
        prompt=PromptTemplate(template=prompt_template,input_variables=["page_content"])

        if not is_valid_url(url):
            return jsonify({ 
                "status": "failed",
                "error": "URL is not valid"}), 400

        loader = get_content(url)
        llm = connect_to_model(model_name)
        summarized_content = get_summarized_content(loader, llm, prompt)
        if 'output_text' in summarized_content:
            summarized_content = summarized_content['output_text']
        return jsonify({"status": "success", "summary": summarized_content}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "failed", "message": str(e)}), 500


@bp.post('/audio-summarize')
def get_audio_summarize():
    data = request.get_json()
    url = data.get("url")
    model_name = os.getenv("MODEL_NAME")
    try:    
        prompt_template="""
            Provide a summary of the following content in 500 words and please use subtitles and bullet points whenever necessary.
            Make sure the summary is easy to understand and captures the main points effectively. Avoid using overly technical language or jargon, and aim for clarity and conciseness.:
            Content:{page_content}
            """
        prompt=PromptTemplate(template=prompt_template,input_variables=["page_content"])

        if not is_valid_url(url):
            return jsonify({ "status": "failed", "error": "URL is not valid"}), 400
    
        loader = audio_to_text_content(url)
        llm = connect_to_model(model_name)
        if(loader):
            summarized_content = ''
            if isinstance(loader, str): 
                loader = [Document(page_content=loader)]
                summarized_content = get_summarized_content_audio(loader, llm, prompt)
            else:
                summarized_content = get_summarized_content(loader, llm, prompt)
            output = ''
            if 'output_text' in summarized_content:
                output = summarized_content['output_text']
            return jsonify({"status": "success", "summary": output}), 200
        else:
            return jsonify({"status": "failed", "message": "unsupported audio url"}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "failed", "message": str(e)}), 500

@bp.post("/audio-transcribe")
def transcribe_audio():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    model_name = os.getenv("MODEL_NAME")
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        # Save the uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        file.save(temp_path)
        transcription = transcribe_audio_file(temp_path)
        if(transcription is None):
            os.remove(temp_path)
            return jsonify({"error": "Transcription failed"}), 500

        llm = connect_to_model(model_name)
        prompt_template="""
            Provide a summary of the following content in 500 words and please use subtitles and bullet points whenever necessary.
            Make sure the summary is easy to understand and captures the main points effectively. Avoid using overly technical language or jargon, and aim for clarity and conciseness.:
            Content:{page_content}
            """
        prompt=PromptTemplate(template=prompt_template,input_variables=["page_content"])

        loader = [Document(page_content=transcription)]
        summarized_content = get_summarized_content_audio(loader, llm, prompt)
        os.remove(temp_path)
        output = ''
        if 'output_text' in summarized_content:
            output = summarized_content['output_text']
           
        return jsonify({
            "status": "success",
            "transcript": output
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



