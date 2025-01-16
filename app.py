from flask import Flask, request, jsonify
from flask_cors import CORS
from uuid import uuid4
from dotenv import load_dotenv
import os

# local module
from process_doc import match_output
from base64_processing import match_extracted_with_template

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

# Upload configurations
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# File type validation
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/',methods=['GET'])
def index():
    return jsonify({
        "message":"You're Connected Successfully."
    })

# Route for uploading files
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    submission_id = uuid4()
    upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(submission_id))
    os.makedirs(upload_folder, exist_ok=True)
    if file and allowed_file(file.filename):
        filename = os.path.join(upload_folder, file.filename)
        file.save(filename)
        return jsonify(
            {"message": "File uploaded successfully", "filename": file.filename, "submission_id": submission_id}), 200

    return jsonify({"error": "Invalid file type"}), 400


# Route for uploading files
@app.route('/api/process_doc', methods=['POST'])
def document_processing():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    submission_id = str(uuid4())
    upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], submission_id)
    os.makedirs(upload_folder, exist_ok=True)
    if file and allowed_file(file.filename):
        filename = os.path.join(upload_folder, file.filename)
        file.save(filename)
        response = match_extracted_with_template(file_path=filename,submission_id=submission_id)
        return jsonify({
            "message": "Data Extracted Successfully.",
            "filename": file.filename,
            "submission_id": submission_id,
            "application_details": response
        }), 200
    # os.rmdir(upload_folder)

    return jsonify({"error": "Invalid file type"}), 400


# Run the app
if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)
