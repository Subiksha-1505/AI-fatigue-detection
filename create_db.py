import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# ========================
# CREATE TABLES
# ========================

cur.execute("""CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT,
    class TEXT,
    subject TEXT,
    topic TEXT,
    marks INTEGER
)""")

# ========================
# INSERT SAMPLE STUDENTS
# ========================
sample_students = [
    ("student1", "1234"),
    ("student2", "1234"),
    ("john", "pass"),
    ("ram", "pass"),
]

cur.executemany("INSERT INTO students (username, password) VALUES (?, ?)", sample_students)

# ========================
# INSERT SAMPLE TEACHERS
# ========================
sample_teachers = [
    ("teacher1", "abcd"),
    ("teacher2", "abcd"),
    ("priya", "teach"),
]

cur.executemany("INSERT INTO teachers (username, password) VALUES (?, ?)", sample_teachers)

# ========================
# INSERT SAMPLE PERFORMANCE
# ========================
sample_performance = [
    ("student1", "10th", "Maths", "Algebra", 85),
    ("student2", "6th", "Science", "Plants", 72),
    ("john", "12th", "Physics", "Waves", 91),
]

cur.executemany("""
INSERT INTO performance (student, class, subject, topic, marks)
VALUES (?, ?, ?, ?, ?)
""", sample_performance)

conn.commit()
conn.close()

print("Database created with sample data! 🎉")
