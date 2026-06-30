"""Hugging Face Spaces entry point for EvalForge."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evalforge.dashboard.app import create_app
from evalforge.storage.db import init_db
from evalforge.benchmarks.registry import register_all

# Initialize database and register default benchmarks
init_db()
register_all()

# Create and launch the Gradio app
app = create_app()

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
