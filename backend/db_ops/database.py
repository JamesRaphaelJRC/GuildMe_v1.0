#!/usr/bin/env python3
''' DB class module
'''
from typing import Union, TypeVar, List, Dict
import os
import re
from pymongo import MongoClient
from bson import InvalidDocument
from pymongo.errors import OperationFailure, WriteError
from backend.models.users import User
from backend.models.conversations import Conversation
from backend.models.messages import Message


OBJECT_TYPES = Union[TypeVar('User'), TypeVar('Conversation')]
CLASSES = ['User', 'Conversation']


def is_str_and_not_None(variables: List) -> bool:
    ''' Verifies if variables are None or not a string
    Return:
        True if list of variables are all not None and of type string
        False otherwise
    '''
    return all(var is not None and isinstance(var, str) for var in variables)


class DB:
    '''' Handles database operations
    '''
    def __init__(self) -> None:
        ''' Initialize new DB instance '''
        # uri = "mongodb+srv://jamesraphaeljrc:1HQBZCmknGU29f6i@guildme.vul6smp.mongodb.net/?retryWrites=true&w=majority&appName=guildme"
        uri = os.environ.get('MONGO_URI', 'mongodb://127.0.0.1:27017')
        # self._client = MongoClient('mongodb://127.0.0.1:27017')
        self._client = MongoClient(uri)
        self._users = self._client.test_db.users
        self._conversations = self._client.test_db.conversations

    def add_user(self, **kwargs) -> User:
        ''' Creates and stores a new user to the databae
        Return:
            The newly created User
        '''
        from backend.utils.utilities import Utils

        utils = Utils()

        user = User(**kwargs)

        original_path = 'frontend/static/images/icons8-avatar-96.png'
        new_path = f'frontend/static/uploads/avatars/{user.id}.png'
        if utils.copy_and_rename_file(original_path, new_path):
            user.avatar = f'uploads/avatars/{user.id}.png'

        self._users.insert_one(user.to_dict())
        return user

    def find_user_by(self, **kwargs) -> Union[User, None]:
        ''' Finds and returns a user by a given key:value pair
        Return:
            A User on success and None otherwise
        '''
        if not kwargs:
            return None
        user_data = self._users.find_one(kwargs)

        if user_data is None:
            return None

        user = User(**user_data)
        return user

    def update_user(self, user_id: str, **kwargs) -> Union[User, None]:
        ''' Updates an already existing user
        Return:
            The updated User on sucess and None otherwise
        '''
        if not is_str_and_not_None([user_id]):
            return None
        user = self.find_user_by(id=user_id)

        if user is None:
            return None

        update = True

        for key, value in kwargs.items():
            if hasattr(user, key):
                old_value = getattr(user, key)
                if old_value == value:
                    update = False
                    break
                setattr(user, key, value)
                user.reset_updated_at_attr()
                update = True

            else:
                raise ValueError('Incorrect attribute', key)
        if update is True:
            user_dict = user.to_dict()
            # Reinstantiates a user and implement pwd hash when pwd is updated
            user = User(**user_dict)
            self._users.update_one({'id': user_id}, {"$set": user.to_dict()})
        return user

    def remove_user(self, user_id: str) -> bool:
        ''' Deletes a user from the users database collection '''
        if not is_str_and_not_None([user_id]):
            return False

        user = self.find_user_by(id=user_id)

        # Check if the user exists
        if not user:
            return False

        try:
            # Delete the user from the database
            deleted_user_id = self._users.delete_one({'id': user_id})

            if deleted_user_id.deleted_count == 0:
                return False

            # Delete the avatar file
            avatar_path = f'frontend/static/{user.avatar}'
            os.remove(avatar_path)
            return True
        except FileNotFoundError:
            print(f"Error: Avatar file not found at {avatar_path}")
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False

    def new_conversation(self, user1_id: str, user2_id: str)\
            -> Union[Conversation, None]:
        ''' Creates and saves a new conversation
        Return:
            New conversation object on success and None otherwise
        '''
        if not is_str_and_not_None([user1_id, user2_id]):
            return None
        participants = [user1_id, user2_id]
        user1_name = self.find_user_by(id=user1_id).username
        user2_name = self.find_user_by(id=user2_id).username
        is_in_chat = {
            user1_name: False,
            user2_name: False,
        }
        conversation = Conversation(
            participants=participants, is_in_chat=is_in_chat)

        self._conversations.insert_one(conversation.to_dict())
        return conversation

    def update_conversation(self, conversation_id: str, **kwargs)\
            -> Union[Conversation, None]:
        ''' Updates an already existing user
        Return:
            The updated User on sucess and None otherwise
        '''
        if not is_str_and_not_None([conversation_id]):
            return None
        conversation = self.find_conversation_by(id=conversation_id)
        if conversation is None:
            return None

        update = True

        for key, value in kwargs.items():
            if hasattr(conversation, key):
                old_value = getattr(conversation, key)
                if old_value == value:
                    update = False
                    break
                setattr(conversation, key, value)
                conversation.reset_updated_at_attr()
                update = True

            else:
                raise ValueError('Incorrect attribute', key)
        if update is True:
            conversation_dict = conversation.to_dict()

            self._conversations.update_one(
                {'id': conversation.id}, {"$set": conversation_dict})
        return conversation

    def find_conversation_by(self, **kwargs) -> Union[Conversation, None]:
        ''' Retrieves a conversation instance by a key/vaalue pair
        Return: A conversation object on success and None otherwise
        '''
        try:
            # Checks if user is searching for participants in conversation
            if kwargs.get('participants'):
                participants = kwargs.get('participants')

                # Search irrespective of sequence user id arrangement
                obj_data = self._conversations.find_one({
                    'participants': {
                        '$all': participants,
                        }
                    })
            else:
                obj_data = self._conversations.find_one(kwargs)

            if obj_data is None:
                obj = None
            else:
                obj = Conversation(**obj_data)
        except InvalidDocument or OperationFailure:
            obj = None
        return obj

    def remove_conversation(self, conversation_id: str) -> bool:
        ''' Deletes a conversation from the conversations collection
        Return:
            True on success, False otherwise
        '''
        if not is_str_and_not_None([conversation_id]):
            return False
        deleted_user_id = self._conversations.delete_one(
                                {'id': conversation_id})
        if deleted_user_id is None:
            return False
        return True

    def new_message(self, sender: str, receiver: str, content: str,
                    content_type: str = 'Text') -> Union[str, None]:
        ''' Creates a new message in a given conversation and updates the
        conversation
        sender and receiver are user ids
        Return:
            message id on success and None otherwise
        '''
        if not is_str_and_not_None([sender, receiver, content, content_type]):
            return None

        participants = [sender, receiver]
        conversation = self.find_conversation_by(participants=participants)

        if conversation is None:
            return None

        sender_name = self.find_user_by(id=sender).username
        receiver_name = self.find_user_by(id=receiver).username

        data = {
            'sender': sender_name,
            'receiver': receiver_name,
            'content': content,
            'content_type': content_type,
        }
        message = Message(**data)

        msg_dict = message.to_dict()
        conversation.messages[message.id] = msg_dict

        # Updates the conversation
        self._conversations.update_one({'id': conversation.id},
                                       {'$set': conversation.to_dict()})
        return message.id

    def get_messages(self, conversation_id: str) -> Union[Dict, None]:
        ''' Gets all message in a given conversation '''
        if not is_str_and_not_None([conversation_id]):
            return None

        conversation = self.find_conversation_by(id=conversation_id)
        if conversation is None:
            return None

        return conversation.messages

    def update_message(self, conversation_id: str, message_id: str, **kwargs)\
            -> Union[Message, None]:
        ''' Updates a message
        Return:
            The updated message
        '''
        if not is_str_and_not_None([conversation_id, message_id]):
            return None
        if message_id is None or not isinstance(message_id, str):
            return None

        conversation = self.find_conversation_by(id=conversation_id)
        if conversation is None:
            return None

        msg_dict = conversation.messages.get(message_id)
        if msg_dict is None:
            return None

        msg_obj = Message(**msg_dict)
        update = True

        for key, value in kwargs.items():
            if hasattr(msg_obj, key):
                old_value = getattr(msg_obj, key)
                if old_value == value:
                    update = False
                    break
                setattr(msg_obj, key, value)
                msg_obj.reset_updated_at_attr()
                update = True

            else:
                raise ValueError('Incorrect attribute', key)

        if update is True:
            msg_path = f'messages.{msg_obj.id}'
            self._conversations.update_one(
                {'id': conversation_id, msg_path: {'$exists': True}},
                {'$set': {msg_path: msg_obj.to_dict()}}
            )
        return msg_obj

    def remove_message(self, conversation_id: str, message_id: str) -> bool:
        ''' Deletes a message from the conversation collection
        Return:
            True on success, False otherwise
        '''
        if not is_str_and_not_None([conversation_id, message_id]):
            return False

        conversation = self.find_conversation_by(id=conversation_id)
        if conversation is None:
            return False

        msg_path = f'messages.{message_id}'
        result = self._conversations.update_one(
            {'id': conversation_id},
            {'$unset': {msg_path: 1}}
            )

        if result.modified_count > 0:
            return True
        else:
            return False

    def unmark_user_is_in_chats(self, user_id: str) -> bool:
        ''' Sets all is_in_chat for all conversations where user is a
        participant to false
        Return:
            True on success, False otherwise
        '''
        if not is_str_and_not_None([user_id]):
            return False

        user = self.find_user_by(id=user_id)
        if not user:
            return False

        username = user.username
        update_path = f'is_in_chat.{username}'

        try:
            self._conversations.update_many(
                {'participants': {'$in': [user_id]}},
                {'$set': {update_path: False}}
            )
            return True
        except WriteError:
            return False

    def update_related_documents(self, user_id: str) -> bool:
        ''' Updates all related documents with new user data
        It updates all user friends with the latest changes to user data
        '''
        if not is_str_and_not_None([user_id]):
            return False

        user = self.find_user_by(id=user_id)
        if not user:
            return False

        # update for friends
        friends = user.friends
        if not friends:
            return False
        friend_ids = [id for id in friends.keys()]

        updated = False
        for id in friend_ids:
            friend = self.find_user_by(id=id)
            # checks for allowed_tracks
            if user.id in friend.allowed_tracks:
                updated_user_data = {
                    'username': user.username,
                    'location': user.location,
                    'avatar': user.avatar
                }
                allowed_tracks = friend.allowed_tracks
                allowed_tracks[user.id] = updated_user_data
                self.update_user(friend.id, allowed_tracks=allowed_tracks)
                updated = True
            # checks for tracking_me
            if user.id in friend.tracking_me:
                trackers = friend.tracking_me
                updated_user_data = {
                    'username': user.username,
                    'avatar': user.avatar
                }
                trackers[user.id] = updated_user_data
                self.update_user(friend.id, tracking_me=trackers)
                updated = True
            # Does for friends
            friends_friends = friend.friends
            updated_user_data = {
                'id': user.id,
                'username': user.username,
                'last_seen': None,
                'avatar': user.avatar
            }
            friends_friends[user.id] = updated_user_data
            self.update_user(friend.id, friends=friends_friends)
            updated = True
        if updated is True:
            return True
        return False

    def search_users(self, user_id: str, query: str) -> Union[Dict | None]:
        ''' Search for friends that match the query string in a given user
        document
        Return:
            Dictionary of users that match the query string
            None otherwise
        '''
        if not is_str_and_not_None([user_id, query]):
            return None

        user = self.find_user_by(id=user_id)
        if not user:
            return None

        user_friends = user.friends
        s_query = query.lower()

        return {
            f_id: friend for f_id, friend in user_friends.items() if
            re.search(re.escape(s_query), friend.get('username', ''),
                      re.IGNORECASE)
            or re.search(re.escape(s_query), friend.get('email', ''),
                         re.IGNORECASE)
            }
