import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from groq import Groq
from ai_evaluator import evaluate_answer_with_ai
from analyzer import analyze_speech
from questions import questions

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".webm", ".ogg", ".mp4", ".mp3", ".wav", ".m4a"}

def get_all_questions():
    all_questions = []

    for category_questions in questions.values():
        for item in category_questions:
            all_questions.append(item)

    return all_questions

def find_question(question_id):
    for item in get_all_questions():
        if item["id"] == question_id:
            return item
    return None

@app.route("/")
def index():
    return render_template("index.html", questions=get_all_questions())

@app.route("/analyze", methods=["POST"])
def analyze():
    audio_file = request.files.get("audio")
    question_id = request.form.get("question_id", "").strip()
    duration_text = request.form.get("duration", "0")
    if audio_file is None or not audio_file.filename:
        return jsonify({"error": "No audio file was submitted."}), 400
    question_data = find_question(question_id)
    if question_data is None:
        return jsonify({"error": "The selected question is invalid."}), 400
    try:
        duration_seconds = float(duration_text)
    except ValueError:
        return jsonify({"error": "The recording duration is invalid."}), 400
    if duration_seconds <= 0 or duration_seconds > 600:
        return jsonify({"error": "The recording duration is outside the allowed range."}), 400
    suffix = Path(audio_file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Unsupported audio format."}), 400
    audio_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temporary_file:
            audio_path = temporary_file.name
            audio_file.save(audio_path)
        transcript = transcribe_audio(audio_path)
        if not transcript:
            return jsonify({"error": "No understandable speech was detected."}), 400
        speech_analysis = analyze_speech(transcript, duration_seconds)
        ai_analysis = evaluate_answer_with_ai(
            question_data["question"],
            transcript,
            question_data["category"],
            question_data["expected_concepts"]
        )
        overall_score = calculate_overall_score(speech_analysis, ai_analysis)
        return jsonify({
            "question": question_data["question"],
            "question_id": question_data["id"],
            "transcript": transcript,
            "overall_score": overall_score,
            "speech": speech_analysis,
            "evaluation": ai_analysis
        })
    except Exception as error:
        app.logger.exception("Interview analysis failed.")
        return jsonify({"error": str(error)}), 500
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)

def transcribe_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            file=audio_file,
            model=os.getenv("GROQ_TRANSCRIPTION_MODEL", "whisper-large-v3-turbo"),
            language="en",
            response_format="json"
        )
    return result.text.strip()

def calculate_overall_score(speech, evaluation):
    scores = evaluation["scores"]
    return round(
        scores["relevance"] * 0.30
        + scores["specificity"] * 0.20
        + scores["structure"] * 0.20
        + scores["communication"] * 0.10
        + speech["pace_score"] * 0.10
        + speech["filler_score"] * 0.10
    )

@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({"error": "The audio recording is too large."}), 413

if __name__ == "__main__":
    app.run(debug=True)
