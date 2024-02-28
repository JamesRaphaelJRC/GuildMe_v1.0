#!/usr/bin/env python3
''' User Model '''
from typing import List, Union
import hashlib
from flask_login import UserMixin
from backend.models.base_model import BaseModel
from backend.models.helpers import is_sha256_hashed_password, is_valid_location


class User(BaseModel, UserMixin):
    ''' Defines the User class '''
    def __init__(self, **kwargs):
        ''' Instantiates a new User object '''
        super().__init__(**kwargs)
        self.full_name = kwargs.get('full_name')
        self.email = kwargs.get('email').lower()
        self.username = kwargs.get('username')
        self._password = self.set_password(kwargs.get('_password'))
        self.reset_token = kwargs.get('reset_token', None)

        # set the default avatar when a new user is created
        self.avatar = kwargs.get('avatar', 'images/icons8-avatar-96.png')
        self.friends = kwargs.get('friends', {})
        self.allowed_tracks = kwargs.get('allowed_tracks', {})
        self.tracking_me = kwargs.get('tracking_me', {})
        self.location = self.set_location(kwargs.get('location'))
        self.session_id = kwargs.get('session_id', None)

    def set_password(self, pwd: str):
        """ Setter of a new password: encrypt in SHA256
        """
        if pwd is None or type(pwd) is not str:
            raise ValueError('Password cannot be None and must be a string')

        # Checks if password is already a hashed password
        # Useful during object reinstantiation from json format
        if is_sha256_hashed_password(pwd):
            password = pwd
        else:
            password = hashlib.sha256(pwd.encode()).hexdigest().lower()
        return password

    def is_valid_password(self, pwd: str) -> bool:
        ''' Validates the hashed password '''
        if pwd is None or type(pwd) is not str:
            return False

        if self._password is None:
            return False

        pwd_enc = pwd.encode()
        return hashlib.sha256(pwd_enc).hexdigest().lower() == self._password

    def update_password(self, new_pwd: str) -> None:
        ''' Updates a User instance password '''
        if new_pwd is None or type(new_pwd) is not str:
            raise ValueError('Password cannot be None and must be a string')
        self._password = self.set_password(new_pwd)

    def set_location(self, coordinates: List[Union[int, float]]) -> dict:
        ''' Sets a user location '''
        if is_valid_location(coordinates):
            location = coordinates
        elif coordinates is None or len(coordinates) != 2:
            location = {}
        elif not all(isinstance(x, (int, float)) for x in coordinates):
            location = {}
        else:
            lat, long = coordinates
            location = {
                "type": "Point",
                "coordinates": [lat, long]
            }
        return location
