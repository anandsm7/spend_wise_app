from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField,DecimalField,SelectField
from wtforms.validators import ValidationError,DataRequired, Length, Email, EqualTo
from spendwell_app.models import User

class RegisterationForm(FlaskForm):

	username = StringField('Username', 
			validators = [DataRequired(), Length(min =2 ,max =15)])
	email = StringField('Email', validators = [DataRequired(),Email()])

	password = PasswordField('Password', validators = [DataRequired()])
	confirm_password = PasswordField('Confirm Password',
	 validators = [DataRequired(), EqualTo('password')])
	submit = SubmitField('Sign Up')

	def validate_username(self, username):
		user = User.query.filter_by(username = username.data).first()
		if user:
			raise ValidationError('User name already exists')

	def validate_email(self, email):
		email = User.query.filter_by(email = email.data).first()
		if email:
			raise ValidationError('You already have an account for this Email ID')

class InsightForm(FlaskForm):
	month = SelectField('Month',choices = [('01','January'),('02','February'),('03','March'),('04','April'),('05','May'),
		('06','June'),('07','July'),('08','August'),('09','September'),('10','October'),('11','November'),('12','December')])


class LoginForm(FlaskForm):

	email = StringField('Email', validators = [DataRequired(),Email()])
	password = PasswordField('Password', validators = [DataRequired()])
	remember = BooleanField('Remember me')
	submit = SubmitField('Login')

class UserLogForm(FlaskForm):
	user_log = TextAreaField('Expense description', validators = [DataRequired(),Length(max=500)])
	amount = DecimalField('Amount', validators = [DataRequired()])
	submit = SubmitField('Add Expense')