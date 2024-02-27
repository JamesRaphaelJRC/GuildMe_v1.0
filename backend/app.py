#!/usr/bin/env python3
''' Flask App module '''
from os import environ, getenv
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_login import LoginManager
from flask_cors import CORS
from backend.views import user_views, pub_views
from backend.api.v1.routes import api
from backend.api.v1.web_socket.chat import socket_io
import requests

# Loads the .env file
load_dotenv()

SECRET_KEY = environ.get('SECRET_KEY') or 'You_will_never_guess_!!!!!!'
UPLOAD_FOLDER = 'frontend/static/uploads/avatars'

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app, resources={r"backend/api/v1/*": {"origins": "*"}})


# Initialize flask app with SockeIO
socket_io.init_app(app)

# Set global strict slashes
app.url_map.strict_slashes = False

# Blueprint registration
app.register_blueprint(user_views)
app.register_blueprint(pub_views)
app.register_blueprint(api)

# Intialize app with flask LoginManager to manage user logins
login = LoginManager(app)

# Set the 'login' view function as the login_view of the login instance
login.login_view = 'pub_views.login'


@app.before_request
def before_request():
    ''' Authenticates every incoming requests to /api/* endpoints '''
    if request.endpoint and request.endpoint.startswith('api'):
        from backend.auth import AUTH
        AUTH.authenticate_user()


@login.user_loader
def load_user(user_id):
    # Load user
    from backend.db_ops.database import DB
    db = DB()
    return db.find_user_by(id=user_id)


@app.errorhandler(404)
def not_found(error) -> str:
    """ Not found handler
    """
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(401)
def unauthorized_error(error) -> str:
    '''
    Unauthorized access error handler
    '''
    return jsonify({"error": "Unauthorized"}), 401


@app.errorhandler(403)
def forbidden_error(error) -> str:
    '''
    Forbidden handler
    '''
    return jsonify({"error": "Forbidden"}), 403


if __name__ == "__main__":
    host = getenv("API_HOST", "0.0.0.0")
    port = getenv("API_PORT", "5000")
    socket_io.run(app, host=host, port=port, debug=True)
