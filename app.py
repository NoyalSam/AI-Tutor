import os
import json
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

app = Flask(__name__)

# Secret key required for Flask session (stores question history per user)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "tutor-ai-secret-2025")

# ── LLM Setup ──────────────────────────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    google_api_key=os.environ.get("GOOGLE_API_KEY"),
)

# ── Chain 1: Question Generator ────────────────────────────────────────────────
# {asked_questions} is injected at runtime — contains all previously asked
# questions for this topic+level so the LLM never repeats them

question_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert tutor and interviewer.
Your job is to generate ONE clear, focused question based on the topic, level, and question number provided.

Rules:
- Generate exactly ONE question
- Match difficulty to the level: easy=basic concepts, medium=application, advanced=deep understanding
- Make it suitable for interview preparation
- NEVER repeat or rephrase any question from the already-asked list below
- If the already-asked list is empty, generate any suitable question
- Return ONLY the question text, no numbering, no extra text""",
    ),
    (
        "human",
        """Topic: {topic}
Level: {level}
Question number: {current} of {total}

Already asked questions (DO NOT repeat or rephrase any of these):
{asked_questions}

Generate a NEW question {current} that is completely different from the above:""",
    ),
])

# RunnablePassthrough() passes all input keys forward unchanged into the prompt
question_chain = (
    RunnablePassthrough()
    | question_prompt
    | llm
    | StrOutputParser()
)

# ── Chain 2: Answer Evaluator ──────────────────────────────────────────────────
evaluator_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a strict but fair technical interviewer evaluating an answer.

Evaluate the answer and return ONLY a valid JSON object:
{{
  "is_correct": true or false,
  "score": number between 0 and 10,
  "verdict": "Good for interview" or "Not good for interview",
  "feedback": "2-3 sentences max. What was right, what was missing, what to improve.",
  "correct_answer": "Write the ideal interview answer in 100-150 words. Concise, clear, and professional. No bullet points, just clean prose a candidate would say out loud.",
  "real_world_example": "One short sentence giving a real-world example ONLY if the concept needs illustration. If it is already simple enough, return an empty string."
}}

Scoring rules — be GENUINE, not generous:
- 9-10: Complete, accurate, well-explained. Ready to impress any interviewer.
- 7-8: Mostly correct but missing 1-2 key details.
- 5-6: Partially correct. Core idea present but explanation is weak or incomplete.
- 3-4: Vague or mostly wrong. Interviewer would not be satisfied.
- 1-2: Incorrect or nearly empty.
- 0: No answer given or completely irrelevant.

Return ONLY the JSON. No markdown, no extra text.""",
    ),
    (
        "human",
        "Topic: {topic}\nLevel: {level}\nQuestion: {question}\nStudent's answer: {answer}\n\nEvaluate:",
    ),
])

# RunnablePassthrough() forwards topic, level, question, answer into the prompt
evaluator_chain = (
    RunnablePassthrough()
    | evaluator_prompt
    | llm
    | StrOutputParser()
)

# ── Chain 3: Next Question (same chain, history-aware) ─────────────────────────
# Reuses question_prompt — RunnablePassthrough carries the full state including
# asked_questions so every subsequent question is unique
next_question_chain = (
    RunnablePassthrough()
    | question_prompt
    | llm
    | StrOutputParser()
)

# ── History Helpers ────────────────────────────────────────────────────────────
def get_history_key(topic: str, level: str) -> str:
    """Build a unique key per topic+level combination."""
    return f"{topic.strip().lower()}::{level.lower()}"


def get_asked_questions(topic: str, level: str) -> list:
    """Fetch previously asked questions for this topic+level from session."""
    key = get_history_key(topic, level)
    history = session.get("question_history", {})
    return history.get(key, [])


def save_question(topic: str, level: str, question: str) -> None:
    """Append a new question to the session history for this topic+level."""
    key = get_history_key(topic, level)
    if "question_history" not in session:
        session["question_history"] = {}
    history = session["question_history"]
    if key not in history:
        history[key] = []
    if question not in history[key]:          # deduplicate just in case
        history[key].append(question)
    session["question_history"] = history     # mark session as modified
    session.modified = True


def format_asked(questions: list) -> str:
    """Format the list for injection into the prompt."""
    if not questions:
        return "None"
    return "\n".join(f"- {q}" for q in questions)


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    """Receive topic + level + total, generate first unique question."""
    data  = request.json
    topic = data.get("topic", "").strip()
    level = data.get("level", "medium")
    total = int(data.get("total", 5))

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    try:
        # Load all previously asked questions for this topic+level
        asked = get_asked_questions(topic, level)

        # Generate Q1 via RunnablePassthrough chain with history injected
        question = question_chain.invoke({
            "topic": topic,
            "level": level,
            "current": 1,
            "total": total,
            "asked_questions": format_asked(asked),
        })

        # Save to session so next session won't repeat it
        save_question(topic, level, question)

        return jsonify({
            "question": question,
            "current": 1,
            "total": total,
            "history_count": len(asked),   # useful for debugging
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/evaluate", methods=["POST"])
def evaluate():
    """Receive answer, evaluate it, return feedback + correct answer."""
    data     = request.json
    topic    = data.get("topic", "")
    level    = data.get("level", "medium")
    question = data.get("question", "")
    answer   = data.get("answer", "").strip()

    if not answer:
        return jsonify({"error": "Answer cannot be empty"}), 400

    try:
        # Evaluate using RunnablePassthrough chain
        raw = evaluator_chain.invoke({
            "topic": topic,
            "level": level,
            "question": question,
            "answer": answer,
        })

        # Clean markdown fences if LLM wraps response
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
        if clean.endswith("```"):
            clean = "\n".join(clean.split("\n")[:-1])

        result = json.loads(clean)
        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse evaluation", "raw": raw}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/next", methods=["POST"])
def next_question():
    """Generate next unique question — never repeats anything in session history."""
    data    = request.json
    topic   = data.get("topic", "")
    level   = data.get("level", "medium")
    current = int(data.get("current", 1))
    total   = int(data.get("total", 5))

    try:
        # Load full history (includes questions from previous sessions too)
        asked = get_asked_questions(topic, level)

        # Generate next question with full history injected via RunnablePassthrough
        question = next_question_chain.invoke({
            "topic": topic,
            "level": level,
            "current": current,
            "total": total,
            "asked_questions": format_asked(asked),
        })

        # Save new question to session history
        save_question(topic, level, question)

        return jsonify({
            "question": question,
            "current": current,
            "total": total,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/history", methods=["GET"])
def view_history():
    """Debug route — see all stored question history in current session."""
    return jsonify(session.get("question_history", {}))


@app.route("/clear_history", methods=["POST"])
def clear_history():
    """Optional: clear history for a specific topic+level or all history."""
    data  = request.json or {}
    topic = data.get("topic", "").strip()
    level = data.get("level", "")

    if topic and level:
        key = get_history_key(topic, level)
        if "question_history" in session:
            session["question_history"].pop(key, None)
            session.modified = True
        return jsonify({"cleared": key})
    else:
        session.pop("question_history", None)
        return jsonify({"cleared": "all"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
