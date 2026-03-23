from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="sit_in_db"
    )


@app.route('/')
def login():
    return render_template('login.html')


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/about')
def about():
    return render_template('about.html')


def get_admin_mock_data():
    stats = {
        'students_registered': 38,
        'currently_sit_in': 0,
        'total_sit_in': 15,
    }

    announcements = [
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

    students = [
        {
            'id_number': '123',
            'name': 'Kimmy K. Negcassa',
            'year_level': '1',
            'course': 'BSIT',
            'remaining': 30,
        },
        {
            'id_number': '1234',
            'name': 'Kris J. Rasi',
            'year_level': '1',
            'course': 'BSIT',
            'remaining': 30,
        },
        {
            'id_number': '2000',
            'name': 'Jude Jefferson L. Sandalo',
            'year_level': '4',
            'course': 'BSIT',
            'remaining': 29,
        },
        {
            'id_number': '123123',
            'name': 'Jermaine A. Aguilar',
            'year_level': '3',
            'course': 'BSIT',
            'remaining': 30,
        },
        {
            'id_number': '123456',
            'name': 'Jan V. Sencador',
            'year_level': '2',
            'course': 'BSIT',
            'remaining': 30,
        },
        {
            'id_number': '3677937',
            'name': 'Jeff Pelorina Salimbangon',
            'year_level': '4',
            'course': 'BSIT',
            'remaining': 27,
        },
    ]

    current_sitins = []

    return stats, announcements, students, current_sitins


@app.route('/admin')
def admin_dashboard():
    stats, announcements, students, current_sitins = get_admin_mock_data()
    return render_template('admin_dashboard.html',
                           stats=stats,
                           announcements=announcements,
                           students=students,
                           current_sitins=current_sitins)


@app.route('/admin/search')
def admin_search():
    return render_template('admin_search.html')


@app.route('/admin/students')
def admin_students():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT id_number, last_name, first_name, middle_name, course, course_level
        FROM users
        WHERE id_number NOT LIKE 'adm-%'
        ORDER BY last_name, first_name
    """)
    users = cursor.fetchall()
    cursor.close()
    db.close()

    students = []
    for user in users:
        full_name = f"{user['last_name']}, {user['first_name']}"
        if user.get('middle_name'):
            full_name = f"{full_name} {user['middle_name']}"

        students.append({
            'id_number': user['id_number'],
            'name': full_name,
            'year_level': user['course_level'],
            'course': user['course'],
            'remaining': 30,
        })

    return render_template('admin_students.html', students=students)


@app.route('/admin/sit-in')
def admin_sit_in():
    return render_template('admin_sit_in.html')


@app.route('/admin/sit-in-records')
def admin_sit_in_records():
    stats, announcements, students, current_sitins = get_admin_mock_data()
    return render_template('admin_sit_in_records.html', current_sitins=current_sitins)


@app.route('/admin/sit-in-reports')
def admin_sit_in_reports():
    return render_template('admin_sit_in_reports.html')


@app.route('/admin/feedback-reports')
def admin_feedback_reports():
    return render_template('admin_feedback_reports.html')


@app.route('/admin/reservations')
def admin_reservations():
    return render_template('admin_reservations.html')


@app.route('/login_user', methods=['POST'])
def login_user():
    id_number = request.form['id_number']
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
    sessions_used = 0
    sessions_remaining = 30

    return render_template('dashboard.html',
                           user=user,
                           sessions_used=sessions_used,
                           sessions_remaining=sessions_remaining)


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


if __name__ == '__main__':
    app.run(debug=True)