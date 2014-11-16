from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from markdown import markdown
import bleach
from flask_sqlalchemy import SQLAlchemy
import db

db = SQLAlchemy()

class Follow(db.Model):
    __tablename__ = 'follow'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followee_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    __tablename__ = 'users'
    
    MAX_USERNAME        = 50
    MAX_EMAIL           = 80
    MAX_PASSWORD        = 128
    MAX_PORTRAIT_PATH   = 150
    
    ROLE_ADMIN  = 'admin'
    ROLE_NORMAL = 'normal'
    
    id              = db.Column(db.Integer, primary_key=True)
    username        = db.Column(db.String(MAX_USERNAME), unique=True)
    email           = db.Column(db.String(MAX_EMAIL), unique=True)
    password_hash   = db.Column(db.String(MAX_PASSWORD))
    role            = db.Column(db.Enum(ROLE_ADMIN, ROLE_NORMAL), default=ROLE_NORMAL)
    banned          = db.Column(db.Boolean, default=False)
    confirmed       = db.Column(db.Boolean, default=False)
    portrait_path   = db.Column(db.String(MAX_PORTRAIT_PATH))
    
    videos          = db.relationship('Video', backref='poster', lazy='dynamic')
    comments        = db.relationship('Comment', backref='replier', lazy='dynamic')
    followees = db.relationship('Follow',
                                foreign_keys=[Follow.follower_id],
                                backref=db.backref('follower', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followee_id],
                                backref=db.backref('followee', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
        
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username



class Video(db.Model):
    __tablename__ = 'videos'
    
    MAX_TITLE   = 100
    
    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(MAX_TITLE))
    desc            = db.Column(db.Text)
    play_count      = db.Column(db.Integer, default=0)
    merit           = db.Column(db.Integer, default=0)
    demerit         = db.Column(db.Integer, default=0)
    upload_time     = db.Column(db.DateTime)
    
    poster_id       = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    comments        = db.relationship('Comment', backref='video', lazy='dynamic')
        
    def __repr__(self):
        return '<Video %r>' % self.title
    
    
    
class Comment(db.Model):
    __tablename__ = 'comments'
    
    id              = db.Column(db.Integer, primary_key=True)
    repliee_id      = db.Column(db.Integer, index=True)
    time            = db.Column(db.DateTime)
    content         = db.Column(db.Text)
    
    replier_id      = db.Column(db.Integer, db.ForeignKey('users.id'))
    video_id        = db.Column(db.Integer, db.ForeignKey('videos.id'))
    
    def __repr__(self):
        return '<Comment %r>' % self.content