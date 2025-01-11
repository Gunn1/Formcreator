from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv('.env')

# Access environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

def geminiQuery(prompt, file=None):
    if file is not None:
      model = genai.GenerativeModel("gemini-1.5-flash")
      response = model.generate_content([prompt, file])
      return response
    else:
      model = genai.GenerativeModel("gemini-1.5-flash")
      response = model.generate_content(prompt)
      return response
def upload_file_to_gemini(file_path):
    try:
        # Initialize the file manager with the API key

        # Upload the file
        uploaded_file = genai.upload_file(file_path)

        # Get the uploaded file's information
        file = uploaded_file.display_name
        print(f"Uploaded file {file}")


        # Return the file URI or other useful information
        return uploaded_file.uri, uploaded_file.display_name

    except Exception as e:
        # Handle errors (e.g., file upload failure)
        print(f"Error uploading file: {e}")
        return None, None
if __name__ == "__main__":
#     response = geminiQuery("""Generate JSON for creating questions in a Google Form quiz based on the Minnesota Comprehensive Assessments (MCA) state standards for 8th-grade math. Create 3 multiple-choice questions. For each question, specify the correct answer. The JSON should follow this format:
# {
#   "requests": [
#     {
#       "createItem": {
#         "item": {
#           "title": "(Question Text)",
#           "questionItem": {
#             "question": {
#               "required": true/false,
#               "choiceQuestion": {
#                 "type": "RADIO",
#                 "options": [
#                   {"value": "(Option 1)"},
#                   {"value": "(Option 2)"},
#                   {"value": "(Option 3)"},
#                   {"value": "(Option 4)"}
#                 ],
#                 "shuffle": true/false
#               },
#                "grading":{
#                     "correctAnswers":{
#                         "answers":[
#                             {"value": "(Correct Answer)"}
#                         ]
#                     },
#                     "pointValue": 1
#                 }
#             }
#           }
#         },
#         "location": {"index": (index number)}
#       }
#     },
#     // More question blocks here...
#   ]
# }""")
#     print(response.text)
    upload_file_to_gemini('Staff Handbook 24-25.pdf')