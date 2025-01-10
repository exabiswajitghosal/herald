from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.schema import HumanMessage, SystemMessage
import json
import os
from dotenv import load_dotenv

load_dotenv()

google_api_key = os.getenv('GEMINI_API_KEY')

PROMPT_TEMPLATE = """
Answer the question based only on the following context don't give reference:
{context}
---
Answer the question based on the above context : {question}
"""


def load_pdf(file_path):
    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        print(f"Loaded {len(documents)} document(s) from PDF.")
        return documents
    except Exception as e:
        print("Error loading PDF:", e)
        return None


def split_text(documents):
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000,
            chunk_overlap=100,
            length_function=len,
            add_start_index=True,
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Split into {len(chunks)} chunk(s).")
        return chunks
    except Exception as e:
        print("Error splitting text:", e)
        return None


def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def generate_content_from_local_pdf_with_gemini_structured(submission_id, file_path):
    documents = load_pdf(file_path)
    if not documents:
        return None

    chunks = split_text(documents)
    if not chunks:
        return None

    file_name_no_ext = os.path.splitext(os.path.basename(file_path))[0]
    chroma_path = f"./chroma/{submission_id}/{file_name_no_ext}"
    ensure_directory_exists(chroma_path)

    try:
        embedding_function = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=google_api_key
        )
        db = Chroma.from_documents(chunks, embedding_function, persist_directory=chroma_path)
        print("Chroma DB initialized successfully.")
    except Exception as e:
        print("Error initializing Chroma DB:", e)
        return None

    try:
        query_text = "Extract all the details from the document in a structured JSON format."
        results = db.similarity_search_with_relevance_scores(query_text, k=1)
        if not results:
            print("No results found in similarity search.")
            return None

        context_text = "\n\n---\n\n".join([doc.page_content for doc, _ in results])
    except Exception as e:
        print("Error during similarity search:", e)
        return None

    system_prompt = """You are an AI assistant specialized in extracting information from a document.
    Please analyze the provided text and extract information in the following JSON format,
    leaving fields empty if the information is not found:
    {
        "coverage_values": [
            {
                "coverage_parameter_id": "cvg_o3mw_cyb_effective_date",
                "value": "<value>",
                "parameter_text": {
                    "applicant_facing_text": "Cyber Effective Date",
                    "agent_facing_text": "Cyber Effective Date"
                },
                "input_type": "date"
            },
            {
                "coverage_parameter_id": "cvg_agj9_cyb_aggregate_limit",
                "value": "<value>",
                "parameter_text": {
                    "applicant_facing_text": "Aggregate Limit",
                    "agent_facing_text": "Aggregate Limit"
                },
                "input_type": "select_one"
            }
        ]
    }"""

    try:
        model = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=google_api_key,
            temperature=0
        )

        response = model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Please extract the information from the following text:\n\n{context_text}")
        ])

        response_text = response.content if hasattr(response, 'content') else response
        parsed_response = json.loads(response_text)

        response_output_path = f"./outputs/{submission_id}_output.json"
        ensure_directory_exists("./outputs")

        with open(response_output_path, "w") as output_file:
            json.dump(parsed_response, output_file, indent=4)

        print(f"Response saved to {response_output_path}")
        return parsed_response

    except json.JSONDecodeError as e:
        print("JSON Decode Error:", e)
        print("Response content:", response_text)
        return None
    except Exception as e:
        print("Unexpected error:", e)
        return None


# Usage Example
# submission_id = "5"
# file_path = "../uploads/App-Cyber_EDITED 1.pdf"
#
# response = generate_content_from_local_pdf_with_gemini_structured(submission_id=submission_id, file_path=file_path)
# print(response)
