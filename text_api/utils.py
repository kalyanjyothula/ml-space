import validators
import requests
import os
import openai
from langchain_openai import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import YoutubeLoader, UnstructuredURLLoader
from pytubefix import YouTube
from moviepy import AudioFileClip

MAX_DURATION = 60 * 1
MAX_FILESIZE = 1 * 1024 * 1024

def is_valid_url(url=''):
    return validators.url(url)

def get_content(url):
    loader = ''
    if "youtube.com" in url.lower():
        loader = YoutubeLoader.from_youtube_url(youtube_url=url, add_video_info=True, language=["en", "id"],translation="en")
    else:
        loader=UnstructuredURLLoader(urls=[url],ssl_verify=False,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"})
    return loader

def get_summarized_content(loader, model, prompt):
    output_summary = ''
    if(loader):
        docs=loader.load() if loader else {}
        chain = load_summarize_chain(model, chain_type="stuff", prompt=prompt, document_variable_name="page_content" )
        output_summary = chain.invoke(docs)
    return output_summary

def connect_to_model(model_name):
    api_key = os.getenv("OPEN_AI_API_KEY")
    TEMP = os.getenv("TEMPERATURE", 0.2)
    llm = ChatOpenAI(openai_api_key=api_key, model=model_name, temperature=TEMP)
    return llm

def audio_to_text_content(url):
    transcription = ''
    file_path = ''
    if "youtube.com" in url.lower():
        yt = YouTube(url)
        if yt.length > MAX_DURATION:
            raise ValueError(f"Video is too long (exceeds {MAX_DURATION//60} minutes).")
        video = yt.streams.get_audio_only()
        if video.filesize and video.filesize > MAX_FILESIZE:
            raise ValueError(f"Audio file is too large (exceeds {MAX_FILESIZE/(1024*1024)} MB).")
        downloaded_file = video.download()
        audio_clip = AudioFileClip(downloaded_file)
        new_path = downloaded_file.replace(' ','_')
        file_path = os.path.splitext(new_path)[0] + '.wav'
        audio_clip.write_audiofile(file_path)
        transcription = transcribe_audio_file(file_path)
        os.remove(downloaded_file)
    else:
        file_path = download_audio_file(url, "temp_audio_file")
        transcription = transcribe_audio_file(file_path)
    # Clean up files
    if os.path.exists(file_path): os.remove(file_path)
    return transcription
 
def transcribe_audio_file(file_path):
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILESIZE:
        raise ValueError(f"File size exceeds {MAX_FILESIZE/(1024*1024)}MB limit.")
    transcription = ''
    with open(file_path, "rb") as audio_file:
        transcription = openai.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe", 
            file=audio_file
        )
    return transcription.text

def download_audio_file(audio_url, save_path):
    response = requests.get(audio_url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return save_path
    else:
        raise Exception("Failed to download audio file")
     
def get_summarized_content_audio(loader, model, prompt):
    output_summary = ''
    if(loader):
        chain = load_summarize_chain(model, chain_type="stuff", prompt=prompt, document_variable_name="page_content")
        output_summary = chain.invoke(loader)
    return output_summary