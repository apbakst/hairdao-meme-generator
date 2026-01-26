"""
FastAPI entrypoint for deployment.
"""
from web_app import app

# Export app for ASGI servers (uvicorn, gunicorn, etc.)
# Run with: uvicorn app:app --host 0.0.0.0 --port 8000
