# 🚀 DEPLOYMENT GUIDE - GITHUB + RENDER

## ✅ PŘIPRAVENO K NAHRÁNÍ!

Všechny deployment soubory jsou ready:
- ✅ `.gitignore` - ignoruje DB backups, cache, Mac files
- ✅ `requirements.txt` - Flask 3.0, gunicorn, werkzeug, openpyxl
- ✅ `runtime.txt` - Python 3.12.6
- ✅ `render.yaml` - Render config s persistent disk

---

## 📦 GITHUB UPLOAD - KROK ZA KROKEM

### 1️⃣ PŘIPRAV GIT REPO (pokud ještě nemáš)

```bash
cd /Users/greendavid/Desktop/green-david-WORK

# Inicializuj Git (pokud nemáš)
git init

# Přidej remote (pokud nemáš)
git remote add origin https://github.com/tvoje-username/green-david-app.git
```

### 2️⃣ COMMIT & PUSH

```bash
# Stage všechno
git add .

# Commit s popisem
git commit -m "Warehouse update + Planning module + Materials system"

# Push na GitHub
git push origin main
```

**NEBO ALTERNATIVNĚ - GitHub Desktop:**
1. Otevři GitHub Desktop
2. Vyber "green-david-WORK" repo
3. Uvidíš changes
4. Napiš commit message: "Warehouse + Planning modules"
5. Klikni "Commit to main"
6. Klikni "Push origin"

---

## 🌐 RENDER DEPLOYMENT

### 1️⃣ CONNECT GITHUB REPO

1. Přihlas se na **https://render.com**
2. Klikni **"New +"** → **"Web Service"**
3. Connect tvůj GitHub repo: `green-david-app`
4. Render najde `render.yaml` automaticky ✅

### 2️⃣ CONFIGURE

Render použije `render.yaml` config:
- ✅ **Runtime:** Python 3.12.6
- ✅ **Build:** `pip install -r requirements.txt`
- ✅ **Start:** `gunicorn main:app`
- ✅ **Persistent Disk:** 1GB pro database

### 3️⃣ DEPLOY

1. Klikni **"Create Web Service"**
2. Render začne deployment (5-10 min)
3. Status: Building → Deploying → Live ✅

### 4️⃣ DATABASE INIT (PRVNÍ DEPLOY)

Po prvním deployi musíš inicializovat DB:

```bash
# V Render Shell (Dashboard → Shell)
python3 run_extended_migration.py
```

Nebo nahraj `app.db` přes Render Dashboard → Files.

---

## 🔧 PO DEPLOYI - TEST

### ✅ Check List:

1. **Homepage** → https://your-app.onrender.com/
   - ✅ Zobrazí login

2. **Login** → `david@greendavid.cz` / tvoje heslo
   - ✅ Přihlásí se

3. **Warehouse** → `/warehouse`
   - ✅ Stats cards
   - ✅ Položky se načtou
   - ✅ +/- tlačítka fungují
   - ✅ Edit funguje

4. **Planning** → `/planning/timeline`
   - ✅ Zobrazí timeline
   - ✅ Nursery funguje
   - ✅ Materials tracking funguje

---

## 🆘 TROUBLESHOOTING

### Problem: "ModuleNotFoundError"
**Fix:** Check `requirements.txt` má všechny packages

### Problem: "Database locked"
**Fix:** Render používá persistent disk - restart service

### Problem: "502 Bad Gateway"
**Fix:** Check Render logs: Dashboard → Logs

### Problem: "Permission denied"
**Fix:** Check main.py má `app.run()` s `host='0.0.0.0'`

---

## 🔄 UPDATE WORKFLOW

**Když děláš změny v budoucnu:**

```bash
# 1. Změň kód lokálně
# 2. Test lokálně: python3 main.py
# 3. Commit
git add .
git commit -m "Fix XYZ"

# 4. Push
git push origin main

# 5. Render auto-deploy! ✅
```

Render automaticky detekuje push a re-deployuje!

---

## 📊 RENDER FEATURES

- ✅ **Auto-deploy** z GitHub
- ✅ **Persistent disk** pro database
- ✅ **HTTPS** automaticky
- ✅ **Custom domain** možné
- ✅ **Environment variables** v dashboard
- ✅ **Logs** real-time
- ✅ **Shell access** pro debugging

---

## 🎉 HOTOVO!

**Po deployi máš:**
- 🌐 Live app na `https://your-app.onrender.com`
- 🔄 Auto-deploy z GitHub
- 💾 Persistent database
- 🔒 HTTPS secured
- 📊 Professional hosting

**Užij si svou app online!** 🚀
