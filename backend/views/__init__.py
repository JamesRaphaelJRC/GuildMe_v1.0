#!/usr/bin/env python3
from flask import Blueprint


user_views = Blueprint('user_views',__name__, url_prefix='/user',
                       template_folder='../../frontend/templates',
                       static_folder='../../frontend/static')
pub_views = Blueprint('pub_views', __name__)

from backend.views.public_views import *
from backend.views.user import *
