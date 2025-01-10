from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai_api = os.getenv('OPENAI_API_KEY')

# Constants
PROMPT_TEMPLATE = """
Answer the question based only on the following context don't give reference:
{context}
---
Answer the question based on the above context : {question}
"""


def load_pdf(file_path):
    """
    Load a PDF document from the local file system.
    """
    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        print(f"Loaded {len(documents)} document(s) from PDF.")
        return documents
    except Exception as e:
        print("Unable to load PDF.", e)
        return None


def split_text(documents: list[Document]):
    """
    Split documents into smaller chunks for embedding.
    """
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000,
            chunk_overlap=100,
            length_function=len,
            add_start_index=True,
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Split into {len(chunks)} chunks.")
        return chunks
    except Exception as e:
        print("Failed to split text.", e)
        return None


def generate_content_from_local_pdf(submission_id, file_path):
    """
    Load a local PDF file, create embeddings, perform a search, and generate structured content.
    """
    documents = load_pdf(file_path)
    if not documents:
        return None

    chunks = split_text(documents)
    if not chunks:
        return None

    file_name_no_ext = os.path.splitext(os.path.basename(file_path))[0]
    chroma_path = f"./chroma/{submission_id}/{file_name_no_ext}"

    try:
        embedding_function = OpenAIEmbeddings(openai_api_key=openai_api)
        db = Chroma.from_documents(chunks, embedding_function, persist_directory=chroma_path)
    except Exception as e:
        print("Failed to initialize Chroma DB.", e)
        return None

    query_text = "Extract all the details from the document in a structured JSON format."

    try:
        results = db.similarity_search_with_relevance_scores(query_text, k=1)
        if not results:
            print("No relevant chunks found.")
            return None

        context_text = "\n\n---\n\n".join([doc.page_content for doc, _ in results])
        print(f"Found {len(results)} relevant chunk(s).")
    except Exception as e:
        print("Error during similarity search.", e)
        return None

    model = ChatOpenAI(model="gpt-4", temperature=0.1)
    with open('../sample/template/template.json') as file:
        structure = file.read()
    system_prompt = (f'You are an AI assistant specialized in extracting information from a document.'
                     f'Please analyze the provided text and extract information in the following JSON format:'
                     f'replace the <value> with actual value'
                     f'{structure}')
    try:
        response = model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Please extract the information from the following text:\n\n{context_text}")
        ])

        response_text = response.content
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if 0 <= json_start < json_end:
            json_str = response_text[json_start:json_end]
            parsed_response = json.loads(json_str)

            response_output_path = f"./output/{submission_id}_output.json"
            os.makedirs(os.path.dirname(response_output_path), exist_ok=True)
            with open(response_output_path, "w") as output_file:
                json.dump(parsed_response, output_file, indent=4)

            return parsed_response
        else:
            print("No JSON content found in response.")
            return None
    except json.JSONDecodeError as e:
        print("Error parsing JSON response:", e)
        return None
    except Exception as e:
        print("Unexpected error:", e)
        return None



# submission_id = "3"
# file_path = "uploads/a79de526-e0cf-4571-a9c0-2f817e4d3735/App-Cyber_EDITED 1.pdf"
#
# response = generate_content_from_local_pdf(submission_id=submission_id, file_path=file_path)
# print(response)