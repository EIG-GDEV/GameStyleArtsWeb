import sqlite3
from flask import g

DATABASE = 'leads.db'

def get_db():
    """Veritabanına bağlanır; satırlara sütun adıyla erişim sağlar"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db(app):
    """'leads' tablosunu oluşturur (yoksa)"""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isim TEXT NOT NULL,
                email TEXT NOT NULL,
                mesaj TEXT,
                tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

def lead_ekle(isim, email, mesaj=""):
    """Yeni kayıt ekler"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute(
        'INSERT INTO leads (isim, email, mesaj) VALUES (?, ?, ?)',
        (isim, email, mesaj)
    )
    db.commit()
    return cursor.lastrowid

def tum_leadler():
    """Tüm kayıtları en yeniden eskiye getirir"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM leads ORDER BY id DESC')
    return [dict(row) for row in cursor.fetchall()]