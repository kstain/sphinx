from flask import Blueprint
from flask import render_template
from sphinx.models.stub_models import Video,User

site = Blueprint('video_site_stub', 'sphinx.www.video_stub')

@site.route('/play', methods=['GET'])
def play_video():
    v = Video('Week12','1','Week12',14)
    return render_template('_videoplayer.html',video = v)
    
    
    
@site.route('/uservideos', methods=['GET'])
def list_uservideos():
    usr = User('XMing')
    list = [Video('Week12','1','Week12',14)]
    return render_template('_uservideos.html',VideoList = list)