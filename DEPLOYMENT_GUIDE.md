# Deployment Guide - CCIS Parking Space System

## Quick Start - Deploy to Render (FREE)

### Step 1: Prepare Your Code
1. Create a GitHub account if you don't have one
2. Create a new repository on GitHub
3. Push your code to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

### Step 2: Deploy on Render
1. Go to https://render.com and sign up (use GitHub login)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: ccis-parking-system
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: Free
5. Click "Create Web Service"
6. Wait 5-10 minutes for deployment
7. Your app will be live at: `https://ccis-parking-system.onrender.com`

### Step 3: Important Notes
- Free tier sleeps after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds
- Database (parking.db) will persist
- HTTPS is included automatically

---

## Alternative: PythonAnywhere (FREE)

### Step 1: Sign Up
1. Go to https://www.pythonanywhere.com
2. Create a free account

### Step 2: Upload Files
1. Go to "Files" tab
2. Upload all your project files
3. Upload parking.db database

### Step 3: Configure Web App
1. Go to "Web" tab
2. Click "Add a new web app"
3. Choose "Flask"
4. Set Python version to 3.10
5. Edit WSGI configuration file:
   ```python
   import sys
   path = '/home/YOUR_USERNAME/parking_app'
   if path not in sys.path:
       sys.path.append(path)
   
   from app import app as application
   ```
6. Reload web app
7. Your app will be at: `https://YOUR_USERNAME.pythonanywhere.com`

---

## Alternative: Railway.app (FREE with limits)

### Step 1: Deploy
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects Flask and deploys
6. Get your live URL from the dashboard

---

## Production Checklist

Before going live, make sure to:

- [ ] Change `debug=False` in app.py (already done)
- [ ] Set a strong SECRET_KEY
- [ ] Use environment variables for sensitive data
- [ ] Set up proper database backups
- [ ] Add rate limiting for security
- [ ] Test all features thoroughly
- [ ] Set up monitoring/logging
- [ ] Configure custom domain (optional)

---

## Custom Domain Setup

After deployment, you can add a custom domain:

1. Buy a domain from Namecheap, GoDaddy, etc.
2. In your hosting provider:
   - Render: Settings → Custom Domains
   - PythonAnywhere: Web tab → Add custom domain
3. Update DNS records (A or CNAME) at your domain registrar
4. Wait 24-48 hours for DNS propagation

---

## Troubleshooting

### App won't start
- Check logs in your hosting dashboard
- Verify requirements.txt has all dependencies
- Ensure parking.db exists and has correct permissions

### Database errors
- Make sure parking.db is uploaded
- Check file permissions (should be writable)
- Consider using PostgreSQL for production

### Slow performance
- Free tiers have limitations
- Upgrade to paid plan for better performance
- Optimize database queries

---

## Need Help?

- Render Docs: https://render.com/docs
- PythonAnywhere Help: https://help.pythonanywhere.com
- Railway Docs: https://docs.railway.app

## Recommended: Start with Render
It's the easiest and most reliable free option with automatic HTTPS and good performance.
