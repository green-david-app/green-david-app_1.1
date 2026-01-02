# Render Setup - Persistent Database

## Problém
Na Renderu se souborový systém resetuje při každém restartu, takže databáze `app.db` se ztratí.

## Řešení

### Možnost 1: Nastavit Environment Variable (Doporučeno)

V Render Dashboard:
1. Jdi do svého Web Service
2. Klikni na "Environment"
3. Přidej novou proměnnou:
   - **Key**: `DB_PATH`
   - **Value**: `/tmp/app.db` (nebo jiná cesta)

**Poznámka**: `/tmp` na Renderu je persistent mezi restarty.

### Možnost 2: Použít Persistent Disk

Pokud máte persistent disk připojený:
1. Nastavte `DB_PATH` na cestu k persistent disku (např. `/persistent/app.db`)
2. Ujistěte se, že adresář existuje

### Možnost 3: Použít PostgreSQL (Pro produkci)

Pro produkční prostředí doporučujeme použít PostgreSQL databázi:
1. Vytvořte PostgreSQL databázi v Render Dashboard
2. Změňte kód, aby používal PostgreSQL místo SQLite

## Aktuální konfigurace

Aplikace automaticky detekuje Render prostředí a použije `/tmp/app.db` pokud není nastavena `DB_PATH` environment variable.

## Ověření

Po nasazení zkontrolujte logy:
- Měli byste vidět, že databáze se vytváří na správné cestě
- Data by se měla zachovat mezi restarty

