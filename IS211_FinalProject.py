from flask import Flask
from flask import render_template
from flask import url_for, redirect
from flask import request
from flask import g
import sqlite3 as lite 


app = Flask(__name__)

def get_db():
    db = lite.connect('database.db')
    db.row_factory = lite.Row
    
    return db

def init_db():  

    db = get_db()

    with app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

