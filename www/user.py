from sphinx.www.base import *
from flask import Blueprint

user_site = Blueprint('user', 'sphinx.www.user')

@user_site.route('/<uid>', methods=['GET'])
def show_user_profile(uid):
    return "Hello %s" % uid
