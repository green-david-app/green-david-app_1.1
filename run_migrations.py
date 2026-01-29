#!/usr/bin/env python3
import sqlite3

def run_migrations():
    db = sqlite3.connect('app.db')
    
    with open('migrations_attachments.sql', 'r') as f:
        sql = f.read()
    
    db.executescript(sql)
    db.commit()
    db.close()
    
    print('✓ Migrations applied successfully')

if __name__ == '__main__':
    run_migrations()
