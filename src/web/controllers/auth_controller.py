"""Auth controller for Auth0 integration
"""

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Blueprint, redirect, render_template, session, url_for, current_app, g, jsonify

# Load environment variables
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

# Create auth blueprint
auth_bp = Blueprint('auth', __name__)

# Setup OAuth object
oauth = None

@auth_bp.record_once
def on_load(state):
    """Initialize OAuth when blueprint is registered with app"""
    global oauth
    oauth = OAuth(state.app)
    
    oauth.register(
        "auth0",
        client_id=env.get("AUTH0_CLIENT_ID"),
        client_secret=env.get("AUTH0_CLIENT_SECRET"),
        client_kwargs={
            "scope": "openid profile email",
        },
        server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
    )

@auth_bp.route("/")
def auth_home():
    """Display auth page with user info if logged in"""
    return render_template('logged_in/dashboard.html')

@auth_bp.route("/dashboard")
def dashboard():
    """Display dashboard page with user info if logged in"""
    return render_template('logged_in/dashboard.html')

@auth_bp.route("/profile")
def profile():
    """Display user profile page with user info"""
    if not is_authenticated():
        return redirect(url_for("auth.auth_home"))
    return render_template('logged_in/profile.html')

@auth_bp.route("/login")
def login():
    """Route for login - redirects to Auth0"""
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("auth.callback", _external=True)
    )

@auth_bp.route("/callback", methods=["GET", "POST"])
def callback():
    """Auth0 callback handler"""
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect(url_for("auth.profile"))

@auth_bp.route("/logout")
def logout():
    """Route for logout - clears session and redirects to Auth0 logout"""
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("auth.auth_home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

# Helper function to check if user is logged in
def is_authenticated():
    """Check if user is authenticated"""
    return "user" in session

# Template helper to check authentication status
@auth_bp.app_context_processor
def inject_auth_status():
    """Add authentication status to template context"""
    return dict(
        is_authenticated=is_authenticated(),
        user=session.get("user", None)
    ) 