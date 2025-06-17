import sqlite3
import os

DB_FILE = 'data/admissions.db'

def connect_db():
    return sqlite3.connect(DB_FILE)

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()
    
    # Проверяем, существует ли таблица users
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        # Создаем таблицу с новыми полями, включая photo_path
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE,
                name TEXT,
                email TEXT,
                age INTEGER,
                gender TEXT,
                photo_path TEXT  -- Добавлено поле для хранения пути к фото
            )
        ''')
    else:
        # Добавляем недостающие колонки, если таблица уже существует
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN photo_path TEXT")
            print("Колонка 'photo_path' добавлена в таблицу 'users'")
        except sqlite3.OperationalError as e:
            # Игнорируем ошибку, если колонка уже существует
            if "duplicate column name" not in str(e):
                raise
    
    # Создаем таблицу applications
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            specialty_code TEXT,
            specialty_title TEXT,
            status TEXT DEFAULT 'submitted',
            submission_date TEXT,
            document_id TEXT,
            admin_response TEXT,
            response_date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Добавляем новые колонки, если их нет
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN specialty_code TEXT")
        print("Колонка 'specialty_code' добавлена в таблицу 'applications'")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise
    
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN specialty_title TEXT")
        print("Колонка 'specialty_title' добавлена в таблицу 'applications'")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise
    
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN admin_response TEXT")
        print("Колонка 'admin_response' добавлена в таблицу 'applications'")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise
    
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN response_date TEXT")
        print("Колонка 'response_date' добавлена в таблицу 'applications'")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise
    
    conn.commit()
    conn.close()

def get_user_by_telegram_id(telegram_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, email, age, gender, photo_path FROM users WHERE telegram_id = ?", (telegram_id,))
    except sqlite3.OperationalError as e:
        # Если ошибка связана с отсутствующей колонкой, возвращаем данные без photo_path
        if "no such column: photo_path" in str(e):
            cursor.execute("SELECT id, name, email, age, gender FROM users WHERE telegram_id = ?", (telegram_id,))
            user_data = cursor.fetchone()
            if user_data:
                # Добавляем None для photo_path
                user_data = list(user_data) + [None]
                return tuple(user_data)
            return None
        else:
            raise
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(telegram_id, name, email, age, gender):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (telegram_id, name, email, age, gender) 
            VALUES (?, ?, ?, ?, ?)
        """, (telegram_id, name, email, age, gender))
        conn.commit()
        user_id = cursor.lastrowid
    finally:
        conn.close()
    return user_id

def update_user_photo(user_id, photo_path):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET photo_path = ? WHERE id = ?", (photo_path, user_id))
        conn.commit()
    finally:
        conn.close()

def create_application(user_id, specialty_code=None, specialty_title=None, document_id=None):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO applications (user_id, specialty_code, specialty_title, status, submission_date, document_id) 
        VALUES (?, ?, ?, 'submitted', datetime('now'), ?)
    """, (user_id, specialty_code, specialty_title, document_id))
    conn.commit()
    app_id = cursor.lastrowid
    conn.close()
    return app_id

def get_application_status(app_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM applications WHERE id = ?", (app_id,))
    status = cursor.fetchone()
    conn.close()
    return status[0] if status else None

def get_application_details(app_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.specialty_code, a.specialty_title, a.status, a.submission_date, 
               a.admin_response, a.response_date, u.name, u.email
        FROM applications a
        JOIN users u ON a.user_id = u.id
        WHERE a.id = ?
    """, (app_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def update_application_status(app_id, status, admin_response):
    conn = connect_db()
    cursor = conn.cursor()
    from datetime import datetime
    response_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        UPDATE applications 
        SET status = ?, admin_response = ?, response_date = ?
        WHERE id = ?
    """, (status, admin_response, response_date, app_id))
    conn.commit()
    conn.close()

def get_applications_by_user(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, specialty_code, specialty_title, status, submission_date 
        FROM applications 
        WHERE user_id = ? 
        ORDER BY submission_date DESC
    """, (user_id,))
    applications = cursor.fetchall()
    conn.close()
    return applications

def check_user_has_application_for_specialty(user_id, specialty_code):
    """Проверяет, есть ли у пользователя уже заявка на данную специальность"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM applications 
        WHERE user_id = ? AND specialty_code = ?
    """, (user_id, specialty_code))
    result = cursor.fetchone()
    conn.close()
    return result is not None

create_tables()