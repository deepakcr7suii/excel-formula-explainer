from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from analyzer import analyze_file
from gemini_helper import setup_gemini, explain_formula
import os

app = Flask(__name__)

# Trust Render's proxy so rate limiter sees real client IPs, not the proxy IP
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

# Upload config
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {'.xlsx'}

# Flask-level enforcement — rejects oversize requests before loading into memory
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Rate limiter — 10 uploads per hour per IP
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

# Setup Gemini
api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    setup_gemini(api_key)

def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'error': 'File too large. Max 5 MB.'}), 413

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({'error': 'Too many uploads. Try again in an hour.'}), 429

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
@limiter.limit("10 per hour")
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Only .xlsx files are allowed'}), 400

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

    except ValueError as e:
        # Formula count cap raises ValueError from analyzer
        return jsonify({'error': str(e)}), 400
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