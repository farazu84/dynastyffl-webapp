"""
Backfill script for loading all historical transactions (2019-2026).

Run from the lhsffl-servers directory:
    venv/bin/python -m app.scripts.backfill_transactions
"""
import sys
import os
import logging

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Load environment variables from .flaskenv (python-dotenv handles spaces in exports)
from dotenv import load_dotenv
flaskenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.flaskenv')
load_dotenv(flaskenv_path)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    from app import create_app
    from config import DevConfig

    app = create_app(DevConfig)

    with app.app_context():
        from app.logic.transactions import backfill_all_transactions
        result = backfill_all_transactions()
        logger.info(f'Backfill result: {result}')


if __name__ == '__main__':
    main()
