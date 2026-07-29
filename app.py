import os
import tempfile

from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from groq import Groq

from ai_evaluator import evaluate_answer
from analyzer import analyze_speech
from questions import questions

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = (
    20 * 1024 * 1024
)

AUDIO_TYPES = {
    ".webm",
    ".ogg",
    ".mp4",
    ".mp3",
    ".wav",
    ".m4a"
}


def get_questions():
    items = []

    for group in questions.values():
        for item in group:
            items.append(item)

    return items


def get_question(question_id):
    for item in get_questions():
        if item["id"] == question_id:
            return item

    return None


@app.route("/")
def index():
    return render_template(
        "index.html",
        questions=get_questions()
    )


@app.route("/analyze", methods=["POST"])
def analyze():
    audio = request.files.get("audio")

    question_id = request.form.get("question_id", "").strip()

    duration_text = request.form.get(
        "duration",
        "0"
    )

    if audio is None or not audio.filename:
        return jsonify(
            {
                "error":
                    "No audio file was submitted."
            }
        ), 400
    question = get_question(question_id)
    if question is None:
        return jsonify(
            {
                "error":
                    "The selected question is invalid."
            }
        ), 400

    try:
        seconds = float(duration_text)
    except ValueError:
        return jsonify(
            {
                "error":
                    "The recording duration is invalid."
            }
        ), 400

    if seconds <= 0 or seconds > 600:
        return jsonify(
            {
                "error":
                    "The recording duration is outside the allowed range."
            }
        ), 400

    ext = Path(audio.filename).suffix.lower()

    if ext not in AUDIO_TYPES:
        return jsonify(
            {
                "error":
                    "Unsupported audio format."
            }
        ), 400

    audio_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=ext,
            delete=False
        ) as temp:
            audio_path = temp.name
            audio.save(audio_path)
        transcript = transcribe(audio_path)
        if not transcript:
            return jsonify(
                {
                    "error":
                        "No understandable speech was detected."
                }
            ), 400

        speech = analyze_speech(
            transcript,
            seconds
        )

        evaluation = evaluate_answer(
            question["question"],
            transcript,
            question["category"],
            question["expected_concepts"]
        )

        total_score = get_total_score(
            speech,
            evaluation
        )

        return jsonify(
            {
                "question": question["question"],
                "question_id": question["id"],
                "transcript": transcript,
                "overall_score": total_score,
                "speech": speech,
                "evaluation": evaluation
            }
        )

    except Exception as error:
        app.logger.exception(
            "Interview analysis failed."
        )

        return jsonify(
            {
                "error": str(error)
            }
        ), 500

    finally:
        if audio_path:
            if os.path.exists(audio_path):
                os.remove(audio_path)


def transcribe(audio_path):
    with open(
        audio_path,
        "rb"
    ) as audio:
        res = client.audio.transcriptions.create(
            file=audio,
            model=os.getenv(
                "GROQ_TRANSCRIPTION_MODEL",
                "whisper-large-v3-turbo"
            ),
            language="en",
            response_format="json"
        )

    return res.text.strip()


def get_total_score(speech, evaluation):
    scores = evaluation["scores"]

    total = (
        scores["relevance"] * 0.30
        + scores["specificity"] * 0.20
        + scores["structure"] * 0.20
        + scores["communication"] * 0.10
        + speech["pace_score"] * 0.10
        + speech["filler_score"] * 0.10
    )

    return round(total)


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify(
        {
            "error":
                "The audio recording is too large."
        }
    ), 413


if __name__ == "__main__":
    app.run(debug=True)