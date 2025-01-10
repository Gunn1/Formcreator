from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv('.env')

# Access environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

def geminiQuery(prompt):

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response
if __name__ == "__main__":
    response = geminiQuery("""Generate JSON for creating questions in a Google Form quiz based on the Minnesota Comprehensive Assessments (MCA) state standards for 8th-grade math. Create 3 multiple-choice questions. For each question, specify the correct answer. The JSON should follow this format:

```json
{
  "requests": [
    {
      "createItem": {
        "item": {
          "title": "(Question Text)",
          "questionItem": {
            "question": {
              "required": true/false,
              "choiceQuestion": {
                "type": "RADIO",
                "options": [
                  {"value": "(Option 1)"},
                  {"value": "(Option 2)"},
                  {"value": "(Option 3)"},
                  {"value": "(Option 4)"}
                ],
                "shuffle": true/false
              },
               "grading":{
                    "correctAnswers":{
                        "answers":[
                            {"value": "(Correct Answer)"}
                        ]
                    },
                    "pointValue": 1
                }
            }
          }
        },
        "location": {"index": (index number)}
      }
    },
    // More question blocks here...
  ]
}""")
    print(response.text)
    