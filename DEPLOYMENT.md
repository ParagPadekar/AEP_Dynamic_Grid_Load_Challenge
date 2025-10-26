# IEEE 738 Dynamic Line Rating - Deployment Guide

## Quick Deployment Options

### Option 1: Render.com (RECOMMENDED)

**Best for:** Hackathon demos, free hosting, easy setup

#### Steps:

1. **Push to GitHub** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit - IEEE 738 DLR System"
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

2. **Deploy to Render**:
   - Go to [render.com](https://render.com)
   - Sign up with GitHub
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml` and deploy both services
   - Wait 5-10 minutes for deployment

3. **Update Frontend API URL**:
   - Once backend deploys, copy its URL (e.g., `https://ieee738-backend.onrender.com`)
   - Update `frontend/src/services/api.js`:
     ```javascript
     const API_BASE_URL = 'https://YOUR-BACKEND-URL.onrender.com';
     ```
   - Commit and push changes

4. **Access Your App**:
   - Frontend: `https://ieee738-frontend.onrender.com`
   - Backend API: `https://ieee738-backend.onrender.com`

**Cost:** FREE (with cold starts)
**Time to Deploy:** 10-15 minutes
**Uptime:** Good for demos, may sleep after 15 min inactivity

---

### Option 2: Vercel (Frontend) + Render (Backend)

**Best for:** Blazing fast frontend, separate services

#### Backend (Render):
1. Go to [render.com](https://render.com)
2. New → Web Service
3. Connect GitHub repo
4. Settings:
   - **Build Command:** `cd backend && pip install -r requirements.txt`
   - **Start Command:** `cd backend && uvicorn main_weather:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3.11

#### Frontend (Vercel):
1. Go to [vercel.com](https://vercel.com)
2. Import GitHub repository
3. Framework Preset: Vite
4. Root Directory: `frontend`
5. Build Command: `npm run build`
6. Output Directory: `dist`
7. Add Environment Variable:
   - `VITE_API_URL` = `https://your-backend.onrender.com`
8. Deploy

**Cost:** FREE
**Time to Deploy:** 10 minutes
**Uptime:** Excellent (Vercel has no cold starts for frontend)

---

### Option 3: Railway.app

**Best for:** All-in-one, modern developer experience

#### Steps:
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. New Project → Deploy from GitHub repo
4. Railway auto-detects Python and Node.js
5. Add two services:
   - **Backend**: Root directory = `backend`, Start command = `uvicorn main_weather:app --host 0.0.0.0 --port $PORT`
   - **Frontend**: Root directory = `frontend`, Build = `npm run build`, Serve with static hosting

**Cost:** $5 free credit (lasts ~2 weeks)
**Time to Deploy:** 10 minutes

---

### Option 4: DigitalOcean App Platform

**Best for:** Production deployment, student credits

#### Prerequisites:
- Apply for [GitHub Student Developer Pack](https://education.github.com/pack) ($200 DigitalOcean credit)

#### Steps:
1. Go to [DigitalOcean](https://www.digitalocean.com)
2. Apps → Create App
3. Connect GitHub repository
4. Configure:
   - **Backend Component:**
     - Type: Web Service
     - Build: `pip install -r backend/requirements.txt`
     - Run: `cd backend && uvicorn main_weather:app --host 0.0.0.0 --port 8080`
   - **Frontend Component:**
     - Type: Static Site
     - Build: `cd frontend && npm install && npm run build`
     - Output: `frontend/dist`

**Cost:** ~$12/month (FREE with student credits)
**Time to Deploy:** 15 minutes

---

## Local Testing Before Deployment

### Test Backend:
```bash
cd backend
python main_weather.py
# Visit http://localhost:8000/health
```

### Test Frontend:
```bash
cd frontend
npm run build
npm run preview
# Visit http://localhost:4173
```

---

## Environment Variables Needed

### Backend:
- `PORT` (auto-set by hosting platforms)
- `PYTHON_VERSION=3.11`

### Frontend:
- `VITE_API_URL` (set to your backend URL)

---

## Post-Deployment Checklist

- [ ] Backend health check works: `/health` endpoint returns 200
- [ ] Frontend loads without errors
- [ ] API calls work (check browser console)
- [ ] Map displays correctly
- [ ] Weather scenarios load
- [ ] Custom weather inputs work
- [ ] Charts render properly

---

## Troubleshooting

### Backend Issues:
- **Cold starts:** First request may take 30s on free tier
- **CORS errors:** Check `main_weather.py` allows frontend origin
- **Module not found:** Verify `requirements.txt` is complete

### Frontend Issues:
- **API errors:** Check `VITE_API_URL` environment variable
- **Blank page:** Check browser console for errors
- **Map not loading:** Verify Leaflet CSS is imported

### Common Fixes:
```bash
# Update CORS in backend/main_weather.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-url.vercel.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Demo URLs (Update After Deployment)

- **Frontend:** https://____________________
- **Backend API:** https://____________________
- **API Docs:** https://____________________/docs
- **GitHub Repo:** https://____________________

---

## Recommended for Hackathon Judges

**Best Setup:**
- **Frontend:** Vercel (instant loading, no cold starts)
- **Backend:** Render (free, reliable)

This gives judges the best experience with minimal loading time!
