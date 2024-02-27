#!/usr/bin/env python3
''' Message Model '''
from backend.models.base_model import BaseModel


class Message(BaseModel):
    ''' Defines the Message class '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sender = kwargs.get('sender', None)
        self.receiver = kwargs.get('receiver', None)
        self.content = kwargs.get('content', None)
        self.content_type = kwargs.get('content_type', 'Text')
        self.read = kwargs.get('read', False)

    def mark_as_read(self) -> None:
        ''' Sets read attribute to True '''
        self.read = True
