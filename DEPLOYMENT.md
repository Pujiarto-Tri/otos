# OTOS - Deployment Guide

## Deployment to Vercel

### Prerequisites
1. Vercel account
2. GitHub repository connected to Vercel

### Setup Steps

1. **Environment Variables in Vercel**
   Set these environment variables in your Vercel dashboard:
   ```
   DEBUG=False
   SECRET_KEY=your-super-secret-key-here
   ALLOWED_HOSTS=.vercel.app,your-domain.com
   DJANGO_SETTINGS_MODULE=otos.settings
   ```

2. **Build Configuration**
   The `vercel.json` file is already configured for Django deployment.

3. **Static Files**
   - Run `npm run build` locally to generate CSS files
   - Commit the generated `static/src/output.css` file
   - Vercel will serve static files automatically

4. **Database**
   - For production, consider using PostgreSQL
   - Set `DATABASE_URL` environment variable if needed
   - Current setup uses SQLite for simplicity

### Local Development

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   npm install
   ```

2. **Build CSS**
   ```bash
   npm run dev  # For development (with watch)
   npm run build  # For production
   ```

3. **Run Server**
   ```bash
   python manage.py runserver
   ```

### Troubleshooting

1. **Static Files Issues**
   - Make sure `static/src/output.css` exists and is committed
   - Check that WhiteNoise is properly configured

2. **Permission Errors**
   - Ensure build scripts have proper permissions
   - Check Vercel build logs for specific errors

3. **Database Issues**
   - For production, migrate to PostgreSQL
   - Use Vercel Postgres or external database service

### Important Notes

- SQLite is not suitable for production on Vercel
- Media files should be served from external storage (AWS S3, Cloudinary, etc.)
- Environment variables should be set in Vercel dashboard, not in code
