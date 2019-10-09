from flask import Flask
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime
from flask_bcrypt import Bcrypt 
from flask_login import LoginManager
from flask_sslify import SSLify


app = Flask(__name__)
# sslify = SSLify(app)
app.config['SECRET_KEY'] = '4773d8da612ab150c488c3c5e62dcf3f'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:your_password@localhost:5432/your_db_name'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from spendwell_app import routes