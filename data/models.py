from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app

import db.models as backend
from db.models import db
from data.cache import SphinxCache

cache = SphinxCache()

class Video(object):
    def __init__(self, title, uid, vid, cnt):
        self.title = title
        self.userid = uid
        self.videoid = vid
        self.playcount = cnt

class User(UserMixin):
    def __init__(self, id, username, email, confirmed, **kwargs):
        super(User, self).__init__(**kwargs)
        self.id = id
        self.username = username
        self.email = email
        self.confirmed = confirmed
    
    @staticmethod
    def from_backend(_user):
        if (_user == None):
            return None
        else:
            return User(id=_user.id, 
                        username=_user.username,
                        email=_user.email,
                        confirmed=_user.confirmed)
    
    # TODO: cache
    def fetch_backend(self):
        return backend.User.query.filter_by(username=self.username).first()
    
    @staticmethod
    def from_id(id):
        return User.from_backend(backend.User.query.filter_by(id=id).first())   
        
    @staticmethod
    def from_email(email):
        return User.from_backend(backend.User.query.filter_by(email=email).first())
        
    @staticmethod
    def from_username(username):
        return User.from_backend(backend.User.query.filter_by(username=username).first())
        
    @staticmethod
    def create(email, username, password):
        _user = backend.User(email=email,
                             username=username,
                             password=password)
        db.session.add(_user)
        db.session.commit()
        return User.from_backend(_user)
       
    def change_password(self, password):
        self.password = password
        _user = User.fetch_backend(self)
        db.session.add(_user)
        db.session.commit()
        
    def verify_password(self, password):
        _user = User.fetch_backend(self)
        return _user.verify_password
        
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(User.fetch_backend(self))
        db.session.commit()
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(User.fetch_backend(self))
        db.session.commit()
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(User.fetch_backend(self))
        db.session.commit()
        return True

