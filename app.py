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
app.config['SOFTWARE_UPLOAD_FOLDER'] = os.path.join('static', 'uploads', 'software')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_SOFTWARE_EXTENSIONS = {'exe', 'msi', 'zip', 'rar', '7z', 'pdf', 'doc', 'docx'}

TOTAL_SESSION_LIMIT = 30

LABS = [
    {
        'code': 'LAB524',
        'label': 'Laboratory 524',
        'description': 'Main programming laboratory',
        'capacity': 50,
        'software': ['Python', 'VS Code', 'Cisco Packet Tracer']
    },
    {
        'code': 'LAB526',
        'label': 'Laboratory 526',
        'description': 'Software development laboratory',
        'capacity': 50,
        'software': ['Java', 'MySQL', 'VS Code']
    },
    {
        'code': 'LAB528',
        'label': 'Laboratory 528',
        'description': 'Systems and networking laboratory',
        'capacity': 50,
        'software': ['Cisco Packet Tracer', 'Wireshark', 'Linux Tools']
    },
    {
        'code': 'LAB530',
        'label': 'Laboratory 530',
        'description': 'Capstone and research laboratory',
        'capacity': 50,
        'software': ['Python', 'VS Code', 'Research Tools']
    },
]

RESERVATION_SLOTS = [
    '07:30-09:00',
    '09:00-10:30',
    '10:30-12:00',
    '13:00-14:30',
    '14:30-16:00',
    '16:00-17:30'
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

ADMIN_SEAT_BLOCK_ID = 'admin-seat-block'

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


def allowed_software_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_SOFTWARE_EXTENSIONS


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
            admin_feedback_text TEXT DEFAULT NULL,
            admin_points_reason TEXT DEFAULT NULL,
            points_awarded INT NOT NULL DEFAULT 0,
            tidiness_status ENUM('tidy', 'not_tidy') DEFAULT NULL,
            admin_reviewed_at DATETIME DEFAULT NULL,
            admin_reviewer_id VARCHAR(20) DEFAULT NULL,
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

    # Backward-compatible column creation for existing databases.
    alter_statements = [
        "ALTER TABLE user_feedback ADD COLUMN admin_feedback_text TEXT DEFAULT NULL",
        "ALTER TABLE user_feedback ADD COLUMN admin_points_reason TEXT DEFAULT NULL",
        "ALTER TABLE user_feedback ADD COLUMN points_awarded INT NOT NULL DEFAULT 0",
        "ALTER TABLE user_feedback ADD COLUMN tidiness_status ENUM('tidy', 'not_tidy') DEFAULT NULL",
        "ALTER TABLE user_feedback ADD COLUMN admin_reviewed_at DATETIME DEFAULT NULL",
        "ALTER TABLE user_feedback ADD COLUMN admin_reviewer_id VARCHAR(20) DEFAULT NULL",
    ]
    for stmt in alter_statements:
        try:
            cursor.execute(stmt)
        except mysql.connector.Error:
            pass

    cursor.close()


def ensure_announcements_table(db):
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INT NOT NULL AUTO_INCREMENT,
            author VARCHAR(100) NOT NULL,
            body TEXT NOT NULL,
            created_by_id VARCHAR(20) DEFAULT NULL,
            status ENUM('active', 'archived') NOT NULL DEFAULT 'active',
            pinned TINYINT(1) NOT NULL DEFAULT 0,
            target_course VARCHAR(50) DEFAULT NULL,
            target_level VARCHAR(20) DEFAULT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            INDEX idx_announcements_status (status),
            INDEX idx_announcements_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # Backward-compatible column creation for existing databases.
    alter_statements = [
        "ALTER TABLE announcements ADD COLUMN pinned TINYINT(1) NOT NULL DEFAULT 0",
        "ALTER TABLE announcements ADD COLUMN target_course VARCHAR(50) DEFAULT NULL",
        "ALTER TABLE announcements ADD COLUMN target_level VARCHAR(20) DEFAULT NULL",
    ]
    for stmt in alter_statements:
        try:
            cursor.execute(stmt)
        except mysql.connector.Error:
            pass

    cursor.close()


def ensure_reservations_table(db):
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INT NOT NULL AUTO_INCREMENT,
            student_id_number VARCHAR(20) NOT NULL,
            lab_code VARCHAR(20) NOT NULL,
            seat_no INT NOT NULL,
            purpose VARCHAR(100) DEFAULT NULL,
            reservation_date DATE NOT NULL,
            reservation_slot VARCHAR(20) NOT NULL,
            status ENUM('pending', 'approved', 'checked_in', 'denied', 'cancelled', 'no_show') NOT NULL DEFAULT 'pending',
            admin_note VARCHAR(255) DEFAULT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            decided_at DATETIME DEFAULT NULL,
            decided_by VARCHAR(20) DEFAULT NULL,
            PRIMARY KEY (id),
            INDEX idx_reservation_student (student_id_number),
            INDEX idx_reservation_lab_date_slot (lab_code, reservation_date, reservation_slot),
            INDEX idx_reservation_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # Backward-compatible status expansion for existing databases.
    try:
        cursor.execute("""
            ALTER TABLE reservations
            MODIFY COLUMN status ENUM('pending', 'approved', 'checked_in', 'denied', 'cancelled', 'no_show')
            NOT NULL DEFAULT 'pending'
        """)
    except mysql.connector.Error:
        pass

    cursor.close()


def ensure_software_table(db):
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS software_assets (
            id INT NOT NULL AUTO_INCREMENT,
            title VARCHAR(150) NOT NULL,
            description TEXT DEFAULT NULL,
            lab_code VARCHAR(20) DEFAULT NULL,
            file_name VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_size INT NOT NULL,
            uploaded_by VARCHAR(50) DEFAULT NULL,
            status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            INDEX idx_software_status (status),
            INDEX idx_software_lab (lab_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    alter_statements = [
        "ALTER TABLE software_assets ADD COLUMN description TEXT DEFAULT NULL",
        "ALTER TABLE software_assets ADD COLUMN lab_code VARCHAR(20) DEFAULT NULL",
        "ALTER TABLE software_assets ADD COLUMN original_name VARCHAR(255) NOT NULL",
        "ALTER TABLE software_assets ADD COLUMN file_size INT NOT NULL",
        "ALTER TABLE software_assets ADD COLUMN uploaded_by VARCHAR(50) DEFAULT NULL",
        "ALTER TABLE software_assets ADD COLUMN status ENUM('active', 'inactive') NOT NULL DEFAULT 'active'",
    ]
    for stmt in alter_statements:
        try:
            cursor.execute(stmt)
        except mysql.connector.Error:
            pass

    cursor.close()


def ensure_users_table(db):
    cursor = db.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN lab_assigned VARCHAR(20) DEFAULT NULL")
    except mysql.connector.Error:
        pass
    cursor.close()


def ensure_rewards_table(db):
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rewards (
            id INT NOT NULL AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            description TEXT DEFAULT NULL,
            points_cost INT NOT NULL,
            is_physical TINYINT(1) NOT NULL DEFAULT 0,
            stock INT DEFAULT NULL,
            status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            INDEX idx_rewards_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    alter_statements = [
        "ALTER TABLE rewards ADD COLUMN description TEXT DEFAULT NULL",
        "ALTER TABLE rewards ADD COLUMN is_physical TINYINT(1) NOT NULL DEFAULT 0",
        "ALTER TABLE rewards ADD COLUMN stock INT DEFAULT NULL",
        "ALTER TABLE rewards ADD COLUMN status ENUM('active', 'inactive') NOT NULL DEFAULT 'active'",
    ]
    for stmt in alter_statements:
        try:
            cursor.execute(stmt)
        except mysql.connector.Error:
            pass

    cursor.execute("SELECT COUNT(*) AS total FROM rewards")
    total = (cursor.fetchone() or {}).get('total', 0)
    if not total:
        seed_rewards = [
            ('CCS Sticker Pack', 'Official CCS sticker set.', 20, 1, 50, 'active'),
            ('Lanyard / ID Holder', 'CCS lanyard with ID holder.', 40, 1, 20, 'active'),
            ('Notebook / Pen Set', 'Branded notebook and pen.', 60, 1, 15, 'active'),
            ('Extra 30 Minutes Lab Time', 'Extend a lab session by 30 minutes.', 15, 0, None, 'active'),
            ('Leaderboard Highlight Badge (1 Week)', 'Show a highlight badge for one week.', 50, 0, None, 'active'),
            ('CCS T-Shirt', 'Limited edition CCS shirt.', 200, 1, 5, 'active'),
        ]
        cursor.executemany("""
            INSERT INTO rewards (name, description, points_cost, is_physical, stock, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, seed_rewards)
        db.commit()

    cursor.close()


def ensure_reward_redemptions_table(db):
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reward_redemptions (
            id INT NOT NULL AUTO_INCREMENT,
            reward_id INT NOT NULL,
            reward_name VARCHAR(100) NOT NULL,
            student_id_number VARCHAR(20) NOT NULL,
            points_cost INT NOT NULL,
            is_physical TINYINT(1) NOT NULL DEFAULT 0,
            status ENUM('pending', 'approved', 'ready', 'claimed', 'denied', 'cancelled')
                NOT NULL DEFAULT 'pending',
            admin_note VARCHAR(255) DEFAULT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT NULL,
            ready_at DATETIME DEFAULT NULL,
            claimed_at DATETIME DEFAULT NULL,
            PRIMARY KEY (id),
            INDEX idx_redemptions_student (student_id_number),
            INDEX idx_redemptions_status (status),
            CONSTRAINT fk_redemptions_reward
                FOREIGN KEY (reward_id) REFERENCES rewards(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    cursor.close()


def get_points_summary(cursor, student_id_number):
    cursor.execute("""
        SELECT COALESCE(SUM(points_awarded), 0) AS earned_points
        FROM user_feedback
        WHERE student_id_number=%s
    """, (student_id_number,))
    earned_points = (cursor.fetchone() or {}).get('earned_points', 0)

    cursor.execute("""
        SELECT COALESCE(SUM(points_cost), 0) AS spent_points
        FROM reward_redemptions
        WHERE student_id_number=%s
          AND status IN ('pending', 'approved', 'ready', 'claimed')
    """, (student_id_number,))
    spent_points = (cursor.fetchone() or {}).get('spent_points', 0)

    available_points = max(int(earned_points) - int(spent_points), 0)
    return int(earned_points), int(spent_points), available_points


def get_taken_seats(cursor, lab_code, reservation_date, reservation_slot):
    cursor.execute("""
        SELECT seat_no
        FROM reservations
        WHERE lab_code=%s
          AND reservation_date=%s
          AND reservation_slot=%s
            AND status IN ('pending', 'approved', 'checked_in')
    """, (lab_code, reservation_date, reservation_slot))
    return {row['seat_no'] for row in cursor.fetchall()}


def get_session_usage(cursor, student_id_number):
    cursor.execute("""
        SELECT
            SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed_count,
            SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) AS active_count
        FROM sit_in_logs
        WHERE student_id_number=%s
    """, (student_id_number,))
    sit_in_counts = cursor.fetchone() or {}
    completed_count = sit_in_counts.get('completed_count') or 0
    active_count = sit_in_counts.get('active_count') or 0

    sessions_used = completed_count
    remaining_sessions = max(TOTAL_SESSION_LIMIT - sessions_used - active_count, 0)

    return {
        'completed': completed_count,
        'active': active_count,
        'used': sessions_used,
        'remaining': remaining_sessions,
    }


def fetch_announcements(limit=10, for_user=None):
    db = get_db()
    ensure_announcements_table(db)
    cursor = db.cursor(dictionary=True)
    safe_limit = max(1, min(int(limit), 50))

    query = """
        SELECT id, author, body, created_at, pinned, target_course, target_level
        FROM announcements
        WHERE status='active'
    """
    params = []
    if for_user and not str(for_user.get('id_number', '')).lower().startswith('adm-'):
        query += """
            AND (target_course IS NULL OR target_course='' OR target_course=%s)
            AND (target_level IS NULL OR target_level='' OR target_level=%s)
        """
        params.extend([(for_user.get('course') or '').strip(), str(for_user.get('course_level') or '').strip()])

    query += f" ORDER BY pinned DESC, created_at DESC LIMIT {safe_limit}"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    db.close()

    announcements = []
    for row in rows:
        created_at = row.get('created_at')
        announcements.append({
            'id': row.get('id'),
            'author': row.get('author') or 'CCS Admin',
            'body': row.get('body') or '',
            'date': created_at.strftime('%Y-%b-%d') if created_at else '',
            'pinned': bool(row.get('pinned')),
            'target_course': row.get('target_course') or '',
            'target_level': row.get('target_level') or ''
        })
    return announcements


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
    ensure_announcements_table(db)

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

    cursor.execute("""
        SELECT id, author, body, created_at, pinned, target_course, target_level
        FROM announcements
        WHERE status='active'
        ORDER BY pinned DESC, created_at DESC
        LIMIT 15
    """)
    announcement_rows = cursor.fetchall()

    cursor.execute("""
        SELECT DISTINCT course
        FROM users
        WHERE id_number NOT LIKE 'adm-%' AND course IS NOT NULL AND course <> ''
        ORDER BY course ASC
    """)
    course_rows = cursor.fetchall()

    cursor.execute("""
        SELECT DISTINCT course_level
        FROM users
        WHERE id_number NOT LIKE 'adm-%' AND course_level IS NOT NULL AND course_level <> ''
        ORDER BY CAST(course_level AS UNSIGNED), course_level ASC
    """)
    level_rows = cursor.fetchall()

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

    announcements = []
    for row in announcement_rows:
        created_at = row.get('created_at')
        announcements.append({
            'id': row.get('id'),
            'author': row.get('author') or 'CCS Admin',
            'body': row.get('body') or '',
            'date': created_at.strftime('%Y-%b-%d') if created_at else '',
            'pinned': bool(row.get('pinned')),
            'target_course': row.get('target_course') or '',
            'target_level': row.get('target_level') or ''
        })

    target_options = {
        'courses': [row['course'] for row in course_rows],
        'levels': [str(row['course_level']) for row in level_rows]
    }

    return stats, announcements, chart_data, target_options


def fetch_leaderboard(limit=10):
    safe_limit = max(1, min(int(limit), 100))

    db = get_db()
    ensure_sit_in_logs_table(db)
    ensure_user_feedback_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            u.id_number,
            u.last_name,
            u.first_name,
            u.middle_name,
            u.course,
            u.course_level,
            COALESCE(stats.admin_points, 0) AS admin_points,
            COALESCE(stats.completed_sessions, 0) AS completed_sessions,
            COALESCE(stats.total_minutes, 0) AS total_minutes,
            COALESCE(stats.average_minutes, 0) AS average_minutes,
            COALESCE(stats.total_minutes, 0) AS total_minutes_for_sort
        FROM users u
        LEFT JOIN (
            SELECT
                s.student_id_number,
                SUM(COALESCE(f.points_awarded, 0)) AS admin_points,
                SUM(CASE WHEN s.status='completed' THEN 1 ELSE 0 END) AS completed_sessions,
                SUM(
                    CASE
                        WHEN s.status='completed' AND s.ended_at IS NOT NULL
                            THEN TIMESTAMPDIFF(MINUTE, s.started_at, s.ended_at)
                        ELSE 0
                    END
                ) AS total_minutes,
                CASE
                    WHEN SUM(CASE WHEN s.status='completed' AND s.ended_at IS NOT NULL THEN 1 ELSE 0 END) > 0
                        THEN SUM(
                            CASE
                                WHEN s.status='completed' AND s.ended_at IS NOT NULL
                                    THEN TIMESTAMPDIFF(MINUTE, s.started_at, s.ended_at)
                                ELSE 0
                            END
                        ) / SUM(CASE WHEN s.status='completed' AND s.ended_at IS NOT NULL THEN 1 ELSE 0 END)
                    ELSE 0
                END AS average_minutes
            FROM sit_in_logs s
            LEFT JOIN user_feedback f ON f.sit_in_log_id = s.id
            GROUP BY s.student_id_number
        ) stats ON stats.student_id_number = u.id_number
        WHERE u.id_number NOT LIKE 'adm-%'
        ORDER BY average_minutes DESC, completed_sessions DESC, total_minutes DESC, u.last_name ASC, u.first_name ASC
    """)
    rows = cursor.fetchall()
    cursor.close()
    db.close()

    for index, row in enumerate(rows, start=1):
        row['rank'] = index
        middle_name = f" {row['middle_name']}" if row.get('middle_name') else ''
        row['full_name'] = f"{row.get('last_name') or ''}, {row.get('first_name') or ''}{middle_name}".strip(', ')
        total_minutes = row.get('total_minutes') or 0
        average_minutes = row.get('average_minutes') or 0
        row['total_hours'] = round(total_minutes / 60, 2)
        row['average_hours'] = round(average_minutes / 60, 2)
        time_points = int(average_minutes // 30)
        row['admin_points'] = int(row.get('admin_points') or 0)
        row['total_points'] = time_points + row['admin_points']

    return rows[:safe_limit], rows


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

    usage = get_session_usage(cursor, student_id)
    completed_sessions = usage['completed']
    remaining_sessions = usage['remaining']

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
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            u.last_name,
            u.first_name,
            u.middle_name,
            u.course,
            u.course_level,
            stats.admin_points,
            stats.completed_sessions
        FROM users u
        JOIN (
            SELECT
                s.student_id_number,
                SUM(COALESCE(f.points_awarded, 0)) AS admin_points,
                SUM(CASE WHEN s.status='completed' THEN 1 ELSE 0 END) AS completed_sessions
            FROM sit_in_logs s
            LEFT JOIN user_feedback f ON f.sit_in_log_id = s.id
            GROUP BY s.student_id_number
        ) stats ON stats.student_id_number = u.id_number
        WHERE u.id_number NOT LIKE 'adm-%'
        ORDER BY admin_points DESC, completed_sessions DESC, u.last_name ASC
        LIMIT 5
    """)
    leaderboard = cursor.fetchall()

    for row in leaderboard:
        mname = f" {row['middle_name'][0]}." if row.get('middle_name') else ""
        row['display_name'] = f"{row['first_name']}{mname} {row['last_name']}"

    cursor.close()
    db.close()
    return render_template('login.html', leaderboard=leaderboard)


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
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    stats, announcements, chart_data, target_options = get_admin_dashboard_data()
    leaderboard_preview, _ = fetch_leaderboard(limit=5)
    return render_template('admin_dashboard.html',
                           stats=stats,
                           announcements=announcements,
                           chart_data=chart_data,
                           target_options=target_options,
                           leaderboard_preview=leaderboard_preview)


@app.route('/admin/analytics')
def admin_analytics():
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    db = get_db()
    ensure_sit_in_logs_table(db)
    ensure_reservations_table(db)
    ensure_user_feedback_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT AVG(TIMESTAMPDIFF(MINUTE, started_at, ended_at)) AS avg_minutes
        FROM sit_in_logs
        WHERE status='completed' AND ended_at IS NOT NULL
    """)
    avg_minutes = float((cursor.fetchone() or {}).get('avg_minutes') or 0)

    cursor.execute("""
        SELECT lab, COUNT(*) AS total
        FROM sit_in_logs
        WHERE lab IS NOT NULL
        GROUP BY lab
        ORDER BY total DESC
        LIMIT 1
    """)
    busiest_lab_row = cursor.fetchone() or {}

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM sit_in_logs
        WHERE started_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """)
    sitins_last_30 = int((cursor.fetchone() or {}).get('total') or 0)

    cursor.execute("""
        SELECT
            SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END) AS approved,
            SUM(CASE WHEN status='denied' THEN 1 ELSE 0 END) AS denied
        FROM reservations
    """)
    reservation_row = cursor.fetchone() or {}
    approved_count = int(reservation_row.get('approved') or 0)
    denied_count = int(reservation_row.get('denied') or 0)
    reservation_total = approved_count + denied_count
    approval_rate = round((approved_count / reservation_total) * 100, 1) if reservation_total else 0

    cursor.execute("""
        SELECT AVG(rating) AS avg_rating
        FROM user_feedback
        WHERE rating IS NOT NULL
    """)
    avg_rating = float((cursor.fetchone() or {}).get('avg_rating') or 0)

    cursor.execute("""
        SELECT lab, COUNT(*) AS total
        FROM sit_in_logs
        WHERE lab IS NOT NULL
        GROUP BY lab
        ORDER BY total DESC
    """)
    sitins_by_lab = cursor.fetchall()

    cursor.execute("""
        SELECT status, COUNT(*) AS total
        FROM reservations
        GROUP BY status
    """)
    reservations_by_status = cursor.fetchall()

    cursor.execute("""
        SELECT rating, COUNT(*) AS total
        FROM user_feedback
        WHERE rating IS NOT NULL
        GROUP BY rating
        ORDER BY rating
    """)
    ratings_distribution = cursor.fetchall()

    cursor.close()
    db.close()

    lab_labels = []
    lab_values = []
    for row in sitins_by_lab:
        lab_info = LAB_LOOKUP.get(row.get('lab'))
        lab_labels.append(lab_info['label'] if lab_info else (row.get('lab') or 'Unassigned'))
        lab_values.append(int(row.get('total') or 0))

    status_order = ['pending', 'approved', 'checked_in', 'denied', 'cancelled', 'no_show']
    status_counts = {status: 0 for status in status_order}
    for row in reservations_by_status:
        status_counts[row['status']] = int(row.get('total') or 0)
    reservation_labels = [status.replace('_', ' ').title() for status in status_order]
    reservation_values = [status_counts[status] for status in status_order]

    rating_labels = [str(value) for value in range(1, 6)]
    rating_counts = {str(value): 0 for value in range(1, 6)}
    for row in ratings_distribution:
        rating_key = str(int(row['rating']))
        rating_counts[rating_key] = int(row.get('total') or 0)
    rating_values = [rating_counts[label] for label in rating_labels]

    busiest_lab_code = busiest_lab_row.get('lab')
    busiest_lab_info = LAB_LOOKUP.get(busiest_lab_code)
    busiest_lab_label = busiest_lab_info['label'] if busiest_lab_info else (busiest_lab_code or 'Unassigned')

    metrics = {
        'avg_minutes': round(avg_minutes, 1),
        'busiest_lab': busiest_lab_label,
        'sitins_last_30': sitins_last_30,
        'approval_rate': approval_rate,
        'avg_rating': round(avg_rating, 2),
    }

    return render_template('admin_analytics.html',
                           metrics=metrics,
                           lab_labels=lab_labels,
                           lab_values=lab_values,
                           reservation_labels=reservation_labels,
                           reservation_values=reservation_values,
                           rating_labels=rating_labels,
                           rating_values=rating_values,
                           approved_count=approved_count,
                           denied_count=denied_count)


@app.route('/admin/leaderboard')
def admin_leaderboard():
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    leaderboard_rows, _ = fetch_leaderboard(limit=100)
    return render_template('admin_leaderboard.html', leaderboard_rows=leaderboard_rows)


@app.route('/admin/announcements/create', methods=['POST'])
def admin_create_announcement():
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    body = (request.form.get('body') or '').strip()
    target_course = (request.form.get('target_course') or '').strip()
    target_level = (request.form.get('target_level') or '').strip()
    pinned = 1 if request.form.get('pinned') == '1' else 0
    if not body:
        flash('Announcement body is required.', 'warning')
        return redirect('/admin')

    author = 'CCS Admin'
    user = session.get('user') or {}
    if user.get('first_name'):
        author = f"{user.get('first_name')} {user.get('last_name') or ''}".strip()

    db = get_db()
    ensure_announcements_table(db)
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO announcements (author, body, created_by_id, status, pinned, target_course, target_level)
        VALUES (%s, %s, %s, 'active', %s, %s, %s)
    """, (author, body, user.get('id_number'), pinned, target_course or None, target_level or None))
    db.commit()
    cursor.close()
    db.close()

    flash('Announcement posted successfully.', 'success')
    return redirect('/admin')


@app.route('/admin/announcements/<int:announcement_id>/update', methods=['POST'])
def admin_update_announcement(announcement_id):
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    body = (request.form.get('body') or '').strip()
    target_course = (request.form.get('target_course') or '').strip()
    target_level = (request.form.get('target_level') or '').strip()
    pinned = 1 if request.form.get('pinned') == '1' else 0

    if not body:
        flash('Announcement body is required.', 'warning')
        return redirect('/admin')

    db = get_db()
    ensure_announcements_table(db)
    cursor = db.cursor()
    cursor.execute("""
        UPDATE announcements
        SET body=%s,
            pinned=%s,
            target_course=%s,
            target_level=%s
        WHERE id=%s AND status='active'
    """, (body, pinned, target_course or None, target_level or None, announcement_id))
    db.commit()
    cursor.close()
    db.close()

    flash('Announcement updated.', 'success')
    return redirect('/admin')


@app.route('/admin/announcements/<int:announcement_id>/delete', methods=['POST'])
def admin_delete_announcement(announcement_id):
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    db = get_db()
    ensure_announcements_table(db)
    cursor = db.cursor()
    cursor.execute("""
        UPDATE announcements
        SET status='archived', pinned=0
        WHERE id=%s
    """, (announcement_id,))
    db.commit()
    cursor.close()
    db.close()

    flash('Announcement deleted.', 'info')
    return redirect('/admin')


@app.route('/admin/announcements/<int:announcement_id>/pin', methods=['POST'])
def admin_pin_announcement(announcement_id):
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    db = get_db()
    ensure_announcements_table(db)
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT pinned
        FROM announcements
        WHERE id=%s AND status='active'
        LIMIT 1
    """, (announcement_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        db.close()
        flash('Announcement not found.', 'warning')
        return redirect('/admin')

    new_value = 0 if row['pinned'] else 1
    cursor = db.cursor()
    cursor.execute("""
        UPDATE announcements
        SET pinned=%s
        WHERE id=%s
    """, (new_value, announcement_id))
    db.commit()
    cursor.close()
    db.close()

    flash('Announcement pin updated.', 'success')
    return redirect('/admin')


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
            ensure_reservations_table(db)
            cursor = db.cursor(dictionary=True)

            cursor.execute("""
                SELECT id_number, last_name, first_name, middle_name, course, course_level
                FROM users
                WHERE id_number = %s AND id_number NOT LIKE 'adm-%'
                LIMIT 1
            """, (searched_id,))
            student = cursor.fetchone()

            if student:
                usage = get_session_usage(cursor, searched_id)
                remaining_sessions = usage['remaining']

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
    ensure_reservations_table(db)
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

        cursor.execute(f"""
            SELECT student_id_number, COUNT(*) AS approved_reservations
            FROM reservations
            WHERE student_id_number IN ({format_strings})
              AND status='approved'
            GROUP BY student_id_number
        """, student_ids)
        for row in cursor.fetchall():
            if row['student_id_number'] not in remaining_lookup:
                remaining_lookup[row['student_id_number']] = {'completed': 0, 'active': 0}
            remaining_lookup[row['student_id_number']]['approved'] = row['approved_reservations'] or 0

    cursor.close()
    db.close()

    students = []
    for user in users:
        full_name = f"{user['last_name']}, {user['first_name']}"
        if user.get('middle_name'):
            full_name = f"{full_name} {user['middle_name']}"

        usage = remaining_lookup.get(user['id_number'], {'completed': 0, 'active': 0, 'approved': 0})
        approved = usage.get('approved', 0)
        remaining_sessions = max(TOTAL_SESSION_LIMIT - usage['completed'] - usage['active'] - approved, 0)

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
        lab_assigned = (request.form.get('lab_assigned') or '').strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not id_number or not last_name or not first_name or not course or not course_level:
            flash('Please fill out all required fields.', 'danger')
            return redirect(url_for('admin_add_student'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('admin_add_student'))

        hashed_pw = generate_password_hash(password)

        if lab_assigned and lab_assigned not in LAB_LOOKUP:
            lab_assigned = ''

        db = get_db()
        ensure_users_table(db)
        cursor = db.cursor()
        try:
            cursor.execute(
                """INSERT INTO users
                       (id_number, last_name, first_name, middle_name, course,
                        course_level, email, address, password, lab_assigned)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (id_number, last_name, first_name, middle_name, course,
                 course_level, email, address, hashed_pw, lab_assigned or None)
            )
            db.commit()
            flash('Student added successfully.', 'success')
            return redirect('/admin/students')
        except mysql.connector.IntegrityError:
            flash('ID number already exists.', 'danger')
        finally:
            cursor.close()
            db.close()

    return render_template('admin_add_student.html', labs=LABS)


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
            ensure_reservations_table(db)
            ensure_users_table(db)
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
                        cursor.execute("""
                            UPDATE users
                            SET lab_assigned=%s
                            WHERE id_number=%s
                              AND id_number NOT LIKE 'adm-%'
                        """, (lab_code, searched_id))
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
            ensure_reservations_table(db)
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
    ensure_users_table(db)
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        last_name = request.form.get('last_name', '').strip()
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        course = request.form.get('course', '').strip()
        course_level = request.form.get('course_level', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        lab_assigned = (request.form.get('lab_assigned') or '').strip()

        if lab_assigned and lab_assigned not in LAB_LOOKUP:
            lab_assigned = ''

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
                address=%s,
                lab_assigned=%s
            WHERE id_number=%s
              AND id_number NOT LIKE 'adm-%'
        """, (last_name, first_name, middle_name, course, course_level, email, address, lab_assigned or None, id_number))
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
        SELECT id_number, last_name, first_name, middle_name, course, course_level, email, address, lab_assigned
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

    return render_template('admin_edit_student.html', student=student, labs=LABS)


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

    # Get filter parameter
    rating_filter = request.args.get('rating')

    db = get_db()
    ensure_user_feedback_table(db)
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT
            f.id,
            f.sit_in_log_id,
            f.rating,
            f.feedback_text,
            f.admin_feedback_text,
            f.admin_points_reason,
            f.points_awarded,
            f.tidiness_status,
            f.admin_reviewed_at,
            f.admin_reviewer_id,
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
    """
    
    params = []
    if rating_filter and rating_filter.isdigit():
        query += " WHERE f.rating = %s "
        params.append(int(rating_filter))

    query += " ORDER BY f.created_at DESC "
    
    cursor.execute(query, params)
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


@app.route('/admin/feedback/<int:feedback_id>/review', methods=['POST'])
def admin_review_feedback(feedback_id):
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    admin_feedback_text = (request.form.get('admin_feedback_text') or '').strip()
    admin_points_reason = (request.form.get('admin_points_reason') or '').strip()
    tidiness_status = (request.form.get('tidiness_status') or '').strip().lower()
    points_raw = (request.form.get('points_awarded') or '').strip()

    if not admin_feedback_text:
        flash('Admin feedback for the student is required.', 'warning')
        return redirect('/admin/feedback-reports')

    if not admin_points_reason:
        flash('Please provide a reason for the awarded points.', 'warning')
        return redirect('/admin/feedback-reports')

    if points_raw:
        try:
            points_awarded = int(points_raw)
        except ValueError:
            flash('Points must be a whole number.', 'danger')
            return redirect('/admin/feedback-reports')
    else:
        points_awarded = 0

    if tidiness_status not in ('tidy', 'not_tidy', ''):
        flash('Invalid criteria tag selected.', 'warning')
        return redirect('/admin/feedback-reports')

    if points_awarded < 0 or points_awarded > 100:
        flash('Points must be between 0 and 100.', 'danger')
        return redirect('/admin/feedback-reports')

    db = get_db()
    ensure_sit_in_logs_table(db)
    ensure_user_feedback_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT f.id, f.sit_in_log_id, s.status
        FROM user_feedback f
        LEFT JOIN sit_in_logs s ON s.id = f.sit_in_log_id
        WHERE f.id=%s
        LIMIT 1
    """, (feedback_id,))
    feedback_row = cursor.fetchone()

    if not feedback_row:
        cursor.close()
        db.close()
        flash('Feedback record not found.', 'warning')
        return redirect('/admin/feedback-reports')

    if feedback_row.get('status') != 'completed':
        cursor.close()
        db.close()
        flash('Admin review is only allowed for completed sessions.', 'warning')
        return redirect('/admin/feedback-reports')

    cursor.execute("""
        UPDATE user_feedback
        SET admin_feedback_text=%s,
            admin_points_reason=%s,
            points_awarded=%s,
            tidiness_status=%s,
            admin_reviewed_at=NOW(),
            admin_reviewer_id=%s
        WHERE id=%s
    """, (
        admin_feedback_text,
        admin_points_reason,
        points_awarded,
        tidiness_status or None,
        (session.get('user') or {}).get('id_number'),
        feedback_id,
    ))
    db.commit()
    cursor.close()
    db.close()

    flash('Admin feedback and points saved.', 'success')
    return redirect('/admin/feedback-reports')


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
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    selected_lab = (request.args.get('lab_code') or LABS[0]['code']).strip()
    selected_date = (request.args.get('reservation_date') or datetime.now().strftime('%Y-%m-%d')).strip()
    selected_slot = (request.args.get('reservation_slot') or RESERVATION_SLOTS[0]).strip()

    if selected_lab not in LAB_LOOKUP:
        selected_lab = LABS[0]['code']
    if selected_slot not in RESERVATION_SLOTS:
        selected_slot = RESERVATION_SLOTS[0]

    db = get_db()
    ensure_sit_in_logs_table(db)
    ensure_reservations_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            r.id,
            r.student_id_number,
            r.lab_code,
            r.seat_no,
            r.purpose,
            r.reservation_date,
            r.reservation_slot,
            r.status,
            r.admin_note,
            r.created_at,
            r.decided_at,
            u.first_name,
            u.last_name,
            u.middle_name
        FROM reservations r
        LEFT JOIN users u ON u.id_number = r.student_id_number
        WHERE r.student_id_number <> %s
        ORDER BY CASE r.status WHEN 'pending' THEN 0 ELSE 1 END, r.created_at DESC
    """, (ADMIN_SEAT_BLOCK_ID,))
    reservation_rows = cursor.fetchall()

    cursor.execute("""
        SELECT id, seat_no, status, student_id_number
        FROM reservations
        WHERE lab_code=%s
          AND reservation_date=%s
          AND reservation_slot=%s
          AND status IN ('pending', 'approved', 'checked_in')
        ORDER BY CASE status WHEN 'approved' THEN 0 ELSE 1 END, created_at DESC
    """, (selected_lab, selected_date, selected_slot))
    seat_map = {}
    for row in cursor.fetchall():
        if row['seat_no'] not in seat_map:
            seat_map[row['seat_no']] = row

    selected_lab_info = LAB_LOOKUP[selected_lab]
    seats = []
    for seat in range(1, selected_lab_info['capacity'] + 1):
        seat_row = seat_map.get(seat)
        is_taken = seat_row is not None
        is_admin_block = bool(seat_row and seat_row['student_id_number'] == ADMIN_SEAT_BLOCK_ID)
        seats.append({
            'seat_no': seat,
            'is_taken': is_taken,
            'is_admin_block': is_admin_block,
            'can_toggle': (not is_taken) or is_admin_block,
            'toggle_label': 'Release' if is_admin_block else 'Mark Occupied'
        })

    cursor.close()
    db.close()

    for row in reservation_rows:
        full_name = f"{row.get('last_name') or ''}, {row.get('first_name') or ''}"
        if row.get('middle_name'):
            full_name = f"{full_name} {row['middle_name']}"
        row['student_name'] = full_name.strip(', ')
        lab_info = LAB_LOOKUP.get(row['lab_code'])
        row['lab_label'] = lab_info['label'] if lab_info else row['lab_code']

    return render_template('admin_reservations.html',
                           reservations=reservation_rows,
                           labs=LABS,
                           slots=RESERVATION_SLOTS,
                           selected_lab=selected_lab,
                           selected_date=selected_date,
                           selected_slot=selected_slot,
                           seats=seats)


@app.route('/admin/reservations/seat/toggle', methods=['POST'])
def admin_toggle_reservation_seat():
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    lab_code = (request.form.get('lab_code') or '').strip()
    reservation_date = (request.form.get('reservation_date') or '').strip()
    reservation_slot = (request.form.get('reservation_slot') or '').strip()
    seat_raw = (request.form.get('seat_no') or '').strip()

    if lab_code not in LAB_LOOKUP or reservation_slot not in RESERVATION_SLOTS:
        flash('Invalid seat toggle request.', 'warning')
        return redirect('/admin/reservations')

    try:
        seat_no = int(seat_raw)
    except ValueError:
        flash('Invalid seat selected.', 'warning')
        return redirect('/admin/reservations')

    if seat_no < 1 or seat_no > LAB_LOOKUP[lab_code]['capacity']:
        flash('Seat number is out of range.', 'warning')
        return redirect('/admin/reservations')

    try:
        datetime.strptime(reservation_date, '%Y-%m-%d')
    except ValueError:
        flash('Invalid reservation date.', 'warning')
        return redirect('/admin/reservations')

    db = get_db()
    ensure_reservations_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, student_id_number, status
        FROM reservations
        WHERE lab_code=%s
          AND seat_no=%s
          AND reservation_date=%s
          AND reservation_slot=%s
          AND status IN ('pending', 'approved')
        ORDER BY CASE status WHEN 'approved' THEN 0 ELSE 1 END, created_at DESC
        LIMIT 1
    """, (lab_code, seat_no, reservation_date, reservation_slot))
    row = cursor.fetchone()

    admin_id = session.get('user', {}).get('id_number', 'admin')
    if not row:
        cursor.execute("""
            INSERT INTO reservations (
                student_id_number, lab_code, seat_no, purpose,
                reservation_date, reservation_slot, status, admin_note,
                decided_at, decided_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'approved', %s, NOW(), %s)
        """, (ADMIN_SEAT_BLOCK_ID, lab_code, seat_no, 'Admin seat block', reservation_date, reservation_slot, 'Occupied by admin seat panel', admin_id))
        db.commit()
        flash(f'PC {seat_no} marked as occupied.', 'success')
    elif row['student_id_number'] == ADMIN_SEAT_BLOCK_ID:
        cursor.execute("""
            DELETE FROM reservations
            WHERE id=%s
        """, (row['id'],))
        db.commit()
        flash(f'PC {seat_no} is now available.', 'success')
    else:
        flash(f'PC {seat_no} is reserved by a student request.', 'warning')

    cursor.close()
    db.close()
    return redirect(f"/admin/reservations?lab_code={lab_code}&reservation_date={reservation_date}&reservation_slot={reservation_slot}")


@app.route('/admin/reservations/seat/block-all', methods=['POST'])
def admin_block_all_seats():
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    lab_code = (request.form.get('lab_code') or '').strip()
    reservation_date = (request.form.get('reservation_date') or '').strip()
    reservation_slot = (request.form.get('reservation_slot') or '').strip()

    if lab_code not in LAB_LOOKUP or reservation_slot not in RESERVATION_SLOTS:
        flash('Invalid seat block request.', 'warning')
        return redirect('/admin/reservations')

    try:
        datetime.strptime(reservation_date, '%Y-%m-%d')
    except ValueError:
        flash('Invalid reservation date.', 'warning')
        return redirect('/admin/reservations')

    db = get_db()
    ensure_reservations_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT seat_no, student_id_number, status
        FROM reservations
        WHERE lab_code=%s
          AND reservation_date=%s
          AND reservation_slot=%s
          AND status IN ('pending', 'approved', 'checked_in')
    """, (lab_code, reservation_date, reservation_slot))
    existing = {row['seat_no']: row for row in cursor.fetchall()}

    admin_id = session.get('user', {}).get('id_number', 'admin')
    capacity = LAB_LOOKUP[lab_code]['capacity']
    blocked_count = 0
    skipped_count = 0

    for seat_no in range(1, capacity + 1):
        row = existing.get(seat_no)
        if row:
            skipped_count += 1
            continue

        cursor.execute("""
            INSERT INTO reservations (
                student_id_number, lab_code, seat_no, purpose,
                reservation_date, reservation_slot, status, admin_note,
                decided_at, decided_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'approved', %s, NOW(), %s)
        """, (ADMIN_SEAT_BLOCK_ID, lab_code, seat_no, 'Admin seat block', reservation_date, reservation_slot, 'Occupied by admin seat panel', admin_id))
        blocked_count += 1

    db.commit()
    cursor.close()
    db.close()

    if blocked_count:
        flash(f'Disabled {blocked_count} PC(s). Skipped {skipped_count} already taken.', 'success')
    else:
        flash('No available PCs to disable for this schedule.', 'info')

    return redirect(f"/admin/reservations?lab_code={lab_code}&reservation_date={reservation_date}&reservation_slot={reservation_slot}")


@app.route('/admin/reservations/seat/unblock-all', methods=['POST'])
def admin_unblock_all_seats():
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    lab_code = (request.form.get('lab_code') or '').strip()
    reservation_date = (request.form.get('reservation_date') or '').strip()
    reservation_slot = (request.form.get('reservation_slot') or '').strip()

    if lab_code not in LAB_LOOKUP or reservation_slot not in RESERVATION_SLOTS:
        flash('Invalid seat release request.', 'warning')
        return redirect('/admin/reservations')

    try:
        datetime.strptime(reservation_date, '%Y-%m-%d')
    except ValueError:
        flash('Invalid reservation date.', 'warning')
        return redirect('/admin/reservations')

    db = get_db()
    ensure_reservations_table(db)
    cursor = db.cursor(dictionary=True)

    admin_id = session.get('user', {}).get('id_number', 'admin')
    cursor.execute("""
        UPDATE reservations
        SET status='cancelled', decided_at=NOW(), decided_by=%s, admin_note=%s
        WHERE lab_code=%s
          AND reservation_date=%s
          AND reservation_slot=%s
          AND student_id_number=%s
          AND status IN ('pending', 'approved')
    """, (admin_id, 'Released from admin seat panel', lab_code, reservation_date, reservation_slot, ADMIN_SEAT_BLOCK_ID))
    db.commit()
    released = cursor.rowcount
    cursor.close()
    db.close()

    if released:
        flash(f'Enabled {released} PC(s).', 'success')
    else:
        flash('No admin-blocked PCs to enable for this schedule.', 'info')

    return redirect(f"/admin/reservations?lab_code={lab_code}&reservation_date={reservation_date}&reservation_slot={reservation_slot}")


@app.route('/admin/reservations/<int:reservation_id>/decision', methods=['POST'])
def admin_reservation_decision(reservation_id):
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    decision = (request.form.get('decision') or '').strip().lower()
    admin_note = (request.form.get('admin_note') or '').strip()

    if decision not in ('approved', 'denied', 'checked_in', 'no_show'):
        flash('Invalid reservation action.', 'danger')
        return redirect('/admin/reservations')

    if decision in ('denied', 'no_show') and not admin_note:
        flash('Please provide a reason for this action.', 'warning')
        return redirect('/admin/reservations')

    db = get_db()
    ensure_sit_in_logs_table(db)
    ensure_reservations_table(db)
    ensure_users_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, student_id_number, lab_code, seat_no, reservation_date, reservation_slot, status
        FROM reservations
        WHERE id=%s
        LIMIT 1
    """, (reservation_id,))
    row = cursor.fetchone()

    if not row:
        cursor.close()
        db.close()
        flash('Reservation request not found.', 'warning')
        return redirect('/admin/reservations')

    if decision in ('approved', 'denied') and row['status'] != 'pending':
        cursor.close()
        db.close()
        flash('Only pending reservations can be updated.', 'warning')
        return redirect('/admin/reservations')

    if decision in ('checked_in', 'no_show') and row['status'] != 'approved':
        cursor.close()
        db.close()
        flash('Only approved reservations can be checked in or marked no-show.', 'warning')
        return redirect('/admin/reservations')

    if decision == 'approved':
        usage = get_session_usage(cursor, row['student_id_number'])
        if usage['remaining'] <= 0:
            cursor.close()
            db.close()
            flash('Student has no remaining sessions for reservation approval.', 'warning')
            return redirect('/admin/reservations')

        cursor.execute("""
            SELECT COUNT(*) AS active_count
            FROM sit_in_logs
            WHERE student_id_number=%s AND status='active'
        """, (row['student_id_number'],))
        if (cursor.fetchone() or {}).get('active_count', 0) > 0:
            cursor.close()
            db.close()
            flash('Student already has an active sit-in session.', 'warning')
            return redirect('/admin/reservations')

        cursor.execute("""
            SELECT id
            FROM reservations
            WHERE id <> %s
              AND lab_code=%s
              AND seat_no=%s
              AND reservation_date=%s
              AND reservation_slot=%s
              AND status IN ('pending', 'approved', 'checked_in')
            LIMIT 1
        """, (row['id'], row['lab_code'], row['seat_no'], row['reservation_date'], row['reservation_slot']))
        if cursor.fetchone():
            cursor.close()
            db.close()
            flash('Seat already taken for that reservation schedule.', 'warning')
            return redirect('/admin/reservations')

            cursor.execute("""
                        UPDATE users
                        SET lab_assigned=%s
                        WHERE id_number=%s
                            AND id_number NOT LIKE 'adm-%'
                """, (row['lab_code'], row['student_id_number']))

    if decision == 'checked_in':
        usage = get_session_usage(cursor, row['student_id_number'])
        if usage['remaining'] <= 0:
            cursor.close()
            db.close()
            flash('Student has no remaining sessions.', 'warning')
            return redirect('/admin/reservations')

        cursor.execute("""
            SELECT COUNT(*) AS active_count
            FROM sit_in_logs
            WHERE student_id_number=%s AND status='active'
        """, (row['student_id_number'],))
        if (cursor.fetchone() or {}).get('active_count', 0) > 0:
            cursor.close()
            db.close()
            flash('Student already has an active sit-in session.', 'warning')
            return redirect('/admin/reservations')

        lab_info = LAB_LOOKUP.get(row['lab_code'])
        if not lab_info:
            cursor.close()
            db.close()
            flash('Invalid laboratory code in reservation.', 'warning')
            return redirect('/admin/reservations')

        cursor.execute("""
            SELECT COUNT(*) AS lab_taken
            FROM sit_in_logs
            WHERE lab=%s AND status='active'
        """, (row['lab_code'],))
        lab_taken = (cursor.fetchone() or {}).get('lab_taken', 0)
        if lab_taken >= lab_info['capacity']:
            cursor.close()
            db.close()
            flash(f"{lab_info['label']} is currently full.", 'warning')
            return redirect('/admin/reservations')

        cursor.execute("""
            SELECT COUNT(*) AS completed_count
            FROM sit_in_logs
            WHERE student_id_number=%s AND status='completed'
        """, (row['student_id_number'],))
        completed_count = (cursor.fetchone() or {}).get('completed_count', 0)

        cursor.execute("""
            INSERT INTO sit_in_logs (student_id_number, purpose, lab, session_no, status)
            VALUES (%s, %s, %s, %s, 'active')
        """, (row['student_id_number'], row.get('purpose') or 'General use', row['lab_code'], completed_count + 1))

    admin_id = session.get('user', {}).get('id_number', 'admin')
    cursor.execute("""
        UPDATE reservations
        SET status=%s,
            admin_note=%s,
            decided_at=NOW(),
            decided_by=%s
        WHERE id=%s
    """, (decision, admin_note or None, admin_id, reservation_id))
    db.commit()
    cursor.close()
    db.close()

    if decision == 'checked_in':
        flash('Student checked in and sit-in session started.', 'success')
    elif decision == 'no_show':
        flash('Reservation marked as no-show.', 'warning')
    else:
        flash(f"Reservation {decision}.", 'success')
    return redirect('/admin/reservations')


@app.route('/login_user', methods=['POST'])
def login_user():
    id_number = (request.form.get('id_number') or '').strip()
    password = request.form['password']

    db = get_db()
    ensure_users_table(db)
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
            'lab_assigned': user.get('lab_assigned') or '',
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
    ensure_reservations_table(db)
    cursor = db.cursor(dictionary=True)

    usage = get_session_usage(cursor, user['id_number'])
    sessions_used = usage['used']

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
            f.id AS feedback_id,
            f.admin_feedback_text,
            f.admin_points_reason,
            f.points_awarded,
            f.tidiness_status,
            f.admin_reviewed_at
        FROM sit_in_logs s
        LEFT JOIN user_feedback f ON f.sit_in_log_id = s.id
        WHERE s.student_id_number=%s
        ORDER BY s.started_at DESC
        LIMIT 5
    """, (user['id_number'],))
    recent_sessions = cursor.fetchall()

    cursor.execute("""
        SELECT
            COUNT(*) AS total_sessions,
            SUM(
                CASE
                    WHEN ended_at IS NOT NULL
                        THEN TIMESTAMPDIFF(MINUTE, started_at, ended_at)
                    ELSE 0
                END
            ) AS total_minutes,
            AVG(
                CASE
                    WHEN ended_at IS NOT NULL
                        THEN TIMESTAMPDIFF(MINUTE, started_at, ended_at)
                    ELSE NULL
                END
            ) AS avg_minutes,
            MAX(
                CASE
                    WHEN ended_at IS NOT NULL
                        THEN TIMESTAMPDIFF(MINUTE, started_at, ended_at)
                    ELSE 0
                END
            ) AS max_minutes
        FROM sit_in_logs
        WHERE student_id_number=%s AND status='completed'
    """, (user['id_number'],))
    summary_row = cursor.fetchone() or {}

    selected_lab = (request.args.get('lab_code') or LABS[0]['code']).strip()
    selected_date = (request.args.get('reservation_date') or datetime.now().strftime('%Y-%m-%d')).strip()
    selected_slot = (request.args.get('reservation_slot') or RESERVATION_SLOTS[0]).strip()

    if selected_lab not in LAB_LOOKUP:
        selected_lab = LABS[0]['code']
    if selected_slot not in RESERVATION_SLOTS:
        selected_slot = RESERVATION_SLOTS[0]

    taken_seats = get_taken_seats(cursor, selected_lab, selected_date, selected_slot)

    cursor.execute("""
        SELECT id, lab_code, seat_no, purpose, reservation_date, reservation_slot, status, created_at
        FROM reservations
        WHERE student_id_number=%s
        ORDER BY created_at DESC
        LIMIT 8
    """, (user['id_number'],))
    reservation_logs = cursor.fetchall()

    cursor.close()
    db.close()

    if active_session:
        lab_info = LAB_LOOKUP.get(active_session['lab'])
        active_session['lab_label'] = lab_info['label'] if lab_info else (active_session['lab'] or 'Unassigned')

    sessions_remaining = usage['remaining']

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

    selected_lab_info = LAB_LOOKUP[selected_lab]
    reservation_seats = []
    for seat in range(1, selected_lab_info['capacity'] + 1):
        reservation_seats.append({
            'seat_no': seat,
            'is_taken': seat in taken_seats
        })

    for row in reservation_logs:
        lab_info = LAB_LOOKUP.get(row['lab_code'])
        row['lab_label'] = lab_info['label'] if lab_info else row['lab_code']

    total_minutes = int(summary_row.get('total_minutes') or 0)
    avg_minutes = float(summary_row.get('avg_minutes') or 0)
    max_minutes = int(summary_row.get('max_minutes') or 0)

    def format_minutes(total):
        hours = total // 60
        minutes = total % 60
        return f"{hours}h {minutes}m"

    sit_in_summary = {
        'total_hours': round(total_minutes / 60, 2),
        'total_sessions': int(summary_row.get('total_sessions') or 0),
        'avg_duration': format_minutes(int(round(avg_minutes))) if avg_minutes else '0h 0m',
        'longest_duration': format_minutes(max_minutes) if max_minutes else '0h 0m',
    }

    can_start_session = active_session is None and sessions_remaining > 0

    leaderboard_preview, leaderboard_all = fetch_leaderboard(limit=8)
    my_rank = next((row for row in leaderboard_all if row['id_number'] == user['id_number']), None)
    announcements = fetch_announcements(limit=10, for_user=user)
    latest_announcement_id = announcements[0]['id'] if announcements else 0
    last_seen_announcement_id = session.get('last_seen_announcement_id', 0)
    has_new_notifications = bool(latest_announcement_id and latest_announcement_id > last_seen_announcement_id)

    return render_template('dashboard.html',
                           user=user,
                           sessions_used=sessions_used,
                           sessions_remaining=sessions_remaining,
                           sessions_total=TOTAL_SESSION_LIMIT,
                           active_session=active_session,
                           lab_cards=lab_cards,
                           announcements=announcements,
                           has_new_notifications=has_new_notifications,
                           recent_sessions=recent_sessions,
                           can_start_session=can_start_session,
                           labs=LABS,
                           slots=RESERVATION_SLOTS,
                           selected_lab=selected_lab,
                           selected_date=selected_date,
                           selected_slot=selected_slot,
                           reservation_seats=reservation_seats,
                           reservation_logs=reservation_logs,
                           purposes=PURPOSES,
                           leaderboard_preview=leaderboard_preview,
                           my_rank=my_rank,
                           sit_in_summary=sit_in_summary)


@app.route('/leaderboard')
def student_leaderboard():
    if 'user' not in session:
        return redirect('/')

    user = session['user']
    if is_admin_user():
        return redirect('/admin/leaderboard')

    leaderboard_rows, leaderboard_all = fetch_leaderboard(limit=100)
    my_rank = next((row for row in leaderboard_all if row['id_number'] == user['id_number']), None)
    return render_template('leaderboard.html', user=user, leaderboard_rows=leaderboard_rows, my_rank=my_rank)


@app.route('/announcements')
def student_announcements():
    if 'user' not in session:
        return redirect('/')

    user = session['user']
    if is_admin_user():
        return redirect('/admin')

    announcements = fetch_announcements(limit=30, for_user=user)
    if announcements:
        session['last_seen_announcement_id'] = announcements[0]['id']
    return render_template('announcements.html',
                           user=user,
                           announcements=announcements)


@app.route('/shop')
def student_shop():
    if 'user' not in session:
        return redirect('/')

    user = session['user']
    if is_admin_user():
        return redirect('/admin/rewards')

    db = get_db()
    ensure_rewards_table(db)
    ensure_reward_redemptions_table(db)
    ensure_user_feedback_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, name, description, points_cost, is_physical, stock, status
        FROM rewards
        WHERE status='active'
        ORDER BY points_cost ASC, name ASC
    """)
    rewards = cursor.fetchall()

    earned_points, spent_points, available_points = get_points_summary(cursor, user['id_number'])

    cursor.execute("""
        SELECT id, reward_name, points_cost, status, is_physical, created_at, ready_at, claimed_at, admin_note
        FROM reward_redemptions
        WHERE student_id_number=%s
        ORDER BY created_at DESC
        LIMIT 10
    """, (user['id_number'],))
    redemptions = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('shop.html',
                           user=user,
                           rewards=rewards,
                           earned_points=earned_points,
                           spent_points=spent_points,
                           available_points=available_points,
                           redemptions=redemptions)


@app.route('/admin/software', methods=['GET', 'POST'])
def admin_software():
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    db = get_db()
    ensure_software_table(db)
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        description = (request.form.get('description') or '').strip()
        lab_code = (request.form.get('lab_code') or '').strip()
        file_obj = request.files.get('file')

        if lab_code and lab_code not in LAB_LOOKUP:
            lab_code = ''

        if not title:
            flash('Title is required.', 'warning')
            return redirect('/admin/software')

        if not file_obj or not file_obj.filename:
            flash('Please choose a file to upload.', 'warning')
            return redirect('/admin/software')

        if not allowed_software_file(file_obj.filename):
            flash('Unsupported file type.', 'danger')
            return redirect('/admin/software')

        original_name = secure_filename(file_obj.filename)
        if not original_name:
            flash('Invalid file name.', 'danger')
            return redirect('/admin/software')

        base_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{original_name}"
        upload_dir = app.config['SOFTWARE_UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        stored_name = base_name
        counter = 1
        while os.path.exists(os.path.join(upload_dir, stored_name)):
            stored_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{counter}_{original_name}"
            counter += 1

        file_path = os.path.join(upload_dir, stored_name)
        file_obj.save(file_path)
        file_size = os.path.getsize(file_path)
        uploaded_by = (session.get('user') or {}).get('id_number')

        cursor.execute("""
            INSERT INTO software_assets (
                title, description, lab_code, file_name, original_name,
                file_size, uploaded_by, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')
        """, (
            title,
            description or None,
            lab_code or None,
            stored_name,
            original_name,
            file_size,
            uploaded_by,
        ))
        db.commit()
        flash('Software uploaded successfully.', 'success')
        return redirect('/admin/software')

    cursor.execute("""
        SELECT id, title, description, lab_code, original_name, file_size, uploaded_by, created_at
        FROM software_assets
        WHERE status='active'
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    db.close()

    for row in rows:
        lab_info = LAB_LOOKUP.get(row.get('lab_code'))
        row['lab_label'] = lab_info['label'] if lab_info else (row.get('lab_code') or 'All Labs')

    return render_template('admin_software.html', rows=rows, labs=LABS)


@app.route('/software')
def student_software():
    if 'user' not in session:
        return redirect('/')

    user = session['user']
    if is_admin_user():
        return redirect('/admin/software')

    db = get_db()
    ensure_users_table(db)
    ensure_software_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT lab_assigned
        FROM users
        WHERE id_number=%s
        LIMIT 1
    """, (user['id_number'],))
    assigned_row = cursor.fetchone() or {}
    
    # Priority 1: Check if student has an ACTIVE sit-in session right now
    ensure_sit_in_logs_table(db)
    cursor.execute("""
        SELECT lab FROM sit_in_logs 
        WHERE student_id_number=%s AND status='active' 
        ORDER BY started_at DESC LIMIT 1
    """, (user['id_number'],))
    active_session = cursor.fetchone()
    
    if active_session:
        assigned_lab = active_session['lab']
    else:
        # Priority 2: Fallback to the persistent lab_assigned column
        assigned_lab = (assigned_row.get('lab_assigned') or '').strip()

    if assigned_lab and assigned_lab not in LAB_LOOKUP:
        assigned_lab = ''

    # Build the query to include both assigned lab and ALL Other Lab sections
    # Excluding libraries or system files, we show assets tagged to the user's lab OR 'All Labs' (null/empty)
    cursor.execute("""
        SELECT id, title, description, lab_code, original_name, file_size, created_at
        FROM software_assets
        WHERE status='active'
        ORDER BY 
            CASE 
                WHEN lab_code = %s THEN 0 
                WHEN lab_code IS NULL OR lab_code = '' THEN 1
                ELSE 2 
            END ASC,
            created_at DESC
    """, (assigned_lab,))
    rows = cursor.fetchall()

    cursor.close()
    db.close()

    for row in rows:
        lab_info = LAB_LOOKUP.get(row.get('lab_code'))
        row['lab_label'] = lab_info['label'] if lab_info else (row.get('lab_code') or 'All Labs')

    lab_info = LAB_LOOKUP.get(assigned_lab)
    assigned_label = lab_info['label'] if lab_info else ''

    return render_template('software.html',
                           rows=rows,
                           labs=LABS,
                           assigned_lab=assigned_lab,
                           assigned_label=assigned_label)


@app.route('/software/download/<int:asset_id>')
def download_software(asset_id):
    if 'user' not in session:
        return redirect('/')

    user = session['user']
    db = get_db()
    ensure_users_table(db)
    ensure_software_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, title, lab_code, file_name, original_name
        FROM software_assets
        WHERE id=%s AND status='active'
        LIMIT 1
    """, (asset_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        db.close()
        flash('File not found.', 'warning')
        return redirect('/software')

    if not is_admin_user():
        cursor.execute("""
            SELECT lab_assigned
            FROM users
            WHERE id_number=%s
            LIMIT 1
        """, (user['id_number'],))
        assigned_row = cursor.fetchone() or {}
        assigned_lab = (assigned_row.get('lab_assigned') or '').strip()
        if assigned_lab and assigned_lab not in LAB_LOOKUP:
            assigned_lab = ''
        if not assigned_lab or (row.get('lab_code') not in (None, '', assigned_lab)):
            cursor.close()
            db.close()
            flash('You are not allowed to access this file.', 'danger')
            return redirect('/software')

    cursor.close()
    db.close()

    upload_dir = app.config['SOFTWARE_UPLOAD_FOLDER']
    file_path = os.path.join(upload_dir, row['file_name'])
    if not os.path.exists(file_path):
        flash('File is missing on the server.', 'warning')
        return redirect('/software')

    return send_file(file_path, as_attachment=True, download_name=row['original_name'])


@app.route('/shop/redeem', methods=['POST'])
def redeem_reward():
    if 'user' not in session:
        return redirect('/')

    user = session['user']
    reward_id = request.form.get('reward_id')

    try:
        reward_id = int(reward_id)
    except (TypeError, ValueError):
        flash('Invalid reward selection.', 'warning')
        return redirect('/shop')

    db = get_db()
    ensure_rewards_table(db)
    ensure_reward_redemptions_table(db)
    ensure_user_feedback_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, name, description, points_cost, is_physical, stock, status
        FROM rewards
        WHERE id=%s
        LIMIT 1
    """, (reward_id,))
    reward = cursor.fetchone()

    if not reward or reward['status'] != 'active':
        cursor.close()
        db.close()
        flash('Reward is not available.', 'warning')
        return redirect('/shop')

    earned_points, spent_points, available_points = get_points_summary(cursor, user['id_number'])
    if available_points < int(reward['points_cost']):
        cursor.close()
        db.close()
        flash('Not enough points to redeem this reward.', 'warning')
        return redirect('/shop')

    if reward['is_physical'] and (reward['stock'] is None or int(reward['stock']) <= 0):
        cursor.close()
        db.close()
        flash('This item is out of stock.', 'warning')
        return redirect('/shop')

    if reward['is_physical']:
        cursor.execute("""
            UPDATE rewards
            SET stock = stock - 1
            WHERE id=%s AND stock > 0
        """, (reward_id,))

    status = 'pending' if reward['is_physical'] else 'approved'
    cursor.execute("""
        INSERT INTO reward_redemptions (
            reward_id, reward_name, student_id_number, points_cost, is_physical, status
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """, (reward_id, reward['name'], user['id_number'], reward['points_cost'], int(reward['is_physical']), status))

    db.commit()
    cursor.close()
    db.close()

    if reward['is_physical']:
        flash('Redemption submitted. We will notify you when it is ready for pickup.', 'success')
    else:
        flash('Reward redeemed successfully.', 'success')
    return redirect('/shop')


@app.route('/admin/rewards')
def admin_rewards():
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    db = get_db()
    ensure_rewards_table(db)
    ensure_reward_redemptions_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, name, description, points_cost, is_physical, stock, status
        FROM rewards
        ORDER BY points_cost ASC, name ASC
    """)
    rewards = cursor.fetchall()

    cursor.execute("""
        SELECT r.id, r.reward_name, r.points_cost, r.is_physical, r.status, r.created_at,
               r.ready_at, r.claimed_at, r.admin_note,
               u.id_number, u.first_name, u.last_name, u.middle_name
        FROM reward_redemptions r
        LEFT JOIN users u ON u.id_number = r.student_id_number
        ORDER BY r.created_at DESC
        LIMIT 50
    """)
    redemptions = cursor.fetchall()
    cursor.close()
    db.close()

    for row in redemptions:
        full_name = f"{row.get('last_name') or ''}, {row.get('first_name') or ''}"
        if row.get('middle_name'):
            full_name = f"{full_name} {row['middle_name']}"
        row['student_name'] = full_name.strip(', ')

    return render_template('admin_rewards.html', rewards=rewards, redemptions=redemptions)


@app.route('/admin/rewards/create', methods=['POST'])
def admin_create_reward():
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    name = (request.form.get('name') or '').strip()
    description = (request.form.get('description') or '').strip()
    points_cost = (request.form.get('points_cost') or '').strip()
    is_physical = 1 if request.form.get('is_physical') == '1' else 0
    stock_raw = (request.form.get('stock') or '').strip()
    status = (request.form.get('status') or 'active').strip()

    if not name or not points_cost.isdigit():
        flash('Reward name and points cost are required.', 'warning')
        return redirect('/admin/rewards')

    stock = None
    if is_physical:
        try:
            stock = int(stock_raw)
        except ValueError:
            stock = 0

    db = get_db()
    ensure_rewards_table(db)
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO rewards (name, description, points_cost, is_physical, stock, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (name, description or None, int(points_cost), is_physical, stock, status))
    db.commit()
    cursor.close()
    db.close()

    flash('Reward added successfully.', 'success')
    return redirect('/admin/rewards')


@app.route('/admin/rewards/<int:reward_id>/update', methods=['POST'])
def admin_update_reward(reward_id):
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    name = (request.form.get('name') or '').strip()
    description = (request.form.get('description') or '').strip()
    points_cost = (request.form.get('points_cost') or '').strip()
    is_physical = 1 if request.form.get('is_physical') == '1' else 0
    stock_raw = (request.form.get('stock') or '').strip()
    status = (request.form.get('status') or 'active').strip()

    if not name or not points_cost.isdigit():
        flash('Reward name and points cost are required.', 'warning')
        return redirect('/admin/rewards')

    stock = None
    if is_physical:
        try:
            stock = int(stock_raw)
        except ValueError:
            stock = 0

    db = get_db()
    ensure_rewards_table(db)
    cursor = db.cursor()
    cursor.execute("""
        UPDATE rewards
        SET name=%s,
            description=%s,
            points_cost=%s,
            is_physical=%s,
            stock=%s,
            status=%s
        WHERE id=%s
    """, (name, description or None, int(points_cost), is_physical, stock, status, reward_id))
    db.commit()
    cursor.close()
    db.close()

    flash('Reward updated successfully.', 'success')
    return redirect('/admin/rewards')


@app.route('/admin/redemptions/<int:redemption_id>/status', methods=['POST'])
def admin_update_redemption_status(redemption_id):
    if not is_admin_user():
        flash('Please log in as admin.', 'danger')
        return redirect('/')

    status = (request.form.get('status') or '').strip()
    admin_note = (request.form.get('admin_note') or '').strip()

    if status not in ('approved', 'ready', 'claimed', 'denied'):
        flash('Invalid redemption status.', 'warning')
        return redirect('/admin/rewards')

    db = get_db()
    ensure_rewards_table(db)
    ensure_reward_redemptions_table(db)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, reward_id, reward_name, is_physical, status
        FROM reward_redemptions
        WHERE id=%s
        LIMIT 1
    """, (redemption_id,))
    redemption = cursor.fetchone()

    if not redemption:
        cursor.close()
        db.close()
        flash('Redemption not found.', 'warning')
        return redirect('/admin/rewards')

    if status == 'denied' and redemption['is_physical']:
        cursor.execute("""
            UPDATE rewards
            SET stock = stock + 1
            WHERE id=%s
        """, (redemption['reward_id'],))

    ready_at = datetime.now() if status == 'ready' else None
    claimed_at = datetime.now() if status == 'claimed' else None

    cursor.execute("""
        UPDATE reward_redemptions
        SET status=%s,
            admin_note=%s,
            updated_at=NOW(),
            ready_at=%s,
            claimed_at=%s
        WHERE id=%s
    """, (status, admin_note or None, ready_at, claimed_at, redemption_id))
    db.commit()
    cursor.close()
    db.close()

    if status == 'ready':
        flash('Reward marked as ready for pickup.', 'success')
    elif status == 'claimed':
        flash('Reward marked as claimed.', 'success')
    elif status == 'denied':
        flash('Redemption denied.', 'warning')
    else:
        flash('Redemption updated.', 'success')

    return redirect('/admin/rewards')


@app.route('/notifications/mark-seen', methods=['POST'])
def mark_notifications_seen():
    if 'user' not in session:
        return jsonify({'ok': False}), 401

    user = session['user']
    announcements = fetch_announcements(limit=1, for_user=user)
    if announcements:
        session['last_seen_announcement_id'] = announcements[0]['id']
    return jsonify({'ok': True})


@app.route('/reservation/create', methods=['POST'])
def create_reservation():
    if 'user' not in session:
        return redirect('/')

    user = session['user']
    lab_code = (request.form.get('lab_code') or '').strip()
    reservation_date = (request.form.get('reservation_date') or '').strip()
    reservation_slot = (request.form.get('reservation_slot') or '').strip()
    purpose = (request.form.get('purpose') or '').strip()
    seat_no_raw = (request.form.get('seat_no') or '').strip()

    if lab_code not in LAB_LOOKUP:
        flash('Please select a valid laboratory.', 'warning')
        return redirect('/dashboard')

    if reservation_slot not in RESERVATION_SLOTS:
        flash('Please select a valid reservation slot.', 'warning')
        return redirect('/dashboard')

    try:
        seat_no = int(seat_no_raw)
    except ValueError:
        flash('Please select a valid PC seat.', 'warning')
        return redirect('/dashboard')

    if seat_no < 1 or seat_no > LAB_LOOKUP[lab_code]['capacity']:
        flash('Selected PC seat is out of range for this laboratory.', 'warning')
        return redirect('/dashboard')

    try:
        reservation_day = datetime.strptime(reservation_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Please choose a valid reservation date.', 'warning')
        return redirect('/dashboard')

    if reservation_day < datetime.now().date():
        flash('Reservation date cannot be in the past.', 'warning')
        return redirect('/dashboard')

    db = get_db()
    ensure_reservations_table(db)
    ensure_sit_in_logs_table(db)
    cursor = db.cursor(dictionary=True)

    usage = get_session_usage(cursor, user['id_number'])
    if usage['remaining'] <= 0:
        cursor.close()
        db.close()
        flash('You have no remaining sessions for reservation.', 'warning')
        return redirect('/dashboard')

    cursor.execute("""
        SELECT id
        FROM reservations
        WHERE lab_code=%s
          AND seat_no=%s
          AND reservation_date=%s
          AND reservation_slot=%s
          AND status IN ('pending', 'approved')
        LIMIT 1
    """, (lab_code, seat_no, reservation_date, reservation_slot))
    if cursor.fetchone():
        cursor.close()
        db.close()
        flash('That PC seat is already reserved for the selected schedule.', 'warning')
        return redirect(f"/dashboard?lab_code={lab_code}&reservation_date={reservation_date}&reservation_slot={reservation_slot}")

    cursor.execute("""
        INSERT INTO reservations (student_id_number, lab_code, seat_no, purpose, reservation_date, reservation_slot, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'pending')
    """, (user['id_number'], lab_code, seat_no, purpose or 'General use', reservation_date, reservation_slot))
    db.commit()
    cursor.close()
    db.close()

    flash('Reservation request submitted. Waiting for admin approval.', 'success')
    return redirect(f"/dashboard?lab_code={lab_code}&reservation_date={reservation_date}&reservation_slot={reservation_slot}")


@app.route('/reservation/seats')
def reservation_seats():
    if 'user' not in session and not is_admin_user():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    lab_code = (request.args.get('lab_code') or '').strip()
    reservation_date = (request.args.get('reservation_date') or '').strip()
    reservation_slot = (request.args.get('reservation_slot') or '').strip()

    if lab_code not in LAB_LOOKUP:
        return jsonify({'success': False, 'message': 'Invalid lab.'}), 400
    if reservation_slot not in RESERVATION_SLOTS:
        return jsonify({'success': False, 'message': 'Invalid time slot.'}), 400

    try:
        datetime.strptime(reservation_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid reservation date.'}), 400

    db = get_db()
    ensure_reservations_table(db)
    cursor = db.cursor(dictionary=True)
    taken = get_taken_seats(cursor, lab_code, reservation_date, reservation_slot)
    capacity = LAB_LOOKUP[lab_code]['capacity']
    seats = []
    for seat in range(1, capacity + 1):
        seats.append({'seat_no': seat, 'is_taken': seat in taken})
    cursor.close()
    db.close()

    return jsonify({
        'success': True,
        'lab_code': lab_code,
        'capacity': capacity,
        'seats': seats
    })


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
    ensure_reservations_table(db)
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

    usage = get_session_usage(cursor, user['id_number'])
    completed_sessions = usage['completed']
    if usage['remaining'] <= 0:
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