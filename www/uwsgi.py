from werkzeug.debug import DebuggedApplication

from sphinx.www.base import *
from sphinx.www.home import home_site
from sphinx.www.user import user_site

app = SphinxApp(__name__)
app.register_blueprint(home_site)
app.register_blueprint(user_site, url_prefix='/user')

app.debug = True
debug_app = DebuggedApplication(app, evalex=True)
