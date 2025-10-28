# PythonAnywhere Deployment Guide

## Part 1: Backend Setup on PythonAnywhere

### Step 1: Create Account
1. Go to [pythonanywhere.com](https://www.pythonanywhere.com)
2. Sign up for **Beginner Account** (FREE, no card required)
3. Verify your email

### Step 2: Upload Code

#### Method 1: Git Clone (Recommended)
1. In PythonAnywhere Dashboard, click **"Consoles"** tab
2. Start a new **Bash console**
3. Run these commands:
```bash
git clone https://github.com/YOUR_USERNAME/HackOHIO.git
cd HackOHIO/backend
```

#### Method 2: Manual Upload
1. Click **"Files"** tab
2. Navigate to home directory
3. Create folder: `HackOHIO/backend`
4. Upload all files from your local `backend/` folder

### Step 3: Install Dependencies
In the Bash console:
```bash
cd ~/HackOHIO/backend

# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Create Web App
1. Go to **"Web"** tab in PythonAnywhere
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"**
4. Select **Python 3.11**
5. Click through to create the app

### Step 5: Configure WSGI File
1. In the **Web** tab, find the **"WSGI configuration file"** link
2. Click to edit it
3. **Delete everything** in the file
4. Replace with this content:

```python
import sys
import os

# !!! IMPORTANT: Replace YOUR_USERNAME with your actual PythonAnywhere username !!!
project_home = '/home/YOUR_USERNAME/HackOHIO/backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Activate virtual environment
activate_this = '/home/YOUR_USERNAME/HackOHIO/backend/venv/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Import FastAPI app
from main_weather import app
application = app
```

5. Click **"Save"**

### Step 6: Configure Virtual Environment Path
1. Still in **Web** tab, scroll to **"Virtualenv"** section
2. Enter the path to your virtual environment:
   ```
   /home/YOUR_USERNAME/HackOHIO/backend/venv
   ```
3. The path should turn green if correct

### Step 7: Update CORS Settings
1. Go back to Bash console
2. Edit `main_weather.py`:
```bash
cd ~/HackOHIO/backend
nano main_weather.py
```

3. Find the CORS middleware section and update it:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",
        "https://*.vercel.app",  # Allow all Vercel domains
        "https://your-app-name.vercel.app"  # Your specific Vercel URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

4. Save: `Ctrl+O`, `Enter`, `Ctrl+X`

### Step 8: Reload Web App
1. Go back to **Web** tab
2. Click the big green **"Reload"** button
3. Wait for it to finish reloading

### Step 9: Test Your Backend
1. Your API will be at: `https://YOUR_USERNAME.pythonanywhere.com`
2. Test endpoints:
   - Health check: `https://YOUR_USERNAME.pythonanywhere.com/health`
   - API docs: `https://YOUR_USERNAME.pythonanywhere.com/docs`
   - Calculate all: `https://YOUR_USERNAME.pythonanywhere.com/calculate_all_with_weather`

3. Open these URLs in your browser to verify

---

## Part 2: Frontend Setup on Vercel

### Step 1: Update API URL
1. Open `frontend/src/services/api.js` locally
2. Update the API URL:
```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL ||
                     'https://YOUR_USERNAME.pythonanywhere.com';
```

3. Commit and push to GitHub:
```bash
git add frontend/src/services/api.js
git commit -m "Update API URL for PythonAnywhere backend"
git push
```

### Step 2: Deploy to Vercel
1. Go to [vercel.com](https://vercel.com)
2. Click **"Sign Up"** or **"Login"**
3. Choose **"Continue with GitHub"**
4. Click **"Import Project"**
5. Select your **HackOHIO** repository

### Step 3: Configure Vercel Project
1. **Framework Preset:** Vite
2. **Root Directory:** `frontend`
3. **Build Command:** `npm run build` (should be auto-detected)
4. **Output Directory:** `dist` (should be auto-detected)
5. **Environment Variables:**
   - Add variable: `VITE_API_URL`
   - Value: `https://YOUR_USERNAME.pythonanywhere.com`

6. Click **"Deploy"**

### Step 4: Wait for Deployment
- Vercel will build and deploy (takes 2-3 minutes)
- You'll get a URL like: `https://your-app.vercel.app`

### Step 5: Update CORS on PythonAnywhere
1. Go back to PythonAnywhere Bash console
2. Edit `main_weather.py` again:
```bash
nano ~/HackOHIO/backend/main_weather.py
```

3. Update CORS to include your actual Vercel URL:
```python
allow_origins=[
    "http://localhost:5173",
    "https://your-actual-app.vercel.app",  # Replace with your Vercel URL
],
```

4. Save and exit
5. Go to **Web** tab and click **"Reload"**

---

## Part 3: Testing

### Test Backend:
1. Visit: `https://YOUR_USERNAME.pythonanywhere.com/health`
   - Should return: `{"status": "healthy"}`

2. Visit: `https://YOUR_USERNAME.pythonanywhere.com/docs`
   - Should show FastAPI interactive docs

3. Test API call:
   - Visit: `https://YOUR_USERNAME.pythonanywhere.com/calculate_all_with_weather`
   - Should return JSON with line data

### Test Frontend:
1. Visit your Vercel URL: `https://your-app.vercel.app`
2. Check browser console (F12) for any errors
3. Try different views:
   - Dashboard view
   - Map view
   - Table view
   - Charts view
4. Test weather scenarios
5. Test custom weather controls

---

## Troubleshooting

### Backend Issues:

**Error: "502 Bad Gateway"**
- Check WSGI file has correct username path
- Verify virtual environment path is correct
- Check error log in Web tab

**Error: "Module not found"**
- Reinstall dependencies in virtual environment
- Make sure you activated venv before pip install

**Error: "CORS policy error"**
- Update CORS origins in `main_weather.py`
- Include your exact Vercel URL
- Reload web app after changes

### Frontend Issues:

**Error: "Network Error" or API calls failing**
- Check `VITE_API_URL` environment variable in Vercel
- Verify PythonAnywhere backend is running
- Check CORS settings include Vercel URL

**Map not loading:**
- Check browser console for errors
- Verify Leaflet CSS is imported

**Blank page:**
- Check Vercel build logs for errors
- Verify build completed successfully

---

## Free Tier Limitations

### PythonAnywhere Free Tier:
- ✅ 1 web app
- ✅ 512 MB disk space
- ✅ HTTPS enabled
- ⚠️ Sleep after inactivity (but wakes up fast)
- ⚠️ Can only access whitelisted sites (not an issue for your app)

### Vercel Free Tier:
- ✅ Unlimited projects
- ✅ 100 GB bandwidth/month
- ✅ No cold starts
- ✅ Automatic HTTPS

---

## Your Live URLs

After deployment, update these:

- **Frontend:** `https://__________.vercel.app`
- **Backend API:** `https://__________.pythonanywhere.com`
- **API Docs:** `https://__________.pythonanywhere.com/docs`

---

## Tips for Hackathon Demo

1. **Test before presenting:** Make sure both services are awake
2. **Keep browser tab open:** Prevents PythonAnywhere from sleeping
3. **Use Vercel URL:** Share this with judges (faster than PythonAnywhere)
4. **Show API docs:** Judges love seeing the `/docs` endpoint
5. **Have backup:** Keep localhost version ready just in case

---

## Need Help?

**PythonAnywhere:**
- Help forum: https://www.pythonanywhere.com/forums/
- FAQ: https://help.pythonanywhere.com/

**Vercel:**
- Docs: https://vercel.com/docs
- Discord: https://vercel.com/discord

---

## Quick Commands Reference

### PythonAnywhere Bash Console:
```bash
# Navigate to project
cd ~/HackOHIO/backend

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Edit files
nano main_weather.py

# Pull latest changes from Git
git pull origin main
```

### After Code Changes:
1. Update code (via Git or file upload)
2. Go to Web tab
3. Click "Reload" button
4. Test the change

---

**You're all set! 🚀**
