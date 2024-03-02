#!/usr/bin/env python3
''' Authentication module '''
from flask import request, abort
from flask_login import current_user
from typing import TypeVar, Union
from backend.db_ops.database import DB

OBJECT_TYPES = Union[TypeVar('User'), TypeVar('Conversation')]


class Auth:
    ''' Authentication class '''
    def __init__(self) -> None:
        self._db = DB()

    def authenticate_user(self):
        ''' Authenticates a user using the session_id stored in the set-cookie
        '''
        if current_user.is_authenticated:
            user = self._db.find_user_by(id=current_user.get_id())

        else:
            session_id = request.cookies.get('session_id')
            if not session_id:
                abort(401)

            user = self._db.find_user_by(session_id=session_id)
            if not user:
                abort(401)

        return user

    def set_session_id(self, user_id: str) -> str:
        ''' Creates a session_id for a user and updates it on the user object
        '''
        from uuid import uuid4
        session_id = str(uuid4())
        self._db.update_user(user_id, session_id=session_id)
        return session_id

    def remove_session_id(self, user_id: str) -> bool:
        ''' Sets a user's session_id property to None '''
        user = self._db.update_user(user_id, session_id=None)
        if user:
            return True
        return False

    def user_exists(self, username_or_email: str) -> bool:
        ''' Validates if a user with same username or email already exists '''
        user = self._db.find_user_by(username=username_or_email)
        if user:
            return True
        user = self._db.find_user_by(email=username_or_email)
        if user:
            return True
        return False

    def register_user(self, full_name: str, email: str, username: str,
                      password: str) -> str:
        ''' Registers a new user by saving the user to the database
        Return:
            user id on success
        '''
        user = self._db.add_user(full_name=full_name, email=email,
                                 username=username, _password=password)
        return user.id

    def is_valid_login(self, email: str, password: str) -> bool:
        ''' Authenticates user's login credentials '''
        user = self._db.find_user_by(email=email)
        if not user:
            return False
        if not user.is_valid_password(password):
            return False
        return True

    def get_password_reset_token(self, email: str) -> str:
        ''' Sets and returns a reset x_token to a valid user '''
        user = self._db.find_user_by(email=email)
        if not user:
            raise ValueError(f'Invalid email {email}')

        from uuid import uuid4

        x_token = str(uuid4())[:8]
        self._db.update_user(user.id, reset_token=x_token)
        return x_token

    def update_password(self, reset_token: str, new_password: str) -> bool:
        ''' Resets password of a valid user using a valid reset x_token '''
        user = self._db.find_user_by(reset_token=reset_token)
        if not user:
            return False
        self._db.update_user(user.id, _password=new_password, reset_token=None)
        return True

    def is_valid_user_and_friend(self, user_id: str, friend_id: str):
        ''' Checks if user and friend exist in the database
        Return:
            A list of User object and User object(friend) on success
        '''
        user = self._db.find_user_by(id=user_id)
        if not user:
            raise ValueError(f'Invalid User {user_id}')

        friend = self._db.find_user_by(id=friend_id)
        if not friend:
            raise ValueError(f'Not a valid friend {friend_id}')
        return [user, friend]

    def is_a_valid_friend(self, user_id: str, friend_id: str) -> bool:
        ''' Verifies if friend is in a user's friends dictionary '''
        user = self._db.find_user_by(id=user_id)
        if not user:
            return False

        user_friends = user.friends
        if friend_id in user_friends:
            return True
        return False

    def get_obj(self, cls: str, id: str) -> Union[OBJECT_TYPES | None]:
        ''' Retrieves an object by class name and unique id '''
        if cls == 'User':
            user = self._db.find_user_by(id=id)
            if not user:
                user = self._db.find_user_by(email=id)
            return user
        if cls == 'Conversation':
            return self._db.find_conversation_by(id=id)

    def conversation_exists(self, user_id: str, friend_id: str) -> bool:
        ''' Validates if conversation between a user and friend already
        exists
        Return:
            True if it already exists
            False otherwise
        '''
        if self._db.find_conversation_by(participants=[user_id, friend_id]):
            return True
        return False

    def has_unread_messages(self, user_id: str, friend_id: str) -> bool:
        ''' Verifies if user has an unread message in conversation
        with friend
        Return:
            True if there is/are unread message(s) where user is the receiver
            False otherwise
        '''
        participants = [user_id, friend_id]
        conversation = self._db.find_conversation_by(participants=participants)
        if not conversation:
            return False
        user_name = self._db.find_user_by(id=user_id).username
        messages = conversation.messages
        if not messages:
            return False
        for message in messages.values():
            if message.get('read') == False and\
                    message.get('receiver') == user_name:
                return True
        return False
    
    def is_valid_email(self, email: str) -> bool:
        ''' Validates an email address
        Return:
            True is email is an email pattern
            False otherwise
        '''
        if email is None or not isinstance(email, str):
            return False

        import re
        email_regex = re.compile(r"[^@]+@[^@]+\.[^@]+")
        if email_regex.match(email):
            return True
        return False

    def confirm_and_delete(self, user_id: str, friend_id: str) -> bool:
        ''' Verifies if user and friend have removed each other as friends
        then deletes the associated conversation
        '''
        if not self.is_a_valid_friend(user_id, friend_id) and\
                not self.is_a_valid_friend(friend_id, user_id):
            participants = [user_id, friend_id]

            conv_id = self._db.find_conversation_by(
                participants=participants).id

            status = self._db.remove_conversation(conv_id)
            return status
        return False
