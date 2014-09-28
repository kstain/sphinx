from sphinx.www.base import *
app = SphinxApp(__name__)

from sphinx.www.user import user_site
app.register_blueprint(user_site, url_prefix='/user')

@app.route('/ping')
def ping():
    return 'pong'

app.debug = True
from werkzeug.debug import DebuggedApplication
debug_app = DebuggedApplication(app, evalex=True)
