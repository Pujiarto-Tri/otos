#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies  
npm install

# Build CSS with Tailwind
npm run build

# Collect static files
python manage.py collectstatic --noinput

# Run migrations (optional, comment out if not needed)
# python manage.py migrate --noinput
