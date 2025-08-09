#!/bin/bash

# Build script for Vercel

set -euo pipefail

export PYTHONUNBUFFERED=1

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing Node.js dependencies..."
npm ci || npm install

echo "Building CSS..."
npm run build

# Apply DB migrations (useful for managed Postgres via DATABASE_URL)
if [ "${DATABASE_URL:-}" != "" ]; then
  echo "Applying database migrations..."
  python manage.py migrate --noinput
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Build completed successfully!"
