from werkzeug.debug import DebuggedApplication

from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

from app import create_app
from app.conf import DevConfig
from app.conf import TestConfig
from app.conf import ProdConfig

from auth import login_manager
from db.models import db
from data.models import cache
from util.email import mail

app = create_app(__name__, DevConfig)

from www.test import site as test_site
from www.auth import site as auth_site
if (app.config['USE_STUB']):
    from stub.home import site as home_site
    from stub.user import site as user_site
    from stub.video import site as video_site
else:
    from www.home import site as home_site
    from www.user import site as user_site
    from www.video import site as video_site
    
app.register_blueprint(home_site)
app.register_blueprint(user_site, url_prefix='/user')
app.register_blueprint(video_site, url_prefix='/video')

app.register_blueprint(auth_site, url_prefix='/auth')
app.register_blueprint(test_site, url_prefix='/test')

bootstrap = Bootstrap(app)
mail.init_app(app)
moment = Moment(app)
db.init_app(app)
cache.init_app(app)
login_manager.init_app(app)

if (app.debug):
    debug_app = DebuggedApplication(app, evalex=True)
