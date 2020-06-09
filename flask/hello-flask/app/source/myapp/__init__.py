#!flask/bin/python

from flask import Flask, session, redirect, url_for, request
from flask_failsafe import failsafe
from markupsafe import escape
from datetime import timedelta
import sys
import json


app = Flask(__name__)
app.secret_key = "any random secret"


def log_console(string):
    print(string, file=sys.stderr)


# expire session
@app.before_request
def before_request():
    app.permanent_session_lifetime = timedelta(seconds=30)


@app.route('/')
def index():
    log_console(session)
    if 'username' in session:
        return 'Logged in as %s' % escape(session['username'])
    return 'You are not logged in'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return '''
        <form method="post">
            <p><input type=text name=username>
            <p><input type=submit value=Login>
        </form>
    '''


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))

