from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)


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
        }
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

        changes = (
            first_name != user['first_name'] or
            middle_name != user['middle_name'] or
            last_name != user['last_name'] or
            course != user['course'] or
            course_level != user['course_level'] or
            email != user['email'] or
            address != user['address']
        )

        if changes:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                UPDATE users SET first_name=%s, middle_name=%s, last_name=%s, course=%s, course_level=%s, email=%s, address=%s
                WHERE id_number=%s
            """, (first_name, middle_name, last_name, course, course_level, email, address, user['id_number']))
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
            })
            flash('A change has been done', 'success')
        else:
            flash('No changes were done', 'info')
        return redirect('/dashboard')

    return render_template('edit_profile.html', user=user)


if __name__ == '__main__':
    app.run(debug=True)