"""
Vercel Serverless Webhook Entrypoint for the UTM FCIM Schedule Bot.
Redirects to root index.handler.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from index import handler  # noqa: F401, E402
