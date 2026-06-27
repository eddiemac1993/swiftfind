#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/eddiemac1993/swiftfind.git"
BRANCH="schoolprocure"
PROJECT_DIR="$HOME/SchoolProcure"

if [ ! -d "$PROJECT_DIR/.git" ]; then
  git clone --branch "$BRANCH" "$REPO_URL" "$PROJECT_DIR"
else
  cd "$PROJECT_DIR"
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull origin "$BRANCH"
fi

cd "$PROJECT_DIR"

if command -v python3.10 >/dev/null 2>&1; then
  python3.10 -m venv .venv
else
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

export DJANGO_DEBUG=False
export DJANGO_ALLOWED_HOSTS="$USER.pythonanywhere.com,$USER.eu.pythonanywhere.com,localhost,127.0.0.1"

python manage.py migrate
python manage.py seed_demo
python manage.py collectstatic --noinput

echo "SchoolProcure is installed at $PROJECT_DIR"
echo "Use $PROJECT_DIR/pythonanywhere_wsgi.py as the PythonAnywhere WSGI file."
