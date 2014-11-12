class Video:
    def __init__(self,title,uid,vid,cnt):
        self.title = title
        self.userid = uid
        self.videoid = vid
        self.playcount = cnt
        
class User:
    def __init__(self,name):
        self.name = name