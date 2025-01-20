from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.chroma import Chroma
import os
import shutil
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def load_documents(submission_id):
    try:
        loader = DirectoryLoader(path="uploads/"+submission_id)
        documents = loader.load()
        return documents
    except Exception as e:
        print("Unable to load documents.", e)
        return None


def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=10000,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)

    return chunks


def save_to_chroma(chunks: list[Document], submission_id):
    chroma_path = f"chroma/{submission_id}"
    # Clear out the database first.
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)

    # Create a new DB from the documents.
    db = Chroma.from_documents(
        chunks, OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY), persist_directory=chroma_path
    )
    db.persist()


def generate_data_store(submission_id):
    try:
        documents = load_documents(submission_id=submission_id)
        if not documents:
            return False
        chunks = split_text(documents=documents)
        save_to_chroma(chunks=chunks, submission_id=submission_id)
        return True
    except Exception as e:
        print("Unable to generate the data store.", e)
        return False