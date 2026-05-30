from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify
from analyzer import analyze_file
from gemini_helper import setup_gemini, explain_formula
import os

app = Flask(__name__)

# Upload config
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {'.xlsx'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Setup Gemini
api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    setup_gemini(api_key)

def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Only .xlsx files are allowed'}), 400

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)

    if size > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large. Max 5 MB.'}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        results = analyze_file(filepath)

        # Send complex formulas to Gemini for explanation
        for formula in results['formulas']:
            if formula['is_complex']:
                ai_result = explain_formula(formula['formula'], formula['cell'])
                formula['explanation'] = ai_result['explanation']
                formula['simplified'] = ai_result['simplified']
            else:
                formula['explanation'] = 'Simple formula — no explanation needed.'
                formula['simplified'] = 'Already simple.'

    except Exception as e:
        return jsonify({'error': f'Failed to analyze file: {str(e)}'}), 500
    finally:
        try:
            os.remove(filepath)
        except:
            pass

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5001)