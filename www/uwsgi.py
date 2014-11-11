from werkzeug.debug import DebuggedApplication

from sphinx.www.base import SphinxApp
from sphinx.www.home import site as home_site
from sphinx.www.home_stub import site as home_site_stub
from sphinx.www.user import site as user_site
from sphinx.www.user_stub import site as user_site_stub
from sphinx.www.test import site as test_site
from sphinx.www.video import site as video_site
from sphinx.www.video_stub import site as video_site_stub

app = SphinxApp(__name__)
app.register_blueprint(home_site)
app.register_blueprint(home_site_stub, url_prefix='/stub')
app.register_blueprint(user_site, url_prefix='/user')
app.register_blueprint(user_site_stub, url_prefix='/stub/user')
app.register_blueprint(test_site, url_prefix='/test')
app.register_blueprint(video_site,url_prefix='/video')
app.register_blueprint(video_site_stub,url_prefix='/stub/video')

app.debug = True
debug_app = DebuggedApplication(app, evalex=True)
