#!/usr/bin/env python3
''' Defines public routes that does not require user authentication '''
from flask import render_template, redirect, url_for, request, flash, jsonify,\
    session
from urllib.parse import urlsplit
import re
from backend.models.forms import LoginForm, SignUpForm
from flask_login import current_user, login_user
from backend.views import pub_views
from backend.auth import AUTH
from backend.db_ops.database import DB
from backend.models.forms import LoginForm, SignUpForm

db = DB()


@pub_views.route('/')
def landing_page():
    ''' Returns the landing/welcome page '''
    return render_template('index.html')


@pub_views.route('/about')
def about():
    ''' Returns the about page '''
    return jsonify({'About page'})
    # return render_template('about.html', page='About')


@pub_views.route('/signup', methods=['GET', 'POST'])
def signup():
    ''' Handles the creation of new User object '''
    if current_user.is_authenticated:
        return redirect(url_for('user_views.dashboard'))
    form = SignUpForm()
    if form.validate_on_submit():
        data = {
            'full_name': form.full_name.data,
            'email': form.email.data.lower(),
            'username': form.username.data,
            'password': form.password.data
        }
        AUTH.register_user(**data)
        flash('Registration was successful, congratulations!')
        return redirect(url_for('pub_views.login'))
    return render_template('accounts.html', form=form, page='signup')


@pub_views.route('/login', methods=['GET', 'POST'])
def login():
    ''' Processes user login by validating user's login credentials '''
    if current_user.is_authenticated:
        return redirect(url_for('user_views.dashboard'))

    # For requests coming from applications
    if request.headers.get('Content-Type') == 'application/json':
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'Incorrect Username or Password'}), 401
        email = data.get('email').lower()
        password = data.get('password')
        email_regex = re.compile(r"[^@]+@[^@]+\.[^@]+")

        if not email_regex.match(email):
            return jsonify({'error': 'Incorrect Username or Password'}), 401
        if AUTH.is_valid_login(email, password):
            user = AUTH.get_obj('User', email)
            if user.session_id is None:
                session_id = AUTH.set_session_id(user.id)
                # sets session_id in user session for further authentication
                session['session_id'] = session_id

                response = jsonify({'Login': 'successful'})
                return response

            return jsonify({"User": "Already Logged in"})
    else:
        form = LoginForm()
        if form.validate_on_submit():
            email = form.email.data.lower()
            if AUTH.is_valid_login(
                    email, form.password.data):
                user = AUTH.get_obj('User', email)

                login_user(user, remember=form.remember_me)

                session_id = AUTH.set_session_id(user.id)
                # sets the session_id for logged in client cookies
                session['session_id'] = session_id

                response = redirect(url_for('user_views.dashboard'))

                # Retrieves the page in cases where the user tries to access a
                # previously visited page after logging out and later logs in
                next_page = request.args.get('next')
                if not next_page or urlsplit(next_page).netloc != '':
                    print('got here')
                    next_page = url_for("user_views.dashboard")

                return response

            flash('Incorrect Email or Password')
            # Prevents re-submission during page refresh
            return redirect(url_for('pub_views.login'))

        return render_template('accounts.html', form=form, page='login')
