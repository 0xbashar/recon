import sqlite3
from pathlib import Path

_conn = None
_cursor = None

def init(db_path):
    global _conn, _cursor
    _conn = sqlite3.connect(db_path)
    _cursor = _conn.cursor()
    _cursor.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE
        )
    ''')
    _cursor.execute('''
        CREATE TABLE IF NOT EXISTS endpoints (
            id INTEGER PRIMARY KEY,
            path TEXT,
            param TEXT,
            UNIQUE(path, param)
        )
    ''')
    _cursor.execute('''
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY,
            url TEXT,
            param TEXT,
            type TEXT,
            platform TEXT,
            confidence INTEGER,
            details TEXT,
            verified BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    _conn.commit()

def save_urls(urls):
    for url in urls:
        try:
            _cursor.execute("INSERT OR IGNORE INTO urls (url) VALUES (?)", (url,))
        except:
            pass
    _conn.commit()

def save_endpoints(endpoints):
    for path, params in endpoints.items():
        for param in params:
            try:
                _cursor.execute("INSERT OR IGNORE INTO endpoints (path, param) VALUES (?, ?)", (path, param))
            except:
                pass
    _conn.commit()

def save_finding(finding):
    _cursor.execute('''
        INSERT INTO findings (url, param, type, platform, confidence, details, verified)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        finding['url'],
        finding.get('param', ''),
        finding['type'],
        finding.get('platform', ''),
        finding.get('confidence', 50),
        str(finding.get('details', '')),
        finding.get('verified', False)
    ))
    _conn.commit()

def close():
    if _conn:
        _conn.close()
