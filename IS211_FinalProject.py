import os
import random
from flask import Flask
from flask import render_template
from flask import url_for, redirect
from flask import request
from flask import g, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import abort
import functools
import sqlite3 as lite 

test_config = None
app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(app.instance_path, 'database.sqlite')
)

if test_config is None:
    app.config.from_pyfile('config.py', silent=True)
else:
    app.config.from_mapping(test_config)

try:
    os.makedirs(app.instance_path)
except OSError:
    pass

'''
Database Initialization
'''

def get_db():
    db = lite.connect(
        app.config['DATABASE'],
        detect_types=lite.PARSE_DECLTYPES
        )
    db.row_factory = lite.Row
    
    return db

def init_db():

    db = get_db()

    with app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

def register_admin():
    username = 'admin'
    password = 'password'

    db = get_db()
    db.execute(
        "INSERT INTO user (username, password) VALUES (?,?)",
        (username, generate_password_hash(password)),
    )
    db.commit()

'''
Authentication Controllers
'''

@app.route('/register', methods=['GET', 'POST'])
def register():
    '''
    Registers a new user
    Validates that their username is not taken
    hashes password
    '''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'
        
        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect('/login')
        flash(error)
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''log in a registered user'''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect Username'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect Password'
        
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect('/')

        flash(error)
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect('/login')

        return view(**kwargs)
    
    return wrapped_view

'''
Blog Dashboard Controllers
'''

@app.route('/')
def dashboard():
    db = get_db()
    posts = db.execute(
        "SELECT p.id, title, body, created, author_id, username"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    return render_template('dashboard.html', posts=posts)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id)"
                " VALUES (?, ?, ?)",
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect('/')

    return render_template('create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        "SELECT p.id, title, body, created, author_id, username"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " WHERE p.id = ?",
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} does not exist")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)
    
    return post

def get_future_post(id):
    """
    a function to retrieve stored posts to publish
    """
    post = get_db().execute(
        "SELECT title, body"
        " FROM future_posts"
        " WHERE id = ?",
        (id,)
    ).fetchone()
    return post

@app.route('/<int:id>/update', methods=['GET', 'POST'])
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required'

        if error is not None:
            flash(error)

        else:
            db = get_db()
            db.execute(
                "UPDATE post SET title = ?, body = ?"
                " WHERE id = ?",
                (title, body, id)
            )
            db.commit()
            return redirect('/')

    return render_template('update.html', post=post)

@app.route('/<int:id>/delete', methods=['POST',])
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute("DELETE FROM post WHERE id = ?", (id,))
    db.commit()
    return redirect('/')

@app.route('/auto', methods=['GET','POST'])
@login_required
def auto_add():
    id = random.randint(1, 2)
    post = get_future_post(id)
    db = get_db()
    db.execute("INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)", (post['title'], post['body'], g.user['id']))
    db.commit()
    return redirect('/')



if __name__ == "__main__":
    init_db()
    register_admin()
    app.run(debug=True)