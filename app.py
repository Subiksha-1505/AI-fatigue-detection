from openai import OpenAI
client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# =========================
# DB CONNECTION FUNCTION
# =========================
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# =========================
# ROUTES
# =========================

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login_action', methods=['POST'])
def login_action():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']   # student or teacher

    conn = get_db()
    cur = conn.cursor()

    if role == "student":
        cur.execute("SELECT * FROM students WHERE username=? AND password=?", (username, password))
    else:
        cur.execute("SELECT * FROM teachers WHERE username=? AND password=?", (username, password))

    user = cur.fetchone()

    if user:
        if role == "student":
            return redirect(url_for('student_dashboard', user_id=user['id']))
        else:
            return redirect(url_for('teacher_dashboard'))
    else:
        return "Invalid Login!"

# =========================
# STUDENT DASHBOARD
# =========================
@app.route('/student/<int:user_id>')
def student_dashboard(user_id):
    classes = ["4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th", "12th"]
    subjects = ["English", "Maths", "Science", "Computer Science"]
    return render_template("student_dashboard.html", classes=classes, subjects=subjects, user_id=user_id)

# =========================
# FETCH QUIZ BASED ON CLASS + SUBJECT
# =========================
@app.route('/quiz/<class_name>/<subject>')
def quiz_page(class_name, subject):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM quizzes WHERE class=? AND subject=?", (class_name, subject))
    quiz = cur.fetchall()
    return render_template("quiz.html", quiz=quiz, class_name=class_name, subject=subject)

# =========================
# TEACHER DASHBOARD
# =========================
@app.route('/teacher')
def teacher_dashboard():
    # Get performance data
    conn1 = get_db()
    cur = conn1.cursor()
    cur.execute("SELECT * FROM performance")
    performance_data = cur.fetchall()
    conn1.close()
    
    # Get quiz results
    conn2 = sqlite3.connect("quiz.db")
    c = conn2.cursor()
    c.execute("SELECT student_name, class, subject, topic, score, typing_speed, time_taken, fatigue_level, attention_level FROM results")
    quiz_results = c.fetchall()
    conn2.close()
    
    # Pass both to template - CORRECTED LINE
    return render_template("teacher_dashboard.html", 
                        performance_data=performance_data, 
                        results=quiz_results)

# -------------------------------------------
# STEP 1: CLASS → SUBJECT → TOPIC MAPPING
# -------------------------------------------

topics_data = {
    "English": ["Tenses", "Nouns", "Prefix & Suffix"],
    "Mathematics": ["Algebra", "Geometry", "Fractions"],
    "Science": ["Electricity", "Force & Motion", "Plants & Animals"],
    "Computer": ["Python Basics", "Algorithms", "Internet Safety"],
    "Social Science": ["History", "Geography", "Civics"],
    "Physics": ["Motion", "Electricity", "Optics"],
    "Chemistry": ["Periodic Table", "Chemical Bonding", "Acids & Bases"],
    "Biology": ["Cell Biology", "Human Physiology", "Genetics"]
}

# -------------------------------------------
# STEP 1: ROUTE TO SHOW TOPICS
# -------------------------------------------
@app.route('/select_topic', methods=['POST'])
def select_topic():
    selected_class = request.form['class']
    selected_subject = request.form['subject']

    # Get topics for the selected subject
    topics = topics_data.get(selected_subject, [])

    return render_template(
        'select_topic.html',
        selected_class=selected_class,
        selected_subject=selected_subject,
        topics=topics
    )

# -------------------------------------------
# STEP 2: REAL AI-BASED QUESTION GENERATOR
# -------------------------------------------

def generate_ai_questions(selected_class, subject, topic):
    prompt = f"""
    You are an expert teacher. Generate 5 quiz questions for:
    Class: {selected_class}
    Subject: {subject}
    Topic: {topic}

    Requirements:
    - Questions should match the difficulty of the given class level.
    - Mix MCQ, fill-in-the-blanks, and short answers.
    - Output ONLY the questions, numbered 1 to 5.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    ai_output = response.choices[0].message.content

    # Split questions into list
    questions = [q.strip() for q in ai_output.split("\n") if q.strip()]

    return questions

# -------------------------------------------
# STEP 2C: ROUTE TO START QUIZ USING AI
# -------------------------------------------
@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    selected_class = request.form['class']
    selected_subject = request.form['subject']
    selected_topic = request.form['topic']

    # Generate questions using AI
    questions = generate_ai_questions(selected_class, selected_subject, selected_topic)

    return render_template(
        'quiz.html',
        selected_class=selected_class,
        selected_subject=selected_subject,
        selected_topic=selected_topic,
        questions=questions
    )

# -------------------------------------------
# STEP 3: AI BASED BEHAVIOUR ANALYSIS
# -------------------------------------------

def analyse_behavior(typing_speed, time_taken, score):
    # Simple AI logic – can be upgraded later

    fatigue = ""
    typing_rate = typing_speed / time_taken

    if typing_rate < 1:
        fatigue = "High fatigue detected — student typing very slow."
    elif typing_rate < 3:
        fatigue = "Moderate fatigue — student slightly slow."
    else:
        fatigue = "Active and alert — typing speed normal."

    attention = ""
    if time_taken > 120:
        attention = "Low attention — took too long for answers."
    elif time_taken > 60:
        attention = "Moderate attention."
    else:
        attention = "High attention — responded quickly."

    performance = ""
    if score == 5:
        performance = "Excellent performance."
    elif score >= 3:
        performance = "Good performance."
    else:
        performance = "Needs improvement."

    return fatigue, attention, performance

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    student = "Student1"  # Replace later with login username

    selected_class = request.form['class']
    selected_subject = request.form['subject']
    selected_topic = request.form['topic']

    typing_speed = int(request.form['typing_speed'])
    time_taken = float(request.form['time_taken'])

    # Collect answers
    answers = []
    questions = request.form.getlist("question_list")
    
    for i in range(1, 6):
        answers.append(request.form.get(f"answer{i}", ""))

    # AI Scoring
    score = evaluate_answers(questions, answers)

    # AI Behaviour analysis
    fatigue, attention, performance = analyse_behavior(typing_speed, time_taken, score)

    # Save to database
    save_result(student, selected_class, selected_subject, selected_topic,
                score, typing_speed, time_taken, fatigue, attention)

    return f"""
    <h2>Quiz Submitted</h2>
    <p>Score: {score}/5</p>
    <p>Fatigue Level: {fatigue}</p>
    <p>Attention Level: {attention}</p>
    <p>Performance: {performance}</p>

    <br><a href='/student_home'>Back to Home</a>
    """

def evaluate_answers(questions, answers):
    formatted_qna = ""
    for q, a in zip(questions, answers):
        formatted_qna += f"Q: {q}\nStudent Answer: {a}\n\n"

    prompt = f"""
    Evaluate the following student answers.

    {formatted_qna}

    Rules:
    - Give a score out of 5.
    - Consider correctness, grammar, and understanding.
    - Return ONLY the number (0–5).
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    score = int(response.choices[0].message.content.strip())
    return score

def save_result(student, classroom, subject, topic, score, typing_speed, time_taken, fatigue, attention):
    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()

    c.execute("""
    INSERT INTO results (student_name, class, subject, topic, score, typing_speed, time_taken, fatigue_level, attention_level)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (student, classroom, subject, topic, score, typing_speed, time_taken, fatigue, attention))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    app.run(debug=True)
