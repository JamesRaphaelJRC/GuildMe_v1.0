#!/usr/bin/env python3
''' BaseModel '''
from uuid import uuid4
from datetime import datetime
from typing import TypeVar, Union


class BaseModel:
    ''' Defines the BaseModel class '''
    def __init__(self, **kwargs):
        ''' Instantiation of a new BaseModel object'''
        self.id = kwargs.get('id', str(uuid4()))
        if kwargs.get('created_at') is not None:
            self.created_at = kwargs.get('created_at')
        else:
            self.created_at = datetime.now().strftime('%Y-%m-%d %H:%M')
        if kwargs.get('updated_at') is not None:
            self.updated_at = kwargs.get('updated_at')
        else:
            self.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M')

    def __str__(self):
        ''' Returns a string representation of BaseModel instance'''
        class_name = type(self).__name__
        return "[{}] ({}) {}".format(class_name, self.id, self.__dict__)

    def to_dict(self):
        ''' Converts an object to a dictionary '''
        dictionary = self.__dict__.copy()
        if '_sa_instance_state' in dictionary.keys():
            del dictionary['_sa_instance_state']
        return dictionary

    def reset_updated_at_attr(self) -> None:
        ''' Sets the updated_at property to the current time of
        update
        '''
        self.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M')
