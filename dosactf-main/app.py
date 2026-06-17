from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
from functools import wraps
import re
import os
from dotenv import load_dotenv
from datetime import timedelta, datetime
import smtplib
from email.message import EmailMessage
import random
import string

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dosa-ctf-ultra-secret-2025-change-me')

# Register Blueprints
from admin import admin_bp
app.register_blueprint(admin_bp)

# ─────────────────────────────────────────────
# Supabase PostgreSQL CONNECTION
# ─────────────────────────────────────────────
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    """Get a connection to Supabase PostgreSQL."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set. Please set it in .env file.")
    conn = psycopg2.connect(DATABASE_URL)
    return conn


# ─────────────────────────────────────────────
# DATABASE INITIALISATION (auto-create tables)
# ─────────────────────────────────────────────
def init_db():
    conn = get_db()
    cur  = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id         SERIAL       PRIMARY KEY,
            username   VARCHAR(50)  NOT NULL UNIQUE,
            email      VARCHAR(120) NOT NULL UNIQUE,
            password   VARCHAR(255) NOT NULL,
            role       TEXT         NOT NULL DEFAULT 'player',
            status     TEXT         NOT NULL DEFAULT 'active',
            score      INTEGER      NOT NULL DEFAULT 0,
            avatar     VARCHAR(4)   DEFAULT NULL,
            created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP    DEFAULT NULL
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER,
            ip_address VARCHAR(45),
            success    SMALLINT DEFAULT 0,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS challenges (
            id         SERIAL PRIMARY KEY,
            title      VARCHAR(100) NOT NULL,
            category   VARCHAR(50) NOT NULL,
            difficulty VARCHAR(50) NOT NULL,
            points     INTEGER NOT NULL,
            description TEXT,
            flag       VARCHAR(255) NOT NULL,
            file_url   VARCHAR(255) DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS solves (
            id           SERIAL PRIMARY KEY,
            user_id      INTEGER NOT NULL,
            challenge_id INTEGER NOT NULL,
            solved_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE,
            UNIQUE (user_id, challenge_id)
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS admin_logs (
            id           SERIAL PRIMARY KEY,
            user_id      INTEGER,
            action       TEXT NOT NULL,
            target       TEXT,
            logged_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS hints (
            id           SERIAL PRIMARY KEY,
            challenge_id INTEGER NOT NULL,
            hint_text    TEXT NOT NULL,
            cost         INTEGER DEFAULT 0,
            FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE
        );
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_hints (
            id           SERIAL PRIMARY KEY,
            user_id      INTEGER NOT NULL,
            hint_id      INTEGER NOT NULL,
            unlocked_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (hint_id) REFERENCES hints(id) ON DELETE CASCADE,
            UNIQUE (user_id, hint_id)
        );
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id           SERIAL PRIMARY KEY,
            user_id      INTEGER,
            title        VARCHAR(100),
            message      TEXT NOT NULL,
            is_read      BOOLEAN DEFAULT FALSE,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id           SERIAL PRIMARY KEY,
            user_id      INTEGER,
            action       VARCHAR(100) NOT NULL,
            details      TEXT,
            ip_address   VARCHAR(45),
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS platform_settings (
            id              SERIAL PRIMARY KEY,
            event_name      VARCHAR(100) DEFAULT 'Dosa CTF',
            event_status    VARCHAR(50) DEFAULT 'Active',
            start_date      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date        TIMESTAMP DEFAULT NULL,
            max_team_size   INTEGER DEFAULT 4,
            flag_cooldown   INTEGER DEFAULT 60,
            alert_email     VARCHAR(120) DEFAULT '',
            webhook_url     VARCHAR(255) DEFAULT '',
            auto_backup     VARCHAR(50) DEFAULT 'Daily',
            retention       VARCHAR(50) DEFAULT '30 Days'
        );
    ''')

    # Ensure platform settings exist
    cur.execute('SELECT COUNT(*) FROM platform_settings')
    if cur.fetchone()[0] == 0:
        cur.execute('INSERT INTO platform_settings (id) VALUES (1)')
        
    # Attempt to add online tracking columns
    try:
        cur.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS last_logout TIMESTAMP DEFAULT NULL;')
        cur.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS is_online BOOLEAN DEFAULT FALSE;')
        cur.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_otp VARCHAR(6) DEFAULT NULL;')
        cur.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_otp_expiry TIMESTAMP DEFAULT NULL;')
        conn.commit()
    except Exception:
        conn.rollback()

    # Attempt to add points_earned to solves for Score Persistence
    try:
        cur.execute('ALTER TABLE solves ADD COLUMN IF NOT EXISTS points_earned INTEGER DEFAULT 0;')
        conn.commit()
    except Exception:
        conn.rollback()
        
    # Fix foreign key for solves to ON DELETE SET NULL to preserve points
    try:
        # PostgreSQL syntax to drop and add constraint
        cur.execute('''
            DO $$ 
            DECLARE constraint_name TEXT;
            BEGIN
                SELECT tc.constraint_name INTO constraint_name
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'solves' AND kcu.column_name = 'challenge_id';
                
                IF constraint_name IS NOT NULL THEN
                    EXECUTE 'ALTER TABLE solves DROP CONSTRAINT ' || constraint_name;
                    EXECUTE 'ALTER TABLE solves ADD CONSTRAINT solves_challenge_id_fkey FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE SET NULL';
                END IF;
            END $$;
        ''')
    except Exception:
        conn.rollback()
    
    cur.execute('SELECT COUNT(*) AS c FROM challenges')
    if cur.fetchone()[0] == 0:
        cur.execute('''
            INSERT INTO challenges (title, category, difficulty, points, description, flag)
            VALUES 
            ('Welcome to Dosa CTF', 'Misc', 'Easy', 10, 'Submit the flag `dosa{welcome_to_the_game}` to start.', 'dosa{welcome_to_the_game}'),
            ('SQL Injection 101', 'Web', 'Medium', 50, 'Find the vulnerability in the login page.', 'dosa{sql_is_fun}')
        ''')

    conn.commit()
    cur.close()
    conn.close()
    print("[DB] Tables ready.")

init_db()


@app.before_request
def check_user_status_and_role():
    # Bypass verification for static assets and authentication pages
    bypass_endpoints = ['static', 'login', 'register', 'logout', 'admin.admin_login']
    if request.endpoint in bypass_endpoints:
        return
        
    if 'user_id' in session:
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute('SELECT status, role FROM users WHERE id = %s', (session['user_id'],))
            row = cur.fetchone()
            cur.close()
            conn.close()
            
            if not row:
                session.clear()
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Account no longer exists.'}), 403
                flash('Your account has been deleted.', 'danger')
                return redirect(url_for('login'))
                
            status, role = row[0], row[1]
            if status == 'banned':
                session.clear()
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Your account has been banned. Session terminated.'}), 403
                flash('Your account has been banned. Session terminated.', 'danger')
                return redirect(url_for('login'))
                
            # Keep role synchronized in real-time
            if session.get('role') != role:
                session['role'] = role
                
        except Exception:
            # Prevent blocking operations if database connection is temporarily interrupted
            pass


# ─────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin access only.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

def is_valid_email(email):
    return re.match(r'^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$', email)

def is_valid_username(username):
    return re.match(r'^[a-zA-Z0-9_]{3,20}$', username)

def log_login_attempt(user_id, ip, success):
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            'INSERT INTO login_logs (user_id, ip_address, success) VALUES (%s, %s, %s)',
            (user_id, ip, 1 if success else 0)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass

def log_admin_action(user_id, action, target):
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            'INSERT INTO admin_logs (user_id, action, target) VALUES (%s, %s, %s)',
            (user_id, action, target)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        pass


# ─────────────────────────────────────────────
# ─────────────────────────────────────────────

def send_otp_email(to_email, otp):
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASSWORD')
    if not smtp_user or not smtp_pass:
        print("[SMTP] SMTP_USER or SMTP_PASSWORD not configured.")
        return False
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Dosa CTF - Password Reset OTP'
        msg['From'] = f"Dosa CTF <{smtp_user}>"
        msg['To'] = to_email
        msg.set_content(f"Your OTP for password reset is: {otp}\n\nThis OTP is valid for 15 minutes.")
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(smtp_user, smtp_pass)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"[SMTP] Failed to send email: {e}")
        return False

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            flash('Please enter your email.', 'danger')
        else:
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute('SELECT id FROM users WHERE email = %s', (email,))
                user = cur.fetchone()
                if user:
                    # Generate OTP
                    otp = ''.join(random.choices(string.digits, k=6))
                    expiry = datetime.now() + timedelta(minutes=15)
                    
                    cur.execute('UPDATE users SET reset_otp = %s, reset_otp_expiry = %s WHERE id = %s',
                                (otp, expiry, user[0]))
                    
                    cur.execute('INSERT INTO activity_logs (user_id, action, details, ip_address) VALUES (%s, %s, %s, %s)', 
                                (user[0], 'Password Reset Requested', f'Reset requested for {email}', request.remote_addr))
                    conn.commit()
                    
                    if send_otp_email(email, otp):
                        flash('An OTP has been sent to your email.', 'success')
                        session['reset_email'] = email
                        cur.close()
                        conn.close()
                        return redirect(url_for('verify_otp'))
                    else:
                        flash('Failed to send OTP email. Please try again later.', 'danger')
                else:
                    # Generic message to prevent email enumeration
                    flash('If an account exists with that email, an OTP has been sent.', 'success')
                cur.close()
                conn.close()
            except Exception as e:
                flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('forgot_password'))
    return render_template('accounts/forgot_password.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'reset_email' not in session:
        flash('Please start the password reset process here.', 'warning')
        return redirect(url_for('forgot_password'))
        
    email = session['reset_email']
    
    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        try:
            conn = get_db()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute('SELECT id, reset_otp, reset_otp_expiry FROM users WHERE email = %s', (email,))
            user = cur.fetchone()
            
            if user and user['reset_otp'] == otp:
                if user['reset_otp_expiry'] and user['reset_otp_expiry'] > datetime.now():
                    session['reset_user_id'] = user['id']
                    # clear OTP
                    cur.execute('UPDATE users SET reset_otp = NULL, reset_otp_expiry = NULL WHERE id = %s', (user['id'],))
                    conn.commit()
                    cur.close()
                    conn.close()
                    flash('OTP verified successfully. Please enter your new password.', 'success')
                    return redirect(url_for('reset_password'))
                else:
                    flash('OTP has expired. Please request a new one.', 'danger')
            else:
                flash('Invalid OTP.', 'danger')
                
            cur.close()
            conn.close()
        except Exception:
            flash('An error occurred.', 'danger')
            
    return render_template('accounts/verify_otp.html', email=email)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_user_id' not in session:
        flash('Unauthorized access. Please verify your OTP first.', 'danger')
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
        elif password != confirm:
            flash('Passwords do not match.', 'danger')
        else:
            try:
                hashed = generate_password_hash(password)
                conn = get_db()
                cur = conn.cursor()
                cur.execute('UPDATE users SET password = %s WHERE id = %s', (hashed, session['reset_user_id']))
                conn.commit()
                cur.close()
                conn.close()
                
                # Clear reset session vars
                session.pop('reset_email', None)
                session.pop('reset_user_id', None)
                
                flash('Your password has been successfully reset. You can now log in.', 'success')
                return redirect(url_for('login'))
            except Exception:
                flash('An error occurred. Please try again.', 'danger')
                
    return render_template('accounts/reset_password.html')

# ─────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')

        errors = []

        if not username or not email or not password or not confirm:
            errors.append('All fields are required.')
        if username and not is_valid_username(username):
            errors.append('Username must be 3–20 chars: letters, numbers, underscores only.')
        if email and not is_valid_email(email):
            errors.append('Enter a valid email address.')
        if password and len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('accounts/register.html',
                                   form_username=username,
                                   form_email=email)

        hashed = generate_password_hash(password)
        # first 2 chars of username as avatar initials
        avatar = username[:2].upper()

        try:
            conn = get_db()
            cur  = conn.cursor()
            cur.execute(
                'INSERT INTO users (username, email, password, avatar) VALUES (%s, %s, %s, %s) RETURNING id',
                (username, email, hashed, avatar)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()

            flash(f'Welcome, {username}! Your account is ready. Please log in.', 'success')
            return redirect(url_for('login'))

        except psycopg2.IntegrityError as e:
            err_msg = str(e)
            if 'username' in err_msg:
                flash('That username is already taken.', 'danger')
            elif 'email' in err_msg:
                flash('That email is already registered.', 'danger')
            else:
                flash('Registration failed. Please try again.', 'danger')
            return render_template('accounts/register.html',
                                   form_username=username,
                                   form_email=email)

    return render_template('accounts/register.html', form_username='', form_email='')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('username', '').strip()
        password   = request.form.get('password', '')
        ip         = request.remote_addr

        if not identifier or not password:
            flash('Please enter your username/email and password.', 'danger')
            return render_template('accounts/login.html', form_identifier=identifier)

        try:
            conn = get_db()
            cur  = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                'SELECT * FROM users WHERE username=%s OR email=%s LIMIT 1',
                (identifier, identifier)
            )
            user = cur.fetchone()
            cur.close()
            conn.close()
        except Exception as ex:
            flash('Database error. Please try again.', 'danger')
            return render_template('accounts/login.html', form_identifier=identifier)

        if user and check_password_hash(user['password'], password):
            if user['status'] == 'banned':
                flash('Your account has been banned. Contact support.', 'danger')
                log_login_attempt(user['id'], ip, False)
                return render_template('accounts/login.html', form_identifier=identifier)

            # Update last_login and online status
            try:
                conn = get_db()
                cur  = conn.cursor()
                cur.execute('UPDATE users SET last_login=CURRENT_TIMESTAMP, is_online=TRUE WHERE id=%s', (user['id'],))
                conn.commit()
                cur.close()
                conn.close()
            except Exception:
                pass

            log_login_attempt(user['id'], ip, True)
            session.clear()
            
            if request.form.get('remember') == 'on':
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
                
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['display_name'] = user.get('display_name') or user['username']
            session['role']     = user['role']
            session['avatar']   = user['avatar'] or user['username'][:2].upper()
            session['avatar_style'] = user.get('avatar_style') or 'linear-gradient(135deg, #1a0a3a, var(--blue))'

            flash(f'Welcome back, {user["username"]}! 🎯', 'success')
            next_page = request.args.get('next')
            if user['role'] == 'admin':
                return redirect(next_page or url_for('admin.admin_dashboard'))
            return redirect(next_page or url_for('dashboard'))
        else:
            if user:
                log_login_attempt(user['id'], ip, False)
            flash('Invalid credentials. Check your username/email and password.', 'danger')
            return render_template('accounts/login.html', form_identifier=identifier)

    return render_template('accounts/login.html', form_identifier='')


@app.route('/logout')
def logout():
    name = session.get('username', 'Operative')
    user_id = session.get('user_id')
    
    if user_id:
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute('UPDATE users SET is_online=FALSE, last_logout=CURRENT_TIMESTAMP WHERE id=%s', (user_id,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception:
            pass
            
    session.clear()
    flash(f'Session terminated. Stay safe, {name}.', 'info')
    return redirect(url_for('login'))


@app.route('/user-profile')
@login_required
def user_profile():
    return render_template('accounts/user_profile.html')


@app.route('/user-settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    user_id = session['user_id']
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if request.method == 'POST':
            form_type = request.form.get('form_type')
            
            if form_type == 'avatar':
                avatar = request.form.get('avatar', '').strip()[:2].upper()
                avatar_style = request.form.get('avatar_style', 'linear-gradient(135deg, #1a0a3a, var(--blue))').strip()
                if not avatar:
                    flash('Avatar initials cannot be empty.', 'danger')
                else:
                    cur.execute('UPDATE users SET avatar = %s, avatar_style = %s WHERE id = %s', (avatar, avatar_style, user_id))
                    conn.commit()
                    session['avatar'] = avatar
                    session['avatar_style'] = avatar_style
                    flash('Avatar updated successfully!', 'success')
            elif form_type == 'password':
                current_pwd = request.form.get('current_password', '')
                new_pwd = request.form.get('new_password', '')
                confirm_pwd = request.form.get('confirm_password', '')
                
                cur.execute('SELECT password FROM users WHERE id = %s', (user_id,))
                user_record = cur.fetchone()
                
                if not check_password_hash(user_record['password'], current_pwd):
                    flash('Current password is incorrect.', 'danger')
                elif len(new_pwd) < 8:
                    flash('New password must be at least 8 characters long.', 'danger')
                elif new_pwd != confirm_pwd:
                    flash('New passwords do not match.', 'danger')
                else:
                    hashed = generate_password_hash(new_pwd)
                    cur.execute('UPDATE users SET password = %s WHERE id = %s', (hashed, user_id))
                    conn.commit()
                    flash('Password updated successfully!', 'success')
            else:
                display_name = request.form.get('display_name', '').strip()
                email = request.form.get('email', '').strip()
                
                if not email:
                    flash('Email is required.', 'danger')
                else:
                    cur.execute(
                        'UPDATE users SET display_name = %s, email = %s WHERE id = %s',
                        (display_name, email, user_id)
                    )
                    conn.commit()
                    # Update session
                    session['display_name'] = display_name or session['username']
                    flash('Profile updated successfully!', 'success')
                
        # Fetch current user data
        cur.execute('SELECT username, email, display_name, avatar_style FROM users WHERE id = %s', (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user.get('display_name'):
            user['display_name'] = user['username']
            
        return render_template('accounts/user_settings.html', user=user)
    except Exception as e:
        flash(f"Error updating profile: {e}", 'danger')
        return render_template('accounts/user_settings.html', user={'username': session['username'], 'display_name': session.get('display_name', session['username']), 'email': ''})


# ─────────────────────────────────────────────
# MAIN PAGES
# ─────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('accounts/index.html')

@app.route('/rules')
def rules():
    return render_template('pages/rules.html')

@app.route('/privacy')
def privacy():
    return render_template('pages/privacy.html')


@app.route('/notifications')
@login_required
def notifications():
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC', (session['user_id'],))
        notifs = cur.fetchall()
        cur.execute('UPDATE notifications SET is_read = TRUE WHERE user_id = %s', (session['user_id'],))
        conn.commit()
        cur.close()
        conn.close()
        return render_template('pages/notifications.html', notifications=notifs)
    except Exception as e:
        flash("Error loading notifications.", "danger")
        return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('pages/dashboard.html')


@app.route('/challenges')
@login_required
def challenges():
    user_id = session['user_id']
    score = 0
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT score FROM users WHERE id = %s', (user_id,))
        row = cur.fetchone()
        if row:
            score = row['score']
        cur.close()
        conn.close()
    except Exception:
        pass
    return render_template('pages/challenges.html', current_score=score)


@app.route('/leaderboard')
def leaderboard():
    return render_template('pages/leaderboard.html')




# Admin routes have been migrated to admin.py


# ─────────────────────────────────────────────
# API: check username/email availability (AJAX)
# ─────────────────────────────────────────────

@app.route('/api/check-username')
def check_username():
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'available': False, 'error': 'Empty'})
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute('SELECT id FROM users WHERE username=%s', (username,))
        taken = cur.fetchone() is not None
        cur.close()
        conn.close()
        return jsonify({'available': not taken})
    except Exception:
        return jsonify({'available': None, 'error': 'DB error'})


@app.route('/api/check-email')
def check_email():
    email = request.args.get('email', '').strip().lower()
    if not email:
        return jsonify({'available': False})
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute('SELECT id FROM users WHERE email=%s', (email,))
        taken = cur.fetchone() is not None
        cur.close()
        conn.close()
        return jsonify({'available': not taken})
    except Exception:
        return jsonify({'available': None})


# ─────────────────────────────────────────────
# CHALLENGE API
# ─────────────────────────────────────────────

@app.route('/api/challenges', methods=['GET'])
@login_required
def get_challenges():
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all challenges
        cur.execute('SELECT id, title, category, difficulty, points, description, file_url FROM challenges')
        challenges = cur.fetchall()
        
        # Get solved challenges for this user
        cur.execute('SELECT challenge_id FROM solves WHERE user_id = %s', (session['user_id'],))
        solved_ids = {row['challenge_id'] for row in cur.fetchall()}
        
        cur.close()
        conn.close()
        
        # Add 'solved' status
        for ch in challenges:
            ch['solved'] = ch['id'] in solved_ids
            
        return jsonify({'success': True, 'challenges': challenges})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/challenges/<int:challenge_id>/hints', methods=['GET'])
@login_required
def get_challenge_hints(challenge_id):
    try:
        user_id = session['user_id']
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all hints for this challenge
        cur.execute('SELECT id, cost, hint_text FROM hints WHERE challenge_id = %s ORDER BY id ASC', (challenge_id,))
        hints = cur.fetchall()
        
        # Get which hints the user has unlocked
        cur.execute('SELECT hint_id FROM user_hints WHERE user_id = %s', (user_id,))
        unlocked = {row['hint_id'] for row in cur.fetchall()}
        
        cur.close()
        conn.close()
        
        # Mask text if not unlocked
        result = []
        for i, h in enumerate(hints):
            is_unlocked = h['id'] in unlocked
            result.append({
                'id': h['id'],
                'cost': h['cost'],
                'unlocked': is_unlocked,
                'text': h['hint_text'] if is_unlocked else None,
                'index': i + 1
            })
            
        return jsonify({'success': True, 'hints': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/challenges/hints/unlock', methods=['POST'])
@login_required
def unlock_hint():
    data = request.get_json()
    if not data or 'hint_id' not in data:
        return jsonify({'success': False, 'message': 'Invalid request'})
        
    hint_id = data['hint_id']
    user_id = session['user_id']
    
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verify hint exists and get cost
        cur.execute('SELECT cost, hint_text FROM hints WHERE id = %s', (hint_id,))
        hint = cur.fetchone()
        if not hint:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Hint not found'})
            
        cost = hint['cost']
        
        # Check if already unlocked
        cur.execute('SELECT 1 FROM user_hints WHERE user_id = %s AND hint_id = %s', (user_id, hint_id))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'success': True, 'text': hint['hint_text'], 'message': 'Already unlocked'})
            
        # Get user score
        cur.execute('SELECT score FROM users WHERE id = %s', (user_id,))
        user_row = cur.fetchone()
        current_score = user_row['score']
        
        # Allow unlocking even if score goes negative? The requirement: "the point need to reduce".
        # Usually it shouldn't be blocked, but let's check if current_score < cost
        # We will just deduct it. Or maybe prevent if score < cost? Let's just deduct it.
        
        # Deduct score and record unlock
        cur.execute('UPDATE users SET score = score - %s WHERE id = %s', (cost, user_id))
        cur.execute('INSERT INTO user_hints (user_id, hint_id) VALUES (%s, %s)', (user_id, hint_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'text': hint['hint_text'], 'message': f'Hint unlocked for {cost} points'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/challenges/submit', methods=['POST'])
@login_required
def submit_flag():
    data = request.get_json()
    if not data or 'challenge_id' not in data or 'flag' not in data:
        return jsonify({'success': False, 'message': 'Invalid request'})
        
    challenge_id = data['challenge_id']
    submitted_flag = data['flag'].strip()
    user_id = session['user_id']
    
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if already solved
        cur.execute('SELECT id FROM solves WHERE user_id = %s AND challenge_id = %s', (user_id, challenge_id))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Already solved!'})
            
        # Get challenge
        cur.execute('SELECT flag, points FROM challenges WHERE id = %s', (challenge_id,))
        challenge = cur.fetchone()
        
        if not challenge:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Challenge not found'})
            
        if challenge['flag'] == submitted_flag:
            # Correct flag!
            try:
                cur.execute('INSERT INTO solves (user_id, challenge_id, points_earned) VALUES (%s, %s, %s)', (user_id, challenge_id, challenge['points']))
            except Exception:
                # Fallback if column points_earned doesn't exist yet (migration error)
                cur.execute('INSERT INTO solves (user_id, challenge_id) VALUES (%s, %s)', (user_id, challenge_id))
            
            cur.execute('UPDATE users SET score = score + %s WHERE id = %s', (challenge['points'], user_id))
            
            # Log activity
            try:
                cur.execute('INSERT INTO activity_logs (user_id, action, details, ip_address) VALUES (%s, %s, %s, %s)', 
                            (user_id, 'Flag Submission', f"Solved challenge {challenge_id} for {challenge['points']} points", request.remote_addr))
            except Exception:
                pass
                
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Flag correct! Points awarded.'})
        else:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Incorrect flag.'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': 'Database error'})


# ─────────────────────────────────────────────
# LIVE STATS & LEADERBOARD API
# ─────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    user_id = session.get('user_id')
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # 1. Total players
        cur.execute("SELECT COUNT(*) FROM users WHERE role = 'player'")
        total_players = cur.fetchone()[0]
        
        # Total users (all roles combined)
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        
        # Total score of all players
        cur.execute("SELECT SUM(score) FROM users WHERE role = 'player'")
        total_score_row = cur.fetchone()
        total_score = total_score_row[0] if total_score_row and total_score_row[0] is not None else 0
        
        # 2. Total challenges
        cur.execute("SELECT COUNT(*) FROM challenges")
        total_challenges = cur.fetchone()[0]
        
        # 3. Total solves
        cur.execute("SELECT COUNT(*) FROM solves")
        total_solves = cur.fetchone()[0]
        
        # 4. User solves
        cur.execute("SELECT COUNT(*) FROM solves WHERE user_id = %s", (user_id,))
        user_solves = cur.fetchone()[0]
        
        # 5. User score & rank
        cur.execute("SELECT score FROM users WHERE id = %s", (user_id,))
        user_score_row = cur.fetchone()
        user_score = user_score_row[0] if user_score_row else 0
        
        cur.execute("SELECT COUNT(*) + 1 FROM users WHERE role = 'player' AND score > %s", (user_score,))
        user_rank = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'total_users': total_users,
            'total_players': total_players,
            'total_score': total_score,
            'total_challenges': total_challenges,
            'total_solves': total_solves,
            'user_solves': user_solves,
            'user_score': user_score,
            'user_rank': user_rank
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard_data():
    period = request.args.get('period', 'overall')
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        if period == 'overall':
            cur.execute('''
                SELECT u.id, u.username, COALESCE(u.display_name, u.username) as display_name, u.score, u.avatar, COALESCE(u.avatar_style, 'linear-gradient(135deg, #1a0a3a, var(--blue))') as avatar_style,
                       (SELECT COUNT(*) FROM solves s WHERE s.user_id = u.id) AS solves
                FROM users u
                WHERE u.role = 'player'
                ORDER BY u.score DESC, u.id ASC
            ''')
        else:
            time_filter = ""
            if period == 'daily':
                time_filter = "AND s.solved_at >= CURRENT_DATE"
            elif period == 'weekly':
                time_filter = "AND s.solved_at >= date_trunc('week', CURRENT_DATE)"
            elif period == 'monthly':
                time_filter = "AND s.solved_at >= date_trunc('month', CURRENT_DATE)"
                
            query = f'''
                SELECT u.id, u.username, COALESCE(u.display_name, u.username) as display_name, u.avatar, COALESCE(u.avatar_style, 'linear-gradient(135deg, #1a0a3a, var(--blue))') as avatar_style,
                       COALESCE(SUM(c.points), 0) AS score,
                       COUNT(s.challenge_id) AS solves
                FROM users u
                LEFT JOIN solves s ON s.user_id = u.id {time_filter}
                LEFT JOIN challenges c ON c.id = s.challenge_id
                WHERE u.role = 'player'
                GROUP BY u.id, u.username, u.display_name, u.avatar, u.avatar_style
                ORDER BY score DESC, u.id ASC
            '''
            cur.execute(query)
            
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        leaderboard = []
        for i, row in enumerate(rows):
            leaderboard.append({
                'rank': i + 1,
                'id': row['id'],
                'username': row['display_name'],
                'score': row['score'],
                'avatar': row['avatar'] or row['username'][:2].upper(),
                'avatar_style': row['avatar_style'],
                'solves': row['solves']
            })
            
        return jsonify({'success': True, 'leaderboard': leaderboard})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)