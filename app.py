from flask import Flask, render_template, request, redirect, session, flash, url_for, send_file, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os
import io
import importlib
from datetime import datetime
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

TOTAL_SESSION_LIMIT = 30

LABS = [
    {'code': 'LAB101', 'label': 'Lab 101', 'description': 'Multimedia & design lab', 'capacity': 20},
    {'code': 'LAB102', 'label': 'Lab 102', 'description': 'Programming and software dev lab', 'capacity': 20},
    {'code': 'LAB103', 'label': 'Lab 103', 'description': 'Networking and infrastructure lab', 'capacity': 20},
    {'code': 'LAB201', 'label': 'Lab 201', 'description': 'Research and capstone lab', 'capacity': 15},
]

PURPOSES = [
    'C',
    'C#',
    'Java',
    'Python',
    'PHP',
    'JavaScript',
    'ASP.Net'
]

LAB_LOOKUP = {lab['code']: lab for lab in LABS}

ANNOUNCEMENTS = [
    {
        'author': 'CCS Admin',
        'date': '2026-Feb-11',
        'body': 'New announcement.'
    },
    {
        'author': 'CCS Admin',
        'date': '2024-May-08',
        'body': 'Important announcement: Explore our latest products and services now!'
    },
]


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="sit_in_db"
    )


def is_admin_user():
    user = session.get('user')
    if not user:
        return False
    return str(user.get('id_number', '')).lower().startswith('adm-')


def ensure_sit_in_logs_table(db):
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sit_in_logs (
            id INT NOT NULL AUTO_INCREMENT,
            student_id_number VARCHAR(20) NOT NULL,
            purpose VARCHAR(100) DEFAULT NULL,
            lab VARCHAR(50) DEFAULT NULL,
            session_no INT DEFAULT 1,
            status ENUM('active', 'completed') NOT NULL DEFAULT 'active',
            started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ended_at DATETIME DEFAULT NULL,
            PRIMARY KEY (id),
            INDEX idx_student_id_number (student_id_number),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    cursor.close()


def ensure_user_feedback_table(db):
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INT NOT NULL AUTO_INCREMENT,
            student_id_number VARCHAR(20) NOT NULL,
            sit_in_log_id INT DEFAULT NULL,
            rating TINYINT DEFAULT NULL,
            feedback_text TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            INDEX idx_student_id_number (student_id_number),
            INDEX idx_sit_in_log_id (sit_in_log_id),
            CONSTRAINT fk_user_feedback_student
                FOREIGN KEY (student_id_number) REFERENCES users(id_number)
                ON DELETE CASCADE,
            CONSTRAINT fk_user_feedback_sit_in
                FOREIGN KEY (sit_in_log_id) REFERENCES sit_in_logs(id)
                ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    cursor.close()


def fetch_sit_in_history(student_id=None, status=None, date_from=None, date_to=None):
    db = get_db()
    ensure_sit_in_logs_table(db)
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT
            s.id,
            s.student_id_number,
            s.lab,
            s.purpose,
            s.session_no,
            s.status,
            s.started_at,
            s.ended_at,
            u.last_name,
            u.first_name,
            u.middle_name,
            u.course,
            u.course_level
        FROM sit_in_logs s
        LEFT JOIN users u ON u.id_number = s.student_id_number
        WHERE 1=1
    """
    params = []

    if student_id:
        query += " AND s.student_id_number = %s"
        params.append(student_id)

    if status in ('active', 'completed'):
        query += " AND s.status = %s"
        params.append(status)

    if date_from:
        query += " AND DATE(s.started_at) >= %s"
        params.append(date_from.strftime('%Y-%m-%d'))

    if date_to:
        query += " AND DATE(s.started_at) <= %s"
        params.append(date_to.strftime('%Y-%m-%d'))

    query += " ORDER BY s.started_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    db.close()

    for row in rows:
        lab_info = LAB_LOOKUP.get(row['lab'])
        row['lab_label'] = lab_info['label'] if lab_info else (row['lab'] or 'Unassigned')
        full_name = f"{row.get('last_name') or ''}, {row.get('first_name') or ''}"
        if row.get('middle_name'):
            full_name = f"{full_name} {row['middle_name']}"
        row['full_name'] = full_name.strip(', ')

    summary = {
        'total': len(rows),
        'active': sum(1 for row in rows if row['status'] == 'active'),
        'completed': sum(1 for row in rows if row['status'] == 'completed')
    }

    return rows, summary


def build_report_filters(arg_source):
    form_values = {
        'student_id': (arg_source.get('student_id') or '').strip(),
        'status': (arg_source.get('status') or 'all').lower(),
        'date_from': (arg_source.get('date_from') or '').strip(),
        'date_to': (arg_source.get('date_to') or '').strip()
    }

    criteria = {
        'student_id': form_values['student_id'] or None,
        'status': form_values['status'] if form_values['status'] in ('active', 'completed') else None,
        'date_from': None,
        'date_to': None
    }

    if form_values['date_from']:
        try:
            criteria['date_from'] = datetime.strptime(form_values['date_from'], '%Y-%m-%d')
        except ValueError:
            flash('Invalid start date. Use YYYY-MM-DD format.', 'danger')
            form_values['date_from'] = ''

    if form_values['date_to']:
        try:
            criteria['date_to'] = datetime.strptime(form_values['date_to'], '%Y-%m-%d')
        except ValueError:
            flash('Invalid end date. Use YYYY-MM-DD format.', 'danger')
            form_values['date_to'] = ''

    return form_values, criteria


def get_admin_dashboard_data():
    db = get_db()
    ensure_sit_in_logs_table(db)

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(*) AS students_registered
        FROM users
        WHERE id_number NOT LIKE 'adm-%'
    """)
    students_registered = cursor.fetchone()['students_registered']

    cursor.execute("""
        SELECT COUNT(*) AS currently_sit_in
        FROM sit_in_logs
        WHERE status = 'active'
    """)
    currently_sit_in = cursor.fetchone()['currently_sit_in']

    cursor.execute("""
        SELECT COUNT(*) AS total_sit_in
        FROM sit_in_logs
    """)
    total_sit_in = cursor.fetchone()['total_sit_in']

    cursor.execute("""
        SELECT
            COALESCE(NULLIF(purpose, ''), 'Unspecified') AS label,
            COUNT(*) AS total
        FROM sit_in_logs
        GROUP BY COALESCE(NULLIF(purpose, ''), 'Unspecified')
        ORDER BY total DESC, label ASC
    """)
    purpose_breakdown = cursor.fetchall()

    cursor.close()
    db.close()

    stats = {
        'students_registered': students_registered,
        'currently_sit_in': currently_sit_in,
        'total_sit_in': total_sit_in,
    }

    chart_data = {
        'labels': [row['label'] for row in purpose_breakdown],
        'values': [row['total'] for row in purpose_breakdown]
    }

    return stats, ANNOUNCEMENTS, chart_data


def lookup_student_session(cursor, student_id):
    cursor.execute("""
        SELECT id_number, last_name, first_name, middle_name, course, course_level
        FROM users
        WHERE id_number = %s AND id_number NOT LIKE 'adm-%'
        LIMIT 1
    """, (student_id,))
    student = cursor.fetchone()
    if not student:
        return None, None, None, None

    cursor.execute("""
        SELECT
            SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed_count,
            SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) AS active_count
        FROM sit_in_logs
        WHERE student_id_number=%s
    """, (student_id,))
    counts = cursor.fetchone()
    completed_sessions = counts['completed_count'] or 0
    active_sessions = counts['active_count'] or 0
    remaining_sessions = max(TOTAL_SESSION_LIMIT - completed_sessions - active_sessions, 0)

    cursor.execute("""
        SELECT lab, purpose, started_at
        FROM sit_in_logs
        WHERE student_id_number=%s AND status='active'
        ORDER BY started_at DESC
        LIMIT 1
    """, (student_id,))
    active_session = cursor.fetchone()
    if active_session:
        lab_info = LAB_LOOKUP.get(active_session['lab'])
        active_session['lab_label'] = lab_info['label'] if lab_info else (active_session['lab'] or 'Unassigned')

    return student, remaining_sessions, active_session, completed_sessions


@app.route('/')
def login():
    return render_template('login.html')


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        id_number = (request.form.get('id_number') or '').strip()
        email = (request.form.get('email') or '').strip()
        new_password = request.form.get('new_password') or ''
        confirm_password = request.form.get('confirm_password') or ''

        if not id_number or not email or not new_password or not confirm_password:
            flash('Please complete all fields.', 'danger')
            return redirect('/reset_password')

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect('/reset_password')

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, id_number
            FROM users
            WHERE id_number = %s AND email = %s
            LIMIT 1
        """, (id_number, email))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            db.close()
            flash('Account not found. Check your ID number and email.', 'danger')
            return redirect('/reset_password')

        hashed_pw = generate_password_hash(new_password)
        cursor.execute("""
            UPDATE users
            SET password = %s
            WHERE id = %s
        """, (hashed_pw, user['id']))
        db.commit()
        cursor.close()
        db.close()

        flash('Password reset successful. Please log in.', 'success')
        return redirect('/')

    return render_template('reset_password.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/admin')
def admin_dashboard():
    stats, announcements, chart_data = get_admin_dashboard_data()
    return render_template('admin_dashboard.html',
                           stats=stats,
                           announcements=announcements,
                           chart_data=chart_data)


@app.route('/admin/search', methods=['GET', 'POST'])
def admin_search():
    student = None
    active_session = None
    recent_sessions = []
    remaining_sessions = None
    searched_id = None

    if request.method == 'POST':
        searched_id = (request.form.get('id_number') or '').strip()
        if not searched_id:
            flash('Please enter a student ID to search.', 'warning')
        else:
            db = get_db()
            ensure_sit_in_logs_table(db)
            cursor = db.cursor(dictionary=True)

            cursor.execute("""
                SELECT id_number, last_name, first_name, middle_name, course, course_level
                FROM users
                WHERE id_number = %s AND id_number NOT LIKE 'adm-%'
                LIMIT 1
            """, (searched_id,))
            student = cursor.fetchone()

            if student:
                cursor.execute("""
                    SELECT
                        SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed_count,
                        SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) AS active_count
                    FROM sit_in_logs
                    WHERE student_id_number=%s
                """, (searched_id,))
                counts = cursor.fetchone()
                completed_sessions = counts['completed_count'] or 0
                active_sessions = counts['active_count'] or 0
                remaining_sessions = max(TOTAL_SESSION_LIMIT - completed_sessions - active_sessions, 0)

                cursor.execute("""
                    SELECT lab, purpose, started_at
                    FROM sit_in_logs
                    WHERE student_id_number=%s AND status='active'
                    ORDER BY started_at DESC
                    LIMIT 1
                """, (searched_id,))
                active_session = cursor.fetchone()
                if active_session:
                    lab_info = LAB_LOOKUP.get(active_session['lab'])
                    active_session['lab_label'] = lab_info['label'] if lab_info else (active_session['lab'] or 'Unassigned')

                cursor.execute("""
                    SELECT lab, purpose, status, started_at, ended_at
                    FROM sit_in_logs
                    WHERE student_id_number=%s
                    ORDER BY started_at DESC
                    LIMIT 8
                """, (searched_id,))
                recent_sessions = cursor.fetchall()
                for row in recent_sessions:
                    lab_info = LAB_LOOKUP.get(row['lab'])
                    row['lab_label'] = lab_info['label'] if lab_info else (row['lab'] or 'Unassigned')
            else:
                flash('Student not found.', 'danger')

            cursor.close()
            db.close()

    return render_template('admin_search.html',
                           student=student,
                           active_session=active_session,
                           recent_sessions=recent_sessions,
                           remaining_sessions=remaining_sessions,
                           searched_id=searched_id)


@app.route('/admin/students')
def admin_students():
    db = get_db()
    ensure_sit_in_logs_table(db)
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT id_number, last_name, first_name, middle_name, course, course_level
        FROM users
        WHERE id_number NOT LIKE 'adm-%'
        ORDER BY last_name, first_name
    """)
    users = cursor.fetchall()

    student_ids = [user['id_number'] for user in users]
    remaining_lookup = {}

    if student_ids:
        format_strings = ','.join(['%s'] * len(student_ids))
        cursor.execute(f"""
            SELECT student_id_number,
                   SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed_sessions,
                   SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) AS active_sessions
            FROM sit_in_logs
            WHERE student_id_number IN ({format_strings})
            GROUP BY student_id_number
        """, student_ids)
        for row in cursor.fetchall():
            remaining_lookup[row['student_id_number']] = {
                'completed': row['completed_sessions'] or 0,
                'active': row['active_sessions'] or 0,
            }

    cursor.close()
    db.close()

    students = []
    for user in users:
        full_name = f"{user['last_name']}, {user['first_name']}"
        if user.get('middle_name'):
            full_name = f"{full_name} {user['middle_name']}"

        usage = remaining_lookup.get(user['id_number'], {'completed': 0, 'active': 0})
        remaining_sessions = max(TOTAL_SESSION_LIMIT - usage['completed'] - usage['active'], 0)

        students.append({
            'id_number': user['id_number'],
            'name': full_name,
            'year_level': user['course_level'],
            'course': user['course'],
            'remaining': remaining_sessions,
        })

    return render_template('admin_students.html', students=students)


@app.route('/admin/students/add', methods=['GET', 'POST'])
def admin_add_student():
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    if request.method == 'POST':
        id_number = request.form['id_number'].strip()
        last_name = request.form['last_name'].strip()
        first_name = request.form['first_name'].strip()
        middle_name = request.form.get('middle_name', '').strip()
        course = request.form['course'].strip()
        course_level = request.form['course_level'].strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not id_number or not last_name or not first_name or not course or not course_level:
            flash('Please fill out all required fields.', 'danger')
            return redirect(url_for('admin_add_student'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('admin_add_student'))

        hashed_pw = generate_password_hash(password)

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                """INSERT INTO users
                       (id_number, last_name, first_name, middle_name, course,
                        course_level, email, address, password)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (id_number, last_name, first_name, middle_name, course,
                 course_level, email, address, hashed_pw)
            )
            db.commit()
            flash('Student added successfully.', 'success')
            return redirect('/admin/students')
        except mysql.connector.IntegrityError:
            flash('ID number already exists.', 'danger')
        finally:
            cursor.close()
            db.close()

    return render_template('admin_add_student.html')


@app.route('/admin/students/reset_sessions', methods=['POST'])
def admin_reset_sessions():
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    db = get_db()
    ensure_sit_in_logs_table(db)
    cursor = db.cursor()
    cursor.execute("DELETE FROM sit_in_logs")
    db.commit()
    cursor.close()
    db.close()

    flash('All student sessions have been reset.', 'success')
    return redirect('/admin/students')


@app.route('/admin/sit-in', methods=['GET', 'POST'])
def admin_sit_in():
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    searched_id = ''
    student = None
    remaining_sessions = None
    active_session = None

    selected_purpose = ''

    if request.method == 'POST':
        searched_id = (request.form.get('id_number') or '').strip()
        lab_code = (request.form.get('lab_code') or '').strip()
        purpose = (request.form.get('purpose') or '').strip()
        selected_purpose = purpose

        if not searched_id:
            flash('Please enter a student ID.', 'warning')
        else:
            db = get_db()
            ensure_sit_in_logs_table(db)
            cursor = db.cursor(dictionary=True)

            student, remaining_sessions, active_session, completed_sessions = lookup_student_session(cursor, searched_id)

            if not student:
                flash('Student not found.', 'danger')
            elif active_session:
                flash('Student already has an active sit-in session.', 'warning')
            elif remaining_sessions <= 0:
                flash('Student has no remaining sessions.', 'warning')
            else:
                lab_info = LAB_LOOKUP.get(lab_code)
                if not lab_info:
                    flash('Please select a valid lab.', 'warning')
                else:
                    cursor.execute("""
                        SELECT COUNT(*) AS lab_taken
                        FROM sit_in_logs
                        WHERE lab=%s AND status='active'
                    """, (lab_code,))
                    lab_taken = cursor.fetchone()['lab_taken']

                    if lab_taken >= lab_info['capacity']:
                        flash(f"{lab_info['label']} is currently full.", 'warning')
                    else:
                        purpose_value = purpose if purpose else 'General use'
                        cursor.execute("""
                            INSERT INTO sit_in_logs (student_id_number, purpose, lab, session_no, status)
                            VALUES (%s, %s, %s, %s, 'active')
                        """, (searched_id, purpose_value, lab_code, completed_sessions + 1))
                        db.commit()
                        cursor.close()
                        db.close()
                        flash('Sit-in session started for student.', 'success')
                        return redirect(f"/admin/sit-in?id_number={searched_id}")

            cursor.close()
            db.close()
    else:
        searched_id = (request.args.get('id_number') or '').strip()
        if searched_id:
            db = get_db()
            ensure_sit_in_logs_table(db)
            cursor = db.cursor(dictionary=True)
            student, remaining_sessions, active_session, _ = lookup_student_session(cursor, searched_id)
            cursor.close()
            db.close()

    student_name = ''
    if student:
        student_name = f"{student['last_name']}, {student['first_name']}"
        if student.get('middle_name'):
            student_name = f"{student_name} {student['middle_name']}"

    return render_template('admin_sit_in.html',
                           labs=LABS,
                           purposes=PURPOSES,
                           searched_id=searched_id,
                           student=student,
                           student_name=student_name,
                           remaining_sessions=remaining_sessions,
                           active_session=active_session,
                           selected_purpose=selected_purpose)


@app.route('/admin/sit-in/lookup')
def admin_sit_in_lookup():
    if not is_admin_user():
        return jsonify({'found': False, 'message': 'Unauthorized.'}), 403

    student_id = (request.args.get('id_number') or '').strip()
    if not student_id:
        return jsonify({'found': False, 'message': 'Please enter a student ID.'}), 400

    db = get_db()
    ensure_sit_in_logs_table(db)
    cursor = db.cursor(dictionary=True)

    student, remaining_sessions, active_session, _ = lookup_student_session(cursor, student_id)
    cursor.close()
    db.close()

    if not student:
        return jsonify({'found': False, 'message': 'Student not found.'})

    full_name = f"{student['last_name']}, {student['first_name']}"
    if student.get('middle_name'):
        full_name = f"{full_name} {student['middle_name']}"

    return jsonify({
        'found': True,
        'student': {
            'id_number': student['id_number'],
            'full_name': full_name,
            'course': student['course'],
            'course_level': student['course_level']
        },
        'remaining_sessions': remaining_sessions,
        'active_session': active_session
    })


@app.route('/admin/sit-in-records')
def admin_sit_in_records():
    db = get_db()
    ensure_sit_in_logs_table(db)
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            s.id AS sit_id,
            s.student_id_number AS id_number,
            CONCAT(
                COALESCE(u.last_name, ''),
                CASE WHEN COALESCE(u.last_name, '') <> '' THEN ', ' ELSE '' END,
                COALESCE(u.first_name, ''),
                CASE
                    WHEN COALESCE(u.middle_name, '') <> '' THEN CONCAT(' ', u.middle_name)
                    ELSE ''
                END
            ) AS name,
            COALESCE(s.purpose, '-') AS purpose,
            COALESCE(s.lab, '-') AS lab,
            s.session_no AS session,
            s.status AS status
        FROM sit_in_logs s
        LEFT JOIN users u ON u.id_number = s.student_id_number
        WHERE s.status = 'active'
        ORDER BY s.started_at DESC
    """)
    current_sitins = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('admin_sit_in_records.html', current_sitins=current_sitins)


@app.route('/admin/sit-in/<int:sit_in_id>/complete', methods=['POST'])
def admin_complete_sit_in(sit_in_id):
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    db = get_db()
    ensure_sit_in_logs_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, status
        FROM sit_in_logs
        WHERE id=%s
        LIMIT 1
    """, (sit_in_id,))
    record = cursor.fetchone()

    if not record:
        flash('Sit-in session not found.', 'warning')
    elif record['status'] != 'active':
        flash('Sit-in session is already completed.', 'info')
    else:
        cursor.execute("""
            UPDATE sit_in_logs
            SET status='completed', ended_at=NOW()
            WHERE id=%s
        """, (sit_in_id,))
        db.commit()
        flash('Sit-in session ended successfully.', 'success')

    cursor.close()
    db.close()
    return redirect(url_for('admin_sit_in_records'))


@app.route('/admin/students/<id_number>/edit', methods=['GET', 'POST'])
def admin_edit_student(id_number):
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        last_name = request.form.get('last_name', '').strip()
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        course = request.form.get('course', '').strip()
        course_level = request.form.get('course_level', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()

        if not last_name or not first_name or not course or not course_level:
            cursor.close()
            db.close()
            flash('Last name, first name, course, and year level are required.', 'danger')
            return redirect(url_for('admin_edit_student', id_number=id_number))

        cursor.execute("""
            UPDATE users
            SET last_name=%s,
                first_name=%s,
                middle_name=%s,
                course=%s,
                course_level=%s,
                email=%s,
                address=%s
            WHERE id_number=%s
              AND id_number NOT LIKE 'adm-%'
        """, (last_name, first_name, middle_name, course, course_level, email, address, id_number))
        db.commit()

        if cursor.rowcount == 0:
            cursor.close()
            db.close()
            flash('Student not found or no changes were made.', 'warning')
            return redirect('/admin/students')

        cursor.close()
        db.close()
        flash('Student details updated successfully.', 'success')
        return redirect('/admin/students')

    cursor.execute("""
        SELECT id_number, last_name, first_name, middle_name, course, course_level, email, address
        FROM users
        WHERE id_number = %s
          AND id_number NOT LIKE 'adm-%'
        LIMIT 1
    """, (id_number,))
    student = cursor.fetchone()
    cursor.close()
    db.close()

    if not student:
        flash('Student not found.', 'danger')
        return redirect('/admin/students')

    return render_template('admin_edit_student.html', student=student)


@app.route('/admin/students/<id_number>/delete', methods=['POST'])
def admin_delete_student(id_number):
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        DELETE FROM users
        WHERE id_number = %s
          AND id_number NOT LIKE 'adm-%'
    """, (id_number,))
    db.commit()

    if cursor.rowcount > 0:
        flash('Student deleted successfully.', 'success')
    else:
        flash('Student not found.', 'warning')

    cursor.close()
    db.close()
    return redirect('/admin/students')


@app.route('/admin/sit-in-reports')
def admin_sit_in_reports():
    form_values, criteria = build_report_filters(request.args)
    history, summary = fetch_sit_in_history(
        student_id=criteria['student_id'],
        status=criteria['status'],
        date_from=criteria['date_from'],
        date_to=criteria['date_to']
    )

    query_params = {
        'student_id': form_values['student_id'],
        'status': form_values['status'] if form_values['status'] in ('active', 'completed') else '',
        'date_from': form_values['date_from'],
        'date_to': form_values['date_to']
    }
    filtered_query = urlencode({k: v for k, v in query_params.items() if v})

    return render_template('admin_sit_in_reports.html',
                           history=history,
                           summary=summary,
                           filters=form_values,
                           filtered_query=filtered_query,
                           has_history=bool(history))


@app.route('/admin/feedback-reports')
def admin_feedback_reports():
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    db = get_db()
    ensure_user_feedback_table(db)
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            f.id,
            f.rating,
            f.feedback_text,
            f.created_at,
            u.id_number,
            u.last_name,
            u.first_name,
            u.middle_name,
            u.course,
            u.course_level,
            s.lab,
            s.purpose,
            s.started_at,
            s.ended_at
        FROM user_feedback f
        LEFT JOIN users u ON u.id_number = f.student_id_number
        LEFT JOIN sit_in_logs s ON s.id = f.sit_in_log_id
        ORDER BY f.created_at DESC
    """)
    feedback_rows = cursor.fetchall()
    cursor.close()
    db.close()

    for row in feedback_rows:
        full_name = f"{row.get('last_name') or ''}, {row.get('first_name') or ''}"
        if row.get('middle_name'):
            full_name = f"{full_name} {row['middle_name']}"
        row['full_name'] = full_name.strip(', ')

        lab_info = LAB_LOOKUP.get(row['lab'])
        row['lab_label'] = lab_info['label'] if lab_info else (row['lab'] or 'Unassigned')

    return render_template('admin_feedback_reports.html', feedback_rows=feedback_rows)


@app.route('/admin/sit-in-reports/pdf')
def admin_sit_in_reports_pdf():
    form_values, criteria = build_report_filters(request.args)
    history, summary = fetch_sit_in_history(
        student_id=criteria['student_id'],
        status=criteria['status'],
        date_from=criteria['date_from'],
        date_to=criteria['date_to']
    )

    if not history:
        flash('No sit-in data available for the selected filters.', 'info')
        redirect_url = '/admin/sit-in-reports'
        if any(form_values.values()):
            query = urlencode({k: v for k, v in form_values.items() if v})
            redirect_url = f"{redirect_url}?{query}"
        return redirect(redirect_url)

    try:
        pagesizes = importlib.import_module('reportlab.lib.pagesizes')
        pdfgen_canvas = importlib.import_module('reportlab.pdfgen.canvas')
        units = importlib.import_module('reportlab.lib.units')
    except ImportError:
        flash('ReportLab is required to export PDF. Install it via "pip install reportlab".', 'danger')
        redirect_url = '/admin/sit-in-reports'
        if any(form_values.values()):
            query = urlencode({k: v for k, v in form_values.items() if v})
            redirect_url = f"{redirect_url}?{query}"
        return redirect(redirect_url)

    landscape = pagesizes.landscape
    letter = pagesizes.letter
    canvas_cls = pdfgen_canvas.Canvas
    inch = units.inch

    buffer = io.BytesIO()
    pdf = canvas_cls(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)
    margin = 0.7 * inch

    title = 'CCS Sit-in History Report'
    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(margin, height - margin, title)
    pdf.setFont('Helvetica', 10)
    filter_text = []
    if form_values['student_id']:
        filter_text.append(f"Student ID: {form_values['student_id']}")
    if criteria['status']:
        filter_text.append(f"Status: {criteria['status'].capitalize()}")
    if form_values['date_from']:
        filter_text.append(f"From: {form_values['date_from']}")
    if form_values['date_to']:
        filter_text.append(f"To: {form_values['date_to']}")
    pdf.drawString(margin, height - margin - 14, ' | '.join(filter_text) or 'All records')
    pdf.drawString(margin, height - margin - 28, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    pdf.setFont('Helvetica-Bold', 10)
    headers = ['ID', 'Student', 'Course', 'Lab', 'Purpose', 'Status', 'Started', 'Ended']
    col_widths = [0.5, 1.5, 1.2, 1.0, 2.2, 0.7, 1.2, 1.2]
    col_positions = [margin]
    for width_ratio in col_widths[:-1]:
        col_positions.append(col_positions[-1] + width_ratio * inch)

    y = height - margin - 50
    for idx, header in enumerate(headers):
        pdf.drawString(col_positions[idx], y, header)
    pdf.line(margin, y - 2, width - margin, y - 2)
    y -= 16

    pdf.setFont('Helvetica', 9)
    for record in history:
        if y < margin:
            pdf.showPage()
            pdf.setFont('Helvetica-Bold', 10)
            for idx, header in enumerate(headers):
                pdf.drawString(col_positions[idx], height - margin, header)
            pdf.line(margin, height - margin - 2, width - margin, height - margin - 2)
            pdf.setFont('Helvetica', 9)
            y = height - margin - 16

        values = [
            str(record['session_no'] or record['id']),
            record['full_name'],
            (record['course'] or ''),
            record['lab_label'],
            (record['purpose'] or 'General use'),
            record['status'].capitalize(),
            record['started_at'].strftime('%Y-%m-%d %H:%M') if record['started_at'] else '',
            record['ended_at'].strftime('%Y-%m-%d %H:%M') if record['ended_at'] else ''
        ]
        for idx, value in enumerate(values):
            pdf.drawString(col_positions[idx], y, value)
        y -= 14

    pdf.setFont('Helvetica-Bold', 10)
    pdf.drawString(margin, y - 10, f"Total records: {summary['total']} | Completed: {summary['completed']} | Active: {summary['active']}")

    pdf.save()
    buffer.seek(0)

    filename = 'sit_in_report.pdf'
    if form_values['date_from'] and form_values['date_to']:
        filename = f"sit_in_report_{form_values['date_from']}_to_{form_values['date_to']}.pdf"

    return send_file(buffer, download_name=filename, as_attachment=True, mimetype='application/pdf')


@app.route('/admin/reservations')
def admin_reservations():
    return render_template('admin_reservations.html')


@app.route('/login_user', methods=['POST'])
def login_user():
    id_number = (request.form.get('id_number') or '').strip()
    password = request.form['password']

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id_number = %s", (id_number,))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    if user and check_password_hash(user['password'], password):
        session['user'] = {
            'id_number': user['id_number'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'middle_name': user['middle_name'] or '',
            'course': user['course'],
            'course_level': user['course_level'],
            'email': user['email'] or '',
            'address': user['address'] or '',
            'photo_path': user.get('photo_path') or '',
        }
        display_name = user.get('first_name') or 'User'
        flash(f"Welcome back, {display_name}!", 'success')
        if user['id_number'].lower().startswith('adm-'):
            return redirect('/admin')
        return redirect('/dashboard')

    flash('Invalid ID number or password.', 'danger')
    return redirect('/')


@app.route('/register_user', methods=['POST'])
def register_user():
    id_number = request.form['id_number']
    last_name = request.form['last_name']
    first_name = request.form['first_name']
    middle_name = request.form['middle_name']
    course = request.form['course']
    course_level = request.form['course_level']
    email = request.form['email']
    address = request.form['address']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    if not id_number.isdigit():
        flash('Only numeric values are accepted for ID number.', 'danger')
        return redirect('/register')

    if password != confirm_password:
        flash('Passwords do not match.', 'danger')
        return redirect('/register')

    hashed_pw = generate_password_hash(password)

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            """INSERT INTO users
               (id_number, last_name, first_name, middle_name, course,
                course_level, email, address, password)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (id_number, last_name, first_name, middle_name, course,
             course_level, email, address, hashed_pw)
        )
        db.commit()
        flash('Registration successful! You can now log in.', 'success')
    except mysql.connector.IntegrityError:
        flash('ID number already exists.', 'danger')
    finally:
        cursor.close()
        db.close()

    return redirect('/')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    user = session['user']
    db = get_db()
    ensure_sit_in_logs_table(db)
    ensure_user_feedback_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(*) AS total_completed
        FROM sit_in_logs
        WHERE student_id_number=%s AND status='completed'
    """, (user['id_number'],))
    sessions_used = cursor.fetchone()['total_completed']

    cursor.execute("""
        SELECT id, lab, purpose, started_at
        FROM sit_in_logs
        WHERE student_id_number=%s AND status='active'
        ORDER BY started_at DESC
        LIMIT 1
    """, (user['id_number'],))
    active_session = cursor.fetchone()

    cursor.execute("""
        SELECT lab, COUNT(*) AS taken
        FROM sit_in_logs
        WHERE status='active'
        GROUP BY lab
    """)
    lab_counts = {row['lab']: row['taken'] for row in cursor.fetchall()}

    cursor.execute("""
        SELECT
            s.id,
            s.lab,
            s.purpose,
            s.status,
            s.started_at,
            s.ended_at,
            f.id AS feedback_id
        FROM sit_in_logs s
        LEFT JOIN user_feedback f ON f.sit_in_log_id = s.id
        WHERE s.student_id_number=%s
        ORDER BY s.started_at DESC
        LIMIT 5
    """, (user['id_number'],))
    recent_sessions = cursor.fetchall()

    cursor.close()
    db.close()

    if active_session:
        lab_info = LAB_LOOKUP.get(active_session['lab'])
        active_session['lab_label'] = lab_info['label'] if lab_info else (active_session['lab'] or 'Unassigned')

    sessions_remaining = max(TOTAL_SESSION_LIMIT - sessions_used - (1 if active_session else 0), 0)

    lab_cards = []
    for lab in LABS:
        taken = lab_counts.get(lab['code'], 0)
        lab_cards.append({
            'code': lab['code'],
            'label': lab['label'],
            'description': lab['description'],
            'capacity': lab['capacity'],
            'taken': taken,
            'available': max(lab['capacity'] - taken, 0),
            'is_full': taken >= lab['capacity']
        })

    for session_item in recent_sessions:
        lab_info = LAB_LOOKUP.get(session_item['lab'])
        session_item['lab_label'] = lab_info['label'] if lab_info else (session_item['lab'] or 'Unassigned')

    can_start_session = active_session is None and sessions_remaining > 0

    return render_template('dashboard.html',
                           user=user,
                           sessions_used=sessions_used,
                           sessions_remaining=sessions_remaining,
                           sessions_total=TOTAL_SESSION_LIMIT,
                           active_session=active_session,
                           lab_cards=lab_cards,
                           announcements=ANNOUNCEMENTS,
                           recent_sessions=recent_sessions,
                           can_start_session=can_start_session)


@app.route('/feedback/submit', methods=['POST'])
def submit_feedback():
    if 'user' not in session:
        return redirect('/')

    user = session['user']
    sit_in_log_id = request.form.get('sit_in_log_id')
    rating_value = request.form.get('rating')
    feedback_text = (request.form.get('feedback_text') or '').strip()

    if not sit_in_log_id or not feedback_text:
        flash('Please provide feedback before submitting.', 'warning')
        return redirect('/dashboard')

    try:
        sit_in_log_id = int(sit_in_log_id)
    except (TypeError, ValueError):
        flash('Invalid session selected for feedback.', 'danger')
        return redirect('/dashboard')

    if not rating_value:
        flash('Please select a rating from 1 to 5.', 'warning')
        return redirect('/dashboard')

    try:
        rating = int(rating_value)
    except ValueError:
        flash('Rating must be a number between 1 and 5.', 'danger')
        return redirect('/dashboard')

    if rating < 1 or rating > 5:
        flash('Rating must be between 1 and 5.', 'danger')
        return redirect('/dashboard')

    db = get_db()
    ensure_sit_in_logs_table(db)
    ensure_user_feedback_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, status
        FROM sit_in_logs
        WHERE id=%s AND student_id_number=%s
        LIMIT 1
    """, (sit_in_log_id, user['id_number']))
    session_row = cursor.fetchone()

    if not session_row or session_row['status'] != 'completed':
        cursor.close()
        db.close()
        flash('Feedback is only available for completed sessions.', 'warning')
        return redirect('/dashboard')

    cursor.execute("""
        SELECT id
        FROM user_feedback
        WHERE sit_in_log_id=%s AND student_id_number=%s
        LIMIT 1
    """, (sit_in_log_id, user['id_number']))
    if cursor.fetchone():
        cursor.close()
        db.close()
        flash('Feedback already submitted for this session.', 'info')
        return redirect('/dashboard')

    cursor.execute("""
        INSERT INTO user_feedback (student_id_number, sit_in_log_id, rating, feedback_text)
        VALUES (%s, %s, %s, %s)
    """, (user['id_number'], sit_in_log_id, rating, feedback_text))
    db.commit()
    cursor.close()
    db.close()

    flash('Thank you for your feedback!', 'success')
    return redirect('/dashboard')


@app.route('/sit_in/start', methods=['POST'])
def start_sit_in():
    if 'user' not in session:
        return redirect('/')

    user = session['user']
    lab_code = request.form.get('lab_code')
    purpose = (request.form.get('purpose') or '').strip()

    lab_info = LAB_LOOKUP.get(lab_code)
    if not lab_info:
        flash('Invalid lab selected.', 'danger')
        return redirect('/dashboard')

    db = get_db()
    ensure_sit_in_logs_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(*) AS active_count
        FROM sit_in_logs
        WHERE student_id_number=%s AND status='active'
    """, (user['id_number'],))
    if cursor.fetchone()['active_count'] > 0:
        cursor.close()
        db.close()
        flash('You already have an active sit-in session.', 'warning')
        return redirect('/dashboard')

    cursor.execute("""
        SELECT COUNT(*) AS completed_count
        FROM sit_in_logs
        WHERE student_id_number=%s AND status='completed'
    """, (user['id_number'],))
    completed_sessions = cursor.fetchone()['completed_count']
    if completed_sessions >= TOTAL_SESSION_LIMIT:
        cursor.close()
        db.close()
        flash('You have reached the maximum number of sessions.', 'warning')
        return redirect('/dashboard')

    cursor.execute("""
        SELECT COUNT(*) AS lab_taken
        FROM sit_in_logs
        WHERE lab=%s AND status='active'
    """, (lab_code,))
    lab_taken = cursor.fetchone()['lab_taken']
    if lab_taken >= lab_info['capacity']:
        cursor.close()
        db.close()
        flash(f"{lab_info['label']} is currently full. Please choose another lab.", 'warning')
        return redirect('/dashboard')

    purpose_value = purpose if purpose else 'General use'

    cursor.execute("""
        INSERT INTO sit_in_logs (student_id_number, purpose, lab, session_no, status)
        VALUES (%s, %s, %s, %s, 'active')
    """, (user['id_number'], purpose_value, lab_code, completed_sessions + 1))
    db.commit()

    cursor.close()
    db.close()

    flash('Sit-in session started.', 'success')
    return redirect('/dashboard')


@app.route('/sit_in/end', methods=['POST'])
def end_sit_in():
    if 'user' not in session:
        return redirect('/')

    user = session['user']
    db = get_db()
    ensure_sit_in_logs_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id
        FROM sit_in_logs
        WHERE student_id_number=%s AND status='active'
        ORDER BY started_at DESC
        LIMIT 1
    """, (user['id_number'],))
    active_session = cursor.fetchone()

    if not active_session:
        cursor.close()
        db.close()
        flash('No active sit-in session to end.', 'info')
        return redirect('/dashboard')

    cursor.execute("""
        UPDATE sit_in_logs
        SET status='completed', ended_at=NOW()
        WHERE id=%s
    """, (active_session['id'],))
    db.commit()
    cursor.close()
    db.close()

    flash('Sit-in session ended. Thank you!', 'success')
    return redirect('/dashboard')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user' not in session:
        return redirect('/')

    user = session['user']
    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        course = request.form['course']
        course_level = request.form['course_level']
        email = request.form['email']
        address = request.form['address']
        photo_file = request.files.get('photo')
        photo_path = user.get('photo_path') or ''
        new_photo_path = photo_path
        photo_changed = False

        if photo_file and photo_file.filename:
            if not allowed_file(photo_file.filename):
                flash('Invalid photo type. Use PNG, JPG, or GIF.', 'danger')
                return redirect('/edit_profile')

            filename = secure_filename(photo_file.filename)
            ext = os.path.splitext(filename)[1].lower()
            stored_name = f"{user['id_number']}{ext}"
            upload_dir = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            photo_file.save(os.path.join(upload_dir, stored_name))
            new_photo_path = f"uploads/{stored_name}"
            photo_changed = new_photo_path != photo_path

        changes = (
            first_name != user['first_name'] or
            middle_name != user['middle_name'] or
            last_name != user['last_name'] or
            course != user['course'] or
            course_level != user['course_level'] or
            email != user['email'] or
            address != user['address'] or
            photo_changed
        )

        if changes:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                UPDATE users SET first_name=%s, middle_name=%s, last_name=%s, course=%s, course_level=%s, email=%s, address=%s, photo_path=%s
                WHERE id_number=%s
            """, (first_name, middle_name, last_name, course, course_level, email, address, new_photo_path, user['id_number']))
            db.commit()
            cursor.close()
            db.close()

            session['user'].update({
                'first_name': first_name,
                'middle_name': middle_name,
                'last_name': last_name,
                'course': course,
                'course_level': course_level,
                'email': email,
                'address': address,
                'photo_path': new_photo_path,
            })
            flash('Changes successful.', 'success')
        else:
            flash('No changes were made.', 'info')
        return redirect('/dashboard')

    return render_template('edit_profile.html', user=user)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)