import base64
import json
import logging
from functools import wraps
from urllib.parse import urlencode

import requests
from flask import request, session, redirect
from werkzeug.exceptions import Forbidden


class OpenIDConnectClients(object):

    def __init__(self):
        self.open_id_providers = {}

    def init_app(self, app, open_id_provider_config):
        with open(open_id_provider_config, "r") as f:
            self.open_id_providers = json.loads(f.read())
            app.route("/oidc_callback")(self._oidc_callback)

    @staticmethod
    def _encode_state(provider_name, original_url):
        state = {"provider": provider_name, "url": original_url}
        return str(base64.urlsafe_b64encode(json.dumps(state).encode("utf-8")), "utf-8")

    @staticmethod
    def _decode_state(state):
        return json.loads(str(base64.b64decode(state), "utf-8"))

    def _get_authorization_url(self, provider_name, original_url):
        provider = self.open_id_providers[provider_name]
        args = {
            "client_id": provider["client_id"],
            "response_type": "code",
            "scope": "openid",
            "redirect_uri": self.open_id_providers["redirect_uri"],
            "state": self._encode_state(provider_name, original_url)
        }
        return self.open_id_providers["authorization_endpoint"] + "?" + urlencode(args)

    def require_guest_login(self, view_func):
        return self._do_require_login(view_func, "guest")

    def require_conext_login(self, view_func):
        return self._do_require_login(view_func, "conext")

    def _do_require_login(self, view_func, provider_name):
        @wraps(view_func)
        def decorated(*args, **kwargs):
            if provider_name not in session:
                auth_url = self._get_authorization_url(provider_name, request.url)
                return redirect(auth_url)
            return view_func(*args, **kwargs)

        return decorated

    def _oidc_callback(self):
        code = request.args["code"]
        state = self._decode_state(request.args["state"])
        original_url = state["url"]
        provider_name = state["provider"]
        conf = self.open_id_providers[provider_name]
        post_data = {"client_id": conf["client_id"],
                     "code": code,
                     "scope": "openid",
                     "client_secret": conf["client_secret"],
                     "redirect_uri": self.open_id_providers["redirect_uri"],
                     "grant_type": "authorization_code"}
        res = requests.post(self.open_id_providers["token_endpoint"], post_data).json()
        if "access_token" not in res:
            logger = logging.getLogger("main")
            logger.error(f"Error response: {str(res)} after post")
            raise Forbidden(description=str(res))

        post_data = {"access_token": res["access_token"]}
        user_info = requests.post(self.open_id_providers["userinfo_endpoint"], post_data).json()
        session[provider_name] = user_info
        return redirect(original_url)


oidc = OpenIDConnectClients()


def configure_oidc(app, conf):
    oidc.init_app(app, conf)
