#!/usr/bin/env python3
''' Chat web socket functionality module '''
from flask import session, request
from flask_login import current_user
from flask_socketio import emit, join_room, send
from backend.api.v1.web_socket.notifications import socket_io
from backend.db_ops import db


@socket_io.on('join')
def on_join(data):
    ''' Checks if room exists in session if not creates new one '''
    room = data.get('room')
    friend = data.get('friend')
    user_sid = request.sid

    join_room(room, user_sid)
    messages_dict = db.get_messages(room)  # room is the conversation id
    # Broadcast prev chats to only user that joined the room
    emit('prevMessages', {"messages": messages_dict}, room=user_sid)


@socket_io.on('newMessage')
def new_message(data):
    ''' Handles new messages '''
    room = data.get('room')
    friend = data.get('friend')
    friend_id = db.find_user_by(username=friend).id
    message = data.get('message')
    user_id = current_user.get_id()
    username = db.find_user_by(id=user_id).username
    db.new_message(user_id, friend_id, message)
    emit("chat", {"message": message, "sender": username}, to=room)
