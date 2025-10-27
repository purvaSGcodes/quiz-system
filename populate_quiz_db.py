import sqlite3

conn = sqlite3.connect("quiz.db")
c = conn.cursor()

# Sample quizzes
c.execute('INSERT OR IGNORE INTO quizzes (id, name) VALUES (1, "HTML")')
c.execute('INSERT OR IGNORE INTO quizzes (id, name) VALUES (2, "CSS")')
c.execute('INSERT OR IGNORE INTO quizzes (id, name) VALUES (3, "DBMS")')

# Sample questions
html_questions = [
    ("What does HTML stand for?", "Hyper Text Markup Language", "High Text Machine Language", "Hyper Tabular Markup Language", "None of these", "1", 1),
    ("Which tag is used to insert an image?", "<img>", "<picture>", "<image>", "<src>", "1", 1)
]

css_questions = [
    ("Which property is used to change text color?", "color", "font-color", "text-color", "fgcolor", "1", 2),
    ("Which is the correct syntax to set background color?", "background-color: red;", "bgcolor=red;", "color-background:red;", "background=red;", "1", 2)
]

dbms_questions = [
    ("What does DBMS stand for?", "Database Management System", "Data Basic Management System", "Data Backup Management System", "Database Main Storage", "1", 3),
    ("Which SQL command is used to remove a table?", "DROP TABLE", "DELETE TABLE", "REMOVE TABLE", "TRUNCATE TABLE", "1", 3)
]

for q in html_questions + css_questions + dbms_questions:
    c.execute('''
    INSERT OR IGNORE INTO questions (question, option1, option2, option3, option4, correct_option, quiz_id)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', q)

conn.commit()
conn.close()
print("Sample quizzes and questions added!")
