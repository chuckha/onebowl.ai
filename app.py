import os
from urllib.parse import urldefrag, urlparse

from flask import Flask, redirect, render_template, request, send_from_directory, session, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from cache import flag as cache_flag, get as cache_get, put as cache_put, recent as cache_recent
from recipe_analyzer import AnalyzeError, analyze_recipe
from recipe_fetcher import FetchError, fetch_recipe

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32))

limiter = Limiter(get_remote_address, app=app, default_limits=[])

APP_PASSWORD = os.environ.get("APP_PASSWORD", "")


def normalize_url(url: str) -> str:
    return urldefrag(url).url


@app.context_processor
def inject_auth():
    return {"authenticated": session.get("authenticated", False)}


@app.route("/favicon.ico")
def favicon():
    return send_from_directory("static", "favicon.svg", mimetype="image/svg+xml")


@app.route("/")
def index():
    return render_template("index.html", recipes=cache_recent())


@app.route("/login", methods=["POST"])
def login():
    password = request.form.get("password", "")
    if APP_PASSWORD and password == APP_PASSWORD:
        session["authenticated"] = True
    return redirect(url_for("index"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/analyze", methods=["POST"])
@limiter.limit("30/hour")
def analyze():
    if not session.get("authenticated"):
        return render_template("error.html", message="Please log in first."), 403

    url = request.form.get("url", "").strip()
    if not url:
        return render_template("error.html", message="Please enter a URL."), 400

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return render_template("error.html", message="Please enter a valid URL."), 400

    url = normalize_url(url)

    cached = cache_get(url)
    if cached is not None:
        return render_template("recipe.html", recipe=cached)

    try:
        raw = fetch_recipe(url)
    except FetchError as exc:
        return render_template("error.html", message=str(exc)), 400

    try:
        recipe = analyze_recipe(raw)
    except AnalyzeError as exc:
        return render_template("error.html", message=str(exc)), 502

    cache_put(url, recipe)
    return render_template("recipe.html", recipe=recipe)


@app.route("/flag/<path:url>", methods=["POST"])
def flag_recipe(url):
    if not session.get("authenticated"):
        return render_template("error.html", message="Please log in first."), 403

    url = normalize_url(url)
    cache_flag(url)
    return redirect(f"/recipe/{url}")


@app.route("/recipe/<path:url>")
def view_recipe(url):
    url = normalize_url(url)
    recipe = cache_get(url)
    if recipe is None:
        return render_template("error.html", message="Recipe not found."), 404
    return render_template("recipe.html", recipe=recipe)


@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template("error.html", message="Too many requests. Please try again later."), 429
