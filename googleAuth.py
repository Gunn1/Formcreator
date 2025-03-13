from flask import Flask, render_template, request, redirect, url_for, session
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from gemini import geminiQuery, upload_file_to_gemini

import google.generativeai as genai
import json
import os
from werkzeug.utils import secure_filename


# Replace with your actual credentials or use environment variables
API_KEY = os.environ.get("GEMINI_API_KEY") # Gemini API Key
CREDENTIALS_FILE = "credentials.json"  # Path to your credentials JSON file

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-pro")
# If modifying these scopes, delete the file token.json.

SCOPES = [
    "openid",  # Include openid explicitly, and keep it in consistent position
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/forms.body",
]
UPLOAD_FOLDER = 'uploads'  # Update to your desired folder for storing images



# Authenticate with Google Forms API using service account
app = Flask(__name__)
app.secret_key = "Supersecurekey"
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_TYPE'] = 'filesystem'  # Or your preferred session type
app.config['SESSION_COOKIE_SECURE'] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure your 'uploads' directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# OAuth Configuration
CREDENTIALS_FILE = "credentials.json"  # Path to your credentials JSON file
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/forms.body",
]
# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# Helper Functions
def create_google_flow() -> Flow:
    """Create an OAuth flow with the required scopes and redirect URI."""
    return Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for("callback", _external=True),
    )

def get_google_service(creds_json: str, service_name: str, version: str):
    """Initialize a Google API client with provided credentials."""
    try:
        creds = Credentials.from_authorized_user_info(json.loads(creds_json), SCOPES)
        return build(service_name, version, credentials=creds)
    except Exception as e:
        print(f"Error initializing {service_name} API: {e}")
        return None

@app.route("/login")
def login():
    """Handle user login and OAuth flow."""
    # Check if credentials are already in the session
    if "credentials" in session:
        try:
            creds = Credentials.from_authorized_user_info(json.loads(session["credentials"]), SCOPES)
            if creds.valid:  # Credentials are still valid
                return redirect(url_for("index"))
            elif creds.expired and creds.refresh_token:  # Refresh expired credentials
                creds.refresh(Request())
                session["credentials"] = creds.to_json()
                return redirect(url_for("index"))
        except Exception as e:
            print(f"Error handling stored credentials: {e}")
    
    # Initiate the OAuth flow if no valid credentials are found
    flow = create_google_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",            # Ensure refresh token is provided
        include_granted_scopes="true",
        prompt='consent'  # Force user re-authorization if needed
# Avoid asking for already-granted scopes
    )
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    """Handle the OAuth callback and store credentials."""
    if "state" not in session or "state" not in request.args:
        return "Missing or invalid state parameter.", 400

    if session["state"] != request.args.get("state"):
        return "State parameter mismatch.", 401

    flow = create_google_flow()
    try:
        flow.fetch_token(authorization_response=request.url)
        session["credentials"] = flow.credentials.to_json()
        return redirect(url_for("index"))
    except Exception as e:
        print(f"Error during OAuth callback: {e}")
        return f"Authentication error: {e}", 500

@app.route("/logout")
def logout():
    """Log the user out by clearing the session."""
    session.clear()
    return redirect(url_for("index"))


@app.route("/", methods=["GET", "POST"])
def index():
    form_url = None
    error_message = None
    form_preview_data = None
    session.setdefault('prompt_history', [])
    prompt_history = session.get('prompt_history', [])
    
    # Initialize Google Forms API
    form_service = None
    if "credentials" in session:
        form_service = get_google_service(session["credentials"], 'forms', 'v1')
        if not form_service:
            error_message = "Failed to initialize Google Forms service."
    else:
        return render_template("index.html")
    
    if request.method == "POST":
        prompt = request.form.get("prompt")
        if not prompt:
            error_message = "Please enter a prompt."
        else:
            
            # Insert the new prompt at the beginning
            session['prompt_history'].append(prompt)

            # Ensure the list doesn't exceed 5 items
            session['prompt_history'] = session['prompt_history'][-5:]

            # Get the first 5 items
            prompt_history = session['prompt_history'][-5:][::-1]
            try:
                uploaded_file = None
                try:
                    
                    file = request.files['file']
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        uploaded_file = upload_file_to_gemini(file_path)
                except:
                    print("No File")


                form_prompt = f"""For each question, specify the correct answer. The JSON should follow this format:
                
                {{
                  "requests": [
                    {{
                      "updateFormInfo": {{
                        "info": {{
                          "title": "(Title)",
                          "description": "(Description)"
                        }},
                        "updateMask": "*"
                      }}
                    }},
                    // Section block:
                    {{
                      "createItem": {{
                        "item": {{
                          "title": "(Section Title)",
                          "pageBreakItem": {{
                            "description": "(Section Description)"
                          }}
                        }},
                        "location": {{"index": (index number)}}
                      }}
                    }},
                    // Multiple-choice question:
                    {{
                      "createItem": {{
                        "item": {{
                          "title": "(Question Text)",
                          "questionItem": {{
                            "question": {{
                              "required": true/false,
                              "choiceQuestion": {{
                                "type": "(CHOICE_TYPE)",  // Use RADIO, CHECKBOX, or DROP_DOWN.
                                "options": [
                                  {{"value": "(Option 1)"}},
                                  {{"value": "(Option 2)"}},
                                  {{"value": "(Option 3)"}},
                                  {{"value": "(Option 4)"}}
                                ],
                                "shuffle": true/false
                              }},
                              "grading": {{
                                "correctAnswers": {{
                                  "answers": [{{"value": "(Correct Answer)"}}]
                                }},
                                "pointValue": (value)
                              }}
                            }}
                          }}
                        }},
                        "location": {{"index": (index number)}}
                      }}
                    }},
                    // Text answer question:
                    {{
                      "createItem": {{
                        "item": {{
                          "title": "(Question Text)",
                          "questionItem": {{
                            "question": {{
                              "required": true/false,
                              "textQuestion": {{}}
                            }}
                          }}
                        }},
                        "location": {{"index": (index number)}}
                      }}
                    }},
                    // File upload question:
                    {{
                      "createItem": {{
                        "item": {{
                          "title": "(Question Text)",
                          "questionItem": {{
                            "question": {{
                              "required": true/false,
                              "fileUploadQuestion": {{
                                "maxFileSize": (value),
                                "allowedFileTypes": ["(file type 1)", "(file type 2)"]
                              }},
                              "grading": {{
                                "pointValue": (value)
                              }}
                            }}
                          }}
                        }},
                        "location": {{"index": (index number)}}
                      }}
                    }},
                    // Date question:
                    {{
                      "createItem": {{
                        "item": {{
                          "title": "(Question Text)",
                          "questionItem": {{
                            "question": {{
                              "required": true/false,
                              "dateQuestion": {{}}
                            }}
                          }}
                        }},
                        "location": {{"index": (index number)}}
                      }}
                    }}
                    // More question blocks can be added here...
                  ]
                }}
                
                **Instructions**:
                - For sections, include a section block using pageBreakItem.
                - For multiple-choice, use choiceQuestion with the proper type (RADIO, CHECKBOX, or DROP_DOWN).
                - For text answers, use textQuestion.
                - For file uploads, use fileUploadQuestion with maxFileSize and allowedFileTypes.
                - For dates, use dateQuestion.
                - Include an image URI with the image key if available. Omit the key if none.
                - Ensure that the correct answer is set and add points for grading.
                - Replace placeholders with appropriate text.
                
                Return only the JSON object. Do not include any backticks, code fences, or extra text.
                """

                gemini_response = geminiQuery(prompt+form_prompt,uploaded_file)
                try:
                    # Validate JSON and extract data
                    data = json.loads(gemini_response.text.replace("`json", "").replace("`", ""))
                    form_preview_data = data
                except json.JSONDecodeError as e:
                    error_message = f"Invalid JSON generated: {e}. Gemini Output: {gemini_response.text}"
                    return render_template("index.html", form_url=form_url, error_message=error_message, prompt_history=prompt_history, form_preview_data=form_preview_data)

                # Create Google Form
                NEW_FORM = {
                    "info": {"title": "Generated Quiz"},  # Truncates title if too long
                }

                if form_service:
                    result = form_service.forms().create(body=NEW_FORM).execute()
                    form_id = result.get("formId")

                    # Update quiz settings and add questions to the form
                    batch_update_body = {
                        "requests": [
                            {"updateSettings": {"settings": {"quizSettings": {"isQuiz": True}}, "updateMask": "*"}},
                            *data["requests"]  # Append the questions generated by Gemini
                        ]
                    }

                    form_service.forms().batchUpdate(formId=form_id, body=batch_update_body).execute()
                    form_url = result.get("responderUri")
                else:
                    error_message = "Google Forms Service not initialized. Check credentials."

            except HttpError as e:
                error_message = f"Google Forms API Error: {e}"
            except Exception as e:
                error_message = f"An unexpected error occurred: {e}"

    return render_template("index.html", form_url=form_url, error_message=error_message, prompt_history=prompt_history, form_preview_data=form_preview_data)


if __name__ == "__main__":
    app.run(debug=False, use_reloader=False, host='0.0.0.0', ssl_context=('certificate.crt', 'private.key'))

    
