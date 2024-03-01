#!/usr/bin/env python3
''' Handles user routes '''
from flask import jsonify, request, url_for
from flask_login import current_user, login_required
from backend.api.v1.routes import api
from backend.auth import AUTH
from backend.db_ops.user_choices import Choice
from backend.db_ops.database import DB

db = DB()
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

@api.route('remove', methods=['DELETE'])
def remove_user():
    ''' GET /api/user/remove
    Handles user removal
    '''
    user = AUTH.authenticate_user()

    # get all user friends ids
    friends = user.friends
    id_list_of_user_friends = [friend_id for friend_id in friends.keys()]

    # remove all conversations if friend had already removed user befor now
    for friend_id in id_list_of_user_friends:
        AUTH.confirm_and_delete(user.id, friend_id)

    # remove user if user is in friends allowed_tracks and tracking_me
    # and vice versa
    for friend_id in id_list_of_user_friends:
        friend = db.find_user_by(id=friend_id)
        if friend:
            friend_allowed_track = friend.allowed_tracks
            if user.id in friend_allowed_track:
                CHOICE.remove_track_access(user.id, friend_id)

            if user.id in friend.tracking_me:
                CHOICE.remove_track_access(friend_id, user.id)

    # finally delete user
    status = db.remove_user(user.id)
    if status:
        redirect_url = url_for('pub_views.landing_page')

        # Return a JSON response with the redirect URL
        response = jsonify({'redirect': redirect_url})
        return response
    return jsonify({'status': 'Something went wrong'}), 401
