from flask import render_template
from flask import Blueprint

site = Blueprint('test_site', 'sphinx.www.test')

@site.route('/hello/<uid>', methods=['GET'])
def hello(uid):
    return "Hello %s" % uid

@site.route('/ping', methods=['GET'])
def ping():
    return 'pong'

@site.route('/video_play', methods=['GET'])
def video_test():
    return render_template('test/video-play.htmlx', user_id='1', video_name='Week12.webm')

@site.route('/video_upload', methods=['GET'])
def video_upload():
    return render_template('test/video-upload.htmlx')