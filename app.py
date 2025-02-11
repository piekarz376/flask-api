import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, session, redirect, url_for

app = Flask(__name__)

# Set a secure secret key for session management
app.secret_key = 'your_secure_secret_key_here'  # Replace with a secure random key

# Hard-coded credentials for the authentication page
USERNAME = "admin"
PASSWORD = "secret"

# Directory and file to store survey responses
DATA_DIR = "data"
RESPONSES_FILE = os.path.join(DATA_DIR, "survey_responses.json")

# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize the responses file if it does not exist
if not os.path.exists(RESPONSES_FILE):
    with open(RESPONSES_FILE, 'w') as f:
        json.dump([], f)

def load_responses():
    """Helper to load survey responses from file."""
    with open(RESPONSES_FILE, 'r') as f:
        return json.load(f)

def save_responses(responses):
    """Helper to save survey responses to file."""
    with open(RESPONSES_FILE, 'w') as f:
        json.dump(responses, f, indent=4)

@app.route('/submit', methods=['POST'])
def submit():
    """
    Accepts survey submissions via POST (JSON payload).
    Expected JSON fields include:
      - overall_satisfaction        (1-10)
      - story_interest              (1-10)
      - dm_character_performance    (1-10)
      - character_diversity         (1-10)
      - favorite_npc                (text)
      - least_favorite_npc          (text)
      - favorite_scene              (text)
      - worst_scene                 (text)
      - improved_since_last       (text)
      - worsened_since_last       (text)
      - additional_feedback         (text)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Optionally, add input validation here

        # Add unique ID and timestamp metadata to the submission
        data['id'] = str(uuid.uuid4())
        data['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # Load current responses, append the new one, and save back to file
        responses = load_responses()
        responses.append(data)
        save_responses(responses)

        return jsonify({"message": "Submission received"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    """
    Handles authentication.
    GET: Serves a simple HTML login form.
    POST: Processes login data. On successful authentication, sets a session variable.
    """
    if request.method == 'GET':
        # Return a basic HTML login form.
        return '''
        <html>
        <head><title>Login</title></head>
        <body>
            <h2>Login to Access Results</h2>
            <form method="post" action="/auth">
                <label>Username: <input type="text" name="username" /></label><br/><br/>
                <label>Password: <input type="password" name="password" /></label><br/><br/>
                <input type="submit" value="Login" />
            </form>
        </body>
        </html>
        '''
    else:  # POST
        username = request.form.get('username')
        password = request.form.get('password')

        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('result'))
        else:
            return '''
            <html>
            <head><title>Login Failed</title></head>
            <body>
                <h2>Login Failed</h2>
                <p>Invalid credentials. Please try again.</p>
                <a href="/auth">Back to Login</a>
            </body>
            </html>
            '''

@app.route('/result', methods=['GET'])
def result():
    """
    Protected endpoint that returns aggregated survey results.
    If the user is not authenticated, they are redirected to /auth.
    """
    if not session.get('logged_in'):
        return redirect(url_for('auth'))

    try:
        responses = load_responses()

        # As an example, compute the average "overall_satisfaction"
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

if __name__ == '__main__':
    # Run on all interfaces so Kubernetes (or any container orchestrator) can route traffic here
    app.run(host='0.0.0.0', port=5000)
