# 🎓 TutorAI — AI-Powered Interview Preparation Tutor

An intelligent interview preparation web application powered by **Google Gemini 2.5 Flash** and **LangChain**. Enter any topic, select your difficulty level, choose how many questions you want, and get evaluated with genuine scoring, correct answers, and real-world examples — all in a clean dark-themed UI.

---

## 📸 Features

- ✅ **Topic-based question generation** — enter any topic like Python, ML, SQL, React, etc.
- ✅ **Three difficulty levels** — Easy, Medium, Advanced
- ✅ **Custom question count** — choose 3, 5, 7, 10 or type any number up to 50
- ✅ **Genuine scoring** — rated out of 10 with honest feedback, not generous scoring
- ✅ **Interview verdict** — "Good for interview" or "Not good for interview"
- ✅ **Correct answer** — concise 100-150 word ideal interview answer
- ✅ **Real-world examples** — short, only shown when the concept needs illustration
- ✅ **No repeated questions** — session history ensures every session asks fresh questions for the same topic and level
- ✅ **Three-stage LangChain prompt chain** — separate chains for question generation, evaluation, and next question
- ✅ **Progress tracking** — dot progress bar and average score at the end

---

## 🏗️ Project Structure

```
ai_tutor/
├── app.py                  # Flask backend — chains, routes, session history
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
└── templates/
    └── index.html          # Frontend UI — 4 screens
```

---

## 🖥️ UI Screens

| Screen | Description |
|---|---|
| **Setup** | Enter topic, pick level, choose question count |
| **Question** | One question at a time with answer textarea |
| **Result** | Score ring, verdict, feedback, correct answer, example |
| **Complete** | Average score across all questions |

---

## ⚙️ How It Works

The app uses a **three-stage LangChain pipe chain** with `RunnablePassthrough`:

```
User enters topic + level + count
        ↓
Chain 1 — Question Generator (/start)
  RunnablePassthrough → question_prompt → Gemini LLM → StrOutputParser
  Injects previously asked questions → generates a NEW unique question
        ↓
User types answer → clicks Submit
        ↓
Chain 2 — Answer Evaluator (/evaluate)
  RunnablePassthrough → evaluator_prompt → Gemini LLM → StrOutputParser
  Returns: JSON with score, verdict, feedback, correct answer, example
        ↓
User clicks "OK I understand"
        ↓
Chain 3 — Next Question Generator (/next)
  RunnablePassthrough → question_prompt → Gemini LLM → StrOutputParser
  Loads full session history → generates next unique question
        ↓
Repeats until all questions done → Complete screen
```

---

## 🔄 No-Repeat Question System

Every question generated is saved to a **Flask session** under a key like `ml::medium`. On every new session for the same topic and level, the full history is injected into the prompt and the LLM is instructed to never repeat or rephrase any previous question.

```
Session 1 → ML + Medium
  Q1: What is supervised learning?     ← saved
  Q2: What is overfitting?             ← saved
  Q3: Explain bias-variance tradeoff   ← saved

Session 2 → ML + Medium (restart)
  Prompt: "DO NOT repeat the above 3 questions"
  Q1: What is cross-validation?        ← brand new
  Q2: Explain gradient descent         ← brand new
  Q3: What is regularization?          ← brand new
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ai-tutor.git
cd ai-tutor
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your API key

```bash
cp .env.example .env
```

Open `.env` and add your Google API key:

```
GOOGLE_API_KEY=your_google_api_key_here
FLASK_SECRET_KEY=any_random_string_here
```

> Get your free API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 5. Run the app

```bash
python app.py
```

Open your browser and go to:

```
http://localhost:5000
```

---

## 🖱️ Usage

1. Enter a **topic** — e.g. `Machine Learning`, `Python decorators`, `SQL joins`
2. Select **difficulty level** — Easy, Medium, or Advanced
3. Choose **number of questions** — click a chip or type a custom number
4. Click **Start Session**
5. Read the question and **type your answer**
6. Click **Submit Answer**
7. View your **score, verdict, feedback, correct answer**
8. Click **OK I understand** to move to the next question
9. After all questions — view your **average score**

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.10+ | Core language |
| Flask | Web server, routing, session management |
| LangChain | LLM chain orchestration |
| LangChain Google GenAI | Gemini model connector |
| Google Gemini 2.5 Flash | AI model for question generation and evaluation |
| python-dotenv | Secure API key management |
| Flask Session | Browser-side session for question history |
| HTML / CSS / JavaScript | Frontend UI — 4 screen flow |

---

## 📦 Dependencies

```
flask>=3.0.0
python-dotenv>=1.0.0
langchain-google-genai>=1.0.0
langchain-core>=0.2.0
```

---

## 📁 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serves the main UI |
| POST | `/start` | Generates first question for a session |
| POST | `/evaluate` | Evaluates user's answer, returns score and feedback |
| POST | `/next` | Generates next unique question |
| GET | `/history` | View all stored question history in session |
| POST | `/clear_history` | Clear history for a topic+level or all |

---

## 🔐 Security Note

- Never commit your `.env` file to GitHub
- The `.env.example` file is safe to commit — it contains no real keys
- Add `.env` to your `.gitignore` file

### Recommended `.gitignore`

```
.env
__pycache__/
*.pyc
venv/
.venv/
```

---

## 🙌 Acknowledgements

- [LangChain](https://www.langchain.com/) — LLM orchestration framework
- [Google Gemini](https://deepmind.google/technologies/gemini/) — AI model
- [Flask](https://flask.palletsprojects.com/) — Python web framework

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
