"""
github_api.py — GitHub REST API Integration
Fetches repositories, stats, and community activity data.
"""

import requests
from collections import Counter
from config import GITHUB_TOKEN

# Build headers (token is optional but avoids rate limiting)
HEADERS = {'Accept': 'application/vnd.github.v3+json'}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'token {GITHUB_TOKEN}'


def search_repositories(query: str, sort: str = 'stars', per_page: int = 12) -> dict:
    """
    Search GitHub for repositories matching a query.
    Returns structured data including name, stars, forks, language, topics.
    """
    url = 'https://api.github.com/search/repositories'
    params = {
        'q': query,
        'sort': sort,
        'order': 'desc',
        'per_page': per_page
    }

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        repos = []
        for item in data.get('items', []):
            repos.append({
                'name':        item['full_name'],
                'short_name':  item['name'],
                'description': item.get('description') or 'No description available.',
                'url':         item['html_url'],
                'stars':       item['stargazers_count'],
                'forks':       item['forks_count'],
                'watchers':    item['watchers_count'],
                'open_issues': item['open_issues_count'],
                'language':    item.get('language') or 'Unknown',
                'topics':      item.get('topics', []),
                'created_at':  item['created_at'][:10],
                'updated_at':  item['updated_at'][:10],
                'size_kb':     item['size'],
                'license':     (item.get('license') or {}).get('name', 'No license'),
                'owner':       item['owner']['login'],
                'avatar':      item['owner']['avatar_url'],
                'is_fork':     item['fork'],
            })

        return {
            'total_count': data.get('total_count', 0),
            'repos': repos,
            'query': query
        }

    except requests.exceptions.Timeout:
        return {'error': 'Request timed out. Check your internet connection.', 'repos': [], 'total_count': 0}
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            return {'error': 'GitHub API rate limit exceeded. Add a token in config.py.', 'repos': [], 'total_count': 0}
        return {'error': str(e), 'repos': [], 'total_count': 0}
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'repos': [], 'total_count': 0}


def get_trending_languages(repos: list) -> dict:
    """
    Extract and count programming language distribution from a list of repos.
    Returns a dict of {language: count} sorted by frequency.
    """
    languages = [r['language'] for r in repos if r['language'] != 'Unknown']
    return dict(Counter(languages).most_common(10))


def get_repo_stats_summary(repos: list) -> dict:
    """Calculate aggregate statistics across all repos."""
    if not repos:
        return {}

    stars_list = [r['stars'] for r in repos]
    forks_list = [r['forks'] for r in repos]

    all_topics = []
    for r in repos:
        all_topics.extend(r['topics'])

    return {
        'total_stars':     sum(stars_list),
        'total_forks':     sum(forks_list),
        'avg_stars':       sum(stars_list) // len(repos),
        'max_stars':       max(stars_list),
        'languages':       get_trending_languages(repos),
        'top_topics':      dict(Counter(all_topics).most_common(15)),
        'unique_languages': len(set(r['language'] for r in repos if r['language'] != 'Unknown'))
    }
