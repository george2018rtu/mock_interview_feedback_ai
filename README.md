# AI Mock Interview Analyzer

Using this software, you can practice behavorial and technical interview question with a real-time coach!

The AI Mock Interview Analyzer is a Flask web application that allows users to answer interview questions verbally. It transcribes spoken responses using Whisper, evaluates them using Llama 3.3 through the Groq API, and provides detailed feedback on answer quality, communication, and interview performance.

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
> *Show the timer, recording indicator, and Stop Recording button while recording.*

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

## Installation

Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/mock_interview_feedback_ai.git
cd mock_interview_feedback_ai
```

Create a virtual environment

Windows

```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

Mac/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create a `.env`

```env
GROQ_API_KEY=YOUR_KEY
GROQ_EVALUATION_MODEL=llama-3.3-70b-versatile
SUPABASE_URL=YOUR_URL
SUPABASE_KEY=YOUR_KEY
```

Run the project

```bash
python app.py
```

Open

```
http://127.0.0.1:5000
```
---

### Login

Login using the guest account:

- **Email:** `guest.user@interviewanalyzer.com`
- **Password:** `guestuser`

This way, you can test out the features of our project!

---

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
