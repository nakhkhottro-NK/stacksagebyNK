"""
config.py - StackSage Configuration
Uses Google Gemini API (FREE) instead of Anthropic.
"""
import os

# Google Gemini API Key (FREE) - get at: aistudio.google.com
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "your_gemini_api_key_here")

# GitHub Token (optional but recommended)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# App settings
DATABASE_PATH = "stacksage.db"
MAX_REPOS     = 12
DEBUG_MODE    = os.environ.get("DEBUG", "false").lower() == "true"
