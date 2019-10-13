import json
from functools import wraps
from urllib.parse import urlencode

import requests
from flask import request, session, redirect, url_for, Blueprint
from munch import munchify
from requests.auth import HTTPBasicAuth


class OpenIDConnectClient(object):

    def __init__(self):
        self.open_id_provider = {}

    def init_app(self, app, open_id_provider_config):
        self.open_id_provider = munchify(json.loads(open(open_id_provider_config, "r").read()))
        app.route("/" + self.open_id_provider.redirect_uri)(self._oidc_callback)

    def _get_authorization_url(self, original_url):
        args = {
            "client_id": self.open_id_provider.client_id,
            "response_type": "code",
            "scope": "openid",
            "redirect_uri": url_for("_oidc_callback", _external=True),
            "state": original_url
        }
        return self.open_id_provider.authorization_endpoint + "?" + urlencode(args)

    def require_login(self, view_func):
        @wraps(view_func)
        def decorated(*args, **kwargs):
            if self.open_id_provider.user_session not in session:
                auth_url = self._get_authorization_url(request.url)
                return redirect(auth_url)
            return view_func(*args, **kwargs)

        return decorated

    def _oidc_callback(self):
        code = request.args["code"]
        conf = self.open_id_provider
        post_data = {"client_id": conf.client_id,
                     "code": code,
                     "scope": "openid",
                     "client_secret": conf.client_secret,
                     "redirect_uri": url_for("_oidc_callback", _external=True),
                     "grant_type": "authorization_code"}
        res = requests.post(conf.token_endpoint, post_data).json()
        post_data = {"access_token": res["access_token"]}
        res = requests.post(conf.userinfo_endpoint, post_data)
        print(res)


oidc = OpenIDConnectClient()
oidc_guest = OpenIDConnectClient()


def configure_oidc(app, conf):
    oidc.init_app(app, conf)


def configure_oidc_guest(app, conf):
    oidc_guest.init_app(app, conf)
