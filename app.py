#just a heads up I use jsonify a lot so that the computer can understand whatever I'm returnig because they can't understand simple python dictonaries
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from flask import (Flask, jsonify, redirect, render_template, request, session, url_for)
from groq import Groq
from supabase import create_client

#import functions from my own python files that will be helpful
from ai_evaluator import evaluate_answer
from analyzer import analyze_speech

#import all the questions
from questions import questions
import pandas as pd

#.env file
load_dotenv()

#create supabase client with API Url and Supabase anon key for easy data storing
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

#create groq client once again (this one will be used for transcription instead of using the AI)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = Flask(__name__)

#this is to make sure that login works properly

#we chose to have logins so we can have an areas to improve page where Supabase stores all the feedback the AI
#has ever for the specific user ID. Right now you can't sign up so I have to manually create accounts for people to use,
#but I don't want people to be signing up yet anyway.
app.secret_key=os.getenv("FLASK_SECRET_KEY")

#limit uploaded files to 20 megabytes
app.config["MAX_CONTENT_LENGTH"] = (
    20 * 1024 * 1024 #20 times 1024 times 1024 bytes
)

#read questions.csv to do sector specific questions etc.
df = pd.read_csv('questions.csv')

AUDIO_TYPES = {".webm", ".ogg", ".mp4", ".mp3", ".wav", ".m4a"}

#as it says, this code accesses the data frames role column, drops all empty rows, and only store the unique values
def get_all_possible_sectors():
    sectors = df["role"].dropna().unique()

    #convert the return data frame as a list.
    return sectors.tolist()

#searches for a specific question
def get_question(question_id):
    #make sure it's string against string comparison
    filtered = df[df["id"].astype(str) == str(question_id)]

    #if no rows match, return none.
    if filtered.empty:
        return None

    #gets the first matching row (there should only be one question each but just in case because sometimes the dataset may have repeated questions)
    row = filtered.iloc[0]

    #convert the row into a dictonary
    return {
        "id": str(row["id"]),
        "question": row["question"],
        "category": row["category"],
        "expected_concepts": str(row["expected_concepts"]).split("|"),
        "role": row["role"],
        "difficulty": row["difficulty"]
    }

@app.route("/")
def index():

    #if we didn't store the user_id from before(meaning we didn't create a user for this person), rediirect them to the login page
    if "user_id" not in session:
        return redirect(url_for("login"))

    #otherwise, just return index.html/the place where the AI feedback and recording area are 
    #also pass in all possible sectors so the html file cna do something like this and have sector specific questions available
    #{% for sector in sectors %}
        #<option>{{ sector }}</option>
    #{% endfor %}

    return render_template(
        "index.html",
        sectors=get_all_possible_sectors()
    )

#get all the questions for the specific sector passed into the function
def get_questions_by_sector(sector):
    #get the data frame for all sectors that match the passed in parameter (role in the csv is essentially 
    # just sector or like software engineer, marketing manager etc.)
    filtered = df[df["role"] == sector]

    #define a list to append all questions for the specific sector as a dictonary rather than a data frame (which wouldn't work)
    questions_list = []

    #do the iteration process in which questions list will have a python dictionary
    #remarking all the information of every question for the specific sector
    for _, row in filtered.iterrows():
        questions_list.append({
            "id": row["id"],
            "question": row["question"],
            "category": row["category"],
            "expected_concepts": row["expected_concepts"].split("|"),
            "role": row["role"],
            "difficulty": row["difficulty"]
        })

    #return the final list with all the questions for the specific sector where each question is represented through a python dictonary
    return questions_list

#this is the route called by java script when the user selects a specific sector
@app.route("/questions")
def filtered_questions():
    #get the sector
    sector = request.args.get("sector", "").strip()

    #if there is no sector return empty json list
    if not sector:
        return jsonify([])

    #otherwise get the list wiht all the questions for that specific secto rusing the previously defined function
    questions_list = get_questions_by_sector(sector)

    #returns matching questions back to java script to read
    return jsonify(questions_list)

#this route only accepts post requests so that the uuser can't access where the analyses are done
#this is because the browser is sending data to the server
@app.route("/analyze", methods=["POST"])
def analyze():
    #make sure the user has an account before allowing them to use the service
    if "user_id" not in session:
        return jsonify({"error": "Please log in first."}), 401

    #gets the uploaded audio from the form
    audio = request.files.get("audio")

    #gets the selected question id
    question_id = request.form.get("question_id", "").strip()

    #gets the "follow up question" the AI returns
    custom_question_text = request.form.get("custom_question_text", "").strip()

    #gets the recording duration
    duration_text = request.form.get("duration", "0")

    #gets the sector selected(yes once again)
    sector = request.form.get("sector", "").strip()

    #checks if there is no audio or the audio doesn't have a file name
    if audio is None or not audio.filename:
        return jsonify({"error": "No audio file was submitted."}), 400

    #if question is a follow up question, set question to be that question because we want the user to be able to
    #use the follow up question as their next question that the AI gives feedback on
    if question_id == "followup":
        question = {"id": "followup", "question": custom_question_text, "category": "behavioral", "expected_concepts": [],}
    else:
        #use the get question function to get the question and set question to be the returned dictonary
        question = get_question(question_id)

        #if there is no question, return error
        if question is None:
            return jsonify({"error":"The selected question is invalid."}), 400
    try:
        seconds = float(duration_text)

    #catch any value errors and returns it
    except ValueError:
        return jsonify({"error": "The recording duration is invalid."}), 400

    #if the recording length is over 10 minutes then it's too long and it will be outside the recording range that we consider acceptable (will take up too much storage, require the
    #AI to analyze too much, etc.) Prevents crashes and makes the analyses a little faster because the API request doesn't instantly return whatever we want.
    #also who answers an interview question for over 10 minutes anyway.
    if seconds > 600:
        return jsonify({"error": "The recording duration is outside the allowed range."}), 400

    #make sure the audio recording using the browser actually returns an audio extension that is appropriate. else return another error.
    ext = Path(audio.filename).suffix.lower()
    if ext not in AUDIO_TYPES:
        return jsonify({"error": "Unsupported audio format."}), 400

    audio_path = None

    try:
        #creates a temporary file on the server. delete=False means Python does not immediately delete it when the with block ends.
        #this is needed because Groq must open the file afterward.

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False ) as temp:
            audio_path = temp.name
            audio.save(audio_path)

        #transcribe audio using the function defined below
        transcript = transcribe(audio_path)

        #if there is no transcription, maybe because the user speaks too bad english or something and the Whisper model from groq can't understand it, raise another error
        if not transcript:
            return jsonify(
                {"error": "No understandable speech was detected."}), 400

        #get all the stats like words per minute etc. using the function from analyzer.py
        speech = analyze_speech(transcript,  seconds)

        #set evaluation to whatever the AI returned (in the form of a python dictonary)
        evaluation = evaluate_answer(question["question"], transcript, question["category"], question["expected_concepts"])

        #get total score using hardcoded weightings based on importance
        total_score = get_total_score(speech, evaluation)

        #for all improvements (otherwise blank list)
        for area in evaluation.get("improvements", []):

            #supabase.table selects the table named whatever you pass in. I called it improvements

            #because the AI returns improvements, we store in Supabase database user_id (so there is personalized areas to improve),
            #the specific sector so that we can show feedback based on the sector of the question, and the actualy feedback itself (which is called area)
            supabase.table("improvements").insert({"user_id": session["user_id"], "sector": sector, "area": area}).execute()

        #return the analyses like overall score, the question, the evaluation (words per minute, filler score, pace score, etc. to help add more feedback)
        return jsonify(
            {"question": question["question"], "question_id": question["id"], "transcript": transcript, "overall_score": total_score, "speech": speech, "evaluation": evaluation})

    #if there is an error, return the analysis failed to the user 
    except Exception as error:
        app.logger.exception("Interview analysis failed.")

        #retur to computer
        return jsonify({"error": str(error)}), 500

    #finally, remove the temporary audio file from local storage of computer no matter if there is an error there, hence the keyword finally:
    finally:
        if audio_path:
            if os.path.exists(audio_path):
                os.remove(audio_path)


#get would be show login page, while post is to check login credentials
@app.route("/login", methods=["GET", "POST"])
def login():

    #initially there will be no errors, but as we go on and there is, we use this to store it.
    error=None

    #if the method is post, or check login credentials
    if request.method=="POST":

        #check the email in the form from login.html
        email=request.form.get(("email")or"").strip()

        #check the password
        password=request.form.get(("password") or "")
        try:
            response=supabase.auth.sign_in_with_password({
                "email":email,
                "password":password
            })
            session["user_id"]=str(response.user.id)
            session["email"]=response.user.email
            #if it's there/in the authentication part of supabase, lead them to index.html which is where the feedback and stuff are shown.
            return redirect(url_for("index"))
        except Exception:
            #otherwise show incorrect email or password
            error="Incorrect email or password"
    #otherwise just show the login.html (don't need to use else statement in this case so this is just the method of 'GET')
    return render_template("login.html", error=error)

#logout just leads you back to login essentially and clears whatever user_id was in session from before so that it doesn't let you access the index.html straight up
#without loggin in again.
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

def transcribe(audio_path):
    #opens the audio file as read-binary mode as the variable audio so that the whisper model can actually transcribe it.
    with open(audio_path, "rb") as audio:
        #what this chunk does is send the audio file to whisper model from groq and ask it to return it in the form of a json. Also language="en" means expect english 
        #in the audio file
        res = client.audio.transcriptions.create(
            file=audio,
            model=os.getenv(
                "GROQ_TRANSCRIPTION_MODEL",
                "whisper-large-v3-turbo"
            ),
            language="en",
            response_format="json"
        )

    #gets the transcript and removes spaces from the beginning and end.
    return res.text.strip()

#get score where relevance is weighted 30% specificity is weight 20% etc.
def get_total_score(speech, evaluation):
    scores = evaluation["scores"]


    #set that score to total so we can round it
    total = (
        scores["relevance"] * 0.30 + scores["specificity"] * 0.20 + scores["structure"] * 0.20 + scores["communication"] * 0.10 + speech["pace_score"] * 0.10 + speech["filler_score"] * 0.10
    )

    #return the rounded total
    return round(total)


@app.route("/dashboard")
def dashboard():
    #first make sure that the user_id is actually in session or else just return to login/if the user tries to do url/dashboard
    #just lead them back to login page
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    #This means:
        #from the improvements table,
        #select all columns,
        #where user_id equals the logged-in user's ID,
        #order newest first,
        #then run the query. 
    res = (supabase.table("improvements").select("*").eq("user_id", session["user_id"]).order("created_at", desc=True).execute())

    #if it returns data, use it, else use an empty list
    rows = res.data or []

    #creates an empty dictionary to group by sector like software engineering: this improvement, that improvement so that it returns improvements for each sector
    grouped_improvements = {}
    #for every database row:
    for row in rows:

        #get the sector for the database row (i have a column for sector in the database)
        sector = row.get("sector") or "Other"

        #if it's not in grouped improvements, then just define it then for future adding
        if sector not in grouped_improvements:
            grouped_improvements[sector] = []

        #add whatever improvement it is
        grouped_improvements[sector].append(row)

    #pretty self explanatory
    return render_template("dashboard.html", grouped_improvements=grouped_improvements)

#flask automatically calls this if the file size is greater than 20mb
@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({"error": "The audio recording is too large."}), 413


if __name__ == "__main__":
    app.run(debug=True)