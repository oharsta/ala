from flask_basicauth import BasicAuth

basic_auth = BasicAuth()


def configure_basic_auth(app):
    basic_auth.init_app(app)
