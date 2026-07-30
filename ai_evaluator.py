import json
import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

#load api client using api key in environment file
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

#define the prompt and send the prompt through the api into the AI and ask it 
#to return a JSON file
def evaluate_answer(question, transcript, category, concepts):
    prompt = f"""
Evaluate this interview answer.

Category: {category}
Question: {question}
Expected concepts: {concepts}
Transcript: {transcript}

Return only valid JSON in exactly this form:
{{
  "scores": {{
    "relevance": 0,
    "specificity": 0,
    "structure": 0,
    "communication": 0
  }},
  "star_detected": false,
  "strengths": [],
  "improvements": [],
  "missing_concepts": [],
  "improved_answer": "",
  "follow_up_question": ""
}}

Each score must be an integer from 0 to 100.
Use STAR for behavioral questions.
Judge only the transcript content.
Give specific constructive feedback.
Return JSON only.
"""

    #create model client and send the message to the groq model defined in the environment folder
    #or if that model doesn't work use the set llama model in the other place of the argument
    res = client.chat.completions.create(
        model=os.getenv("GROQ_EVALUATION_MODEL", "llama-3.3-70b-versatile"),
        #message format
        messages=[
            {
                "role": "system",
                "content":
                    "You are an interview coach. Return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        #make sure the model doesn't return something random and make it more predictable
        temperature=0.2,
        response_format={
            "type": "json_object"
        }
    )

    #evaluate the content of the message from the json and do checks to see if it's null
    content = res.choices[0].message.content
    if not content:
        raise ValueError("The evaluation API returned no content.")
    #load it as a python dictionary
    result = json.loads(content)

    #validate the answer to make sure the AI returned what we want through another defined function
    validate_result(result)
    return result


#validate the result
def validate_result(result):
    required = {
        "scores",
        "star_detected",
        "strengths",
        "improvements",
        "missing_concepts",
        "improved_answer",
        "follow_up_question"
    }

    #if what the model returned in the form of a python dictonary doesn't have one of the things in required, then raise
    #the value error
    if not required.issubset(result):
        raise ValueError("The evaluation response is incomplete.")

    score_names = {"relevance", "specificity", "structure", "communication"}

    #access the scores part of the JSON file the AI returned
    scores = result["scores"]

    #check to see if what they returned includes the key words in score_names
    #if not , raise value error
    if not score_names.issubset(scores):
        raise ValueError("The evaluation scores are incomplete.")

    #iterate through the scores to check if the AI returned something that isn't an integer or between 0 and 100.
    for name in score_names:
        score = scores[name]
        if not isinstance(score, int):
            raise ValueError("Evaluation scores must be integers.")
        if score < 0 or score > 100:
            raise ValueError("Evaluation scores must be from 0 to 100.")