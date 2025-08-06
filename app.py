from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

from routes import main_routes, auth_routes, admin_routes
app.register_blueprint(main_routes.bp)
app.register_blueprint(auth_routes.bp)
app.register_blueprint(admin_routes.bp)

if __name__ == '__main__':
    app.run(debug=True)
