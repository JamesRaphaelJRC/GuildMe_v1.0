#!/usr/bin/env python3
''' Form module using flask-form '''
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
import re
from backend.auth import AUTH


class LoginForm(FlaskForm):
    ''' Defines the login form '''
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remeber Me')
    submit = SubmitField('Sign In')


class SignUpForm(FlaskForm):
    ''' Defines the sign-up form for new User registration '''
    full_name = StringField('Full name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm password',
                                     validators=[DataRequired(),
                                                 EqualTo('password')])
    submit = SubmitField('Sign up')

    def validate_username(self, username):
        ''' Checks if username already exists/used
            username.data fetches the username inputed in the SignUp form
        '''
        special_characters_pattern = re.compile(r'[@_!#$%^&*()<>?/\|}{~:]')
        if special_characters_pattern.search(username.data):
            raise ValidationError(
                'Username must not contain special characters')
        if AUTH.user_exists(username.data):
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        ''' Checks if email already exists/used
            email.data fetches the email entered in the SignUp form
        '''
        if AUTH.user_exists(email.data):
            raise ValidationError('Please use a different email.')

