#!/usr/bin/env python3
''' Handles user routes '''
from flask import jsonify, request
from flask_login import current_user, login_required
from backend.api.v1.routes import api
from backend.auth import AUTH
from backend.db_ops.user_choices import Choice

CHOICE = Choice()


@login_required
@api.route('/user_info')
def get_user_info() -> str:
    ''' GET api/user_info
    Return: user information (excluding some sensitive data)
    '''
    if not current_user.is_authenticated:
        return jsonify({'status': 'unknown user'}), 401

    user_id = current_user.get_id()
    user = AUTH.get_obj('User', user_id)
    if not user:
        return jsonify({'user': None}), 401
    user_dict = user.to_dict()
    del user_dict['_password']
    del user_dict['reset_token']

    return jsonify(user_dict)


@login_required
@api.route('/update_location/', methods=['POST'])
def update_location() -> str:
    ''' POST api/user/update_location
    Updates the current user's location '''
    if not current_user.is_authenticated:
        return jsonify({'status': 'unknown user'}), 401
    data = request.get_json()
    longitude = data.get('longitude')
    latitude = data.get('latitude')
    location = [latitude, longitude]

    user_id = current_user.get_id()

    if CHOICE.set_location(user_id, location):
        return jsonify({'status': 'success'})
    return jsonify({'status': 'failure'}), 400
