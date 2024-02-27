#!/usr/bin/env python3
''' Conversations Model '''
from backend.models.base_model import BaseModel
from backend.models.messages import Message


class Conversation(BaseModel):
    ''' Defines the Conversations class '''
    def __init__(self, **kwargs):
        ''' Instantiates a new Conversations instance '''
        super().__init__(**kwargs)
        self.participants = kwargs.get('participants')
        self.messages = kwargs.get('messages', {})
        self.is_in_chat = kwargs.get('is_in_chat', {})
