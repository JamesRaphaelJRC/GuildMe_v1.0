#!/usr/bin/env python3
''' Config class'''
import os

# Load .env file in development
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

class Config:
    MONGO_URI = os.getenv('MONGODB_URI') or 'mongodb://127.0.0.1:27017'
