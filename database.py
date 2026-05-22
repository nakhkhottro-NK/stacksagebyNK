"""
database.py — SQLite Persistence Layer
Adds: share links, user accounts.
"""

import sqlite3
import json
import hashlib
import secrets
from datetime import datetime
from config import DATABASE_PATH


def _get_conn():
    return sqlite3.connect(DATABASE_PATH)


def init_db():
    conn = _get_conn()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL, domain TEXT NOT NULL,
        timestamp TEXT NOT NULL, results_json TEXT NOT NULL,
        ai_insights TEXT, user_id INTEGER )''')

    c.execute('''CREATE TABLE IF NOT EXISTS bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo_name TEXT NOT NULL, repo_url TEXT NOT NULL,
        stars INTEGER DEFAULT 0, language TEXT DEFAULT 'Unknown',
        description TEXT, added_at TEXT NOT NULL,
        user_id INTEGER )''')

    c.execute('''CREATE TABLE IF NOT EXISTS share_links (
        token TEXT PRIMARY KEY, search_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(search_id) REFERENCES searches(id) )''')

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL )''')

    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
        created_at TEXT NOT NULL )''')
    c.execute('''CREATE TABLE IF NOT EXISTS student_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    display_name TEXT NOT NULL DEFAULT '',
    bio TEXT DEFAULT '',
    skill_level TEXT DEFAULT 'beginner',
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) )''')

c.execute('''CREATE TABLE IF NOT EXISTS skill_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    topic TEXT NOT NULL,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    badge TEXT DEFAULT '',
    taken_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) )''')

c.execute('''CREATE TABLE IF NOT EXISTS student_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    tech_stack TEXT DEFAULT '',
    github_url TEXT DEFAULT '',
    live_url TEXT DEFAULT '',
    status TEXT DEFAULT 'in_progress',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) )''')

c.execute('''CREATE TABLE IF NOT EXISTS ai_chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    sent_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) )''')

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully.")


# ── Searches ────────────────────────────────────────────────
def save_search(query, domain, results, ai_insights, user_id=None):
    conn = _get_conn(); c = conn.cursor()
    c.execute('INSERT INTO searches (query,domain,timestamp,results_json,ai_insights,user_id) VALUES (?,?,?,?,?,?)',
        (query, domain, datetime.now().strftime('%Y-%m-%d %H:%M'),
         json.dumps(results), ai_insights, user_id))
    conn.commit()
    rid = c.lastrowid
    conn.close()
    return rid


def get_recent_searches(limit=10):
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT id,query,domain,timestamp FROM searches ORDER BY id DESC LIMIT ?', (limit,))
    rows = c.fetchall(); conn.close()
    return [{'id': r[0], 'query': r[1], 'domain': r[2], 'timestamp': r[3]} for r in rows]


def get_search_by_id(search_id):
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT id,query,domain,timestamp,results_json,ai_insights FROM searches WHERE id = ?', (search_id,))
    row = c.fetchone(); conn.close()
    if row:
        return {'id': row[0], 'query': row[1], 'domain': row[2],
                'timestamp': row[3], 'results': json.loads(row[4]),
                'ai_insights': row[5]}
    return None


# ── Bookmarks ──────────────────────────────────────────────
def add_bookmark(repo_name, repo_url, stars, language, description, user_id=None):
    conn = _get_conn(); c = conn.cursor()
    c.execute('INSERT INTO bookmarks (repo_name,repo_url,stars,language,description,added_at,user_id) VALUES (?,?,?,?,?,?,?)',
        (repo_name, repo_url, stars, language, description,
         datetime.now().strftime('%Y-%m-%d %H:%M'), user_id))
    conn.commit(); conn.close()


def get_bookmarks(user_id=None):
    conn = _get_conn(); c = conn.cursor()
    if user_id is not None:
        c.execute('SELECT id,repo_name,repo_url,stars,language,description,added_at FROM bookmarks WHERE user_id = ? ORDER BY id DESC', (user_id,))
    else:
        c.execute('SELECT id,repo_name,repo_url,stars,language,description,added_at FROM bookmarks ORDER BY id DESC')
    rows = c.fetchall(); conn.close()
    return [{'id': r[0], 'repo_name': r[1], 'repo_url': r[2], 'stars': r[3],
             'language': r[4], 'description': r[5], 'added_at': r[6]} for r in rows]


def delete_bookmark(bookmark_id):
    conn = _get_conn(); c = conn.cursor()
    c.execute('DELETE FROM bookmarks WHERE id = ?', (bookmark_id,))
    conn.commit(); conn.close()


# ── Share Links (NEW) ───────────────────────────────────────
def create_share_link(token, search_id):
    conn = _get_conn(); c = conn.cursor()
    c.execute('INSERT INTO share_links (token,search_id,created_at) VALUES (?,?,?)',
              (token, search_id, datetime.now().isoformat()))
    conn.commit(); conn.close()


def get_shared_search(token):
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT search_id FROM share_links WHERE token = ?', (token,))
    row = c.fetchone(); conn.close()
    if row:
        return get_search_by_id(row[0])
    return None


# ── Users (NEW) ────────────────────────────────────────────
def _hash_pw(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def save_user(email, password):
    try:
        conn = _get_conn(); c = conn.cursor()
        c.execute('INSERT INTO users (email,password_hash,created_at) VALUES (?,?,?)',
                  (email, _hash_pw(password), datetime.now().isoformat()))
        conn.commit()
        uid = c.lastrowid
        conn.close()
        return uid
    except sqlite3.IntegrityError:
        return None


def get_user(email, password):
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT id FROM users WHERE email=? AND password_hash=?',
              (email, _hash_pw(password)))
    row = c.fetchone(); conn.close()
    return row[0] if row else None


def create_user_session(user_id):
    token = secrets.token_urlsafe(24)
    conn = _get_conn(); c = conn.cursor()
    c.execute('INSERT INTO sessions (token,user_id,created_at) VALUES (?,?,?)',
              (token, user_id, datetime.now().isoformat()))
    conn.commit(); conn.close()
    return token
