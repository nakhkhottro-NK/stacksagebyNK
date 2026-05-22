"""
ai_analyzer.py — AI Analysis using Google Gemini (FREE)
"""
import json
import os

def _call_gemini(prompt: str) -> str:
    try:
        import google.generativeai as genai
        from config import GEMINI_API_KEY
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"AI analysis unavailable: {str(e)}"


def analyze_repos(query: str, repos_data: dict) -> str:
    repos = repos_data.get("repos", [])[:10]
    repo_summary = [
        {"name": r["name"], "description": (r["description"] or '')[:100],
         "stars": r["stars"], "forks": r["forks"],
         "language": r["language"], "topics": r["topics"][:6]}
        for r in repos
    ]
    prompt = f"""You are a senior technology trend analyst.
I searched GitHub for: "{query}"
Repository data:
{json.dumps(repo_summary, indent=2)}

Provide structured analysis with these exact section headers:

## TREND SUMMARY
What major trends does this data reveal?

## DOMINANT TECHNOLOGIES
Which languages and tools dominate and why?

## COMMUNITY HEALTH
Analyze star-to-fork ratios and engagement.

## RISING STARS
Pick 2-3 repos with highest potential.

## GAPS AND OPPORTUNITIES
What is missing in this ecosystem?

## FUTURE OUTLOOK
Where is this domain headed in 2 years?

## ONE-LINE VERDICT
One powerful sentence summarizing this ecosystem.

Reference actual repo names and numbers. Max 500 words."""
    return _call_gemini(prompt)


def generate_learning_path(domain: str, languages: dict = None, topics: dict = None) -> str:
    top_langs = ", ".join(list(languages.keys())[:5]) if languages else "various"
    top_topics = ", ".join(list(topics.keys())[:10]) if topics else "various"
    prompt = f"""Create a practical learning roadmap for someone entering "{domain}".
Most-used languages in real projects: {top_langs}
Key topics from open-source repos: {top_topics}

## PHASE 1: Foundations (Weeks 1-4)
List 4 concrete steps to get started.

## PHASE 2: Building Projects (Months 2-3)
Describe 3 mini-projects that build skills.

## PHASE 3: Advanced Mastery (Months 4-6)
Name 3 advanced skills for job-readiness.

## KEY RESOURCES
Best 3 types of resources for this domain.

## TIME ESTIMATE
Honest estimate for beginners vs experienced devs.

Keep it practical and encouraging. Max 350 words."""
    return _call_gemini(prompt)


def compare_technologies(tech_list: list, domain: str) -> str:
    techs = ", ".join(tech_list)
    prompt = f"""Compare these technologies in the {domain} domain: {techs}

Create a markdown comparison table:

| Technology | Primary Use | Learning Curve | Job Market | Best For |
|---|---|---|---|---|

Then write a 3-sentence recommendation on which to learn first and why.
Max 200 words."""
    return _call_gemini(prompt)


def chat_about_results(user_message: str, context: str, history: list) -> str:
    history_str = ""
    for h in history[-6:]:
        role = "User" if h.get("role") == "user" else "Assistant"
        history_str += f"{role}: {h.get('text','')}\n"

    prompt = f"""You are StackSage AI, an expert software-trend assistant.
You are chatting with a developer about their GitHub analysis results.

== Analysis context ==
{context if context else 'No specific search context.'}

== Previous conversation ==
{history_str if history_str else '(start of conversation)'}

User: {user_message}

Reply in a concise, friendly, practical tone (2-4 short paragraphs max).
Use markdown for lists or code."""
    return _call_gemini(prompt)


def recommend_repos(query: str, repos: list) -> str:
    summary = [
        {"name": r["name"], "stars": r["stars"], "language": r["language"],
         "description": (r["description"] or '')[:80]}
        for r in repos[:10]
    ]
    prompt = f"""User searched for: "{query}"
Top repositories found:
{json.dumps(summary, indent=2)}

Recommend 3 repos most worth exploring:

### Best for Beginners
**[repo name]** - One-line reason (max 25 words).

### Best for Production Use
**[repo name]** - One-line reason.

### Hidden Gem
**[repo name]** - One-line reason.

Pick from the list above. Be specific. Max 150 words total."""
    return _call_gemini(prompt)


def compare_domains_ai(domain_a: str, domain_b: str,
                       data_a: dict, data_b: dict) -> str:
    prompt = f"""Compare two technology domains based on real GitHub data:

== {domain_a} ==
Total repos found: {data_a['total_found']}
Top languages: {list(data_a['languages'].keys())[:5]}
Total stars (top 10): {data_a['total_stars']:,}
Avg stars/repo: {data_a['avg_stars']:,}

== {domain_b} ==
Total repos found: {data_b['total_found']}
Top languages: {list(data_b['languages'].keys())[:5]}
Total stars (top 10): {data_b['total_stars']:,}
Avg stars/repo: {data_b['avg_stars']:,}

## ECOSYSTEM MATURITY
Which domain has a more mature ecosystem and why?

## COMMUNITY SIZE
Compare community engagement (stars, repos).

## JOB MARKET OUTLOOK
Which has better career prospects in 2026?

## LEARNING DIFFICULTY
Which is easier to start with?

## VERDICT
One paragraph: who should pick which, and why.

Max 400 words. Be honest, no hedging."""
    return _call_gemini(prompt)
