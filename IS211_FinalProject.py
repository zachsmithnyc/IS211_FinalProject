from flask import Flask
from flask import render_template
from flask import url_for, redirect
from flask import request
from flask import g, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import abort
import functools
import sqlite3 as lite 


app = Flask(__name__)

'''
Database Initialization
'''

def get_db():
    db = lite.connect('database.db')
    db.row_factory = lite.Row
    
    return db

def init_db():  

    db = get_db()

    with app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

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
            session['user.id'] = user['id']
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
    @functools.wrap(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect('/login')

        return view(**kwargs)
    
    return wrapped_view

'''
Blog Dashboard Controllers
'''



if __name__ == "__main__":
    app.run(debug=True)