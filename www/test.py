from sphinx.www.base import *
from flask import render_template
from flask import Blueprint

test_site = Blueprint('test', 'sphinx.www.test')

@test_site.route('/hello/<uid>', methods=['GET'])
def hello(uid):
    return "Hello %s" % uid

@test_site.route('/ping', methods=['GET'])
def ping():
    return 'pong'

@test_site.route('/video_play', methods=['GET'])
def video_test():
    return render_template('test/video-play.htmlx', user_id='1', video_name='Week12.webm')

@test_site.route('/video_upload', methods=['GET'])
def video_upload():
    return render_template('test/video-upload.htmlx')