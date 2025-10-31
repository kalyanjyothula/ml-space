import requests
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import fitz 
from flask import jsonify
from dotenv import load_dotenv
from rag_on_doc.utils import get_qdrant_vectorstore, store_pdf_in_qdrant

load_dotenv()

OPENAI_API_KEY = os.getenv('OPEN_AI_API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4o-mini')
topic = "Excel Sheet"

main_url ="https://www.w3schools.com/excel/"


excel_links = [
    "index.php",
    "excel_introduction.php",
    "excel_get_started.php",
    "excel_overview.php",
    "excel_syntax.php",
    "excel_ranges.php",
    "excel_filling.php",
    "excel_fill_double_click.php",
    "excel_move_cells.php",
    "excel_add_cells.php",
    "excel_delete_cells.php",
    "excel_undo_redo.php",
    "excel_formulas.php",
    "excel_rel_ref.php",
    "excel_abs_ref.php",
    "excel_addition.php",
    "excel_subtraction.php",
    "excel_multiplication.php",
    "excel_division.php",
    "excel_parantheses.php",
    "excel_functions.php",
    "excel_formatting.php",
    "excel_format_painter.php",
    "excel_format_colors.php",
    "excel_format_fonts.php",
    "excel_format_borders.php",
    "excel_format_numbers.php",
    "excel_format_grids.php",
    "excel_format_settings.php",
    "excel_sort.php",
    "excel_filter.php",
    "excel_tables.php",
    "excel_table_design.php",
    "excel_table_resizing.php",
    "excel_table_removing_duplicates.php",
    "excel_convert_table_to_range.php",
    "excel_table_style.php",
    "excel_conditional_formatting.php",
    "excel_highlight_cell_rules.php",
    "excel_cf_greater_than.php",
    "excel_cf_less_than.php",
    "excel_cf_between.php",
    "excel_cf_equal_to.php",
    "excel_cf_text_that_contains.php",
    "excel_cf_date_occurring.php",
    "excel_cf_duplicate_unique.php",
    "excel_cf_top_bottom_rules.php",
    "excel_cf_above_below_average.php",
    "excel_cf_data_bars.php",
    "excel_cf_color_scales.php",
    "excel_cf_icon_sets.php",
    "excel_cf_manage_rules.php",
    "excel_charts.php",
    "excel_charts_bar.php",
    "excel_charts_stacked.php",
    "excel_charts_cols.php",
    "excel_charts_cols_stacked.php",
    "excel_charts_pie.php",
    "excel_charts_line.php",
    "excel_charts_line_stacked.php",
    "excel_charts_line_stacked_100p.php",
    "excel_charts_radar.php",
    "excel_charts_customization.php",
    "excel_table_pivot_intro.php",
    "excel_case_poke_shop.php",
    "excel_case_poke_shop_style.php",
    "excel_and.php",
    "excel_average.php",
    "excel_averageif.php",
    "excel_averageifs.php",
    "excel_concat.php",
    "excel_count.php",
    "excel_counta.php",
    "excel_countblank.php",
    "excel_countif.php",
    "excel_countifs.php",
    "excel_if.php",
    "excel_ifs.php",
    "excel_left.php",
    "excel_lower.php",
    "excel_max.php",
    "excel_median.php",
    "excel_min.php",
    "excel_mode.php",
    "excel_npv.php",
    "excel_or.php",
    "excel_rand.php",
    "excel_right.php",
    "excel_stdevp.php",
    "excel_stdevs.php",
    "excel_sum.php",
    "excel_sumif.php",
    "excel_sumifs.php",
    "excel_trim.php",
    "excel_vlookup.php",
    "excel_xor.php",
    "excel_howto_convert_time_to_seconds.php",
    "excel_howto_find_the_difference_between_two_times.php",
    "excel_howto_net_present_value.php",
    "excel_howto_remove_duplicates.php",
    "excel_exercises.php",
    "excel_syllabus.php",
    "excel_study_plan.php",
    "excel_exam.php",
    "excel_training.php",
    "excel_keyboard_shortcuts.php"
]



def extract_clean_text(url):
    print(f"Fetching: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    # print(soup, "soup")

    # Remove unwanted sections
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Remove unwanted sections by class names
    classes_to_remove = ["w3-sidebar", "sidesection","leftmenuinner", 
                        "ws-hide-on-logged-in", "footer", "topnavcontainer",
                        "w3-clear", 'user-profile-bottom-wrapper', "ga-bottom",
                        "fa", ]
    for class_name in classes_to_remove:
        for tag in soup.select(f".{class_name}"):
            tag.decompose()
    
    ids_to_remove = ["spacemyfooter", "top-nav-bar"]
    for id_name in ids_to_remove:
        for tag in soup.select(f"#{id_name}"):
            tag.decompose()



    # Extract visible text
    text = soup.get_text(separator="\n")
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return text

def crawl_and_extract():
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)

    llm = ChatOpenAI(model=MODEL_NAME, temperature=0.3, openai_api_key=OPENAI_API_KEY)

    prompt = PromptTemplate(
        input_variables=["topic", "chunk"],
        template=(
            """ You are an expert content extractor and an Excel professional with over 15 years of hands-on experience teaching, mentoring, and guiding 1,000+ students in mastering Microsoft Excel — from beginner to advanced level.
            Your role is to think, read, and interpret the content like an Excel subject-matter expert who deeply understands formulas, functions, formatting, and data operations.
            From the given article chunk, extract ONLY the text relevant to the topic: '{topic}'.
            Ignore and completely exclude:
                1. Navigation menus (such as 'leftmenuinner' sections)
                2. Advertisements or promotional snippets
                3.Example placeholders unrelated to the core topic
                4.Boilerplate or layout text (like 'ws-hide-on-logged-in', headers, or footers)
            Focus on extracting meaningful, educational, topic-relevant explanations, instructions, or definitions that help someone learn, understand, and apply the given Excel topic practically.
            Article chunk:
            {chunk}
            Return only clean, concise, and topic-relevant sentences — written as if you are preparing high-quality training material for Excel learners.
    """
        ),
    )

    chain = prompt | llm

    batch_size = 10
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)

    for batch_start in range(0, len(excel_links), batch_size):
        batch_urls = excel_links[batch_start:batch_start + batch_size]
        batch_results = []
        index = batch_start // batch_size + 1
        print("Processing batch:",index)

        for url in batch_urls:
            text = extract_clean_text(main_url + url)
            chunks = splitter.split_text(text)

            for i, chunk in enumerate(chunks):
                response = chain.invoke({"topic": topic, "chunk": chunk})
                batch_results.append(response.content.strip())
        # Save batch results to a text file
        batch_filename = os.path.join(output_dir, f"batch_{batch_start // batch_size + 1}.txt")
        with open(batch_filename, "w", encoding="utf-8") as f:
            for idx, result in enumerate(batch_results, 1):
                f.write(f"{result}\n\n")
        print("batch saved to", batch_filename)

def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

def extract_content_from_pdf():
    file = "/Users/kalyanjyothula/Desktop/Home/GenAI/Excel-app/18BCS5EL-U5.pdf"
    text =  extract_text_from_pdf(file)
    if not text.strip():
            return jsonify({"error": "No text found in PDF"}), 400

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)
    print(f"Total chunks created: {len(chunks)}")
    collection_name="Excel_Docs_DB"
    vectorstore = get_qdrant_vectorstore(collection_name=collection_name)
    total = store_pdf_in_qdrant(vectorstore, chunks, collection_name=collection_name)
    print(f"Stored {total} chunks for the PDF.")    

def store_to_qdrant():
    vectorstore = get_qdrant_vectorstore(collection_name="Excel_Docs_DB")
    for i in range(12):
        if( i <= 0): continue
        with open(f"results/batch_{i}.txt", "r", encoding="utf-8") as f:
            content = f.read()
        chunks = content.split("\n\n")
        total = store_pdf_in_qdrant(vectorstore, chunks, collection_name="Excel_Docs_DB")
        print(f"Stored {total} chunks from batch_{i}.txt to Qdrant.")

if __name__ == "__main__":
    # crawl_and_extract()
    OPENAI_API_KEY = os.getenv('OPEN_AI_API_KEY')
    MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4o-mini')
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    # extract_content_from_pdf()
    store_to_qdrant()
