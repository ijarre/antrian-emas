#!/usr/bin/env python3
"""
ANTAM Bot Control Dashboard
A Flask web app to schedule and monitor your queue registration bots
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file
import sqlite3
import json
from datetime import datetime, timedelta
import threading
import time
import logging
import random
from pathlib import Path
import subprocess
import os
from functools import wraps
import base64
import pytz

app = Flask(__name__, template_folder='templates')
app.secret_key = "your-secret-key-change-this"

# Timezone setup - WIB (UTC+7)
WIB = pytz.timezone('Asia/Jakarta')

# Database setup
DB_PATH = "bot_control.db"
LOGS_DIR = Path("logs")
SCREENSHOTS_DIR = Path("screenshots")

# Create directories
LOGS_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)

class BotController:
    def __init__(self):
        self.init_db()
        self.scheduler_running = False
        self.running_bots = {}  # Track running bot instances {run_id: bot_thread}
        self.start_scheduler()
        
    def init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Sites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Schedules table  
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                scheduled_time TEXT NOT NULL,
                duration_minutes INTEGER DEFAULT 15,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (site_id) REFERENCES sites (id)
            )
        ''')
        
        # Bot runs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_id INTEGER,
                site_name TEXT,
                site_url TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                status TEXT, -- pending, running, success, failed, timeout, cancelled
                attempts INTEGER DEFAULT 0,
                log_file TEXT,
                screenshot_file TEXT,
                error_message TEXT,
                FOREIGN KEY (schedule_id) REFERENCES schedules (id)
            )
        ''')
        
        # User settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                ktp_last_6 TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default data if empty
        cursor.execute("SELECT COUNT(*) FROM sites")
        if cursor.fetchone()[0] == 0:
            default_sites = [
                ("Graha Dipta Main", "http://antrigrahadipta.com"),
                ("Site B Alternative", "http://site-b.com"),
                ("Site C Backup", "http://site-c.com")
            ]
            cursor.executemany("INSERT INTO sites (name, url) VALUES (?, ?)", default_sites)
            
        conn.commit()
        conn.close()
        
    def get_db_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
        
    def start_scheduler(self):
        """Start background scheduler thread"""
        if not self.scheduler_running:
            self.scheduler_running = True
            scheduler_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
            scheduler_thread.start()
            
    def scheduler_loop(self):
        """Main scheduler loop - adaptive checking"""
        while self.scheduler_running:
            try:
                # Check if we have any schedules that need checking
                conn = self.get_db_connection()
                active_schedules = conn.execute(
                    "SELECT COUNT(*) FROM schedules WHERE enabled = 1"
                ).fetchone()[0]
                conn.close()
                
                if active_schedules > 0:
                    self.check_and_run_scheduled_bots()
                    sleep_time = 60  # Check every minute when active schedules exist
                else:
                    sleep_time = 300  # Check every 5 minutes when no schedules
                    
            except Exception as e:
                logging.error(f"Scheduler error: {e}")
                sleep_time = 60
                
            time.sleep(sleep_time)
            
    def check_and_run_scheduled_bots(self):
        """Check for bots that should run now"""
        conn = self.get_db_connection()
        # Use WIB timezone for scheduling
        now = datetime.now(WIB)
        current_time = now.strftime("%H:%M")
        
        # Find schedules that should run now
        query = '''
            SELECT s.*, st.name as site_name, st.url as site_url
            FROM schedules s
            JOIN sites st ON s.site_id = st.id
            WHERE s.enabled = 1 AND st.enabled = 1 AND s.scheduled_time = ?
        '''
        
        schedules = conn.execute(query, (current_time,)).fetchall()
        
        for schedule in schedules:
            # Check if already running today
            today = now.strftime("%Y-%m-%d")
            existing_run = conn.execute('''
                SELECT id FROM bot_runs
                WHERE schedule_id = ? AND date(start_time) = ?
                AND status IN ('running', 'success')
            ''', (schedule['id'], today)).fetchone()
            
            if not existing_run:
                self.start_bot_run(schedule)
                
        conn.close()
        
    def start_bot_run(self, schedule):
        """Start a bot run for a schedule"""
        conn = self.get_db_connection()
        
        # Create bot run record
        run_id = conn.execute('''
            INSERT INTO bot_runs (schedule_id, site_name, site_url, start_time, status)
            VALUES (?, ?, ?, ?, 'running')
        ''', (schedule['id'], schedule['site_name'], schedule['site_url'], datetime.now(WIB))).lastrowid
        
        conn.commit()
        conn.close()
        
        # Start bot in separate thread
        bot_thread = threading.Thread(
            target=self.run_bot_instance,
            args=(run_id, schedule),
            daemon=True
        )
        bot_thread.start()

        # Track the running bot
        self.running_bots[run_id] = {
            'thread': bot_thread,
            'bot_instance': None,  # Will be set in run_bot_instance
            'cancelled': False
        }
        
    def run_bot_instance(self, run_id, schedule):
        """Run the actual bot instance"""
        try:
            from antam_bot import ANTAMQueueBot
            
            # Get user settings
            conn = self.get_db_connection()
            user_settings = conn.execute("SELECT * FROM user_settings WHERE id = 1").fetchone()
            
            if not user_settings:
                self.update_bot_run(run_id, 'failed', error_message='No user settings configured')
                return
                
            # Configure bot
            site_config = {
                'name': schedule['site_name'],
                'url': schedule['site_url']
            }
            
            bot = ANTAMQueueBot()
            bot.user_data = {
                'name': user_settings['name'],
                'ktp': user_settings['ktp_last_6'],
                'phone': user_settings['phone_number']
            }

            # Store bot instance for potential cancellation
            if run_id in self.running_bots:
                self.running_bots[run_id]['bot_instance'] = bot
            
            # Run bot
            start_time = datetime.now(WIB)
            success = False
            attempt_count = 0

            end_time = start_time + timedelta(minutes=schedule['duration_minutes'])
            
            while datetime.now(WIB) < end_time and not success:
                # Check if cancelled
                if run_id in self.running_bots and self.running_bots[run_id]['cancelled']:
                    self.update_bot_run(run_id, 'cancelled', end_time=datetime.now(WIB), attempts=attempt_count)
                    bot.cleanup()
                    self.disable_schedule_after_run(schedule['id'])
                    self.running_bots.pop(run_id, None)
                    return

                attempt_count += 1
                self.update_bot_run(run_id, 'running', attempts=attempt_count)

                if bot.fill_form(schedule['site_url']):
                    success = True
                    break

                time.sleep(random.uniform(3, 8))
                
            # Update final status
            final_status = 'success' if success else 'timeout'
            self.update_bot_run(
                run_id,
                final_status,
                end_time=datetime.now(WIB),
                attempts=attempt_count
            )

            # Auto-disable schedule after first run (one-time behavior)
            self.disable_schedule_after_run(schedule['id'])

            bot.cleanup()

            # Remove from running bots tracking
            self.running_bots.pop(run_id, None)
            
        except Exception as e:
            self.update_bot_run(run_id, 'failed', error_message=str(e))
            # Auto-disable schedule even if failed (one-time behavior)
            self.disable_schedule_after_run(schedule['id'])
            # Remove from running bots tracking
            self.running_bots.pop(run_id, None)
            
    def update_bot_run(self, run_id, status, end_time=None, attempts=None, error_message=None):
        """Update bot run status"""
        conn = self.get_db_connection()
        
        updates = ['status = ?']
        params = [status]
        
        if end_time:
            updates.append('end_time = ?')
            params.append(end_time)
            
        if attempts is not None:
            updates.append('attempts = ?')
            params.append(attempts)
            
        if error_message:
            updates.append('error_message = ?')
            params.append(error_message)
            
        params.append(run_id)
        
        query = f"UPDATE bot_runs SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, params)
        conn.commit()
        conn.close()

    def disable_schedule_after_run(self, schedule_id):
        """Disable schedule after it runs once (one-time behavior)"""
        try:
            conn = self.get_db_connection()
            conn.execute("UPDATE schedules SET enabled = 0 WHERE id = ?", (schedule_id,))
            conn.commit()
            conn.close()
            logging.info(f"Schedule {schedule_id} disabled after one-time run")
        except Exception as e:
            logging.error(f"Error disabling schedule {schedule_id}: {e}")

    def cancel_bot_run(self, run_id):
        """Cancel a running bot instance"""
        if run_id in self.running_bots:
            try:
                # Mark as cancelled
                self.running_bots[run_id]['cancelled'] = True

                # Try to cleanup bot instance if available
                bot_instance = self.running_bots[run_id]['bot_instance']
                if bot_instance:
                    bot_instance.cleanup()

                logging.info(f"Bot run {run_id} marked for cancellation")
                return True
            except Exception as e:
                logging.error(f"Error cancelling bot run {run_id}: {e}")
                return False
        return False

    def clear_all_running_bots(self):
        """Clear all running bot instances and update database"""
        try:
            # Cancel all running bots
            cancelled_count = 0
            for run_id in list(self.running_bots.keys()):
                if self.cancel_bot_run(run_id):
                    cancelled_count += 1

            # Update all hanging runs in database
            conn = self.get_db_connection()
            conn.execute('''
                UPDATE bot_runs
                SET status = 'cancelled', end_time = CURRENT_TIMESTAMP
                WHERE status = 'running'
            ''')
            db_updated = conn.total_changes
            conn.commit()
            conn.close()

            # Clear the running bots dictionary
            self.running_bots.clear()

            logging.info(f"Cleared {cancelled_count} running bots and updated {db_updated} database records")
            return cancelled_count, db_updated
        except Exception as e:
            logging.error(f"Error clearing running bots: {e}")
            return 0, 0

# Simple auth decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != 'admin' or auth.password != 'admin':
            return ('Authentication required', 401, {
                'WWW-Authenticate': 'Basic realm="Screenshots"'
            })
        return f(*args, **kwargs)
    return decorated_function

# Initialize controller
controller = BotController()

@app.route('/')
def dashboard():
    """Main dashboard"""
    conn = controller.get_db_connection()
    
    # Get recent bot runs
    recent_runs = conn.execute('''
        SELECT * FROM bot_runs 
        ORDER BY start_time DESC 
        LIMIT 10
    ''').fetchall()
    
    # Get active schedules
    schedules = conn.execute('''
        SELECT s.*, st.name as site_name
        FROM schedules s
        JOIN sites st ON s.site_id = st.id
        WHERE s.enabled = 1
        ORDER BY s.scheduled_time
    ''').fetchall()
    
    # Get stats (using WIB timezone)
    today = datetime.now(WIB).strftime("%Y-%m-%d")
    stats = {
        'total_runs_today': conn.execute(
            "SELECT COUNT(*) FROM bot_runs WHERE date(start_time) = ?", (today,)
        ).fetchone()[0],
        'successful_today': conn.execute(
            "SELECT COUNT(*) FROM bot_runs WHERE date(start_time) = ? AND status = 'success'", (today,)
        ).fetchone()[0],
        'active_schedules': len(schedules)
    }
    
    conn.close()
    
    return render_template('dashboard.html', 
                         recent_runs=recent_runs, 
                         schedules=schedules,
                         stats=stats)


@app.route('/schedules')
def schedules():
    """View schedules"""
    conn = controller.get_db_connection()

    schedules = conn.execute('''
        SELECT s.*, st.name as site_name
        FROM schedules s
        JOIN sites st ON s.site_id = st.id
        ORDER BY s.scheduled_time
    ''').fetchall()

    conn.close()
    return render_template('schedules.html', schedules=schedules)

@app.route('/schedules/toggle/<int:schedule_id>', methods=['POST'])
def toggle_schedule(schedule_id):
    """Toggle schedule enabled/disabled status"""
    try:
        conn = controller.get_db_connection()

        # Get current status
        schedule = conn.execute("SELECT enabled FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
        if schedule:
            new_status = 0 if schedule['enabled'] else 1
            conn.execute("UPDATE schedules SET enabled = ? WHERE id = ?", (new_status, schedule_id))
            conn.commit()

            status_text = "enabled" if new_status else "disabled"
            flash(f'Schedule {status_text} successfully!', 'success')
        else:
            flash('Schedule not found!', 'error')

        conn.close()
    except Exception as e:
        flash(f'Error toggling schedule status: {str(e)}', 'error')

    return redirect(url_for('schedules'))

@app.route('/schedules/delete/<int:schedule_id>', methods=['POST'])
def delete_schedule(schedule_id):
    """Delete schedule"""
    try:
        conn = controller.get_db_connection()

        # Delete the schedule
        conn.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
        conn.commit()
        conn.close()
        flash('Schedule deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting schedule: {str(e)}', 'error')

    return redirect(url_for('schedules'))

@app.route('/add-task')
def add_task():
    """Show combined site and schedule creation form"""
    return render_template('add_task.html')

@app.route('/add-task', methods=['POST'])
def create_task():
    """Create site and schedule in one action"""
    site_name = request.form['site_name']
    site_url = request.form['site_url']
    scheduled_time = request.form['scheduled_time']
    duration = request.form.get('duration', 15, type=int)

    try:
        conn = controller.get_db_connection()

        # Create site first
        site_id = conn.execute(
            "INSERT INTO sites (name, url) VALUES (?, ?)",
            (site_name, site_url)
        ).lastrowid

        # Create schedule for the site (enabled by default, will auto-disable after first run)
        conn.execute('''
            INSERT INTO schedules (site_id, scheduled_time, duration_minutes, enabled)
            VALUES (?, ?, ?, 1)
        ''', (site_id, scheduled_time, duration))

        conn.commit()
        conn.close()

        flash(f'Task "{site_name}" created successfully! It will run once at {scheduled_time} and then disable automatically.', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'Error creating task: {str(e)}', 'error')
        return redirect(url_for('add_task'))

@app.route('/settings')
def settings():
    """User settings"""
    conn = controller.get_db_connection()
    user_settings = conn.execute("SELECT * FROM user_settings WHERE id = 1").fetchone()
    conn.close()
    return render_template('settings.html', settings=user_settings)

@app.route('/settings/save', methods=['POST'])
def save_settings():
    """Save user settings"""
    name = request.form['name']
    ktp = request.form['ktp_last_6']
    phone = request.form['phone_number']
    
    conn = controller.get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO user_settings (id, name, ktp_last_6, phone_number, updated_at)
        VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (name, ktp, phone))
    conn.commit()
    conn.close()
    
    return redirect(url_for('settings'))

@app.route('/api/runs/recent')
def api_recent_runs():
    """API endpoint for recent runs"""
    conn = controller.get_db_connection()
    runs = conn.execute('''
        SELECT * FROM bot_runs 
        ORDER BY start_time DESC 
        LIMIT 20
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(run) for run in runs])

@app.route('/run-now/<int:schedule_id>')
def run_now(schedule_id):
    """Manually trigger a schedule"""
    conn = controller.get_db_connection()
    schedule = conn.execute('''
        SELECT s.*, st.name as site_name, st.url as site_url
        FROM schedules s
        JOIN sites st ON s.site_id = st.id
        WHERE s.id = ?
    ''', (schedule_id,)).fetchone()

    if schedule:
        controller.start_bot_run(schedule)

    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/cancel-run/<int:run_id>', methods=['POST'])
def cancel_run(run_id):
    """Cancel a running bot instance"""
    try:
        if controller.cancel_bot_run(run_id):
            flash('Bot run cancelled successfully!', 'success')
        else:
            flash('Unable to cancel bot run (may have already finished)', 'warning')
    except Exception as e:
        flash(f'Error cancelling bot run: {str(e)}', 'error')

    return redirect(url_for('dashboard'))

@app.route('/clear-all-bots', methods=['POST'])
def clear_all_bots():
    """Clear all running bot instances"""
    try:
        cancelled_count, db_updated = controller.clear_all_running_bots()
        if cancelled_count > 0 or db_updated > 0:
            flash(f'Cleared {cancelled_count} running bots and updated {db_updated} database records', 'success')
        else:
            flash('No running bots found to clear', 'warning')
    except Exception as e:
        flash(f'Error clearing bots: {str(e)}', 'error')

    return redirect(url_for('dashboard'))

@app.route('/debug/screenshots')
@require_auth
def screenshots():
    """View screenshots (admin only)"""
    try:
        screenshots_list = []
        for img_file in SCREENSHOTS_DIR.glob('*.png'):
            stat = img_file.stat()
            # Convert to WIB timezone for display
            modified_time = datetime.fromtimestamp(stat.st_mtime, WIB)
            screenshots_list.append({
                'filename': img_file.name,
                'size': f"{stat.st_size / 1024:.1f} KB",
                'modified': modified_time.strftime('%Y-%m-%d %H:%M:%S WIB')
            })

        # Sort by modification time (newest first)
        screenshots_list.sort(key=lambda x: x['modified'], reverse=True)

        return render_template('screenshots.html', screenshots=screenshots_list)
    except Exception as e:
        flash(f'Error loading screenshots: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/debug/screenshots/<filename>')
@require_auth
def view_screenshot(filename):
    """Serve screenshot file (admin only)"""
    try:
        img_path = SCREENSHOTS_DIR / filename
        if img_path.exists() and img_path.suffix.lower() == '.png':
            return send_file(img_path, mimetype='image/png')
        else:
            return "Screenshot not found", 404
    except Exception as e:
        return f"Error loading screenshot: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)