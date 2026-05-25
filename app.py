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
                      get_platform_stats, add_xp, get_xp_data, update_streak)
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
        update_streak(uid)
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

    xp_data = get_xp_data(user['id'])
    return render_template('student_zone.html',
                           current_user=user,
                           profile=profile,
                           tests=tests,
                           projects=projects,
                           chat_history=history,
                           best_badge=best_badge,
                           stats=stats,
                           xp_data=xp_data)


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

    add_xp(user['id'], 'test')
    if badge:
        add_xp(user['id'], badge)
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
    add_xp(user['id'], 'project')
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
# AI CODE REVIEWER
# ════════════════════════════════════════════════════════════════

@app.route('/code-reviewer')
def code_reviewer():
    return render_template('code_reviewer.html')


@app.route('/api/review-code', methods=['POST'])
def review_code():
    data     = request.get_json()
    code     = data.get('code', '').strip()[:3000]
    language = data.get('language', 'auto').strip()
    focus    = data.get('focus', 'general').strip()
    if not code:
        return jsonify({'error': 'No code provided'}), 400

    prompt = (
        f"You are an expert code reviewer. Review this {language} code:\n\n"
        f"```{language}\n{code}\n```\n\n"
        f"Focus area: {focus}\n\n"
        "Provide a structured review:\n\n"
        "## What's Good\nList 2-3 positive aspects.\n\n"
        "## Bugs & Issues\nList any bugs or errors.\n\n"
        "## Performance\nAny performance issues.\n\n"
        "## Security\nAny security vulnerabilities.\n\n"
        "## Suggestions\n3-5 specific improvements with code examples.\n\n"
        "## Overall Score\nRate X/10 with one-line summary.\n\n"
        "Be specific and constructive."
    )
    try:
        from config import get_ai_response
        review = get_ai_response(prompt)
        user = get_current_user()
        if user:
            add_xp(user['id'], 'chat')
        return jsonify({'success': True, 'review': review})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ════════════════════════════════════════════════════════════════
# GITHUB USER ANALYZER
# ════════════════════════════════════════════════════════════════

@app.route('/github-analyzer')
def github_analyzer():
    return render_template('github_analyzer.html')


@app.route('/api/analyze-github-user', methods=['POST'])
def analyze_github_user():
    data     = request.get_json()
    username = data.get('username', '').strip()
    if not username:
        return jsonify({'error': 'Username required'}), 400

    import requests as req_lib
    from config import GITHUB_TOKEN
    headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}

    try:
        user_r = req_lib.get(f'https://api.github.com/users/{username}', headers=headers, timeout=8)
        if user_r.status_code == 404:
            return jsonify({'error': f'User "{username}" not found'}), 404
        user_data = user_r.json()

        repos_r = req_lib.get(
            f'https://api.github.com/users/{username}/repos?sort=stars&per_page=20',
            headers=headers, timeout=8
        )
        repos = repos_r.json() if repos_r.status_code == 200 else []

        languages = {}
        total_stars = 0
        total_forks = 0
        for repo in repos:
            if not repo.get('fork'):
                lang = repo.get('language')
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1
                total_stars += repo.get('stargazers_count', 0)
                total_forks += repo.get('forks_count', 0)

        top_repos = sorted(
            [r for r in repos if not r.get('fork')],
            key=lambda x: x.get('stargazers_count', 0), reverse=True
        )[:5]

        repo_summary = ', '.join([r['name'] + ' (' + str(r.get('stargazers_count',0)) + ' stars)' for r in top_repos])
        prompt = (
            f"Analyze this GitHub developer: {username}\n"
            f"Name: {user_data.get('name', username)}\n"
            f"Bio: {user_data.get('bio', 'No bio')}\n"
            f"Followers: {user_data.get('followers', 0)}, Repos: {user_data.get('public_repos', 0)}\n"
            f"Stars: {total_stars}, Languages: {list(languages.keys())[:5]}\n"
            f"Top repos: {repo_summary}\n\n"
            "Write a brief analysis (max 200 words):\n"
            "## Developer Summary\n## Strengths\n## Tech Focus\n## One-line verdict"
        )
        from config import get_ai_response
        analysis = get_ai_response(prompt)

        return jsonify({
            'success': True,
            'profile': {
                'name':        user_data.get('name', username),
                'bio':         user_data.get('bio', ''),
                'avatar':      user_data.get('avatar_url', ''),
                'followers':   user_data.get('followers', 0),
                'following':   user_data.get('following', 0),
                'repos':       user_data.get('public_repos', 0),
                'location':    user_data.get('location', ''),
                'blog':        user_data.get('blog', ''),
                'joined':      user_data.get('created_at', '')[:10],
                'total_stars': total_stars,
                'total_forks': total_forks,
                'languages':   languages,
                'top_repos':   [{'name': r['name'], 'stars': r.get('stargazers_count',0),
                                  'url': r['html_url'], 'desc': r.get('description',''),
                                  'language': r.get('language','')} for r in top_repos],
                'analysis':    analysis,
                'github_url':  f'https://github.com/{username}'
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ════════════════════════════════════════════════════════════════
# XP API
# ════════════════════════════════════════════════════════════════

@app.route('/api/student/xp')
def get_student_xp():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify(get_xp_data(user['id']))


# ════════════════════════════════════════════════════════════════
# HEALTH + ERROR HANDLERS
# ════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════
# README GENERATOR
# ════════════════════════════════════════════════════════════════

@app.route('/readme-generator')
def readme_generator():
    return render_template('readme_generator.html')


@app.route('/api/generate-readme', methods=['POST'])
def generate_readme():
    data = request.get_json()
    project_name  = data.get('project_name', '').strip()[:100]
    description   = data.get('description', '').strip()[:500]
    tech_stack    = data.get('tech_stack', '').strip()[:200]
    features      = data.get('features', '').strip()[:500]
    github_url    = data.get('github_url', '').strip()[:200]
    author        = data.get('author', '').strip()[:60]

    if not project_name:
        return jsonify({'error': 'Project name is required'}), 400

    prompt = f"""Generate a professional, complete README.md for a GitHub project.

Project Name: {project_name}
Description: {description}
Tech Stack: {tech_stack}
Key Features: {features}
GitHub URL: {github_url if github_url else 'https://github.com/username/' + project_name.lower().replace(' ', '-')}
Author: {author if author else 'Developer'}

Create a full README.md with these sections:
- Title with badges (build, license, stars)
- Short description
- Table of contents
- Features list
- Tech stack
- Installation steps
- Usage examples
- Contributing guide
- License

Use proper markdown formatting. Make it look professional and complete.
Return ONLY the markdown content, no extra text."""

    try:
        from config import get_ai_response
        readme = get_ai_response(prompt)
        return jsonify({'success': True, 'readme': readme})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ════════════════════════════════════════════════════════════════
# SKILL CERTIFICATE GENERATOR
# ════════════════════════════════════════════════════════════════

@app.route('/api/student/certificate/<int:test_id>')
def generate_certificate(test_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    tests = get_skill_tests(user['id'])
    test  = next((t for t in tests if t['id'] == test_id), None)

    if not test:
        return "Test not found", 404

    if test['pct'] < 70:
        return "Score must be 70% or above to get a certificate", 403

    profile = get_or_create_profile(user['id'], user['email'])

    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate
        from reportlab.pdfgen import canvas as rl_canvas
        import io
        from datetime import datetime

        buf = io.BytesIO()
        c   = rl_canvas.Canvas(buf, pagesize=landscape(A4))
        W, H = landscape(A4)

        # Background
        c.setFillColor(colors.HexColor('#06060f'))
        c.rect(0, 0, W, H, fill=1, stroke=0)

        # Border gradient effect
        c.setStrokeColor(colors.HexColor('#7c5cfc'))
        c.setLineWidth(3)
        c.roundRect(20, 20, W-40, H-40, 12, fill=0, stroke=1)

        c.setStrokeColor(colors.HexColor('#c026d3'))
        c.setLineWidth(1)
        c.roundRect(26, 26, W-52, H-52, 10, fill=0, stroke=1)

        # Header
        c.setFillColor(colors.HexColor('#7c5cfc'))
        c.rect(0, H-80, W, 80, fill=1, stroke=0)

        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 28)
        c.drawCentredString(W/2, H-55, 'StackSage')
        c.setFont('Helvetica', 12)
        c.drawCentredString(W/2, H-72, 'GitHub Trend Intelligence Platform')

        # Certificate title
        c.setFillColor(colors.HexColor('#f0f0ff'))
        c.setFont('Helvetica-Bold', 36)
        c.drawCentredString(W/2, H-150, 'Certificate of Achievement')

        # Decorative line
        c.setStrokeColor(colors.HexColor('#c026d3'))
        c.setLineWidth(2)
        c.line(W/2 - 200, H-165, W/2 + 200, H-165)

        # This is to certify
        c.setFillColor(colors.HexColor('#a0a0cc'))
        c.setFont('Helvetica', 14)
        c.drawCentredString(W/2, H-200, 'This is to certify that')

        # Student name
        c.setFillColor(colors.HexColor('#b794f4'))
        c.setFont('Helvetica-Bold', 40)
        c.drawCentredString(W/2, H-250, profile['display_name'])

        # Has successfully
        c.setFillColor(colors.HexColor('#a0a0cc'))
        c.setFont('Helvetica', 14)
        c.drawCentredString(W/2, H-285, 'has successfully completed the skill assessment in')

        # Topic
        c.setFillColor(colors.HexColor('#7c9eff'))
        c.setFont('Helvetica-Bold', 30)
        c.drawCentredString(W/2, H-330, test['topic'])

        # Score & badge
        badge_text = f"Score: {test['score']}/{test['total']} ({test['pct']}%)"
        badge_colors = {'gold': '#f6c90e', 'silver': '#b0bec5', 'bronze': '#cd7f32'}
        badge_col = badge_colors.get(test['badge'], '#7c9eff')

        c.setFillColor(colors.HexColor(badge_col))
        c.setFont('Helvetica-Bold', 18)
        c.drawCentredString(W/2, H-370, badge_text)

        if test['badge']:
            c.setFont('Helvetica-Bold', 16)
            medals = {'gold': '🥇 Gold Badge', 'silver': '🥈 Silver Badge', 'bronze': '🥉 Bronze Badge'}
            c.drawCentredString(W/2, H-395, medals.get(test['badge'], ''))

        # Footer
        c.setStrokeColor(colors.HexColor('#7c5cfc'))
        c.setLineWidth(1)
        c.line(60, 80, W-60, 80)

        c.setFillColor(colors.HexColor('#606080'))
        c.setFont('Helvetica', 10)
        date_str = test['taken_at'][:10]
        c.drawString(60, 60, f'Date: {date_str}')
        c.drawCentredString(W/2, 60, 'stacksagebynk.onrender.com')
        c.drawRightString(W-60, 60, f'Certificate ID: SS-{test_id:04d}')

        c.save()
        buf.seek(0)

        filename = f"StackSage_Certificate_{test['topic'].replace(' ', '_')}_{profile['display_name']}.pdf"
        return send_file(buf, mimetype='application/pdf',
                        download_name=filename, as_attachment=True)

    except ImportError:
        return "ReportLab not installed", 500
    except Exception as e:
        return f"Certificate generation error: {str(e)}", 500


# ════════════════════════════════════════════════════════════════
# DAILY TO-DO LIST
# ════════════════════════════════════════════════════════════════

@app.route('/api/todos', methods=['GET'])
def api_get_todos():
    user = get_current_user()
    if not user: return jsonify({'error': 'Not logged in'}), 401
    from database import get_todos
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    return jsonify({'todos': get_todos(user['id'], date)})

@app.route('/api/todos', methods=['POST'])
def api_add_todo():
    user = get_current_user()
    if not user: return jsonify({'error': 'Not logged in'}), 401
    from database import add_todo
    data = request.get_json()
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    tid  = add_todo(user['id'], data.get('text','').strip()[:200], date)
    return jsonify({'success': True, 'id': tid})

@app.route('/api/todos/<int:tid>/toggle', methods=['POST'])
def api_toggle_todo(tid):
    user = get_current_user()
    if not user: return jsonify({'error': 'Not logged in'}), 401
    from database import toggle_todo
    toggle_todo(tid, user['id'])
    return jsonify({'success': True})

@app.route('/api/todos/<int:tid>', methods=['DELETE'])
def api_delete_todo(tid):
    user = get_current_user()
    if not user: return jsonify({'error': 'Not logged in'}), 401
    from database import delete_todo
    delete_todo(tid, user['id'])
    return jsonify({'success': True})


# ════════════════════════════════════════════════════════════════
# HABIT TRACKER
# ════════════════════════════════════════════════════════════════

@app.route('/api/habits', methods=['GET'])
def api_get_habits():
    user = get_current_user()
    if not user: return jsonify({'error': 'Not logged in'}), 401
    from database import get_habits, get_habit_logs
    date   = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    habits = get_habits(user['id'])
    logs   = get_habit_logs(user['id'], date)
    return jsonify({'habits': habits, 'logs': logs})

@app.route('/api/habits', methods=['POST'])
def api_add_habit():
    user = get_current_user()
    if not user: return jsonify({'error': 'Not logged in'}), 401
    from database import add_habit
    data = request.get_json()
    hid  = add_habit(user['id'], data.get('name','').strip()[:80], data.get('emoji','✅'))
    return jsonify({'success': True, 'id': hid})

@app.route('/api/habits/<int:hid>', methods=['DELETE'])
def api_delete_habit(hid):
    user = get_current_user()
    if not user: return jsonify({'error': 'Not logged in'}), 401
    from database import delete_habit
    delete_habit(hid, user['id'])
    return jsonify({'success': True})

@app.route('/api/habits/<int:hid>/toggle', methods=['POST'])
def api_toggle_habit(hid):
    user = get_current_user()
    if not user: return jsonify({'error': 'Not logged in'}), 401
    from database import toggle_habit_log
    date = request.get_json().get('date', datetime.now().strftime('%Y-%m-%d'))
    done = toggle_habit_log(user['id'], hid, date)
    if done: add_xp(user['id'], 'chat')
    return jsonify({'success': True, 'done': done})


# ════════════════════════════════════════════════════════════════
# POMODORO TIMER (no DB needed — frontend only + XP on complete)
# ════════════════════════════════════════════════════════════════

@app.route('/api/pomodoro/complete', methods=['POST'])
def pomodoro_complete():
    user = get_current_user()
    if not user: return jsonify({'error': 'Not logged in'}), 401
    add_xp(user['id'], 'test')
    return jsonify({'success': True, 'xp_gained': 20})


# ════════════════════════════════════════════════════════════════
# DAILY CODING CHALLENGE
# ════════════════════════════════════════════════════════════════

@app.route('/api/daily-challenge', methods=['GET'])
def get_daily_challenge():
    user = get_current_user()
    if not user: return jsonify({'error': 'Not logged in'}), 401
    from database import get_or_create_challenge
    from config import get_ai_response

    today   = datetime.now().strftime('%Y-%m-%d')
    profile = get_or_create_profile(user['id'], user['email'])

    prompt = (
        f"Generate a short daily coding challenge for a {profile['skill_level']} developer.\n"
        "Return ONLY a JSON object (no markdown) like this:\n"
        '{"topic": "Python", "question": "What does len([1,2,3]) return?", "answer": "3"}\n'
        "Keep the question short (1-2 sentences). Answer should be concise (1-10 words).\n"
        "Make it educational and practical."
    )

    challenge = get_or_create_challenge(user['id'], today, '', '', '')

    if challenge['new']:
        try:
            import json as _json
            raw = get_ai_response(prompt).strip()
            if raw.startswith('```'): raw = raw.split('```')[1]; raw = raw[4:] if raw.startswith('json') else raw
            data = _json.loads(raw)
            from database import get_or_create_challenge as gcc
            challenge = gcc(user['id'], today, data['topic'], data['question'], data['answer'])
        except:
            challenge = {'question': 'What does list.append() do in Python?',
                         'answer': 'Adds an element to the end of the list',
                         'user_answer': '', 'solved': False}

    return jsonify({'challenge': challenge, 'date': today})


@app.route('/api/daily-challenge/submit', methods=['POST'])
def submit_daily_challenge():
    user = get_current_user()
    if not user: return jsonify({'error': 'Not logged in'}), 401
    from database import submit_challenge
    data    = request.get_json()
    today   = datetime.now().strftime('%Y-%m-%d')
    correct = submit_challenge(user['id'], today, data.get('answer', ''))
    if correct:
        add_xp(user['id'], 'test')
    return jsonify({'success': True, 'correct': correct})


# ════════════════════════════════════════════════════════════════
# TECH WORD OF THE DAY
# ════════════════════════════════════════════════════════════════

_word_cache = {}

@app.route('/api/word-of-day', methods=['GET'])
def word_of_day():
    from config import get_ai_response
    import hashlib
    today = datetime.now().strftime('%Y-%m-%d')
    if today in _word_cache:
        return jsonify(_word_cache[today])
    prompt = (
        f"Today is {today}. Generate a 'Tech Word of the Day' for developers.\n"
        "Return ONLY a JSON object (no markdown):\n"
        '{"word": "Recursion", "category": "Programming", "definition": "A function that calls itself.", '
        '"example": "def factorial(n): return 1 if n<=1 else n*factorial(n-1)", '
        '"used_by": "Python, JavaScript, Java"}\n'
        "Pick an interesting, educational tech term. Keep definition under 20 words."
    )
    try:
        import json as _json
        raw = get_ai_response(prompt).strip()
        if raw.startswith('```'): raw = raw.split('```')[1]; raw = raw[4:] if raw.startswith('json') else raw
        data = _json.loads(raw)
        _word_cache[today] = data
        return jsonify(data)
    except:
        fallback = {'word': 'API', 'category': 'Web Development',
                    'definition': 'Interface allowing software components to communicate.',
                    'example': 'fetch("https://api.github.com/users/torvalds")',
                    'used_by': 'Every modern web application'}
        return jsonify(fallback)


# ════════════════════════════════════════════════════════════════
# JSON FORMATTER TOOL
# ════════════════════════════════════════════════════════════════

@app.route('/json-formatter')
def json_formatter():
    return render_template('json_formatter.html')


@app.route('/china-hub')
def china_hub():
    return render_template('china_hub.html')

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
