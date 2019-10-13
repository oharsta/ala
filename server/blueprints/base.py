import logging
import os
from datetime import datetime
from functools import wraps

from flask import Blueprint, jsonify, current_app, render_template, redirect, request as current_request, session
from werkzeug.exceptions import HTTPException, BadRequest

from server.db.user import User
from server.oidc import oidc

base_blueprint = Blueprint("base_blueprint", __name__, url_prefix="/")

contact_attributes = [("roepnaam", "nickname"), ("emailadres", "email"),
                      ("telefoonnummer1_toegangscode", "phone_access_code"),
                      ("telefoonnummer1_telefoonnummer", "phone"),
                      ("correspondentietaal", "language")]


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


def check_user(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            user_info = oidc._retrieve_userinfo()
            sub = oidc.user_getinfo(fields=["sub"])
            if sub["sub"]:
                user = User.find_by_sub(sub["sub"])
                if not user:
                    return redirect("/contact")
                session["user"] = user
            else:
                oidc.logout()
                return redirect("/login")
        return f(*args, **kwargs)

    return decorated


def _template_context(additional_ctx={}):
    ctx = {"configuration": current_app.app_config}
    if "user" in session:
        ctx["user"] = session["user"]
    return {**ctx, **additional_ctx}


@base_blueprint.route("/", strict_slashes=False)
def index():
    return render_template("index.html", **_template_context())


@base_blueprint.route("/logout", strict_slashes=False)
def logout():
    oidc.logout()
    session.clear()
    return redirect("/")


@base_blueprint.route("/login", strict_slashes=False, methods=["GET"])
@oidc.require_login
@check_user
def login():
    return redirect("/overview")


@base_blueprint.route("/overview", strict_slashes=False, methods=["GET"])
@oidc.require_login
@check_user
def overview():
    return render_template("overview.html", **_template_context())


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
