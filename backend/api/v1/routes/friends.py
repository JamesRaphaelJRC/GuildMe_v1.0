#!/usr/bin/env python3
''' Handles user-friend requests '''
from flask import jsonify, request
from flask_login import current_user, login_required
from backend.api.v1.routes import api
from backend.auth import AUTH
from backend.db_ops import db
from backend.db_ops.user_choices import Choice

CHOICE = Choice()


@login_required
@api.route('/friends')
def get_user_friends():
    ''' GET api/user/friends
    Retrieves all user friends and adds a new key (unread_messages)
    with a boolean value. True if user has unread message from friend
    '''
    user = AUTH.authenticate_user()
    user_dict = user.to_dict()
    friends = user_dict.get('friends')
    for friend in friends.values():
        # adds new key/value for unread messages
        if AUTH.has_unread_messages(user.id, friend.get('id')):
            friend["unread_messages"] = True
        else:
            friend["unread_messages"] = False
    return jsonify(friends)


@login_required
@api.route('/friends/new', methods=['POST'])
def add_friend():
    ''' POST api/user/friends/new
    Handles new friend addition to user's friends
    '''
    user = AUTH.authenticate_user()
    friend = request.get_json().get('friend')
    friend = db.find_user_by(username=friend)
    if not friend:
        return jsonify({"error": "Invalid friend"}), 400
    friend_id = friend.id
    if CHOICE.add_friend(user.id, friend_id):
        return jsonify({'status': 'friend added'})
    return jsonify({'status': 'something went wrong, check friend id'})


@login_required
@api.route('/friends/remove', methods=['DELETE'])
def remove_friend():
    ''' DELETE /api/user/friends/remove
    Handles removal of a friend from user's friend
    '''
    user = AUTH.authenticate_user()
    friend_name = request.get_json().get('friend')
    friend_id = CHOICE.remove_friend(user.id, friend_name)
    if friend_id:
        return jsonify({'status': 'friend removed', 'friend_id': friend_id})
    return jsonify({'status': 'something went wrong, check friend id'}), 400


@login_required
@api.route('/friends/allow_track', methods=['GET', 'POST'])
def allow_track_access():
    ''' POST /api/user/friends/allow_track
    Handles user's choice to allow a friend to track

        GET /api/user/friends/allow_track
    Retrieves all friends that gave user the allow_track permission
    i.e all friends user can track
    '''
    user = AUTH.authenticate_user()

    if request.method == 'POST':
        friend = request.get_json().get('friend')
        friend = db.find_user_by(username=friend)
        if not friend:
            return jsonify({"error": "Invalid friend"}), 400

        friend_id = friend.id

        if CHOICE.allow_track_access(user.id, friend_id):
            return jsonify({'status': 'Track permission allowed'})
        return jsonify(
            {'status': 'something went wrong, check friend id'}
            ), 400
    else:
        # For GET requests
        permitted_friends = user.allowed_tracks
        return jsonify({'friends': permitted_friends})


@api.route('/friends/tracking_me')
def tracking_me():
    ''' GET /api/user/friends/tracking_me
    Return all friends user granted the allow_track permission
    i.e. friends tracking user
    '''
    user = AUTH.authenticate_user()
    permitted_friends = user.tracking_me
    return jsonify({'friends': permitted_friends})


@login_required
@api.route('/friends/disallow_track', methods=['POST'])
def disallow_track_access():
    ''' POST /api/user/friends/disallow_track
    Handles user's choice to disallow a friend from tracking user
    '''
    user = AUTH.authenticate_user()
    friend = request.get_json().get('friend')
    friend = db.find_user_by(username=friend)
    if not friend:
        return jsonify({"error": "Invalid friend"}), 400

    friend_id = friend.id

    if CHOICE.remove_track_access(user.id, friend_id):
        return jsonify({'status': 'Track permission disallowed'})
    return jsonify({'status': 'something went wrong, check friend id'}), 400


@login_required
@api.route('/friend/current_location', methods=['POST'])
def get_friend_location():
    ''' POST /api/user/friend/current_location
    Handle process with retrieval of friend current location
    '''
    user_id = AUTH.authenticate_user().id
    friend = request.get_json().get('friend')
    if not friend:
        return jsonify({"error": "Invalid friend"}), 400

    location = CHOICE.get_friend_location(user_id, friend)
    if location:
        return jsonify({'location': location})
    if location is None:
        return jsonify({"error": "Invalid friend/ no track access"}), 400
    if location is False:
        return jsonify({"error": "Friend has no location"}), 404


@api.route('/friends/search', methods=['POST'])
def search_friends():
    ''' POST /api/user/friends/search
    Handles search friend request
    '''
    user = AUTH.authenticate_user()
    query = str(request.get_json().get('query'))
    if query:
        friends = db.search_users(user.id, query)
        if friends is not None:  # also returns when friends is {}
            return jsonify(friends)
    return jsonify({'error': 'Empty or invalid search query'}), 400
