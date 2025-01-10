from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import Flow
import json
import os
import google.generativeai as genai

# Configuration
API_KEY = os.environ.get("API_KEY")  # Gemini API Key
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/forms.body",
]
CREDENTIALS_FILE = "credentials.json"

genai.configure(api_key=API_KEY)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Important for sessions
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Helper function to create a Google OAuth flow
def create_google_flow():
    return Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for("callback", _external=True),
    )


@app.route("/login")
def login():
    flow = create_google_flow()
    authorization_url, state = flow.authorization_url(include_granted_scopes="true")
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    if "state" not in session:
        return "Session state missing", 400
    if "state" not in request.args:
        return "Request state missing", 400
    if session["state"] != request.args.get("state"):
        return "State mismatch", 401

    flow = create_google_flow()
    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception as e:
        return f"Error fetching token: {e}", 500

    session["credentials"] = flow.credentials.to_json()
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/", methods=["GET", "POST"])
def index():
    form_service = None
    form_url = None
    error_message = None
    form_preview_data = None
    prompt_history = session.get('prompt_history', [])

    if "credentials" in session:
        try:
            creds = json.loads(session["credentials"])
            credentials = build('forms', 'v1', credentials=creds)
        except Exception as e:
            error_message = f"Error authenticating with Google Forms API: {e}"
    else:
        return render_template("index.html")

    if request.method == "POST":
        prompt = request.form.get("prompt")
        if not prompt:
            error_message = "Please enter a prompt."
        else:
            prompt_history.append(prompt)
            session['prompt_history'] = prompt_history[-5:]  # Keep the last 5 prompts
            try:
                gemini_response = genai.GenerativeModel("gemini-pro").generate(prompt)
                try:
                    data = json.loads(gemini_response.replace("`json", "").replace("`", ""))
                    form_preview_data = data
                except json.JSONDecodeError as e:
                    error_message = f"Invalid JSON generated: {e}"
                    return render_template("index.html", form_url=form_url, error_message=error_message)

                # Create Google Form
                NEW_FORM = {"info": {"title": prompt[:50] if len(prompt) > 50 else prompt}}
                if form_service:
                    result = form_service.forms().create(body=NEW_FORM).execute()
                    form_id = result.get("formId")

                    # Enable Quiz Mode
                    QUIZ_SETTINGS = {
                        "requests": [
                            {
                                "updateSettings": {
                                    "settings": {
                                        "quizSettings": {"isQuiz": True}
                                    },
                                    "updateMask": "*"
                                }
                            }
                        ]
                    }
                    form_service.forms().batchUpdate(formId=form_id, body=QUIZ_SETTINGS).execute()

                    # Add questions
                    form_service.forms().batchUpdate(formId=form_id, body=data).execute()
                    form_url = result.get("responderUri")
                else:
                    error_message = "Google Forms service not initialized. Check credentials."
            except HttpError as e:
                error_message = f"Google Forms API error: {e}"
            except Exception as e:
                error_message = f"An unexpected error occurred: {e}"

    return render_template(
        "index.html",
        form_url=form_url,
        error_message=error_message,
        prompt_history=prompt_history,
        form_preview_data=form_preview_data,
    )


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=5001)
