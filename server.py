from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
from flask.ext.bcrypt import Bcrypt
import re
app = Flask(__name__)
app.secret_key= 'secret'

bcrypt = Bcrypt(app)
mysql = MySQLConnector(app, 'wall')
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['post'])
def add_user():
    flag = False
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    pword = request.form['pass']
    pword2 = request.form['pass2']
    query = "SELECT COUNT(email) AS num FROM users WHERE email=:email"
    data = {'email':email}
    check = mysql.query_db(query, data)
    if len(fname) < 2:
        flag = True
        flash('First Name must be at least 2 characters')
    if len(lname) < 2:
        flag = True
        flash('Last Name must be at least 2 characters')
    if len(email) < 1 or not EMAIL_REGEX.match(email):
        flag = True
        flash('Email invalid')
    elif check[0]['num'] > 0:
        flag = True
        flash('An account with this email already exists')
    if len(pword) < 8:
        flag = True
        flash('Password must be at least 8 characters')
    elif pword != pword2:
        flag = True
        flash('Passwords don\'t match')
    if flag:
        return redirect('/')

    pwhash = bcrypt.generate_password_hash(pword)
    query = "INSERT INTO users(first_name, last_name, email, pass_hash, created_at) VALUES (:fname, :lname, :email, :pass_hash, NOW())"
    data = {'fname':fname, 'lname':lname, 'email':email, 'pass_hash':pwhash}
    mysql.query_db(query,data)
    query = "SELECT * FROM users WHERE email = :email LIMIT 1"
    data = {'email':email}
    user = mysql.query_db(query, data)[0]
    session['id'] = user['id']
    print session['id']
    session['name'] = user['first_name'] + ' ' + user['last_name']
    return redirect('/wall')

@app.route('/login', methods=['post'])
def login():
    email = request.form['email']
    password = request.form['pass']
    query = "SELECT * FROM users WHERE email = :email LIMIT 1"
    data = {'email':email}
    user = mysql.query_db(query, data)
    if len(user) == 0:
        flash('Invalid Email')
        return redirect('/')
    user = user[0]
    if bcrypt.check_password_hash(user['pass_hash'], password):
        session['id'] = user['id']
        session['name'] = user['first_name'] + ' ' + user['last_name']
        return redirect('/wall')
    else:
        flash('Invalid Password')
        return redirect('/')

@app.route('/wall', methods=['get', 'post'])
def wall():
    if not 'id' in session:
        flash('Not Logged In')
        return redirect('/')
    query = """SELECT first_name, last_name, messages.created_at AS tstamp, messages.id AS mid, message
    FROM users JOIN messages ON users.id = messages.user_id ORDER BY tstamp DESC"""
    messages = mysql.query_db(query)
    query = """SELECT first_name, last_name, comments.message_id AS mid, comments.created_at AS tstamp, comment
    FROM users JOIN comments ON users.id = comments.user_id"""
    comments = mysql.query_db(query)
    return render_template('wall.html', messages=messages, comments=comments)

@app.route('/logout', methods=['get', 'post'])
def logout():
    session.clear()
    return redirect('/')

@app.route('/message', methods=['post'])
def add_message():
    message = request.form['message']
    if len(message) < 1:
        return redirect('/wall')
    query = "INSERT INTO messages(user_id, message, created_at) VALUES(:user_id, :message, NOW())"
    data = {'user_id': session['id'], 'message': message}
    mysql.query_db(query, data)
    return redirect('/wall')

@app.route('/comment', methods=['post'])
def add_comment():
    mid = request.form['submit']
    comment = request.form['comment']
    query = "INSERT INTO comments(user_id, message_id, comment, created_at) VALUES(:uid, :mid, :comment, NOW())"
    data = {'uid': session['id'], 'mid': mid, 'comment':comment}
    mysql.query_db(query, data)
    return redirect('/wall')

app.run(debug=True)
