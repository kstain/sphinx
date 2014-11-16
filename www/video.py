from flask import Blueprint
from flask import render_template

site = Blueprint('video', 'www.video')

# @site.route('/play', methods=['GET'])
# def play_video(userid,videoid):
#     page_title='NyanNyan'
#     desc='Blablabla'
#     return render_template('_videoplayer.html',video_data = video)
# 
# @site.route('/uservideos', methods=['GET'])
# def list_uservideos(userid,sort='time'):
#     return render_template('_uservideos.html')