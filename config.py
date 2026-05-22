"""
config.py - StackSage Configuration
Supports both DeepSeek (paid) and Google Gemini (free)
"""
import os

# ── DeepSeek API (Paid) ─────────────────────────────────────
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# ── Google Gemini API (Free) ────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ── Auto-select: DeepSeek if available, else Gemini ─────────
def get_ai_response(prompt: str) -> str:
    """Call DeepSeek if key exists, otherwise fall back to Gemini."""
    if DEEPSEEK_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com"
            )
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"DeepSeek error: {str(e)}"

    elif GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Gemini error: {str(e)}"

    else:
        return "No AI API key found. Please set DEEPSEEK_API_KEY or GEMINI_API_KEY in environment variables."

# ── GitHub Token ─────────────────────────────────────────────
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# ── App settings ─────────────────────────────────────────────
DATABASE_PATH = "stacksage.db"
MAX_REPOS     = 12
DEBUG_MODE    = os.environ.get("DEBUG", "false").lower() == "true"
