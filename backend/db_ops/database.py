#!/usr/bin/env python3
''' DB class module
'''
from pymongo import MongoClient
from bson import InvalidDocument
from pymongo.errors import OperationFailure
from backend.models.users import User
from backend.models.conversations import Conversation
from backend.models.messages import Message
from typing import Union, TypeVar, List, Dict

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
        self._client = MongoClient('mongodb://127.0.0.1:27017')
        self._users = self._client.test_db.users
        self._conversations = self._client.test_db.conversations

    def add_user(self, **kwargs) -> User:
        ''' Creates and stores a new user to the databae
        Return:
            The newly created User
        '''
        user = User(**kwargs)
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
        deleted_user_id = self._users.delete_one({'id': user_id})
        if deleted_user_id is None:
            return False
        return True

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
        self._conversations.update_many(
            {'participants': {'$in': [user_id]}},
            {'$set': {'is_in_chat.' + user.username: False}}
        )
        return True
