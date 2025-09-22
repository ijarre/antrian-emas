#!/usr/bin/env python3
"""Seed ANTAM sites and war times into the database.
Safe to re-run: will not duplicate existing entries (matches by exact name + url).
"""
import sqlite3
from datetime import datetime

DB_PATH = 'bot_control.db'

SITES = [
    ("Bintaro", "https://www.antributikbintaro.com", "07:00"),
    ("Serpong", "https://antributikserpong.com", "07:00"),
    ("Setiabudi", "https://www.antributikemas.com", "07:30"),
    ("Bekasi", "https://www.antributikbekasi.com", "07:30"),
    ("Pulogadung", "http://antrigrahadipta.com/", "15:00"),
    ("TB Simatupang", "https://antrisimatupang.com", "15:00"),
]

def ensure_tables(conn):
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        enabled BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER,
        scheduled_time TEXT NOT NULL,
        duration_minutes INTEGER DEFAULT 15,
        enabled BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (site_id) REFERENCES sites (id)
    )''')
    conn.commit()


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_tables(conn)
    cur = conn.cursor()

    report = []

    for name, url, war_time in SITES:
        # Check or insert site
        cur.execute('SELECT id FROM sites WHERE name = ? AND url = ?', (name, url))
        row = cur.fetchone()
        if row:
            site_id = row['id'] if isinstance(row, sqlite3.Row) else row[0]
            site_status = 'exists'
        else:
            cur.execute('INSERT INTO sites (name, url, enabled) VALUES (?, ?, 1)', (name, url))
            site_id = cur.lastrowid
            site_status = 'created'
        # Check schedule for that war time
        cur.execute('SELECT id FROM schedules WHERE site_id = ? AND scheduled_time = ?', (site_id, war_time))
        sched_row = cur.fetchone()
        if sched_row:
            sched_status = 'schedule exists'
        else:
            cur.execute('INSERT INTO schedules (site_id, scheduled_time, duration_minutes, enabled) VALUES (?, ?, ?, 1)', (site_id, war_time, 15))
            sched_status = 'schedule created'

        report.append({'site': name, 'url': url, 'time': war_time, 'site_status': site_status, 'schedule_status': sched_status})

    conn.commit()
    conn.close()

    # Print summary
    created_sites = sum(1 for r in report if r['site_status'] == 'created')
    created_scheds = sum(1 for r in report if r['schedule_status'] == 'schedule created')
    print(f"Seed complete: {created_sites} new sites, {created_scheds} new schedules")
    for r in report:
        print(f"- {r['site']} ({r['time']}) -> {r['site_status']}, {r['schedule_status']}")

if __name__ == '__main__':
    seed()
