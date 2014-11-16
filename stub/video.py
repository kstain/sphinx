from flask import Blueprint
from flask import render_template
from data.models import Video, User

site = Blueprint('video', 'stub.video')

@site.route('/play', methods=['GET'])
def play_video():
    v = Video('Week12','1','Week12',14)
    return render_template('_videoplayer.html',video = v)

@site.route('/uservideos', methods=['GET'])
def list_uservideos():
    usr = User(id=0, username='XMing')
    list = [Video('Week12','1','Week12',14)]
    return render_template('_uservideos.html',VideoList = list)