#!/usr/bin/env python3
''' User preference/choices '''
from typing import Union, List
from backend.db_ops.database import DB
from backend.auth import AUTH


class Choice:
    ''' Sets various permissions to the database based on user choices '''
    def __init__(self) -> None:
        self._db = DB()

    def set_location(self, user_id: str,
                     location: List[Union[int, float]]) -> bool:
        ''' Sets a user location '''
        user = self._db.find_user_by(id=user_id)
        if not user:
            return False
        self._db.update_user(user_id, location=location)
        return True

    def remove_location(self, user_id: str) -> bool:
        ''' Removes a user location '''
        user = self._db.find_user_by(id=user_id)
        if not user:
            return False
        self._db.update_user(user.id, location=None)
        return True

    def add_friend(self, user_id: str, friend_id: str) -> bool:
        ''' Adds a new friend to a user and friend friends dictionary
        Raise:
            ValueError when user or friend does not exist
        '''
        user, friend = AUTH.is_valid_user_and_friend(user_id, friend_id)
        # Get and update friends dictionary of the user
        user_friend_dict = user.friends
        new_friend = {
            'id': friend_id,
            'username': friend.username,
            'last_seen': None,
            'avatar': friend.avatar
            }
        user_friend_dict[friend_id] = new_friend
        self._db.update_user(user_id, friends=user_friend_dict)

        # add user to friend's friend_dict too
        friend_friends_dict = friend.friends
        user_data = {
            'id': user_id,
            'username': user.username,
            'last_seen': None,
            'avatar': user.avatar
            }
        friend_friends_dict[user_id] = user_data
        self._db.update_user(friend_id, friends=friend_friends_dict)
        return True

    def remove_friend(self, user_id: str, friend_id: str) -> bool:
        ''' Removes a friend from a user's friend dictionary
        Raise:
            ValueError when user or friend does not exist
        '''
        user = AUTH.is_valid_user_and_friend(user_id, friend_id)[0]

        friend_dict = user.friends
        if friend_id in friend_dict:
            del friend_dict[friend_id]
        else:
            return False
        self._db.update_user(user_id, friends=friend_dict)
        return True

    def allow_track_access(self, user_id: str, friend_id: str) -> bool:
        ''' Adds a user's id and location to a dictionary of allowed tracks
            of a valid friend, enabling friend to track the user.
            allowed_tracks is a dict of friends a user is allowed to track
        Raise:
            ValueError if user or friend does not exists
        '''
        if not AUTH.is_a_valid_friend(user_id, friend_id):
            return False

        user, friend = AUTH.is_valid_user_and_friend(user_id, friend_id)
        friend_allowed_tracks = friend.allowed_tracks
        if user_id in friend_allowed_tracks:
            return True
        friend_allowed_tracks.update({user_id: user.location})
        self._db.update_user(friend_id, allowed_tracks=friend_allowed_tracks)
        return True

    def remove_track_access(self, user_id: str, friend_id: str) -> bool:
        ''' Removes track access by removing user from friend allowed_tracks
        disabling friend from tracking the user
        '''
        if not AUTH.is_a_valid_friend(user_id, friend_id):
            return False

        user, friend = AUTH.is_valid_user_and_friend(user_id, friend_id)
        friend_allowed_tracks = friend.allowed_tracks
        if user.id not in friend_allowed_tracks:
            return False
        del friend_allowed_tracks[user_id]
        self._db.update_user(friend_id, allowed_tracks=friend_allowed_tracks)
        return True

    def create_conversation(self, user_id: str, friend_id: str) -> str:
        ''' Creates a new conversation
        Return:
            The conversation id on success
            None otherwise
        '''
        return self._db.new_conversation(user_id, friend_id).id

    def user_currently_in_chat(self, user_id: str, friend_id: str) -> bool:
        ''' Verifies if a user is currently in the chatbox of chat with
        friend in the Conversation object in the database
        Return:
            True if user is in the chat space
            False otherwise
        '''
        users_name = self._db.find_user_by(id=user_id).username
        participants = [user_id, friend_id]
        conversation = self._db.find_conversation_by(participants=participants)
        is_in_chat = conversation.is_in_chat
        if is_in_chat.get(users_name) is True:
            return True
        return False

    def get_friend_location(self, user_id: str, friend_name: str)\
            -> Union[List[float], bool, None]:
        ''' Returns a friend location if friend is in the user's allowed_tracks
        the allowed_tracks is a dict of users who granted a given user access
        know their location
        Return:
            friend's current location on success,
            None if friend is not in user's allowed track or does not exist.
            False if friend's coordinates is empty (i.e. friend might have
            disallowed his location)
        '''
        user = self._db.find_user_by(id=user_id)
        friend = self._db.find_user_by(username=friend_name)
        friend_id = friend.id
        if friend_id:
            user_allowed_tracks = user.allowed_tracks
            if friend_id in user_allowed_tracks:
                friend_location = friend.location.get('coordinates')

                if friend_location:
                    return friend_location
                return False
        return None
