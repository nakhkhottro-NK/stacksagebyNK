"""
visualizer.py — Chart & Visualization Generation
Produces base64-encoded PNG charts using matplotlib and wordcloud.
All charts use a dark cyberpunk theme for visual consistency.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend (no display needed)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from wordcloud import WordCloud
import base64
import io

# ── Global Theme ──────────────────────────────────────────────
BG_DARK   = '#131a2c'
BG_PANEL  = '#1a2342'
ACCENT    = '#7c9eff'
ACCENT2   = '#b794f4'
TEXT      = '#e8ecf5'
GRID_CLR  = '#2a3552'
CMAP      = 'cool'


def _fig_to_b64(fig) -> str:
    """Convert a matplotlib Figure to a base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=130,
                facecolor=BG_DARK, edgecolor='none')
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return encoded


def _apply_theme(ax):
    """Apply consistent dark theme to an axes object."""
    ax.set_facecolor(BG_PANEL)
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    for spine in ax.spines.values():
        spine.set_color(GRID_CLR)
    ax.grid(True, color=GRID_CLR, alpha=0.6, linestyle='--', linewidth=0.5)


# ── 1. Stars Bar Chart ─────────────────────────────────────────
def create_stars_chart(repos: list) -> str | None:
    if not repos:
        return None

    top = sorted(repos, key=lambda r: r['stars'], reverse=True)[:8]
    names  = [r['name'].split('/')[-1][:22] for r in top]
    stars  = [r['stars'] for r in top]
    colors = plt.cm.cool(np.linspace(0.2, 0.9, len(names)))

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG_DARK)
    bars = ax.barh(names[::-1], stars[::-1], color=colors[::-1],
                   edgecolor=GRID_CLR, linewidth=0.5, height=0.65)
    _apply_theme(ax)
    ax.set_xlabel('GitHub Stars ⭐', fontsize=10)
    ax.set_title('Top Repositories by Stars', color=ACCENT, fontsize=13,
                 fontweight='bold', pad=12)

    max_s = max(stars) if stars else 1
    for bar, star in zip(bars, stars[::-1]):
        ax.text(bar.get_width() + max_s * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f'{star:,}', va='center', ha='left', color=TEXT, fontsize=8)
    plt.tight_layout()
    return _fig_to_b64(fig)


# ── 2. Language Donut Chart ────────────────────────────────────
def create_language_chart(languages: dict) -> str | None:
    if not languages:
        return None

    labels = list(languages.keys())
    sizes  = list(languages.values())
    palette = [ACCENT, ACCENT2, '#3fb950', '#d2a8ff', '#ffa657',
               '#79c0ff', '#ff7b72', '#56d364', '#e3b341', '#a5d6ff']

    fig, ax = plt.subplots(figsize=(7, 6))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(BG_DARK)

    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%',
        colors=palette[:len(labels)], startangle=140,
        wedgeprops=dict(width=0.55, edgecolor=BG_DARK, linewidth=2),
        textprops={'color': TEXT, 'fontsize': 9}
    )
    for at in autotexts:
        at.set_fontsize(8)
        at.set_color('#ffffff')

    ax.set_title('Language Distribution', color=ACCENT, fontsize=13,
                 fontweight='bold', pad=16)
    plt.tight_layout()
    return _fig_to_b64(fig)


# ── 3. Activity Scatter Plot ───────────────────────────────────
def create_activity_scatter(repos: list) -> str | None:
    if not repos:
        return None

    stars  = [r['stars'] for r in repos]
    forks  = [r['forks'] for r in repos]
    names  = [r['name'].split('/')[-1][:14] for r in repos]
    colors = np.arange(len(repos))

    fig, ax = plt.subplots(figsize=(9, 5.5))
    fig.patch.set_facecolor(BG_DARK)
    sc = ax.scatter(stars, forks, c=colors, cmap='cool', s=180,
                    alpha=0.85, edgecolors=ACCENT2, linewidth=0.8)

    for i, name in enumerate(names):
        ax.annotate(name, (stars[i], forks[i]),
                    textcoords='offset points', xytext=(6, 4),
                    fontsize=7.5, color=TEXT)

    _apply_theme(ax)
    ax.set_xlabel('Stars ⭐', fontsize=10)
    ax.set_ylabel('Forks 🍴', fontsize=10)
    ax.set_title('Community Activity Map  (Stars vs Forks)', color=ACCENT,
                 fontsize=13, fontweight='bold', pad=12)

    cbar = plt.colorbar(sc, ax=ax)
    cbar.ax.set_ylabel('Repo Rank', color=TEXT, fontsize=8)
    cbar.ax.tick_params(colors=TEXT)
    plt.tight_layout()
    return _fig_to_b64(fig)


# ── 4. Topics Word Cloud ───────────────────────────────────────
def create_wordcloud(topics: dict, query: str) -> str | None:
    if not topics:
        return None

    # Build weighted text corpus
    text = ' '.join(f'{k} ' * v for k, v in topics.items())
    text += f' {query} ' * 6  # Emphasise the search term

    wc = WordCloud(
        width=900, height=420,
        background_color=BG_DARK,
        colormap='cool',
        max_words=70,
        prefer_horizontal=0.75,
        min_font_size=10,
        max_font_size=90,
        collocations=False
    ).generate(text)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    fig.patch.set_facecolor(BG_DARK)
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    ax.set_title(f'Topic Cloud — "{query}"', color=ACCENT, fontsize=13,
                 fontweight='bold', pad=12)
    plt.tight_layout()
    return _fig_to_b64(fig)


# ── 5. Activity Timeline ───────────────────────────────────────
def create_timeline_chart(repos: list) -> str | None:
    if not repos:
        return None

    from collections import Counter
    year_counts = Counter(r['updated_at'][:4] for r in repos)
    years  = sorted(year_counts.keys())
    counts = [year_counts[y] for y in years]

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(BG_DARK)
    ax.plot(years, counts, color=ACCENT, linewidth=2.5,
            marker='o', markersize=9, markerfacecolor=ACCENT2,
            markeredgecolor=ACCENT, markeredgewidth=1.5)
    ax.fill_between(years, counts, alpha=0.15, color=ACCENT)

    _apply_theme(ax)
    ax.set_xlabel('Year of Last Update', fontsize=10)
    ax.set_ylabel('Number of Repos', fontsize=10)
    ax.set_title('Recent Activity Timeline', color=ACCENT, fontsize=13,
                 fontweight='bold', pad=12)
    ax.set_xticks(years)
    plt.tight_layout()
    return _fig_to_b64(fig)
