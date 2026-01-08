# ⚡ QUICK START - GITHUB + RENDER

## 🚀 3 KROKY K DEPLOYI

### 1. GITHUB PUSH
```bash
cd /Users/greendavid/Desktop/green-david-WORK
git add .
git commit -m "Warehouse + Planning + Materials update"
git push origin main
```

### 2. RENDER CONNECT
1. https://render.com → New + → Web Service
2. Connect GitHub repo
3. Create Web Service (použije render.yaml automaticky)

### 3. WAIT & TEST
- Build: ~5 min
- URL: https://your-app.onrender.com
- Login: david@greendavid.cz

---

## ✅ FILES READY

- `.gitignore` - ignores DB backups, cache, Mac files
- `requirements.txt` - Flask 3.0, gunicorn, werkzeug, openpyxl
- `runtime.txt` - Python 3.12.6
- `render.yaml` - Auto-config with persistent disk
- `DEPLOYMENT_GUIDE.md` - Full detailed instructions

---

## 🔄 FUTURE UPDATES

```bash
git add .
git commit -m "Your changes"
git push origin main
# Render auto-deploys! ✅
```

---

## 🆘 HELP

Problem? Read **DEPLOYMENT_GUIDE.md** for:
- Troubleshooting
- Database init
- Environment variables
- Custom domain setup

---

**Your app is ready to go live! 🎉**
