#!/usr/bin/env python3
''' Websocket notification module '''
from flask import jsonify, request
from flask_socketio import emit, join_room, leave_room
from backend.api.v1.web_socket import socket_io
from backend.auth import AUTH
from backend.db_ops import db
from backend.db_ops.redis import RedisClient

redis_client = RedisClient()


@socket_io.on('connect')
def handle_connection():
    ''' creates a room for user to allow user to receive notifications
    room name == the user id. Thus every user have a room where he receives
    notifications
    '''
    user_id = AUTH.authenticate_user().id
    join_room(user_id)

    # check if user has unread notification and alert if true
    unread_notifications = redis_client.get_unread_notifications(user_id)
    if len(unread_notifications) > 0:
        emit('alert_user', room=user_id)

    # deletes every message > threshold day
    redis_client.delete_read_notifications_older_than(user_id, 15)


@socket_io.on('new_friend_request')
def send_friend_request(data):
    ''' Handles friend requests '''
    user = AUTH.authenticate_user()
    friend_data = data.get('data')

    if friend_data:
        if AUTH.is_valid_email(friend_data):
            friend = db.find_user_by(email=friend_data)
            if not friend:
                emit('error', {'message': f'No user with email: {friend_data}'
                               }, room=user.id)
                return
        else:
            friend = db.find_user_by(username=friend_data)
            if not friend:
                emit('error', {
                    'message': f'Username {friend_data} does not exist'
                    }, room=user.id)
                return
        if friend.username == user.username:
            emit('error', {'message': 'You cannot add yourself as a friend!'},
                 room=user.id)
            return
        if friend.id in user.friends:
            emit('error', {'message': f'{friend_data} is already your friend'},
                 room=user.id)
            return
        message = f"{user.username} sent you a friend request"
        notification = redis_client.new_notification(
            user.id, friend.id, message, 'friend request')
        if notification is False:
            emit('error', {'message': 'You already sent a friend request'},
                 room=user.id)
            return
        emit(
            'success', {'message': 'Your request has been sent successfully!'},
            room=user.id
            )
        emit('alert_user', room=friend.id)
        return
    emit('error', {'message': 'Enter a username or email'}, room=user.id)


@socket_io.on('get_friend_requests')
def get_friend_requests():
    ''' Handles retrieval of friend requests '''
    user_id = AUTH.authenticate_user().id
    friend_reqs = redis_client.get_friend_requests(user_id)
    emit('user_friend_requests', {'data': friend_reqs})


@socket_io.on('get_general_notifications')
def get_general_notifications():
    ''' Handles retrieval of user general notifications '''
    user_id = AUTH.authenticate_user().id
    gen_notifications = redis_client.get_general_notifications(user_id)
    emit('show_general_notifications', {'data': gen_notifications})


@socket_io.on('accepted_request')
def handle_accepted_friend_request(data):
    ''' Handles accepted friend request notification '''
    friend = data.get('friend')
    notification_id = data.get('id')
    user = AUTH.authenticate_user()
    friend_obj = db.find_user_by(username=friend)
    friend_id = friend_obj.id
    # Creat a new notification and alert friend that his request is accepted
    message = f'{user.username} accepted your friend request'
    notification_type = 'general'
    notification = redis_client.new_notification(user.id, friend_id, message,
                                                 notification_type)
    if notification:
        emit('alert_user', room=friend_id)
        emit('success', {
            'message': f'You are now friends with {friend_obj.username}'
            }, room=user.id)
        # reload the general notifications of the friend
        emit('reload_general_notification', room=friend_id)

    # delete the friend request notification
    status = redis_client.delete_notification(user.id, notification_id)
    if status:
        emit('reload_friend_request', room=user.id)


@socket_io.on('mark as read')
def mark_notification_as_read(data):
    ''' Marks a notification as read '''
    user = AUTH.authenticate_user()
    notification_id = str(data.get('id'))
    status = redis_client.mark_as_read(user.id, notification_id)
    if status:
        emit('blurr read', room=user.id)


@socket_io.on('delete friend request')
def delete_notification(data):
    ''' Deletes a given user friend request when rejected '''
    user = AUTH.authenticate_user()
    notification_id = str(data.get('id'))
    status = redis_client.delete_notification(user.id, notification_id)
    if status:
        emit('reload_friend_request', room=user.id)


@socket_io.on('allowed track')
def allowed_track(data):
    ''' Notifies friend that a user has granted track access
    notifies user too.
    route has already done verifications
    '''
    user = AUTH.authenticate_user()
    friend_name = data.get('friend')
    friend = db.find_user_by(username=friend_name)

    message = f"{user.username} granted you access to track them"
    notif = redis_client.new_notification(user.id, friend.id, message,
                                          'general')
    if notif:
        emit('alert_user', room=friend.id)
    user_msg = f"You allowed {friend_name} to track you"
    user_notif = redis_client.new_notification(friend.id, user.id, user_msg,
                                               'general')
    if user_notif:
        emit('alert_user', room=user.id)


@socket_io.on('disallowed track')
def disallowed_track(data):
    ''' Notifies user when a track is disallowed by user '''
    user = AUTH.authenticate_user()
    friend_name = data.get('friend')
    friend = db.find_user_by(username=friend_name)

    message = f"You disallowed {friend_name} from tracking you"
    notif = redis_client.new_notification(friend.id, user.id, message,
                                          'general')
    if notif:
        emit('alert_user', room=user.id)


@socket_io.on('verify to delete')
def verify_then_delete(data):
    ''' Verifies if both friends have unfriend themselves
    then delete the conversation (containing all messages)
    '''
    user_id = AUTH.authenticate_user().id
    friend = data.get('friend')
    friend_id = db.find_user_by(username=friend).id

    status = AUTH.confirm_and_delete(user_id, friend_id)


@socket_io.on('send error message')
def send_error_notification(data):
    ''' Sends an error message to a user '''
    user_id = AUTH.authenticate_user().id
    message = data.get('message')
    emit('error', {'message': message}, room=user_id)


@socket_io.on('send success message')
def send_success_notification(data):
    ''' Sends a success message to a user '''
    user_id = AUTH.authenticate_user().id
    message = data.get('message')
    emit('success', {'message': message}, room=user_id)


@socket_io.on('reload profile')
def reload_profile(data):
    '''' reloads profile of a user/friend '''
    friend = data.get('friend')
    user_id = AUTH.authenticate_user().id
    if not friend:
        return
    friend = db.find_user_by(username=friend)
    if friend:
        emit('profile reload', room=friend.id)
        emit('profile reload', room=user_id)
