from flask import Flask, request, render_template, session, redirect, url_for
import random
import psycopg2
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'очень_секретная_строка_123'

answers = [
    "Без сомнений",
    "Скорее всего да",
    "Спроси позже",
    "Не рассчитывай на это",
    "Определённо нет",
    "Да, но не сейчас",
    "Сложно сказать",
    "Знаки указывают на да"
]

# Получаем параметры из docker-compose
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "magic")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_chatgpt_response(user_question, template="Ты ассистент. Отвечай только 'Да' или 'Нет'."):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": template},
                {"role": "user", "content": user_question}
            ],
            max_tokens=20,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка: {str(e)}"
    
    
# Функция подключения к базе
def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/')
def index():
    question = request.args.get('q')
    answer = None
    username = session.get('user')

    if question:
        template = "Ты ассистент. Отвечай только 'Да' или 'Нет'."
        answer = get_chatgpt_response(question, template)


        if username:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO questions (user_id, question, answer) VALUES (%s, %s, %s)",
                (user_id, question, answer)
            )
            conn.commit()
            conn.close()

    history = []
    if username:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT question, answer
            FROM questions
            JOIN users ON users.id = questions.user_id
            WHERE users.username = %s
            ORDER BY questions.id DESC
        ''', (username,))
        history = cursor.fetchall()
        conn.close()

    return render_template('index.html', question=question, answer=answer, history=history)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    hashed = generate_password_hash(password)

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
        conn.commit()
        session['user'] = username
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
    row = cursor.fetchone()
    conn.close()

    if row and check_password_hash(row[0], password):
        session['user'] = username

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
