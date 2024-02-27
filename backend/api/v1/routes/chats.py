#!/usr/bin/env python3
''' Handle user-friend conversations '''
from flask import jsonify, request, render_template
from backend.api.v1.routes import api
from backend.auth import AUTH
from backend.db_ops.user_choices import Choice
from backend.db_ops import db

CHOICE = Choice()


@api.route('/friend/conversation', methods=['POST'])
def get_conversations() -> str:
    ''' POST /friend/
    creates a new conversation for user and friend if none exists
    Return:
        All messages in the conversation involving user and friend
    '''
    user = AUTH.authenticate_user()
    user_id = user.id
    friend = request.get_json().get('friend')
    friend_id = db.find_user_by(username=friend).id
    if friend_id:
        if not AUTH.conversation_exists(user_id, friend_id):
            conv_id = CHOICE.create_conversation(user_id, friend_id)
        else:
            conv_id = db.find_conversation_by(
                participants=[user_id, friend_id]).id
        messages = db.get_messages(conv_id)
        messages['conversation_id'] = conv_id
        return jsonify(messages)
    else:
        return jsonify({"error": "Friend ID is required"}), 400


@api.route('/friend/conversation/read', methods=['POST'])
def mark_as_read() -> str:
    ''' POST api/user/friend/conversation/read
    Marks read messages as read
    '''
    user = AUTH.authenticate_user()
    user_id = user.id
    conversation_id = request.get_json().get('conversation_id')
    msg_id_list = request.get_json().get('messages')
    if conversation_id and msg_id_list:
        for msg_id in msg_id_list:
            db.update_message(conversation_id, msg_id, read=True)
        return jsonify({"success": "messages updated"})
    return jsonify({"error": "Invalid credentials"}), 400


@api.route('/isInChat/update', methods=['POST'])
def update_user_is_in_chat() -> str:
    ''' POST /api/user/isInChat/update
    Updates is_in_chat property of a conversation between a user and friend
    '''
    user = AUTH.authenticate_user()
    user_id = user.id
    friend = request.get_json().get('friend')
    status = request.get_json().get('status')

    if friend:
        friend_id = db.find_user_by(username=friend).id

        # validate friend id and prevent storage when they're not friends
        if friend_id and AUTH.is_a_valid_friend(user.id, friend_id)\
                and AUTH.is_a_valid_friend(friend_id, user_id):
            participants = [user_id, friend_id]
            conversation = db.find_conversation_by(participants=participants)
            if not conversation:
                conversation = db.new_conversation(user_id, friend_id)
            is_in_chat = conversation.is_in_chat
            data = {
                user.username: status,
                friend: is_in_chat.get(friend)
            }
            conv_id = conversation.id
            db.update_conversation(conv_id, is_in_chat=data)
            return jsonify({"update": "success"})
    # sets all is_in_chat property of user to false if no friend
    db.unmark_user_is_in_chats(user_id)
    return jsonify({"update": "All set to false"})


@api.route('/isInChat', methods=['POST'])
def user_is_in_chat() -> str:
    ''' POST api/user/isInChat
    '''
    friend = request.get_json().get('friend')
    user_id = AUTH.authenticate_user().id
    friend_id = db.find_user_by(username=friend).id
    if friend_id:
        status = CHOICE.user_currently_in_chat(user_id, friend_id)
        return jsonify({"status": status})
    return jsonify({"error": "Invalid credentials"}), 400
