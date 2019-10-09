from flask import render_template, flash,url_for,request, redirect
from spendwell_app import app, db, bcrypt
from spendwell_app.models import User, Log
from datetime import datetime
from spendwell_app.forms import RegisterationForm, LoginForm, UserLogForm, InsightForm
from flask_login import login_required,login_user, current_user, logout_user
from spendwell_app import ml_classifier
from sqlalchemy import text

import plotly
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import json



@app.route('/')
@app.route('/home')
def home():
	return render_template('home.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/register', methods = ['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegisterationForm()
	if form.validate_on_submit():
		# hashed_password = bcrypt.generate_password_hash(form.password.data)#.decode('utf8')
		user = User(username = form.username.data, email = form.email.data, password = form.password.data)
		db.session.add(user)
		db.session.commit()
		flash(f'Hey {form.username.data}! Your account created sucessfully','success')
		return redirect(url_for('login'))
	return render_template('register.html', title = 'Register', form= form)

@app.route('/login',methods = ['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email = form.email.data).first()
		if user and user.password == form.password.data:
			login_user(user, remember = form.remember.data)
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('user_log'))
		else:
			flash('Login Unsucessfully please check your email and password', 'danger')
	return render_template('login.html', title = 'Login', form= form)

@app.route('/user_log', methods = ['GET','POST'])
@login_required
def user_log():
	form = UserLogForm()
	if form.validate_on_submit():
		category = ml_classifier.predictor(user_log = form.user_log.data)
		log = Log(user_log = form.user_log.data , category = category, amount = form.amount.data,author = current_user)
		db.session.add(log)
		db.session.commit()
		flash(f'Your Expense has been Logged to Category: {category.capitalize()}','success')
		return redirect(url_for('user_log'))
	return render_template('user_log.html', title = 'Expense', form = form)

@app.route('/recomnd', methods = ['GET','POST'])
@login_required
def recomnd():
	amount = []
	category = []
	info = db.engine.execute(f"SELECT SUM(amount),category FROM log WHERE user_id = {current_user.id} AND extract(month from transaction_date) = 09 GROUP BY category;")
	res = [i for i in info]
	for val in res:
		amount.append(int(val[0]))
		category.append(val[1])
	h_cat = category[np.argmax(amount)]
	userText = request.args.get('msg')
	return render_template('recomnd.html', h_cat = h_cat)

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    return str(ml_classifier.chatbot_intent_predict(user_query = userText))

@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('home'))

@app.route('/account')
@login_required
def account():
	image_file = url_for('static', filename = 'profile_pic/' + current_user.image_file)
	return render_template('account.html', title='Account', image_file = image_file)

@app.route('/insight',methods=['GET', 'POST'])
@login_required
def insight():
	form = InsightForm()
	current_month = form.month.data
	year = '2019'
	if current_month != 'None':
		month = current_month
	else:
		month = '0'+ str(datetime.now().month)

	month_name = ['January','February','March','April','May','June','July','August','September','October','November','December']
	month_id = month.lstrip('0')
	c_month = month_name[int(month_id) - 1]
	print(c_month)
	#logs = Log.query.filter_by(user_id = current_user.id).all()
	pie_plot = generate_plot(month)
	yplot = year_plot(year)
	return render_template('insight.html', title = 'Insight', plot = pie_plot, y_plot = yplot,c_month = c_month,form = form)

def year_plot(year):
	amount = []
	date = []
	year_log = db.engine.execute(text(f"SELECT SUM(amount),transaction_date::date FROM log WHERE user_id = {current_user.id} AND extract(year from transaction_date) = 2019 GROUP BY transaction_date::date;"))
	res = [y for y in year_log]
	for val in res:
		amount.append(val[0])
		date.append(val[1])
	fig = go.Figure()
	data = fig.add_trace(go.Scatter(
		x=date,
		y=amount,
		name="Amount",
		line_color='deepskyblue',
		opacity=0.8))

	graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

	return graphJSON

def generate_plot(month):
	amount = []
	category = []
	logs = db.engine.execute(text(f"SELECT SUM(amount),category,transaction_date::date FROM log WHERE user_id = {current_user.id} AND extract(month from transaction_date) = {month} GROUP BY category,transaction_date;"))
	res = [l for l in logs]
	for val in res:
		amount.append(val[0])
		category.append(val[1])
	# data = [go.Pie(labels = category,values = amount,name = 'Amount',hole =.5,marker_colors = ['#f74545','#d0ed28','#1af01e','#f79225'])]
	data = [go.Pie(
		labels = category,
		values = amount,
        name = 'Amount',
        hole =.5,
        marker_colors = ['#f74545','#d0ed28','#1af01e','#f79225'] )]

	graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

	return graphJSON
