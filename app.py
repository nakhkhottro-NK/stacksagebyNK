"""
StackSage v2.0 - GitHub Trend Intelligence & AI-Powered Tech Analysis
Main Flask Application — Production Ready
"""

from flask import (Flask, render_template, request, jsonify, redirect,
                   url_for, flash, send_file, abort, Response)
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
                      save_user, get_user, create_user_session)
import json
import io
import os
import secrets
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "stacksage_secret_2025_change_me")


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

    # 1. Fetch GitHub Data
    repos_data = search_repositories(query, per_page=12)

    if 'error' in repos_data and not repos_data.get('repos'):
        flash(f"GitHub API error: {repos_data['error']}", 'error')
        return redirect(url_for('index'))

    repos = repos_data['repos']
    if not repos:
        flash(f'No repositories found for "{query}". Try a different keyword.', 'error')
        return redirect(url_for('index'))

    # 2. Compute Statistics
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

    # 3. AI Insights
    ai_insights = analyze_repos(query, repos_data)
    learning_path = generate_learning_path(domain, languages, all_topics)
    ai_recommendations = recommend_repos(query, repos)

    tech_comparison = None
    if len(languages) >= 2:
        tech_comparison = compare_technologies(list(languages.keys())[:4], domain)

    # 4. Generate Charts
    charts = {
        'stars': create_stars_chart(repos),
        'languages': create_language_chart(languages),
        'activity': create_activity_scatter(repos),
        'wordcloud': create_wordcloud(all_topics, query),
        'timeline': create_timeline_chart(repos)
    }

    # 5. Persist to DB
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
# DOMAIN COMPARISON (NEW)
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
# AI CHAT (NEW)
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
# SHARE LINK (NEW)
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
# PDF EXPORT (NEW)
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
    # Production (gunicorn)
    init_db()
