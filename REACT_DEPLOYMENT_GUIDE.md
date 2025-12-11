# React Standalone Deployment Setup

**Completed:** December 10, 2025

---

## ✅ What Was Done

### 1. **Removed Node.js Development Dependencies**
   - ❌ Removed `proxy` setting from `package.json` (was proxying to Django)
   - ❌ Removed dependency on npm dev server for frontend

### 2. **Built React as Static Production Application**
   - ✅ Created optimized production build (`npm run build`)
   - ✅ Build size: ~70KB gzipped
   - ✅ Static files ready for deployment

### 3. **Integrated React with Django**
   - ✅ Configured Django to serve React's `index.html` as main template
   - ✅ Added `labhub/templates/` directory to Django's TEMPLATES
   - ✅ Created URL route to serve React app on `/`

### 4. **Updated API Calls**
   - ✅ Changed from relative URLs (`/pipeline/...`) to absolute URLs (`http://localhost:8000/pipeline/...`)
   - ✅ Updated both endpoints: `/recordings/` and `/pipelines/`

### 5. **Automated Build Deployment**
   - ✅ Added `build-django` script to package.json that auto-copies build to Django

---

## 📁 New Architecture

### Before (Node.js + Django)
```
React Dev Server (localhost:3000)
    ↓ proxy
Django API (localhost:8000)
```

### After (Django serves both)
```
Django Server (localhost:8000)
├─ Static Files (React app)
├─ API Endpoints (/qmodel/, /pipeline/)
└─ Templates (index.html)
```

---

## 🚀 How to Use

### Development Workflow

**Option 1: Develop with Django + Built React (Recommended)**
```bash
# Build React once (copies to Django automatically)
cd my-app
npm run build-django

# Start Django server
cd ..
python manage.py runserver

# Visit http://localhost:8000
# React app is served from Django
```

**Option 2: Development with npm (React dev server)**
```bash
# Start npm dev server (if you want hot reload during dev)
cd my-app
npm start

# In another terminal, start Django
cd ..
python manage.py runserver

# Visit http://localhost:3000 for React dev server
# Note: API calls will go to http://localhost:8000
```

**Option 3: Production Deployment**
```bash
# Build React and copy to Django
cd my-app
npm run build-django

# Collect Django static files
cd ..
python manage.py collectstatic --noinput

# Run Django with gunicorn
gunicorn labhub.wsgi:application --bind 0.0.0.0:8000
```

---

## 📝 Files Changed

### 1. `labhub/settings.py`
```python
# Added labhub/templates to Django's TEMPLATES dirs
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "labhub" / "templates"],  # ← Added this
        ...
    }
]
```

### 2. `labhub/urls.py`
```python
# Added route to serve React app
from django.views.generic import TemplateView

urlpatterns = [
    ...
    path("", TemplateView.as_view(template_name="index.html"), name="react-app"),  # ← Added
]
```

### 3. `my-app/package.json`
```json
{
  "scripts": {
    "build": "react-scripts build && cp -r build/* ../labhub/templates/",
    "build-django": "react-scripts build && cp -r build/* ../labhub/templates/"
  }
  // Removed: "proxy": "http://127.0.0.1:8000"
}
```

### 4. `my-app/src/App.js`
```javascript
// Changed from:
const API_BASE = '/pipeline';

// To:
const API_BASE = 'http://localhost:8000/pipeline';
```

---

## 🗂️ Folder Structure After Setup

```
labhub/
├── settings.py          # Django config (updated)
├── urls.py              # Django routing (updated)
├── templates/           # ← React build files copied here
│   ├── index.html       # Main React app entry
│   ├── favicon.ico
│   ├── manifest.json
│   └── static/
│       ├── js/
│       │   ├── main.8aa70f1a.js    # Bundled React
│       │   └── 453.96453769.chunk.js
│       └── css/
│           └── main.e6c13ad2.css
└── __init__.py

my-app/
├── src/
│   └── App.js          # Updated with absolute URLs
├── build/              # Production build output
│   ├── index.html
│   ├── static/
│   └── ...
└── package.json        # Updated scripts
```

---

## ✅ Verification Checklist

```bash
# 1. Verify Django config
python manage.py check

# 2. Test Django server
python manage.py runserver

# 3. Visit http://localhost:8000 in browser
# You should see the React app with:
# - Home page with "New Pipeline" and "Submit Pipeline" buttons
# - Token Control panel in top-right
# - Blue gradient background
```

---

## 🔑 Key Changes Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Frontend Server** | npm dev server (Node.js) | Django static files |
| **Port** | 3000 (React) + 8000 (API) | 8000 (both) |
| **API Calls** | Relative URLs with proxy | Absolute URLs |
| **Deployment** | 2 servers needed | 1 server (Django) |
| **Build Step** | `npm start` | `npm run build-django` |
| **Node.js Dependency** | ✅ Required | ❌ Dev-only (optional) |

---

## 🚀 Deployment Guide

### Local Development
```bash
# 1. Build React
cd my-app
npm run build-django

# 2. Run Django
cd ..
python manage.py runserver

# 3. Open http://localhost:8000
```

### Production (using gunicorn + nginx)

**Step 1: Build React**
```bash
cd my-app
npm run build-django
```

**Step 2: Collect static files**
```bash
cd ..
python manage.py collectstatic --noinput
```

**Step 3: Run with gunicorn**
```bash
pip install gunicorn
gunicorn labhub.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120
```

**Step 4: Nginx config (reverse proxy)**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/staticfiles/;
    }
}
```

---

## 🔄 Updating React App

When you make changes to React code:

```bash
# 1. Make changes to src/App.js or components
# 2. Rebuild and copy to Django
cd my-app
npm run build-django

# 3. Restart Django
cd ..
python manage.py runserver
```

Or use the simpler command:
```bash
cd my-app && npm run build-django && cd .. && python manage.py runserver
```

---

## 🐛 Troubleshooting

### Issue: React app shows 404
**Solution:** Make sure Django templates path is correct
```bash
python manage.py check  # Should show "System check identified no issues"
```

### Issue: API calls fail (CORS)
**Solution:** Update the API_BASE URL to match your Django server
```javascript
// In App.js
const API_BASE = 'http://your-django-domain.com/pipeline';
```

### Issue: Static files not loading
**Solution:** Collect static files
```bash
python manage.py collectstatic --noinput
```

### Issue: Need hot-reload during development
**Solution:** Use npm dev server instead
```bash
cd my-app
npm start

# In another terminal:
cd ..
python manage.py runserver
# Visit http://localhost:3000 instead of 8000
```

---

## 📊 Benefits of This Setup

✅ **Single Server:** One Django instance serves both frontend + API  
✅ **Production Ready:** Optimized React build with minified code  
✅ **No Node.js in Production:** Only needed for development builds  
✅ **Simplified Deployment:** No npm/Node.js runtime required in production  
✅ **Better Security:** Single origin for CORS (no cross-origin requests)  
✅ **Smaller Docker Image:** No Node.js runtime needed  
✅ **Standard Django Setup:** Uses Django's built-in static file serving  

---

## 📚 Related Documentation

- `DEVELOPMENT_GUIDE.md` - Complete technical reference
- `PROJECT_SUMMARY.md` - Project overview
- `README.md` - General project info

---

**Status:** ✅ React integrated with Django  
**Build Size:** 70KB gzipped  
**Servers Needed:** 1 (Django)  
**Next Step:** Run `python manage.py runserver` and visit `http://localhost:8000`
