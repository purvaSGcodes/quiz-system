import sqlite3

conn = sqlite3.connect('quiz.db')
c = conn.cursor()

print("=== Quizzes ===")
for row in c.execute("SELECT * FROM quizzes"):
    print(row)

print("\n=== Questions ===")
for row in c.execute("SELECT * FROM questions"):
    print(row)

conn.close()
