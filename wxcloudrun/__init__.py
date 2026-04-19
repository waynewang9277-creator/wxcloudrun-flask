from flask import Flask

app = Flask(__name__)
app.config['DEBUG'] = True

from wxcloudrun import views
app.register_blueprint(views.count_bp)