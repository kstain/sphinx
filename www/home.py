from flask import Blueprint
from flask import render_template

from sphinx.www.base import *

home_site = Blueprint('home', 'sphinx.www.home')

@home_site.route('/ping', methods=['GET'])
def ping():
    return 'pong'

@home_site.route('/hello', methods=['GET'])
def hello():
    return 'world'

@home_site.route('/video_test')
def video_test():
     return render_template('video-test.htmlx', user_id='1', video_name='Week12.webm')
