#!/usr/bin/env bash
# One-command setup for Obsidian Clipper.
set -euo pipefail

echo "→ Obsidian Clipper setup"

# Check Python version
python3 -c "import sys; assert sys.version_info >= (3, 11), 'Python 3.11+ required'" \
  || { echo "ERROR: Python 3.11+ is required."; exit 1; }

# Create and activate virtual environment
if [ ! -d "venv" ]; then
  echo "→ Creating virtual environment…"
  python3 -m venv venv
fi
source venv/bin/activate

# Install dependencies
echo "→ Installing dependencies…"
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# Set up .env if missing
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "→ Created .env from .env.example — add your ANTHROPIC_API_KEY"
else
  echo "→ .env already exists — skipping"
fi

echo ""
echo "Setup complete. Next steps:"
echo "  1. Edit .env and set your ANTHROPIC_API_KEY"
echo "  2. Edit config.yaml and set vault.path to your Obsidian vault"
echo "  3. Test with: source venv/bin/activate && python clip.py <youtube-url>"
echo "  4. Set up a keyboard shortcut via Automator or Raycast (see README)"
