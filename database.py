"""
database.py — SQLite Persistence Layer
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

    c.execute('''CREATE TABLE IF NOT EXISTS student_xp (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        streak INTEGER DEFAULT 0,
        last_login TEXT DEFAULT '',
        FOREIGN KEY(user_id) REFERENCES users(id) )''')

    c.execute('''CREATE TABLE IF NOT EXISTS study_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) )''')

    c.execute('''CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        done INTEGER DEFAULT 0,
        date TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) )''')

    c.execute('''CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        emoji TEXT DEFAULT '✅',
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) )''')

    c.execute('''CREATE TABLE IF NOT EXISTS habit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        habit_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) )''')

    c.execute('''CREATE TABLE IF NOT EXISTS daily_challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        topic TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        user_answer TEXT DEFAULT '',
        solved INTEGER DEFAULT 0,
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


# ── Share Links ─────────────────────────────────────────────
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


# ── Users ───────────────────────────────────────────────────
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


def get_user_by_id(user_id):
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT id, email, created_at FROM users WHERE id=?', (user_id,))
    row = c.fetchone(); conn.close()
    if row:
        return {'id': row[0], 'email': row[1], 'created_at': row[2]}
    return None


def create_user_session(user_id):
    token = secrets.token_urlsafe(24)
    conn = _get_conn(); c = conn.cursor()
    c.execute('INSERT INTO sessions (token,user_id,created_at) VALUES (?,?,?)',
              (token, user_id, datetime.now().isoformat()))
    conn.commit(); conn.close()
    return token


def get_user_from_session(token):
    if not token:
        return None
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT user_id FROM sessions WHERE token=?', (token,))
    row = c.fetchone(); conn.close()
    return row[0] if row else None


def delete_session(token):
    conn = _get_conn(); c = conn.cursor()
    c.execute('DELETE FROM sessions WHERE token=?', (token,))
    conn.commit(); conn.close()


# ── Student Profile ─────────────────────────────────────────
def get_or_create_profile(user_id, email):
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT id, display_name, bio, skill_level FROM student_profiles WHERE user_id=?', (user_id,))
    row = c.fetchone()
    if not row:
        name = email.split('@')[0]
        c.execute(
            'INSERT INTO student_profiles (user_id, display_name, bio, skill_level, created_at) VALUES (?,?,?,?,?)',
            (user_id, name, '', 'beginner', datetime.now().isoformat())
        )
        conn.commit()
        profile = {'display_name': name, 'bio': '', 'skill_level': 'beginner'}
    else:
        profile = {'display_name': row[1], 'bio': row[2], 'skill_level': row[3]}
    conn.close()
    return profile


def update_profile(user_id, display_name, bio, skill_level):
    conn = _get_conn(); c = conn.cursor()
    c.execute(
        'UPDATE student_profiles SET display_name=?, bio=?, skill_level=? WHERE user_id=?',
        (display_name, bio, skill_level, user_id)
    )
    conn.commit(); conn.close()


# ── Skill Tests ─────────────────────────────────────────────
def save_skill_test(user_id, topic, score, total):
    pct = (score / total) * 100
    badge = 'gold' if pct >= 90 else ('silver' if pct >= 70 else ('bronze' if pct >= 50 else ''))
    conn = _get_conn(); c = conn.cursor()
    c.execute(
        'INSERT INTO skill_tests (user_id, topic, score, total, badge, taken_at) VALUES (?,?,?,?,?,?)',
        (user_id, topic, score, total, badge, datetime.now().isoformat())
    )
    conn.commit(); conn.close()
    return badge


def get_skill_tests(user_id):
    conn = _get_conn(); c = conn.cursor()
    c.execute(
        'SELECT id, topic, score, total, badge, taken_at FROM skill_tests WHERE user_id=? ORDER BY taken_at DESC',
        (user_id,)
    )
    rows = c.fetchall(); conn.close()
    return [
        {'id': r[0], 'topic': r[1], 'score': r[2], 'total': r[3],
         'badge': r[4], 'pct': round((r[2]/r[3])*100), 'taken_at': r[5]}
        for r in rows
    ]


# ── Projects ────────────────────────────────────────────────
def add_project(user_id, title, description, tech_stack, github_url, live_url, status):
    now = datetime.now().isoformat()
    conn = _get_conn(); c = conn.cursor()
    c.execute(
        '''INSERT INTO student_projects
           (user_id, title, description, tech_stack, github_url, live_url, status, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?)''',
        (user_id, title, description, tech_stack, github_url, live_url, status, now, now)
    )
    conn.commit()
    pid = c.lastrowid; conn.close()
    return pid


def get_projects(user_id):
    conn = _get_conn(); c = conn.cursor()
    c.execute(
        '''SELECT id, title, description, tech_stack, github_url, live_url, status, created_at, updated_at
           FROM student_projects WHERE user_id=? ORDER BY updated_at DESC''',
        (user_id,)
    )
    rows = c.fetchall(); conn.close()
    return [
        {'id': r[0], 'title': r[1], 'description': r[2], 'tech_stack': r[3],
         'github_url': r[4], 'live_url': r[5], 'status': r[6],
         'created_at': r[7], 'updated_at': r[8]}
        for r in rows
    ]


def update_project(project_id, user_id, title, description, tech_stack, github_url, live_url, status):
    conn = _get_conn(); c = conn.cursor()
    c.execute(
        '''UPDATE student_projects SET title=?, description=?, tech_stack=?, github_url=?,
           live_url=?, status=?, updated_at=? WHERE id=? AND user_id=?''',
        (title, description, tech_stack, github_url, live_url, status,
         datetime.now().isoformat(), project_id, user_id)
    )
    conn.commit(); conn.close()


def delete_project(project_id, user_id):
    conn = _get_conn(); c = conn.cursor()
    c.execute('DELETE FROM student_projects WHERE id=? AND user_id=?', (project_id, user_id))
    conn.commit(); conn.close()


# ── AI Chat ─────────────────────────────────────────────────
def save_chat_message(user_id, role, message):
    conn = _get_conn(); c = conn.cursor()
    c.execute(
        'INSERT INTO ai_chats (user_id, role, message, sent_at) VALUES (?,?,?,?)',
        (user_id, role, message, datetime.now().isoformat())
    )
    conn.commit(); conn.close()


def get_chat_history(user_id, limit=30):
    conn = _get_conn(); c = conn.cursor()
    c.execute(
        'SELECT role, message, sent_at FROM ai_chats WHERE user_id=? ORDER BY sent_at DESC LIMIT ?',
        (user_id, limit)
    )
    rows = c.fetchall(); conn.close()
    return [{'role': r[0], 'message': r[1], 'sent_at': r[2]} for r in reversed(rows)]


def clear_chat_history(user_id):
    conn = _get_conn(); c = conn.cursor()
    c.execute('DELETE FROM ai_chats WHERE user_id=?', (user_id,))
    conn.commit(); conn.close()


# ── Platform Stats ───────────────────────────────────────────
def get_platform_stats():
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    total_users = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM searches')
    total_searches = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM student_projects')
    total_projects = c.fetchone()[0]
    conn.close()
    return {
        'total_users': total_users,
        'total_searches': total_searches,
        'total_projects': total_projects
    }


# ── XP & Level System ────────────────────────────────────────
XP_REWARDS = {
    'login':    5,
    'search':   10,
    'test':     20,
    'gold':     50,
    'silver':   30,
    'bronze':   15,
    'project':  25,
    'chat':     5,
}

LEVELS = [
    (0,    'Beginner',     '🌱'),
    (100,  'Explorer',     '🔍'),
    (250,  'Developer',    '💻'),
    (500,  'Coder',        '⚡'),
    (1000, 'Senior Dev',   '🚀'),
    (2000, 'Architect',    '🏗️'),
    (5000, 'Legend',       '👑'),
]

def get_level_info(xp):
    level_name, level_icon = 'Beginner', '🌱'
    level_num = 1
    for i, (req, name, icon) in enumerate(LEVELS):
        if xp >= req:
            level_name = name
            level_icon = icon
            level_num  = i + 1
    next_xp = LEVELS[level_num][0] if level_num < len(LEVELS) else None
    return {'name': level_name, 'icon': level_icon, 'num': level_num, 'next_xp': next_xp}


def get_or_create_xp(user_id):
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT xp, level, streak, last_login FROM student_xp WHERE user_id=?', (user_id,))
    row = c.fetchone()
    if not row:
        c.execute('INSERT INTO student_xp (user_id, xp, level, streak, last_login) VALUES (?,0,1,0,?)',
                  (user_id, datetime.now().date().isoformat()))
        conn.commit()
        conn.close()
        return {'xp': 0, 'level': 1, 'streak': 0, 'last_login': datetime.now().date().isoformat()}
    conn.close()
    return {'xp': row[0], 'level': row[1], 'streak': row[2], 'last_login': row[3]}


def add_xp(user_id, action):
    points = XP_REWARDS.get(action, 0)
    if not points:
        return 0
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT xp FROM student_xp WHERE user_id=?', (user_id,))
    row = c.fetchone()
    if not row:
        c.execute('INSERT INTO student_xp (user_id, xp, level, streak, last_login) VALUES (?,?,1,0,?)',
                  (user_id, points, datetime.now().date().isoformat()))
    else:
        new_xp = row[0] + points
        level_info = get_level_info(new_xp)
        c.execute('UPDATE student_xp SET xp=?, level=? WHERE user_id=?',
                  (new_xp, level_info['num'], user_id))
    conn.commit(); conn.close()
    return points


def update_streak(user_id):
    """Call on login — updates streak and awards login XP."""
    conn = _get_conn(); c = conn.cursor()
    today = datetime.now().date().isoformat()
    c.execute('SELECT xp, streak, last_login FROM student_xp WHERE user_id=?', (user_id,))
    row = c.fetchone()
    if not row:
        c.execute('INSERT INTO student_xp (user_id, xp, level, streak, last_login) VALUES (?,5,1,1,?)',
                  (user_id, today))
        conn.commit(); conn.close()
        return {'streak': 1, 'xp_gained': 5}

    xp, streak, last_login = row
    yesterday = (datetime.now().date() - __import__('datetime').timedelta(days=1)).isoformat()

    if last_login == today:
        conn.close()
        return {'streak': streak, 'xp_gained': 0}
    elif last_login == yesterday:
        streak += 1
    else:
        streak = 1

    xp += XP_REWARDS['login']
    level_info = get_level_info(xp)
    c.execute('UPDATE student_xp SET xp=?, level=?, streak=?, last_login=? WHERE user_id=?',
              (xp, level_info['num'], streak, today, user_id))
    conn.commit(); conn.close()
    return {'streak': streak, 'xp_gained': XP_REWARDS['login']}


def get_xp_data(user_id):
    data = get_or_create_xp(user_id)
    level_info = get_level_info(data['xp'])
    pct = 0
    if level_info['next_xp']:
        prev_xp = LEVELS[level_info['num'] - 1][0]
        pct = round(((data['xp'] - prev_xp) / (level_info['next_xp'] - prev_xp)) * 100)
    return {
        'xp': data['xp'],
        'streak': data['streak'],
        'level_name': level_info['name'],
        'level_icon': level_info['icon'],
        'level_num':  level_info['num'],
        'next_xp':    level_info['next_xp'],
        'level_pct':  min(pct, 100),
    }


# ── Todo List ────────────────────────────────────────────────
def get_todos(user_id, date):
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT id, text, done FROM todos WHERE user_id=? AND date=? ORDER BY id', (user_id, date))
    rows = c.fetchall(); conn.close()
    return [{'id': r[0], 'text': r[1], 'done': bool(r[2])} for r in rows]

def add_todo(user_id, text, date):
    conn = _get_conn(); c = conn.cursor()
    c.execute('INSERT INTO todos (user_id, text, done, date) VALUES (?,?,0,?)', (user_id, text, date))
    conn.commit(); tid = c.lastrowid; conn.close()
    return tid

def toggle_todo(todo_id, user_id):
    conn = _get_conn(); c = conn.cursor()
    c.execute('UPDATE todos SET done = 1 - done WHERE id=? AND user_id=?', (todo_id, user_id))
    conn.commit(); conn.close()

def delete_todo(todo_id, user_id):
    conn = _get_conn(); c = conn.cursor()
    c.execute('DELETE FROM todos WHERE id=? AND user_id=?', (todo_id, user_id))
    conn.commit(); conn.close()


# ── Habit Tracker ────────────────────────────────────────────
def get_habits(user_id):
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT id, name, emoji, created_at FROM habits WHERE user_id=? ORDER BY id', (user_id,))
    rows = c.fetchall(); conn.close()
    return [{'id': r[0], 'name': r[1], 'emoji': r[2], 'created_at': r[3]} for r in rows]

def add_habit(user_id, name, emoji='✅'):
    conn = _get_conn(); c = conn.cursor()
    c.execute('INSERT INTO habits (user_id, name, emoji, created_at) VALUES (?,?,?,?)',
              (user_id, name, emoji, datetime.now().isoformat()))
    conn.commit(); hid = c.lastrowid; conn.close()
    return hid

def delete_habit(habit_id, user_id):
    conn = _get_conn(); c = conn.cursor()
    c.execute('DELETE FROM habits WHERE id=? AND user_id=?', (habit_id, user_id))
    c.execute('DELETE FROM habit_logs WHERE habit_id=? AND user_id=?', (habit_id, user_id))
    conn.commit(); conn.close()

def toggle_habit_log(user_id, habit_id, date):
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT id FROM habit_logs WHERE user_id=? AND habit_id=? AND date=?', (user_id, habit_id, date))
    row = c.fetchone()
    if row:
        c.execute('DELETE FROM habit_logs WHERE id=?', (row[0],))
        done = False
    else:
        c.execute('INSERT INTO habit_logs (user_id, habit_id, date) VALUES (?,?,?)', (user_id, habit_id, date))
        done = True
    conn.commit(); conn.close()
    return done

def get_habit_logs(user_id, date):
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT habit_id FROM habit_logs WHERE user_id=? AND date=?', (user_id, date))
    rows = c.fetchall(); conn.close()
    return [r[0] for r in rows]


# ── Daily Challenge ──────────────────────────────────────────
def get_or_create_challenge(user_id, date, topic, question, answer):
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT id, question, answer, user_answer, solved FROM daily_challenges WHERE user_id=? AND date=?',
              (user_id, date))
    row = c.fetchone()
    if not row:
        c.execute('INSERT INTO daily_challenges (user_id, date, topic, question, answer) VALUES (?,?,?,?,?)',
                  (user_id, date, topic, question, answer))
        conn.commit()
        conn.close()
        return {'question': question, 'answer': answer, 'user_answer': '', 'solved': False, 'new': True}
    conn.close()
    return {'question': row[1], 'answer': row[2], 'user_answer': row[3], 'solved': bool(row[4]), 'new': False}

def submit_challenge(user_id, date, user_answer):
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT answer FROM daily_challenges WHERE user_id=? AND date=?', (user_id, date))
    row = c.fetchone()
    if not row:
        conn.close()
        return False
    correct = user_answer.strip().lower() in row[0].lower()
    c.execute('UPDATE daily_challenges SET user_answer=?, solved=? WHERE user_id=? AND date=?',
              (user_answer, 1 if correct else 0, user_id, date))
    conn.commit(); conn.close()
    return correct
