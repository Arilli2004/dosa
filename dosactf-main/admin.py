from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash
from functools import wraps
from psycopg2.extras import RealDictCursor

admin_bp = Blueprint('admin', __name__)

# ─────────────────────────────────────────────
# ADMIN AUTH DECORATOR
# ─────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            # Return JSON for API routes, redirect for page routes
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Not authenticated'}), 401
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('admin.admin_login'))
        if session.get('role') not in ('admin', 'super_admin'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Admin access only'}), 403
            flash('Admin access only.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# ADMIN AUTHENTICATION
# ─────────────────────────────────────────────
@admin_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if 'user_id' in session and session.get('role') == 'admin':
        return redirect(url_for('admin.admin_dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('username', '').strip()
        password   = request.form.get('password', '')
        ip         = request.remote_addr

        if not identifier or not password:
            flash('Please enter your username/email and password.', 'danger')
            return render_template('admin_pages/admin_Login.html', form_identifier=identifier)

        # Lazy imports to prevent circular dependency
        from app import get_db, log_login_attempt

        try:
            conn = get_db()
            cur  = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                'SELECT u.*, p.display_name, p.score, p.avatar, p.avatar_style, s.last_login, s.last_logout, s.is_online, s.reset_otp, s.reset_otp_expiry FROM users u LEFT JOIN user_profiles p ON u.id = p.user_id LEFT JOIN user_status s ON u.id = s.user_id WHERE u.username=%s OR u.email=%s LIMIT 1',
                (identifier, identifier)
            )
            user = cur.fetchone()
            cur.close()
            conn.close()
        except Exception as ex:
            flash('Database error. Please try again.', 'danger')
            return render_template('admin_pages/admin_Login.html', form_identifier=identifier)

        if user and check_password_hash(user['password'], password):
            if user['status'] == 'banned':
                flash('Your account has been banned. Contact support.', 'danger')
                log_login_attempt(user['id'], ip, False)
                return render_template('admin_pages/admin_Login.html', form_identifier=identifier)

            if user['role'] != 'admin':
                flash('Access denied: Admin accounts only.', 'danger')
                log_login_attempt(user['id'], ip, False)
                return render_template('admin_pages/admin_Login.html', form_identifier=identifier)

            # Update last_login
            try:
                conn = get_db()
                cur  = conn.cursor()
                cur.execute('UPDATE user_status SET last_login=CURRENT_TIMESTAMP WHERE user_id=%s', (user['id'],))
                conn.commit()
                cur.close()
                conn.close()
            except Exception:
                pass

            log_login_attempt(user['id'], ip, True)
            session.clear()
            
            if request.form.get('remember') == 'on':
                from datetime import timedelta
                from flask import current_app
                session.permanent = True
                current_app.permanent_session_lifetime = timedelta(days=30)
                
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['role']     = user['role']
            session['avatar']   = user['avatar'] or user['username'][:2].upper()

            flash(f'Welcome back, Admin {user["username"]}! ⚙️', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.admin_dashboard'))
        else:
            if user:
                log_login_attempt(user['id'], ip, False)
            flash('Invalid credentials. Check your username/email and password.', 'danger')
            return render_template('admin_pages/admin_Login.html', form_identifier=identifier)

    return render_template('admin_pages/admin_Login.html', form_identifier='')


# ─────────────────────────────────────────────
# ADMIN PAGES
# ─────────────────────────────────────────────
@admin_bp.route('/admin-dashboard')
@admin_required
def admin_dashboard():
    from app import get_db
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Recent admin logs
        cur.execute('''
            SELECT al.action, al.target, al.created_at, u.username
            FROM admin_logs al
            LEFT JOIN users u ON al.user_id = u.id
            ORDER BY al.created_at DESC LIMIT 10
        ''')
        admin_logs = cur.fetchall()
        
        # Recent flag submissions (solves)
        cur.execute('''
            SELECT s.solved_at, u.username, c.title
            FROM solves s
            JOIN users u ON s.user_id = u.id
            JOIN challenges c ON s.challenge_id = c.id
            ORDER BY s.solved_at DESC LIMIT 10
        ''')
        recent_solves = cur.fetchall()
        
        cur.close()
        conn.close()
        return render_template('admin_pages/admin_dashboard.html', admin_logs=admin_logs, recent_solves=recent_solves)
    except Exception as e:
        return render_template('admin_pages/admin_dashboard.html', admin_logs=[], recent_solves=[])


@admin_bp.route('/admin-leaderboard')
@admin_required
def admin_leaderboard():
    return render_template('admin_pages/admin_leaderboard.html')


@admin_bp.route('/admin-profile')
@admin_required
def admin_profile():
    from app import get_db
    user_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT u.*, p.display_name, p.score, p.avatar, p.avatar_style, s.last_login, s.last_logout, s.is_online, s.reset_otp, s.reset_otp_expiry FROM users u LEFT JOIN user_profiles p ON u.id = p.user_id LEFT JOIN user_status s ON u.id = s.user_id WHERE u.id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('admin_pages/admin_profile.html', user=user)


@admin_bp.route('/admin-settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    from app import get_db
    from werkzeug.security import generate_password_hash, check_password_hash
    user_id = session['user_id']
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        if request.method == 'POST':
            form_type = request.form.get('form_type')
            
            if form_type == 'platform':
                event_name = request.form.get('event_name', '').strip()
                event_status = request.form.get('event_status', '').strip()
                start_date = request.form.get('start_date') or None
                end_date = request.form.get('end_date') or None
                max_team_size = request.form.get('max_team_size', 4)
                flag_cooldown = request.form.get('flag_cooldown', 60)
                alert_email = request.form.get('alert_email', '').strip()
                webhook_url = request.form.get('webhook_url', '').strip()
                auto_backup = request.form.get('auto_backup', 'Daily').strip()
                retention = request.form.get('retention', '30 Days').strip()
                
                cur.execute('''
                    UPDATE platform_settings SET 
                    event_name=%s, event_status=%s, start_date=%s, end_date=%s, 
                    max_team_size=%s, flag_cooldown=%s, alert_email=%s, 
                    webhook_url=%s, auto_backup=%s, retention=%s 
                    WHERE id=1
                ''', (event_name, event_status, start_date, end_date, max_team_size, 
                      flag_cooldown, alert_email, webhook_url, auto_backup, retention))
                conn.commit()
                flash('Platform settings updated successfully!', 'success')
                
                from app import log_admin_action
                log_admin_action(session['user_id'], 'Updated Settings', 'Platform Config')
                
            elif form_type == 'profile':
                display_name = request.form.get('display_name', '').strip()
                email = request.form.get('email', '').strip()
                # Assuming 'bio' is an existing column, if not we will skip bio
                # Since we didn't add bio column yet, let's just do display_name and email
                if not email:
                    flash('Email is required.', 'danger')
                else:
                    cur.execute(
                        'UPDATE user_profiles SET display_name = %s WHERE user_id = %s',
                        (display_name, user_id)
                    )
                    cur.execute(
                        'UPDATE users SET email = %s WHERE id = %s',
                        (email, user_id)
                    )
                    conn.commit()
                    session['display_name'] = display_name or session['username']
                    flash('Profile updated successfully!', 'success')
            
            elif form_type == 'password':
                current_password = request.form.get('current_password')
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')
                
                if not current_password or not new_password or not confirm_password:
                    flash('All password fields are required.', 'danger')
                elif new_password != confirm_password:
                    flash('New passwords do not match.', 'danger')
                else:
                    cur.execute('SELECT password FROM users WHERE id = %s', (user_id,))
                    user_record = cur.fetchone()
                    if user_record and check_password_hash(user_record['password'], current_password):
                        new_hash = generate_password_hash(new_password)
                        cur.execute('UPDATE users SET password = %s WHERE id = %s', (new_hash, user_id))
                        conn.commit()
                        flash('Password updated successfully!', 'success')
                        from app import log_admin_action
                        log_admin_action(session['user_id'], 'Updated Password', 'Security')
                    else:
                        flash('Incorrect current password.', 'danger')
        # Fetch current user data
        cur.execute("SELECT u.*, p.display_name, p.score, p.avatar, p.avatar_style, s.last_login, s.last_logout, s.is_online, s.reset_otp, s.reset_otp_expiry FROM users u LEFT JOIN user_profiles p ON u.id = p.user_id LEFT JOIN user_status s ON u.id = s.user_id WHERE u.id = %s", (user_id,))
        user = cur.fetchone()
        
        # Fetch platform settings
        cur.execute('SELECT * FROM platform_settings WHERE id = 1')
        settings = cur.fetchone()
        if not settings:
            settings = {}
            
        cur.close()
        conn.close()
        
        return render_template('admin_pages/admin_settings.html', user=user, settings=settings)
        
    except Exception as e:
        flash(f'Error loading settings: {str(e)}', 'danger')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/add-challenge')
@admin_required
def add_challenge():
    return render_template('admin_pages/add_challenge.html')

@admin_bp.route('/admin-notify')
@admin_required
def admin_notify():
    return render_template('admin_pages/admin_notify.html')

@admin_bp.route('/api/admin/notify', methods=['POST'])
@admin_required
def api_admin_notify():
    from app import get_db
    data = request.get_json()
    if not data or 'title' not in data or 'message' not in data or 'target' not in data:
        return jsonify({'success': False, 'message': 'Missing fields'})
        
    target = data['target']
    title = data['title']
    message = data['message']
    
    try:
        conn = get_db()
        cur = conn.cursor()
        if target == 'all':
            cur.execute('SELECT id FROM users')
            users = cur.fetchall()
            for u in users:
                cur.execute('INSERT INTO notifications (user_id, title, message) VALUES (%s, %s, %s)', (u[0], title, message))
        else:
            cur.execute('SELECT id FROM users WHERE username = %s', (target,))
            row = cur.fetchone()
            if not row:
                return jsonify({'success': False, 'message': 'User not found'})
            cur.execute('INSERT INTO notifications (user_id, title, message) VALUES (%s, %s, %s)', (row[0], title, message))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error sending notification: {e}")
        return jsonify({'success': False, 'message': 'Database error'})


@admin_bp.route('/edit-challenges', methods=['GET', 'POST'])
@admin_required
def edit_challenges():
    from app import get_db
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('''
            SELECT c.*,
                   (SELECT COUNT(*) FROM solves s WHERE s.challenge_id = c.id) AS solve_count
            FROM challenges c ORDER BY c.id
        ''')
        rows = cur.fetchall()
        cur.execute('SELECT * FROM hints')
        hints_rows = cur.fetchall()
        hints_by_chal = {}
        for h in hints_rows:
            cid = h['challenge_id']
            if cid not in hints_by_chal:
                hints_by_chal[cid] = []
            hints_by_chal[cid].append({'text': h['hint_text'], 'cost': h['cost']})
        cur.close()
        conn.close()

        challenges = []
        for r in rows:
            cat = r['category']
            if cat in ['Rev', 'Reverse', 'Reversing']:
                cat = 'Reversing'
            icon_map = {'Web': '🌐', 'Pwn': '💀', 'Crypto': '🔐', 'Forensics': '🔍', 'Reversing': '🔄', 'Misc': '🎲'}
            icon = icon_map.get(cat, '🎲')
            challenges.append({
                'id': r['id'],
                'name': r['title'],
                'cat': cat,
                'icon': icon,
                'diff': r['difficulty'],
                'pts': r['points'],
                'solves': r['solve_count'],
                'attempts': r['solve_count'] + 5,
                'desc': r['description'] or '',
                'flag': r['flag'],
                'file_url': r['file_url'] or '',
                'hints': hints_by_chal.get(r['id'], [])
            })
    except Exception as e:
        challenges = []
        flash(f'Error loading challenges: {e}', 'danger')

    return render_template('admin_pages/edit_challenges.html', challenges=challenges)


@admin_bp.route('/remove-challenges')
@admin_required
def remove_challenges():
    return render_template('admin_pages/remove_challenges.html')


@admin_bp.route('/view-users')
@admin_required
def view_users():
    return render_template('admin_pages/view_users.html')


@admin_bp.route('/ban-users')
@admin_required
def ban_users():
    return render_template('admin_pages/ban_users.html')


@admin_bp.route('/edit-user-role')
@admin_required
def edit_user_role():
    return render_template('admin_pages/edit_user_role.html')


# ─────────────────────────────────────────────
# CHALLENGE CRUD API (ADMIN ONLY)
# ─────────────────────────────────────────────
@admin_bp.route('/api/admin/challenges', methods=['GET'])
@admin_required
def admin_get_challenges():
    from app import get_db
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('''
            SELECT c.*, 
                   (SELECT COUNT(*) FROM solves s WHERE s.challenge_id = c.id) AS solves
            FROM challenges c
        ''')
        rows = cur.fetchall()
        # Get all hints
        cur.execute('SELECT * FROM hints')
        hints_rows = cur.fetchall()
        hints_by_chal = {}
        for h in hints_rows:
            cid = h['challenge_id']
            if cid not in hints_by_chal:
                hints_by_chal[cid] = []
            hints_by_chal[cid].append({'text': h['hint_text'], 'cost': h['cost']})
            
        cur.close()
        conn.close()
        
        challenges = []
        for r in rows:
            cat = r['category']
            if cat in ['Rev', 'Reverse', 'Reversing']:
                cat = 'Reversing'
            icon = '🎲'
            if cat == 'Web': icon = '🌐'
            elif cat == 'Pwn': icon = '💀'
            elif cat == 'Crypto': icon = '🔐'
            elif cat == 'Forensics': icon = '🔍'
            elif cat == 'Reversing': icon = '🔄'
            
            challenges.append({
                'id': r['id'],
                'name': r['title'],
                'cat': cat,
                'icon': icon,
                'diff': r['difficulty'],
                'pts': r['points'],
                'solves': r['solves'],
                'attempts': r['solves'] + 5,  # Placeholder for attempts
                'author': 'Admin',
                'desc': r['description'],
                'flag': r['flag'],
                'file_url': r['file_url'],
                'hints': hints_by_chal.get(r['id'], [])
            })
        return jsonify({'success': True, 'challenges': challenges})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/api/admin/challenges/add', methods=['POST'])
@admin_required
def admin_add_challenge():
    from app import get_db
    data = request.get_json()
    if not data or not all(k in data for k in ['title', 'category', 'difficulty', 'points', 'description', 'flag']):
        return jsonify({'success': False, 'message': 'Missing required fields'})
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO challenges (title, category, difficulty, points, description, flag, file_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            data['title'].strip(),
            data['category'].strip(),
            data['difficulty'].strip(),
            int(data['points']),
            data['description'].strip(),
            data['flag'].strip(),
            data.get('file_url')
        ))
        challenge_id = cur.fetchone()[0]
        
        # Insert hints if any
        if 'hints' in data and isinstance(data['hints'], list):
            for h in data['hints']:
                h_text = h.get('text', '').strip()
                h_cost = int(h.get('cost', 0))
                if h_text:
                    cur.execute('''
                        INSERT INTO hints (challenge_id, hint_text, cost)
                        VALUES (%s, %s, %s)
                    ''', (challenge_id, h_text, h_cost))
                    
        conn.commit()
        cur.close()
        conn.close()
        
        # Log admin action
        from app import log_admin_action
        log_admin_action(session['user_id'], 'Created Challenge', data['title'].strip())
        
        return jsonify({'success': True, 'message': 'Challenge deployed successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@admin_bp.route('/api/admin/challenges/edit/<int:challenge_id>', methods=['POST'])
@admin_required
def admin_edit_challenge(challenge_id):
    from app import get_db
    data = request.get_json()
    if not data or not all(k in data for k in ['title', 'category', 'difficulty', 'points', 'description', 'flag']):
        return jsonify({'success': False, 'message': 'Missing required fields'})
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            UPDATE challenges 
            SET title=%s, category=%s, difficulty=%s, points=%s, description=%s, flag=%s, file_url=%s
            WHERE id=%s
        ''', (
            data['title'].strip(),
            data['category'].strip(),
            data['difficulty'].strip(),
            int(data['points']),
            data['description'].strip(),
            data['flag'].strip(),
            data.get('file_url'),
            challenge_id
        ))
        # Replace hints
        cur.execute('DELETE FROM hints WHERE challenge_id = %s', (challenge_id,))
        if 'hints' in data and isinstance(data['hints'], list):
            for h in data['hints']:
                h_text = h.get('text', '').strip()
                h_cost = int(h.get('cost', 0))
                if h_text:
                    cur.execute('''
                        INSERT INTO hints (challenge_id, hint_text, cost)
                        VALUES (%s, %s, %s)
                    ''', (challenge_id, h_text, h_cost))
                    
        conn.commit()
        cur.close()
        conn.close()
        
        # Log admin action
        from app import log_admin_action
        log_admin_action(session['user_id'], 'Edited Challenge', data['title'].strip())
        
        return jsonify({'success': True, 'message': 'Challenge updated successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@admin_bp.route('/api/admin/challenges/delete/<int:challenge_id>', methods=['POST'])
@admin_required
def admin_delete_challenge(challenge_id):
    from app import get_db
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Get target challenge info before delete
        cur.execute('SELECT title, points FROM challenges WHERE id=%s', (challenge_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Challenge not found'})
            
        challenge_title = row[0]
        challenge_points = row[1]
        
        # Deduct points from users who solved it
        cur.execute('''
            UPDATE user_profiles SET score = score - %s 
            WHERE user_id IN (SELECT user_id FROM solves WHERE challenge_id = %s)
        ''', (challenge_points, challenge_id))
        
        cur.execute('DELETE FROM challenges WHERE id=%s', (challenge_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        # Log admin action
        from app import log_admin_action
        log_admin_action(session['user_id'], 'Deleted Challenge', challenge_title)
        
        return jsonify({'success': True, 'message': 'Challenge deleted successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@admin_bp.route('/api/admin/upload', methods=['POST'])
@admin_required
def admin_upload_file():
    import os
    from flask import current_app
    from werkzeug.utils import secure_filename
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part in request'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
        
    try:
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
            
        filename = secure_filename(file.filename)
        # Avoid overriding files with duplicate names
        base, extension = os.path.splitext(filename)
        counter = 1
        while os.path.exists(os.path.join(upload_folder, filename)):
            filename = f"{base}_{counter}{extension}"
            counter += 1
            
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        file_url = f"/static/uploads/{filename}"
        return jsonify({
            'success': True,
            'file_url': file_url,
            'filename': filename
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@admin_bp.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_get_users():
    from app import get_db
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('''
            SELECT u.id, u.username, u.email, u.role, u.status, p.score, u.created_at, p.avatar, s.is_online, s.last_logout
            FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            LEFT JOIN user_status s ON u.id = s.user_id
            ORDER BY p.score DESC, u.id ASC
        ''')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        users_list = []
        for r in rows:
            users_list.append({
                'id': f"#{r['id']:04d}",
                'db_id': r['id'],
                'name': r['username'],
                'email': r['email'],
                'role': r['role'].capitalize(),
                'status': r['status'].capitalize(),
                'score': r['score'],
                'joined': r['created_at'].strftime('%Y-%m-%d') if r['created_at'] else 'N/A',
                'avatar': r['avatar'] or r['username'][:2].upper(),
                'is_online': bool(r['is_online']),
                'last_logout': r['last_logout'].strftime('%Y-%m-%d %H:%M:%S') if r['last_logout'] else 'Never'
            })
        return jsonify({'success': True, 'users': users_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/api/admin/users/role/<int:user_id>', methods=['POST'])
@admin_required
def admin_update_user_role(user_id):
    from app import get_db
    data = request.get_json()
    if not data or 'role' not in data:
        return jsonify({'success': False, 'message': 'Missing role'})
    
    role = data['role'].lower().strip()
    if role not in ['admin', 'player']:
        return jsonify({'success': False, 'message': 'Invalid role'})
        
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Prevent modifying own role
        if user_id == session.get('user_id'):
            return jsonify({'success': False, 'message': 'Cannot modify your own role'})
            
        # Get target username
        cur.execute('SELECT username FROM users WHERE id=%s', (user_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'User not found'})
            
        target_name = row[0]
        
        cur.execute('UPDATE users SET role=%s WHERE id=%s', (role, user_id))
        conn.commit()
        cur.close()
        conn.close()
        
        # Log admin action
        from app import log_admin_action
        log_admin_action(session['user_id'], 'Changed Role', f'Set {target_name} to {role}')
        
        return jsonify({'success': True, 'message': f'Role updated to {role} successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@admin_bp.route('/api/admin/users/status/<int:user_id>', methods=['POST'])
@admin_required
def admin_update_user_status(user_id):
    from app import get_db
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'success': False, 'message': 'Missing status'})
    
    status = data['status'].lower().strip()
    if status not in ['active', 'banned', 'inactive']:
        return jsonify({'success': False, 'message': 'Invalid status'})
        
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Prevent modifying own status
        if user_id == session.get('user_id'):
            return jsonify({'success': False, 'message': 'Cannot modify your own status'})
            
        # Get target username and role
        cur.execute('SELECT username, role FROM users WHERE id=%s', (user_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'User not found'})
            
        target_name = row[0]
        target_role = row[1]
        
        if target_role == 'admin':
            return jsonify({'success': False, 'message': 'Cannot ban another admin'})
        
        cur.execute('UPDATE users SET status=%s WHERE id=%s', (status, user_id))
        conn.commit()
        cur.close()
        conn.close()
        
        # Log admin action
        from app import log_admin_action
        log_admin_action(session['user_id'], 'Changed Status', f'Set {target_name} to {status}')
        
        return jsonify({'success': True, 'message': f'Status updated to {status} successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@admin_bp.route('/api/admin/recent-submissions', methods=['GET'])
@admin_required
def admin_recent_submissions():
    from app import get_db
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('''
            SELECT u.username, c.title, s.solved_at
            FROM solves s
            JOIN users u ON s.user_id = u.id
            JOIN challenges c ON s.challenge_id = c.id
            ORDER BY s.solved_at DESC
            LIMIT 5
        ''')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        submissions = []
        for r in rows:
            time_str = r['solved_at'].strftime('%H:%M') if r['solved_at'] else '--:--'
            submissions.append({
                'time': time_str,
                'user': r['username'],
                'challenge': r['title'],
                'status': 'Correct Flag'
            })
        return jsonify({'success': True, 'submissions': submissions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/api/admin/logs', methods=['GET'])
@admin_required
def admin_get_logs():
    from app import get_db
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('''
            SELECT u.username, al.action, al.target, al.logged_at
            FROM admin_logs al
            LEFT JOIN users u ON al.user_id = u.id
            ORDER BY al.logged_at DESC
            LIMIT 6
        ''')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        logs = []
        for r in rows:
            time_str = r['logged_at'].strftime('%H:%M') if r['logged_at'] else '--:--'
            admin_name = r['username'] or 'System'
            logs.append({
                'time': time_str,
                'admin': admin_name,
                'action': r['action'],
                'target': r['target']
            })
        return jsonify({'success': True, 'logs': logs})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
