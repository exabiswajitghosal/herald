import json

import requests
from dotenv import load_dotenv
import os
import base64

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pdf2image import convert_from_path
from io import BytesIO


# Load environment variables
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

def pdf_to_base64_images(pdf_path, dpi=200):
    """Convert PDF pages to Base64-encoded images."""
    base64_images = []
    try:
        pages = convert_from_path(pdf_path, dpi=dpi)
        for page in pages:
            buffered = BytesIO()
            page.save(buffered, format="PNG")
            img = base64.b64encode(buffered.getvalue()).decode("utf-8")
            img_base64 = f"data:image/png;base64,{img}"

            base64_images.append(img_base64)
    except Exception as e:
        print(f"Error converting PDF to Base64 images: {e}")
    return base64_images

def fetch_insights(pdf_path,submission_id):
    """Fetch insights from the OpenAI API by sending PDF pages as Base64 images."""
    try:
        # Convert PDF to Base64 images
        images = pdf_to_base64_images(pdf_path)
        if not images:
            return "No images generated from the PDF."

        # Construct API request payload
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all information from the document in JSON format"}
                ]
            }
        ]

        # Attach images to the payload
        for img_base64 in images:
            messages[0]["content"].append({
                "type": "image_url",  # Adjust if image_base64 is not compatible
                "image_url": {"url": img_base64}
            })

        data = {
            "model": "gpt-4o",
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0,
        }

        # Send the request
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_api_key}",
            },
        )

        if response.status_code == 200:
            response_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No insights.")
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if 0 <= json_start < json_end:
                json_str = response_text[json_start:json_end]
                parsed_response = json.loads(json_str)

                response_output_path = f"./output/{submission_id}/extracted_data.json"
                os.makedirs(os.path.dirname(response_output_path), exist_ok=True)
                with open(response_output_path, "w") as output_file:
                    json.dump(parsed_response, output_file, indent=4)

                return parsed_response
        else:
            print(f"API Error: {response.status_code}, {response.text}")
            return "Error: Unable to fetch insights."

    except Exception as e:
        return f"Error fetching insights: {str(e)}"


def match_extracted_with_template(file_path,submission_id):
    # file_path = f'uploads/a79de526-e0cf-4571-a9c0-2f817e4d3735/sample1.pdf'
    data = fetch_insights(pdf_path=file_path,submission_id=submission_id)
    model = ChatOpenAI(model="gpt-4o", temperature=0.1)
    with open('sample/template/template.json') as file:
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

            response_output_path = f"./output/{submission_id}/output.json"
            os.makedirs(os.path.dirname(response_output_path), exist_ok=True)
            with open(response_output_path, "w") as output_file:
                json.dump(parsed_response, output_file, indent=4)

            return parsed_response
        else:
            print("No JSON content found in response.")
            return None
    finally:
        print("process done")

