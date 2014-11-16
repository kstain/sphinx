from flask_cache import Cache

class SphinxCache(Cache):
    def init_app(self, app):
        super(SphinxCache, self).init_app(
            app=app,
            config={'CACHE_TYPE': app.config['CACHE_TYPE']}
        )