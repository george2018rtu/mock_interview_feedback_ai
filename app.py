import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from flask import (Flask,jsonify,redirect,render_template,request,session,url_for)
from groq import Groq
from supabase import create_client
from ai_evaluator import evaluate_answer
from analyzer import analyze_speech
from questions import questions
import pandas as pd
load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = Flask(__name__)
app.secret_key=os.getenv("FLASK_SECRET_KEY")
app.config["MAX_CONTENT_LENGTH"] = (
    20 * 1024 * 1024
)

df = pd.read_csv('questions.csv')

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

def get_all_possible_sectors():
    sectors = df["role"].dropna().unique()
    return sectors.tolist()

def get_question(question_id):
    filtered = df[df["id"].astype(str) == str(question_id)]
    if filtered.empty:
        return None
    row = filtered.iloc[0]
    return {
        "id": str(row["id"]),
        "question": row["question"],
        "category": row["category"],
        "expected_concepts": str(
            row["expected_concepts"]
        ).split("|"),
        "role": row["role"],
        "difficulty": row["difficulty"]
    }

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "index.html",
        sectors=get_all_possible_sectors()
    )


def get_questions_by_sector(sector):
    filtered = df[df["role"] == sector]
    questions_list = []
    for _, row in filtered.iterrows():
        questions_list.append({
            "id": row["id"],
            "question": row["question"],
            "category": row["category"],
            "expected_concepts": row["expected_concepts"].split("|"),
            "role": row["role"],
            "difficulty": row["difficulty"]
        })
    return questions_list

@app.route("/questions")
def filtered_questions():
    sector = request.args.get("sector", "").strip()
    if not sector:
        return jsonify([])
    questions_list = get_questions_by_sector(sector)
    return jsonify(questions_list)

@app.route("/analyze", methods=["POST"])
def analyze():
    if "user_id" not in session:
        return jsonify({
            "error": "Please log in first."
        }), 401

    audio = request.files.get("audio")
    question_id = request.form.get("question_id", "").strip()
    duration_text = request.form.get(
        "duration",
        "0"
    )
    sector = request.form.get("sector", "").strip()
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
        for area in evaluation.get("improvements", []):
            supabase.table("improvements").insert({
                "user_id": session["user_id"],
                "sector": sector,
                "area": area
            }).execute()

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

@app.route("/login", methods=["GET", "POST"])
def login():
    error=None
    if request.method=="POST":
        email=request.form.get(("email")or"").strip()
        password=request.form.get(("password") or "")
        try:
            response=supabase.auth.sign_in_with_password({
                "email":email,
                "password":password
            })
            session["user_id"]=str(response.user.id)
            session["email"]=response.user.email
            return redirect(url_for("index"))
        except Exception:
            error="Incorrect email or password"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

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
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    result = (
        supabase
        .table("improvements")
        .select("*")
        .eq("user_id", session["user_id"])
        .order("created_at", desc=True)
        .execute()
    )
    rows = result.data or []
    grouped_improvements = {}
    for row in rows:
        sector = row.get("sector") or "Other"
        if sector not in grouped_improvements:
            grouped_improvements[sector] = []
        grouped_improvements[sector].append(row)

    return render_template(
        "dashboard.html",
        grouped_improvements=grouped_improvements
    )

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