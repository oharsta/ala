import logging
import os
from functools import wraps

from flask import Blueprint, jsonify, current_app, render_template, redirect, request as current_request, session
from werkzeug.exceptions import HTTPException, BadRequest

from server.oidc import oidc

base_blueprint = Blueprint("base_blueprint", __name__, url_prefix="/")


def json_endpoint(f):
    @wraps(f)
    def json_decorator(*args, **kwargs):
        try:
            body, status = f(*args, **kwargs)
            response = jsonify(body)
            return response, status
        except Exception as e:
            response = jsonify(message=e.description if isinstance(e, HTTPException) else str(e))
            logging.getLogger().exception(response)
            if isinstance(e, HTTPException):
                response.status_code = e.code
            else:
                response.status_code = 500
            return response

    return json_decorator


def _template_context(additional_ctx={}):
    ctx = {"configuration": current_app.app_config}
    for name in ["guest", "conext"]:
        if name in session:
            ctx[name] = session[name]
    return {**ctx, **additional_ctx}


@base_blueprint.route("/", strict_slashes=False)
@oidc.require_guest_login
def index():
    return render_template("index.html", **_template_context())


@base_blueprint.route("/connect", strict_slashes=False, methods=["GET"])
@oidc.require_guest_login
@oidc.require_conext_login
def connect():
    return render_template("connect.html", **_template_context())


@base_blueprint.route("/logout", strict_slashes=False)
def logout():
    session.clear()
    return redirect("/")


@base_blueprint.route("/health", strict_slashes=False)
@json_endpoint
def health():
    if "error" in current_request.args:
        raise BadRequest()
    return {"status": "UP"}, 200


@base_blueprint.route("/info", strict_slashes=False)
@json_endpoint
def info():
    file = f"{os.path.dirname(os.path.realpath(__file__))}/git.info"
    with open(file) as f:
        return {"git": f.read()}, 200
