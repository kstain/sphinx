from werkzeug.debug import DebuggedApplication

from sphinx.www.base import *
from sphinx.www.home import home_site
from sphinx.www.home_stub import home_site as home_stub
from sphinx.www.user import user_site
from sphinx.www.user_stub import user_site as user_stub
from sphinx.www.test import test_site

app = SphinxApp(__name__)
app.register_blueprint(home_site)
app.register_blueprint(home_stub, url_prefix='/stub')
app.register_blueprint(user_site, url_prefix='/user')
app.register_blueprint(user_stub, url_prefix='/stub/user')
app.register_blueprint(test_site, url_prefix='/test')

app.debug = True
debug_app = DebuggedApplication(app, evalex=True)
