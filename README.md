# AI Mock Interview Analyzer

Using this software, you can practice behavorial and technical interview questions with a real-time coach!

Just a heads up, you need an API key to run this project for Groq and Supabase. If you want to see the functionality, access this url:
https://mockinterviewfeedbackai-production.up.railway.app/ 

---

## Demo

### Home Screen

> <img width="1910" height="890" alt="image" src="https://github.com/user-attachments/assets/e48d2902-fd31-4a3b-8507-3206d351f884" />
>
> *Screenshot of the landing page with the question selector and Start Recording button.*

---

### Recording an Answer

> <img width="1913" height="893" alt="image" src="https://github.com/user-attachments/assets/9ff7a093-6de6-457d-8928-4a2dcf3717d9" />

>
> *Shows the timer, recording indicator, and Stop Recording button while recording.*

---

### AI Feedback

> <img width="1892" height="875" alt="image" src="https://github.com/user-attachments/assets/4ae5b511-17eb-456b-ba0d-847f51522625" />

>
> *Display the completed analysis with scores, strengths, improvements, and follow-up question.*

---

## Features

- Record interview responses directly in the browser

- Automatic speech-to-text transcription

- AI-powered interview evaluation

- Scores responses based on

  - Relevance
  - Specificity
  - Structure
  - Communication

- STAR method detection for behavioral questions

- Personalized strengths and improvement suggestions

- AI-generated follow-up interview questions

- Stores feedback for the user in Supabase

---

## Built With

| Technology | Purpose |
|------------|---------|
| Flask | Backend API |
| JavaScript | Frontend logic |
| HTML/CSS | User Interface |
| MediaRecorder API | Audio recording |
| Groq API | AI inference |
| Whisper | Speech transcription |
| Llama 3.3 | Interview evaluation |
| Supabase | Database |

---

## How It Works

```text
User
   │
   ▼
Browser records audio
   │
   ▼
Flask Backend
   │
   ▼
Whisper
(Audio → Text)
   │
   ▼
Llama 3.3 (Groq)
   │
   ▼
Interview Evaluation
   │
   ▼
Feedback Displayed
   │
   ▼
Saved to Supabase
```

---

## Screenshots

### Areas to Improve Section

> <img width="1891" height="871" alt="image" src="https://github.com/user-attachments/assets/601c4af9-716c-48e7-9e5b-53ccffba8456" />
*This stores all of the AI's attempts to give improvement feedback for each specific sector


---

### Supabase Dashboard

> <img width="1866" height="906" alt="image" src="https://github.com/user-attachments/assets/1fdc21d9-78c3-4f45-976d-2437dc4c3f2c" />

*Stores all feedback comments from the AI into one database

---

## How to run our project

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/mock_interview_feedback_ai.git
cd mock_interview_feedback_ai
```

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure Environment Variables (because this project needs API keys)

Create a `.env` file in the project's root directory with the following:

```env
GROQ_API_KEY=YOUR_GROQ_API_KEY
GROQ_EVALUATION_MODEL=llama-3.3-70b-versatile
GROQ_TRANSCRIPTION_MODEL=whisper-large-v3-turbo
SUPABASE_URL=YOUR_SUPABASE_URL
SUPABASE_KEY=YOUR_SUPABASE_KEY
FLASK_SECRET_KEY=YOUR_SECRET_FLASK_KEY
```

Alternatively, you can access our web application here if you do not want to set up any API keys....
https://mockinterviewfeedbackai-production.up.railway.app/ 

## 5. Run the Application (or use the URL to our web application)

```bash
python app.py
```

The application will be available at:

```
http://127.0.0.1:5000
```

---

# Guest Login

Use the guest account to try the features, including using our interview analysis, and seeing a display of all feedback points for you specifically stored in a database in Supabase(in areas to improve)

| Field | Value |
|-------|-------|
| **Email** | `guest.user@interviewanalyzer.com` |
| **Password** | `guestuser` |

The guest account provides access to the application's interview practice and AI feedback features.

## Project Structure

```
INTERVIEW-ANALYZER/
│
├── app.py
├── analyzer.py
├── ai_evaluator.py
├── questions.py
├── questions.csv
├── requirements.txt
├── .env
│
├── static/
│   ├── script.js
│   └── styles.css
│
└── templates/
    └── index.html
    └── dashboard.html (areas to improve page but I just named it dashboard)
    └── login.html

```

---

## Example AI Feedback

```
Overall Score: 88/100

Strengths
• Good organization
• Clear communication
• Relevant examples

Improvements
• Include measurable results
• Expand technical explanation

Missing Concepts
• Quantified impact

Follow-Up Question
Describe a challenge you faced during that project.
```

---

## Future Improvements

- Allow users to sign up
- Progress dashboard
- Historical interview tracking
- Personalized daily practice
- Resume upload
- AI-generated interview sessions
- Industry-specific interview modes
- AWS deployment
- Analytics dashboard

---

## Authors

George Wang

Daniel Chen

---

## License

Educational project.
