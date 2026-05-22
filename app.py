"""
StackSage v2.0 - GitHub Trend Intelligence & AI-Powered Tech Analysis
Main Flask Application — Production Ready
"""

from flask import (Flask, render_template, request, jsonify, redirect,
                   url_for, flash, send_file, abort, make_response)
from github_api import search_repositories, get_trending_languages, get_repo_stats_summary
from ai_analyzer import (analyze_repos, generate_learning_path,
                         compare_technologies, chat_about_results,
                         recommend_repos, compare_domains_ai)
from visualizer import (create_stars_chart, create_language_chart,
                        create_activity_scatter, create_wordcloud,
                        create_timeline_chart)
from database import (init_db, save_search, get_recent_searches, get_search_by_id,
                      add_bookmark, get_bookmarks, delete_bookmark,
                      create_share_link, get_shared_search,
                      save_user, get_user, create_user_session,
                      get_user_from_session, get_user_by_id, delete_session,
                      get_or_create_profile, update_profile,
                      save_skill_test, get_skill_tests,
                      add_project, get_projects, update_project, delete_project,
                      save_chat_message, get_chat_history, clear_chat_history,
                      get_platform_stats)
import json
import io
import os
import secrets
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "stacksage_secret_2025_change_me")


def get_current_user():
    token = request.cookies.get('session_token')
    uid = get_user_from_session(token)
    if uid:
        return get_user_by_id(uid)
    return None


@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())


# ════════════════════════════════════════════════════════════════
# CORE ROUTES
# ════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    recent_searches = get_recent_searches(5)
    bookmarks_count = len(get_bookmarks())
    return render_template('index.html',
                           recent_searches=recent_searches,
                           bookmarks_count=bookmarks_count)


@app.route('/analyze', methods=['POST'])
def analyze():
    query = request.form.get('query', '').strip()
    domain = request.form.get('domain', query)

    if not query:
        flash('Please enter a search query.', 'error')
        return redirect(url_for('index'))

    repos_data = search_repositories(query, per_page=12)

    if 'error' in repos_data and not repos_data.get('repos'):
        flash(f"GitHub API error: {repos_data['error']}", 'error')
        return redirect(url_for('index'))

    repos = repos_data['repos']
    if not repos:
        flash(f'No repositories found for "{query}". Try a different keyword.', 'error')
        return redirect(url_for('index'))

    languages = get_trending_languages(repos)
    all_topics = {}
    for r in repos:
        for t in r['topics']:
            all_topics[t] = all_topics.get(t, 0) + 1

    stats = {
        'total_found': repos_data['total_count'],
        'analyzed': len(repos),
        'total_stars': sum(r['stars'] for r in repos),
        'total_forks': sum(r['forks'] for r in repos),
        'avg_stars': sum(r['stars'] for r in repos) // max(len(repos), 1),
        'top_repo': max(repos, key=lambda r: r['stars'])['name'].split('/')[-1],
        'languages': languages,
        'top_topics': dict(sorted(all_topics.items(), key=lambda x: x[1], reverse=True)[:15])
    }

    ai_insights = analyze_repos(query, repos_data)
    learning_path = generate_learning_path(domain, languages, all_topics)
    ai_recommendations = recommend_repos(query, repos)

    tech_comparison = None
    if len(languages) >= 2:
        tech_comparison = compare_technologies(list(languages.keys())[:4], domain)

    charts = {
        'stars': create_stars_chart(repos),
        'languages': create_language_chart(languages),
        'activity': create_activity_scatter(repos),
        'wordcloud': create_wordcloud(all_topics, query),
        'timeline': create_timeline_chart(repos)
    }

    search_id = save_search(query, domain, repos, ai_insights)

    return render_template('results.html',
        query=query, domain=domain, repos=repos, stats=stats,
        ai_insights=ai_insights, learning_path=learning_path,
        ai_recommendations=ai_recommendations,
        tech_comparison=tech_comparison, charts=charts,
        search_id=search_id
    )


@app.route('/history')
def history():
    searches = get_recent_searches(20)
    return render_template('history.html', searches=searches)


@app.route('/bookmarks')
def bookmarks():
    books = get_bookmarks()
    return render_template('bookmarks.html', bookmarks=books)


# ════════════════════════════════════════════════════════════════
# DOMAIN COMPARISON
# ════════════════════════════════════════════════════════════════

@app.route('/compare')
def compare_page():
    return render_template('compare.html')


@app.route('/compare/run', methods=['POST'])
def compare_run():
    domain_a = request.form.get('domain_a', '').strip()
    domain_b = request.form.get('domain_b', '').strip()

    if not domain_a or not domain_b:
        flash('Please enter both domains.', 'error')
        return redirect(url_for('compare_page'))

    data_a = search_repositories(domain_a, per_page=10)
    data_b = search_repositories(domain_b, per_page=10)

    if not data_a.get('repos') or not data_b.get('repos'):
        flash('One of the domains returned no results.', 'error')
        return redirect(url_for('compare_page'))

    def _build(d):
        repos = d['repos']
        langs = get_trending_languages(repos)
        return {
            'total_found': d['total_count'],
            'total_stars': sum(r['stars'] for r in repos),
            'total_forks': sum(r['forks'] for r in repos),
            'avg_stars': sum(r['stars'] for r in repos) // max(len(repos), 1),
            'languages': langs,
            'top_repos': sorted(repos, key=lambda r: r['stars'], reverse=True)[:5],
            'repos': repos,
        }

    side_a = _build(data_a)
    side_b = _build(data_b)
    ai_verdict = compare_domains_ai(domain_a, domain_b, side_a, side_b)

    return render_template('compare_results.html',
                           domain_a=domain_a, domain_b=domain_b,
                           side_a=side_a, side_b=side_b,
                           ai_verdict=ai_verdict)


# ════════════════════════════════════════════════════════════════
# AI CHAT
# ════════════════════════════════════════════════════════════════

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json() or {}
    user_msg = data.get('message', '').strip()
    search_id = data.get('search_id')
    history_msgs = data.get('history', [])

    if not user_msg:
        return jsonify({'error': 'Empty message.'}), 400

    context = ""
    if search_id:
        s = get_search_by_id(int(search_id))
        if s:
            context = (f"Search query: {s['query']}\n"
                       f"Domain: {s['domain']}\n"
                       f"Top repos: {[r['name'] for r in s['results'][:5]]}\n"
                       f"AI insights summary: {s['ai_insights'][:600]}\n")

    reply = chat_about_results(user_msg, context, history_msgs)
    return jsonify({'reply': reply})


# ════════════════════════════════════════════════════════════════
# BOOKMARK API
# ════════════════════════════════════════════════════════════════

@app.route('/api/bookmark', methods=['POST'])
def bookmark():
    data = request.get_json()
    add_bookmark(
        data.get('repo_name', ''), data.get('repo_url', ''),
        data.get('stars', 0), data.get('language', 'Unknown'),
        data.get('description', '')
    )
    return jsonify({'success': True, 'message': 'Bookmarked successfully!'})


@app.route('/api/bookmark/<int:bid>', methods=['DELETE'])
def remove_bookmark(bid):
    delete_bookmark(bid)
    return jsonify({'success': True})


@app.route('/api/quick-compare', methods=['POST'])
def quick_compare():
    data = request.get_json()
    techs = data.get('technologies', [])
    domain = data.get('domain', 'general')
    if len(techs) < 2:
        return jsonify({'error': 'Please provide at least 2 technologies.'})
    result = compare_technologies(techs, domain)
    return jsonify({'comparison': result})


# ════════════════════════════════════════════════════════════════
# SHARE LINK
# ════════════════════════════════════════════════════════════════

@app.route('/api/share/<int:search_id>', methods=['POST'])
def make_share_link(search_id):
    token = secrets.token_urlsafe(8)
    create_share_link(token, search_id)
    return jsonify({
        'success': True,
        'url': request.host_url.rstrip('/') + url_for('view_shared', token=token)
    })


@app.route('/shared/<token>')
def view_shared(token):
    s = get_shared_search(token)
    if not s:
        flash('This shared link is invalid or expired.', 'error')
        return redirect(url_for('index'))

    repos = s['results']
    languages = get_trending_languages(repos)
    all_topics = {}
    for r in repos:
        for t in r.get('topics', []):
            all_topics[t] = all_topics.get(t, 0) + 1

    stats = {
        'total_found': len(repos),
        'analyzed': len(repos),
        'total_stars': sum(r['stars'] for r in repos),
        'total_forks': sum(r['forks'] for r in repos),
        'avg_stars': sum(r['stars'] for r in repos) // max(len(repos), 1),
        'languages': languages,
    }
    charts = {
        'stars': create_stars_chart(repos),
        'languages': create_language_chart(languages),
        'wordcloud': create_wordcloud(all_topics, s['query']),
    }
    return render_template('shared.html',
                           query=s['query'], stats=stats,
                           repos=repos, charts=charts,
                           ai_insights=s['ai_insights'])


# ════════════════════════════════════════════════════════════════
# PDF EXPORT
# ════════════════════════════════════════════════════════════════

@app.route('/export/pdf/<int:search_id>')
def export_pdf(search_id):
    s = get_search_by_id(search_id)
    if not s:
        abort(404)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, PageBreak)
    except ImportError:
        return ("Install reportlab to enable PDF export: pip install reportlab", 500)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=0.6*inch, bottomMargin=0.6*inch,
                            leftMargin=0.6*inch, rightMargin=0.6*inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('TitleX', parent=styles['Title'],
                                 fontSize=22, textColor=colors.HexColor('#58a6ff'),
                                 spaceAfter=12)
    h2_style = ParagraphStyle('H2X', parent=styles['Heading2'],
                              fontSize=14, textColor=colors.HexColor('#1f6feb'),
                              spaceBefore=14, spaceAfter=6)
    body = styles['BodyText']

    elements = [
        Paragraph(f"StackSage Report: {s['query']}", title_style),
        Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}", body),
        Spacer(1, 14),
        Paragraph("Summary", h2_style),
    ]

    repos = s['results']
    total_stars = sum(r['stars'] for r in repos)
    total_forks = sum(r['forks'] for r in repos)

    summary_data = [
        ['Metric', 'Value'],
        ['Repositories analyzed', str(len(repos))],
        ['Total stars', f"{total_stars:,}"],
        ['Total forks', f"{total_forks:,}"],
        ['Top repository', repos[0]['name'] if repos else '-'],
    ]
    t = Table(summary_data, colWidths=[2.5*inch, 3.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1f6feb')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t)

    elements.append(Paragraph("AI Insights", h2_style))
    insights_clean = (s['ai_insights'] or 'No insights available.').replace('\n', '<br/>')
    elements.append(Paragraph(insights_clean[:4500], body))

    elements.append(PageBreak())
    elements.append(Paragraph("Top Repositories", h2_style))

    repo_rows = [['Repository', 'Stars', 'Forks', 'Language']]
    for r in repos[:15]:
        repo_rows.append([
            r['name'][:40],
            f"{r['stars']:,}",
            f"{r['forks']:,}",
            r.get('language', '-') or '-',
        ])
    rt = Table(repo_rows, colWidths=[3*inch, 1*inch, 1*inch, 1.3*inch])
    rt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#58a6ff')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 4),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(rt)

    doc.build(elements)
    buf.seek(0)
    return send_file(buf, mimetype='application/pdf',
                     download_name=f"stacksage_{s['query'].replace(' ', '_')}.pdf",
                     as_attachment=True)


# ════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ════════════════════════════════════════════════════════════════

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')

        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('signup'))
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('signup'))
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('signup'))

        uid = save_user(email, password)
        if uid is None:
            flash('An account with that email already exists.', 'error')
            return redirect(url_for('signup'))

        token = create_user_session(uid)
        resp  = make_response(redirect(url_for('student_zone')))
        resp.set_cookie('session_token', token, max_age=60*60*24*30, httponly=True, samesite='Lax')
        flash('Welcome to StackSage! Your Student Zone is ready.', 'success')
        return resp

    return render_template('auth.html', mode='signup', current_user=None)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        uid = get_user(email, password)
        if uid is None:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

        token = create_user_session(uid)
        resp  = make_response(redirect(url_for('student_zone')))
        resp.set_cookie('session_token', token, max_age=60*60*24*30, httponly=True, samesite='Lax')
        flash('Welcome back!', 'success')
        return resp

    return render_template('auth.html', mode='login', current_user=None)


@app.route('/logout')
def logout():
    token = request.cookies.get('session_token')
    if token:
        delete_session(token)
    resp = make_response(redirect(url_for('index')))
    resp.delete_cookie('session_token')
    flash('You have been logged out.', 'success')
    return resp


# ════════════════════════════════════════════════════════════════
# STUDENT ZONE
# ════════════════════════════════════════════════════════════════

@app.route('/student-zone')
def student_zone():
    user = get_current_user()
    if not user:
        flash('Please log in to access your Student Zone.', 'error')
        return redirect(url_for('login'))

    profile  = get_or_create_profile(user['id'], user['email'])
    tests    = get_skill_tests(user['id'])
    projects = get_projects(user['id'])
    history  = get_chat_history(user['id'], limit=20)
    stats    = get_platform_stats()

    badge_rank = {'gold': 3, 'silver': 2, 'bronze': 1, '': 0}
    best_badge = max((t['badge'] for t in tests), key=lambda b: badge_rank.get(b, 0), default='')

    return render_template('student_zone.html',
                           current_user=user,
                           profile=profile,
                           tests=tests,
                           projects=projects,
                           chat_history=history,
                           best_badge=best_badge,
                           stats=stats)


@app.route('/student-zone/profile', methods=['POST'])
def update_student_profile():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401

    data         = request.get_json()
    display_name = data.get('display_name', '').strip()[:60]
    bio          = data.get('bio', '').strip()[:300]
    skill_level  = data.get('skill_level', 'beginner')

    if skill_level not in ('beginner', 'intermediate', 'advanced'):
        skill_level = 'beginner'

    update_profile(user['id'], display_name, bio, skill_level)
    return jsonify({'success': True})


@app.route('/api/student/generate-test', methods=['POST'])
def generate_skill_test():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401

    data  = request.get_json()
    topic = data.get('topic', 'Python').strip()[:50]
    level = data.get('level', 'beginner')

    prompt = f"""Generate a skill test for a {level} developer on the topic: {topic}.
Return ONLY a JSON object (no markdown, no extra text) in this exact format:
{{
  "topic": "{topic}",
  "questions": [
    {{
      "q": "Question text here?",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "answer": 0
    }}
  ]
}}
- Generate exactly 5 questions.
- "answer" is the 0-based index of the correct option.
- Questions should match {level} difficulty.
- Keep each question short and clear."""

    try:
        import google.generativeai as genai
        from config import GEMINI_API_KEY
        genai.configure(api_key=GEMINI_API_KEY)
        model    = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        text     = response.text.strip()
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        quiz = json.loads(text)
        return jsonify({'success': True, 'quiz': quiz})
    except Exception as e:
        return jsonify({'error': f'Could not generate quiz: {str(e)}'}), 500


@app.route('/api/student/submit-test', methods=['POST'])
def submit_skill_test():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401

    data      = request.get_json()
    topic     = data.get('topic', 'Unknown')
    answers   = data.get('answers', [])
    questions = data.get('questions', [])

    score = sum(
        1 for i, q in enumerate(questions)
        if i < len(answers) and answers[i] == q.get('answer')
    )
    total = len(questions)
    badge = save_skill_test(user['id'], topic, score, total)
    pct   = round((score / total) * 100) if total else 0

    return jsonify({'success': True, 'score': score, 'total': total,
                    'pct': pct, 'badge': badge})


@app.route('/api/student/projects', methods=['POST'])
def create_project():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json()
    pid  = add_project(
        user['id'],
        data.get('title', 'Untitled')[:100],
        data.get('description', '')[:500],
        data.get('tech_stack', '')[:200],
        data.get('github_url', '')[:300],
        data.get('live_url', '')[:300],
        data.get('status', 'in_progress')
    )
    return jsonify({'success': True, 'id': pid})


@app.route('/api/student/projects/<int:pid>', methods=['PUT'])
def edit_project(pid):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json()
    update_project(
        pid, user['id'],
        data.get('title', '')[:100],
        data.get('description', '')[:500],
        data.get('tech_stack', '')[:200],
        data.get('github_url', '')[:300],
        data.get('live_url', '')[:300],
        data.get('status', 'in_progress')
    )
    return jsonify({'success': True})


@app.route('/api/student/projects/<int:pid>', methods=['DELETE'])
def remove_project(pid):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401
    delete_project(pid, user['id'])
    return jsonify({'success': True})


@app.route('/api/student/chat', methods=['POST'])
def student_ai_chat():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401

    data    = request.get_json()
    message = data.get('message', '').strip()[:1000]
    if not message:
        return jsonify({'error': 'Empty message'}), 400

    history  = get_chat_history(user['id'], limit=10)
    profile  = get_or_create_profile(user['id'], user['email'])

    context = "\n".join(
        f"{'Student' if m['role']=='user' else 'AI'}: {m['message']}"
        for m in history[-6:]
    )

    prompt = f"""You are a personal AI tutor inside StackSage, helping a {profile['skill_level']}-level developer.
The student's name is {profile['display_name']}.

Recent conversation:
{context}

Student: {message}

Respond helpfully and concisely. Focus on practical advice, code examples when useful.
Keep your response under 300 words."""

    try:
        import google.generativeai as genai
        from config import GEMINI_API_KEY
        genai.configure(api_key=GEMINI_API_KEY)
        model    = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        reply    = response.text.strip()
    except Exception as e:
        reply = f"Sorry, I couldn't connect to the AI right now. ({e})"

    save_chat_message(user['id'], 'user', message)
    save_chat_message(user['id'], 'ai',   reply)

    return jsonify({'success': True, 'reply': reply})


@app.route('/api/student/chat/clear', methods=['POST'])
def clear_student_chat():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401
    clear_chat_history(user['id'])
    return jsonify({'success': True})


@app.route('/api/stats')
def public_stats():
    return jsonify(get_platform_stats())


# ════════════════════════════════════════════════════════════════
# HEALTH + ERROR HANDLERS
# ════════════════════════════════════════════════════════════════

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'StackSage', 'version': '2.0'})


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


# ════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("  StackSage v2.0 — GitHub Trend Intelligence")
    print("  http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
else:
    init_db()
