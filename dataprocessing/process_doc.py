import json
import os
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from datetime import datetime

from dataprocessing.create_database import generate_data_store

load_dotenv()

openai_api = os.getenv("OPENAI_API_KEY")

PROMPT_TEMPLATE = """
Answer the question based only on the following context don't give reference:
{context}
---
Answer the question based on the above context : {question}
"""


def generate_content_from_documents(submission_id):

    response = generate_data_store(submission_id=submission_id)
    if not response:
        return None
    query_text = '''extract all the details in json format '''
    chroma_path = f"./chroma/{submission_id}"
    # Prepare the DB.
    embedding_function = OpenAIEmbeddings(openai_api_key=openai_api)
    db = Chroma(persist_directory=chroma_path, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    if len(results) == 0 or results[0][1] < 0.5:
        return None
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    model = ChatOpenAI(model="gpt-4o")
    response_text = model.predict(prompt)
    sources = [doc.metadata.get("source", None) for doc, _score in results]
    if not response_text:
        return None

    formatted_response = json.dumps({
        "response": response_text,
        "sources": sources,
        "date": datetime.now().date().strftime("%Y-%m-%d"),
    })
    if response_text is not None:
        return formatted_response
    return None


def match_output(submission_id):
    data = generate_content_from_documents(submission_id=submission_id)
    model = ChatOpenAI(model="gpt-4o", temperature=0.1)
    with open('../sample/template/template.json') as file:
        structure = file.read()
    system_prompt = (f'You are an AI assistant specialized in extracting information from a document.'
                     f'Please analyze the provided text and extract information in the following JSON format:'
                     f'replace the <value> with actual value and keep field blank if value is not found.'
                     f'Return the full structure given below:'
                     f'{structure}')
    try:
        response = model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Please extract the information from the following text:\n\n{data}")
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
    finally:
        print("process done")

# submission_id = "a79de526-e0cf-4571-a9c0-2f817e4d3735"
# # file_path = "uploads/a79de526-e0cf-4571-a9c0-2f817e4d3735/App-Cyber_EDITED 1.pdf"
# file_path = "uploads/a79de526-e0cf-4571-a9c0-2f817e4d3735/sample1.pdf"
#
# response = match_output(submission_id=submission_id)
# print(response)