from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
import config

pymysql.install_as_MySQLdb()

app = Flask(__name__, instance_relative_config=True)
app.config['DEBUG'] = config.DEBUG
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}/flask_demo'.format(config.username, config.password, config.db_address)

db = SQLAlchemy(app)

from wxcloudrun import views
from wxcloudrun.routes.battery_test import battery_test_bp
app.register_blueprint(battery_test_bp, url_prefix='/api/battery-test')

app.config.from_object('config')
