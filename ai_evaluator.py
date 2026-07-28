import json
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def evaluate_answer_with_ai(question, transcript, category, expected_concepts):
    prompt = f"""
Evaluate this interview answer.

Category: {category}
Question: {question}
Expected concepts: {expected_concepts}
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
    response = client.chat.completions.create(
        model=os.getenv("GROQ_EVALUATION_MODEL", "llama-3.3-70b-versatile"),
        messages=[
            {"role": "system", "content": "You are an interview coach. Return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("The evaluation API returned no content.")
    result = json.loads(content)
    validate_evaluation(result)
    return result

def validate_evaluation(result):
    required = {"scores", "star_detected", "strengths", "improvements", "missing_concepts", "improved_answer", "follow_up_question"}
    if not required.issubset(result):
        raise ValueError("The evaluation response is incomplete.")
    score_names = {"relevance", "specificity", "structure", "communication"}
    if not score_names.issubset(result["scores"]):
        raise ValueError("The evaluation scores are incomplete.")
    for name in score_names:
        score = result["scores"][name]
        if not isinstance(score, int) or not 0 <= score <= 100:
            raise ValueError("Evaluation scores must be integers from 0 to 100.")
