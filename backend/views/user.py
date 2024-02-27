#!/usr/bin/env python3
''' Handle user routes '''
from flask import redirect, render_template, url_for, request, jsonify,\
    session, flash
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required, logout_user
import os
from flask_socketio import emit
from backend.views import user_views
from backend.auth import AUTH
from backend.db_ops.database import DB
from backend.utils import utils

db = DB()

UPLOAD_FOLDER = 'frontend/static/uploads/avatars'
MAX_FILE_SIZE_MB = 2


@user_views.route("/logout")
@login_required
def logout():
    ''' Handles user logout '''
    # For requests from an application
    if request.headers.get('Content-Type') == 'application/json':
        user = AUTH.authenticate_user()
        user_id = user.id
        AUTH.remove_session_id(user_id)
        logout_user()  # also removes any remeber-me cookie

        # Redirect URL after successful logout
        redirect_url = url_for('pub_views.landing_page')

        # Return a JSON response with the redirect URL
        response = jsonify({'redirect': redirect_url})
        return response

    else:
        if current_user.is_authenticated:
            user_id = current_user.get_id()
            AUTH.remove_session_id(user_id)
            logout_user()
        return redirect(url_for('pub_views.landing_page'))


@user_views.route('/', methods=['GET'])
@login_required
def dashboard():
    ''' Returns the user's dashboard page '''
    user = AUTH.authenticate_user()
    return render_template('dashboard.html', user=user)


@user_views.route('/uploads', methods=['POST', 'GET'])
@login_required
def upload_file():
    user_id = current_user.get_id()
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '' or file is None:
            flash('No selected file')
            return redirect(request.url)

        if file and utils.allowed_file(file.filename):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(file.filename)

            # using the unique user id as the avatar name
            ext = filename.rsplit('.', 1)[1]
            new_name = f'{user_id}.{ext}'

            file_path = os.path.join(UPLOAD_FOLDER, new_name)
            file.save(file_path)

            # checks if the file size > MAX_FILE_SIZE_MB
            if utils.get_file_size_mb(file_path) > MAX_FILE_SIZE_MB:
                utils.compress_image(file_path, file_path)

            img_path = f'uploads/avatars/{new_name}'  # use relative path
            db.update_user(user_id, avatar=img_path)
            return redirect(url_for('user_views.dashboard'))

    return redirect(url_for('user_views.dashboard'))
