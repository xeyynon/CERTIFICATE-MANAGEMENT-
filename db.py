import sqlite3

def init_db():
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS certificates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            event TEXT NOT NULL,
            cert_path TEXT NOT NULL,
            date_issued TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_certificate(cert_id, name, event, path, date_issued):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('''
        INSERT INTO certificates (id, name, event, cert_path, date_issued)
        VALUES (?, ?, ?, ?, ?)
    ''', (cert_id, name, event, path, date_issued))
    conn.commit()
    conn.close()

def get_certificate(cert_id):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('SELECT * FROM certificates WHERE id = ?', (cert_id,))
    data = c.fetchone()
    conn.close()
    return data
