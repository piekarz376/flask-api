from flask import Blueprint, Flask, request, jsonify, session, redirect, url_for
import os, json, uuid
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Directory and file to store survey responses
DATA_DIR = "data"
RESPONSES_FILE = os.path.join(DATA_DIR, "survey_responses.json")

# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(RESPONSES_FILE):
    with open(RESPONSES_FILE, 'w') as f:
        json.dump([], f)

def load_responses():
    with open(RESPONSES_FILE, 'r') as f:
        return json.load(f)

def save_responses(responses):
    with open(RESPONSES_FILE, 'w') as f:
        json.dump(responses, f, indent=4)

@api_bp.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Add unique ID and timestamp
        data['id'] = str(uuid.uuid4())
        data['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        responses = load_responses()
        responses.append(data)
        save_responses(responses)

        return jsonify({"message": "Submission received"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'GET':
        return '''
        <html>
        <head><title>Login</title></head>
        <body>
            <h2>Login to Access Results</h2>
            <form method="post" action="/api/auth">
                <label>Username: <input type="text" name="username" /></label><br/><br/>
                <label>Password: <input type="password" name="password" /></label><br/><br/>
                <input type="submit" value="Login" />
            </form>
        </body>
        </html>
        '''
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        if username == "admin" and password == "secret":
            session['logged_in'] = True
            return redirect(url_for('api.result'))
        else:
            return '''
            <html>
            <head><title>Login Failed</title></head>
            <body>
                <h2>Login Failed</h2>
                <p>Invalid credentials. Please try again.</p>
                <a href="/api/auth">Back to Login</a>
            </body>
            </html>
            '''

@api_bp.route('/result', methods=['GET'])
def result():
    if not session.get('logged_in'):
        return redirect(url_for('api.auth'))
    try:
        responses = load_responses()
        if responses:
            total = sum(float(r.get('overall_satisfaction', 0)) for r in responses)
            average = total / len(responses)
        else:
            average = None

        result_data = {
            "total_submissions": len(responses),
            "average_overall_satisfaction": average,
            "responses": responses
        }
        return jsonify(result_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

app = Flask(__name__)
app.secret_key = 'test_secret'
app.register_blueprint(api_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
