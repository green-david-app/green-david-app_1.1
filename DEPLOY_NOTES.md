# POZNÁMKY K DEPLOYI NA RENDER

## ✅ OPRAVENO

### 1. Databázová cesta
- **PŘED**: Kontrolovalo `/persistent` a `/data`
- **PO**: Prioritně kontroluje `/var/data` (tvůj Render persistent disk)
- **Soubor**: `main.py`, řádky 11-27

### 2. Načítání Tasks a Issues z API
- **PŘED**: `loadOps()` vracela prázdné `todos: []`
- **PO**: `loadOps()` je async a načítá data z `/api/tasks` a `/api/issues`
- **Soubor**: `jobs.html`

### 3. Ukládání Issues přes API
- **PŘED**: `addProblem()` ukládala jen do localStorage
- **PO**: `addProblem()` volá `POST /api/issues`
- **Soubor**: `jobs.html`

### 4. Ukládání Tasks přes API
- **PŘED**: `addTodo()` ukládala do localStorage + "best-effort" API
- **PO**: `addTodo()` volá `POST /api/tasks` a čeká na odpověď
- **Soubor**: `jobs.html`

### 5. Všechny operace jsou async
- `renderOperativa()` - async, čeká na loadOps()
- `addProblem()`, `resolveProblem()`, `deleteProblem()` - async
- `addTodo()`, `completeTodo()`, `toggleTodo()`, `deleteTodo()` - async

## 🚀 JAK NASADIT

1. **Nahraj upravené soubory na GitHub**:
   ```bash
   git add main.py jobs.html
   git commit -m "Fix: Load data from /var/data persistent disk + API sync"
   git push origin main
   ```

2. **Render automaticky deployuje** z GitHubu

3. **Zkontroluj v Logs**, že vidíš:
   ```
   [DB] Using database: /var/data/app.db
   ```

## 📊 CO SE NAČÍTÁ Z API

- **Jobs**: `/api/jobs` - zakázky
- **Employees**: `/api/employees` - zaměstnanci  
- **Tasks**: `/api/tasks?job_id=X` - úkoly pro zakázku
- **Issues**: `/api/issues?job_id=X` - problémy pro zakázku

## ⚠️ DŮLEŽITÉ

- Data jsou nyní **persistentní** v `/var/data/app.db`
- **Nemazat** Render persistent disk, jinak ztratíš data!
- localStorage se už **nepoužívá** pro tasks a issues
