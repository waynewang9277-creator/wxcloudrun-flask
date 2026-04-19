from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from wxcloudrun import views
app.register_blueprint(views.count_bp)

from wxcloudrun.routes.battery_test import battery_test_bp
app.register_blueprint(battery_test_bp, url_prefix='/api/battery-test')