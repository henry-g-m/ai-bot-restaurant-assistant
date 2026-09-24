#!/bin/bash
# Run the full regression test suite for ai-bot-restaurant-assistant

set -e

echo "=== Running full regression tests ==="
cd "$(dirname "$0")"

# Install dev dependencies if needed
pip install -r ".venv/Lib/site-packages/pyproject.toml" 2>/dev/null || pip install pytest httpx

# Run all tests in the project's tests directory
cd tests
python -m pytest --tb=short 2>&1 | tee test_results.log
