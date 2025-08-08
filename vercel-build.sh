#!/bin/bash

# Build script for Vercel

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing Node.js dependencies..."
npm install

echo "Building CSS..."
npm run build

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Build completed successfully!"
