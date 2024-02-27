#!/usr/bin/env python3
from flask import Blueprint

api = Blueprint('api', __name__, url_prefix='/api/user/')

from backend.api.v1.routes.user import *
from backend.api.v1.routes.friends import *
from backend.api.v1.routes.chats import *
