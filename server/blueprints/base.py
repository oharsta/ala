import hashlib
import logging
import os
from datetime import datetime, timedelta
from functools import wraps
import urllib.parse

from flask import Blueprint, jsonify, current_app, render_template, redirect, session, \
    request
from werkzeug.exceptions import HTTPException

from server.db.user import User
from server.oidc import oidc

base_blueprint = Blueprint("base_blueprint", __name__, url_prefix="/")

protected_properties = ["eduperson_principal_name", "eduperson_entitlement", "eduperson_unique_id_per_sp", "sub_hash"]


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


@base_blueprint.route("/", strict_slashes=False)
def index():
    redirect_uri = request.args.get("redirect_uri")
    if not redirect_uri:
        return render_template("error.html", **{"error": "No redirect_uri was provided."})

    profile = request.args.get("profile", "edubadges")

    if profile not in current_app.app_config.profile:
        return redirect(f"{redirect_uri}?error=unknown_profile_{profile}")

    session["redirect_uri"] = redirect_uri
    session["profile"] = profile
    state = request.args.get("state")
    if state:
        session["state"] = state

    return redirect("/login")


@base_blueprint.route("/login", strict_slashes=False)
@oidc.require_guest_login
def login():
    return redirect("/connect")


@base_blueprint.route("/connect", strict_slashes=False)
@oidc.require_guest_login
@oidc.require_conext_login
def connect():
    conext = session["conext"]
    guest = session["guest"]

    required_attributes = current_app.app_config.profile[session["profile"]].required_attributes
    missing_attributes = [k for k in required_attributes if k not in conext]

    if len(missing_attributes) > 0:
        return redirect(f"{session['redirect_uri']}?error=required_attribues_missing_{'_'.join(missing_attributes)}")

    user = User.find_by_eduperson_principal_name(guest["eduperson_principal_name"])
    if not user:
        return redirect(f"{session['redirect_uri']}?error=user_{guest['eduperson_principal_name']}_"
                        f"not_provisioned_in_guest_idp")

    sub_hash = hashlib.sha256(bytes(conext["sub"], "utf-8")).hexdigest()
    pre_existing_user = User.find_by_sub_hash(sub_hash)
    if pre_existing_user and pre_existing_user["_id"] != user["_id"]:
        return redirect(f"{session['redirect_uri']}?error=sub_{conext['sub']}_already_linked_"
                        f"to_{conext['schac_home_organization']}")

    user["eduperson_entitlement"] = "urn:mace:eduid.nl:entitlement:verified-by-institution"
    expiry_seconds = current_app.app_config.cron.expiry_duration_seconds
    user["expiry_date"] = datetime.now() + timedelta(seconds=expiry_seconds)
    user["sub_hash"] = sub_hash
    # Copy all attributes from conext to the user - ARP values will filter upstream
    for k, v in conext.items():
        if k not in protected_properties:
            user[k] = v

    logger = logging.getLogger("main")
    logger.info(f"Marking User {guest['eduperson_principal_name']} as verified-by-institution")

    User.save_or_update(user)

    uri = session["redirect_uri"]
    state = session["state"]

    uri = f"{uri}?state={urllib.parse.quote(state)}" if state else uri
    return redirect(uri)


@base_blueprint.route("/health", strict_slashes=False)
@json_endpoint
def health():
    return {"status": "UP"}, 200


@base_blueprint.route("/info", strict_slashes=False)
@json_endpoint
def info():
    file = f"{os.path.dirname(os.path.realpath(__file__))}/git.info"
    with open(file) as f:
        return {"git": f.read()}, 200
