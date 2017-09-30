#!/usr/bin/python
# -*- coding: utf-8 -*-



from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app =  Flask(__name__)

# Config MySQL
# mysql -u root -p
# show databases;
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'smartbarterdb'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor' # this works with ... for getting dict instead of tuples
# init mysql
mysql = MySQL(app)

# home
@app.route("/")
def home():
	return render_template('home.html')


# About us
@app.route("/aboutus")
def aboutus():
	return render_template('aboutus.html')


# Error 404 handler
@app.errorhandler(404)
def not_found(error):
	return render_template('404.html'),404

### Articles

@app.route('/articles')
def articles():
	# Create cursor
	cur = mysql.connection.cursor()

	# Get all the articles
	result = cur.execute("SELECT * FROM products")

	# fetch
	articles = cur.fetchall() # as we used app.config['MYSQL_CURSORCLASS'] = 'DictCursor' we are going to get dictionaries here 

	if result > 0:
		return render_template('articles.html', articles =  articles)
	else:
		msg = 'No articles found'
		return render_template('articles.html', msg = msg)

	#close connection
	cur.close()
	
# Single Article
@app.route('/article/<string:id>/')
def article(id):
	# Create cursor
	cur = mysql.connection.cursor()

	# Get all the articles
	result = cur.execute("SELECT * FROM products WHERE id = %s", [id])

	# fetch
	article = cur.fetchone()

	return render_template('article.html', article = article)

### Registration

# Register form class
class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min = 1, max = 50)])
	username = StringField('Username', [validators.Length(min = 4, max = 25)])
	email = StringField('Email', [validators.Length(min = 6, max = 50)])
	password = StringField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message = 'passwords do not match')])
	confirm = PasswordField('Confirm Password')

# User register
@app.route('/register', methods = ['GET', 'POST'])
def index():
	form = RegisterForm(request.form) #this request object is imported from flask
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))

		# Create Cursor
		cur = mysql.connection.cursor()

		# Execute Query
		cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s,%s,%s,%s)",
			(name, email, username, password))

		# Commit to DB
		mysql.connection.commit()

		# Close Connection
		cur.close()

		# Flash message in html
		# OBS: THIS FOLOWING MESSAGE IS NOT RENDERING!!!!!! FIX LATER
		flash('Now you are registered and can logg in', 'success')

		# Redirect to index
		return redirect(url_for('index'))

	return render_template('register.html', form = form)

# User login
@app.route('/login', methods = ['GET','POST'])
def login():
	if request.method == 'POST':
		#get form fields
		username = request.form['username']
		password_candidate = request.form['password'] 

		# Create cursor
		cur = mysql.connection.cursor()

		# Get user by username
		result = cur.execute("SELECT * FROM users WHERE username = %s",[username])

		if result > 0: # if there is at least one result found
			# Get stored hash
			data = cur.fetchone() # execute the former query and take the first row
			password = data['password']

			# Compare passwords
			if sha256_crypt.verify(password_candidate,password):
				# Passed
				session['logged_in'] = True # session is a function/object (not sure) of flask
				session['username'] = username

				flash('You are now logged in', 'success')
				return redirect(url_for('dashboard'))

			else:
				error =  "Invalid Login"
				return render_template('login.html',error = error)
			# Close session
			cur.close()
		else:
		 	error =  "Username Not Found"
		 	return render_template('login.html',error = error)

	return render_template('login.html')


# Check if user logged in
# This function will be used as a decorator for prohibiting people not logged to enter in to the url
def is_logged_in(f):
	@wraps(f)
	def wrap(*args,**kwargs):
		if 'logged_in' in session:
			return f(*args,**kwargs)
		else:
			flash('Unauthorized, please log in','danger')
			return redirect(url_for('login'))
	return wrap


# Logout
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('Now you are logged out','success')
	#return render_template('/login.html')
	return redirect(url_for('login')) 


# Dashboard 
@app.route('/dashboard')
@is_logged_in
def dashboard():
	# Create cursor
	cur = mysql.connection.cursor()

	# Get all the articles
	result = cur.execute("SELECT * FROM products WHERE user_name = %s", [session['username']])

	# fetch
	articles = cur.fetchall() # as we used app.config['MYSQL_CURSORCLASS'] = 'DictCursor' we are going to get dictionaries here 

	if result > 0:
		return render_template('dashboard.html', articles =  articles)
	else:
		msg = 'No articles found'
		return render_template('dashboard.html', msg = msg)

	#close connection
	cur.close()
	return render_template('dashboard.html')

### Article presentation

# Article Form class
class ArticleForm(Form):
	article_name = StringField('Article Name', [validators.Length(min = 1, max = 80)])
	description = StringField('Description', [validators.Length(max = 200)])
	valoration = StringField('Valoration(1 to 10)', [validators.Length(min = 1)])


# Add Article 
@app.route('/add_article', methods = ['GET','POST'])
@is_logged_in
def add_article():
	form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		article_name = form.article_name.data
		description = form.description.data
		valoration = form.valoration.data

		# Create cursor
		cur = mysql.connection.cursor()

		# Execute
		cur.execute("INSERT INTO products(article_name,description,valoration,user_name) VALUES(%s,%s,%s,%s)",
		[article_name, description,valoration, session['username'] ] )

		# Commit changes
		mysql.connection.commit()

		# Close Connection
		cur.close()

		flash('Article created','success')

		return redirect(url_for('dashboard'))

	return render_template('add_article.html', form = form)




""" PIP LIBRARIES INSTALLED
flask
pip install flask-mysqldb 
Flask-WTF (FORM VALIDATION)
passlib (help with passwords)
"""




"""
def connect_db():
	return sqlite3.connect("library.db")
	#return sqlite3.connect("/Users/pasquinell/Code/backend-projects/flask-first/flask-first/library.db")
"""
"""@app.route('/')
def home():
	db_connection = connect_db()
	cursor = db_connection.execute('SELECT id, name FROM author;')
	authors = [dict(id =  row[0],name = row[1]) for row in cursor.fetchall()]
	print(authors)
	return render_template('templates/home.html', authors = authors)
"""


"""
@app.route('/author/<string:authors_last_name>')
def author(authors_last_name):
	if authors_last_name not in AUTHORS_INFO:
		abort(404)
	return render_template('routing/author.html',
							author = AUTHORS_INFO[authors_last_name])

@app.route('/author/<string:authors_last_name>/edit')
def author_admin(authors_last_name):
	abort(401) # administration permsions

@app.errorhandler(404)
def not_found(error):
	return render_template('routing/404.html'),404"""