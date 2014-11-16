from flask import Flask

def create_app(name, conf):
    app = Flask(__name__, template_folder='../templates')
    app.config.from_object(conf)
    conf.init_app(app)
    return app
