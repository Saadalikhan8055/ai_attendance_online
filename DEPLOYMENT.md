# Deployment Guide - AI Attendance Online on Render

## Prerequisites
- GitHub account with your code pushed
- Render account (free tier available at render.com)

## Step 1: Push Your Code to GitHub

```bash
git init
git add .
git commit -m "Initial commit: AI Attendance App"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai_attendance_online.git
git push -u origin main
```

## Step 2: Create PostgreSQL Database on Render

1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Database"
3. Select "PostgreSQL"
4. Fill in details:
   - **Name**: `ai-attendance-db`
   - **Database**: `attendancedb`
   - **User**: `attendanceuser`
   - Select a region close to you
5. Click "Create Database"
6. Wait for database to initialize (2-3 minutes)
7. **Copy the Internal Database URL** (you'll need this)

## Step 3: Deploy Flask App on Render

1. From Render dashboard, click "New +" → "Web Service"
2. Connect your GitHub repository
3. Fill in deployment details:
   - **Name**: `ai-attendance-app`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free (for testing) or Starter ($7/month)

4. Add Environment Variables (click "Advanced" → "Add Environment Variable"):
   - **DATABASE_URL**: Paste the Internal Database URL from your PostgreSQL instance
   - **FLASK_SECRET**: Generate a random secret (e.g., using `python -c "import secrets; print(secrets.token_hex(32))"`)
   - **FLASK_ENV**: `production`

   Example:
   ```
   DATABASE_URL: postgresql://attendanceuser:password@dpg-xxx.render.internal/attendancedb
   FLASK_SECRET: your_random_secret_key_here
   FLASK_ENV: production
   ```

5. Click "Create Web Service"
6. Wait for deployment (3-5 minutes)

## Step 4: Initialize Database

After the app deploys:

1. Go to your app URL (e.g., `https://ai-attendance-app.onrender.com`)
2. The app will auto-create tables on first run
3. Create your first admin user by going to `/register`

## Step 5: Test Your Deployment

- Visit your app: `https://ai-attendance-app.onrender.com`
- Register a user
- Log in to dashboard
- Create a class
- Test attendance capture

## Troubleshooting

### "Application failed to start"
- Check Render logs: Click your service → "Logs"
- Ensure DATABASE_URL is correct
- Verify FLASK_SECRET is set

### "Import error: No module named..."
- Requirements.txt is missing a dependency
- Add it and push to GitHub (auto-redeploy)

### "ProgrammingError: relation ... does not exist"
- Database tables weren't created
- Check that the app started successfully
- Try accessing `/register` to trigger table creation

### App keeps restarting
- Check memory/CPU limits (might be hitting limits)
- Upgrade to Starter tier for more resources

## Important Notes

⚠️ **Face Recognition Performance**: 
- Face recognition works but is CPU-intensive
- May be slow on free tier
- Upgrade instance type for better performance

⚠️ **File Storage**: 
- Uploaded images stored locally on Render
- Will be lost if instance restarts (Render updates weekly)
- For production, use AWS S3 or Azure Blob Storage

⚠️ **Scaling**: 
- Use Starter tier ($7/month) or higher for production
- Free tier sleeps if no activity for 15+ minutes

## Next Steps for Production

1. **Add S3/Blob Storage**: Store uploaded images persistently
2. **Enable HTTPS**: Render provides free SSL
3. **Set up custom domain**: Point your domain to Render
4. **Enable backups**: Set up database backups in Render
5. **Monitor performance**: Use Render metrics

## Useful Links

- [Render Docs](https://render.com/docs)
- [Render Dashboard](https://dashboard.render.com)
- [Flask Deployment Guide](https://flask.palletsprojects.com/deployment/)

---

**Deployed by**: GitHub Copilot
**App Type**: Flask + SQLAlchemy
**Database**: PostgreSQL
**Host**: Render
