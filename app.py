from urllib.parse import urlparse

from flask import Flask, render_template, request

from recipe_analyzer import AnalyzeError, analyze_recipe
from recipe_fetcher import FetchError, fetch_recipe

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    url = request.form.get("url", "").strip()
    if not url:
        return render_template("error.html", message="Please enter a URL."), 400

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return render_template("error.html", message="Please enter a valid URL."), 400

    try:
        raw = fetch_recipe(url)
    except FetchError as exc:
        return render_template("error.html", message=str(exc)), 400

    try:
        recipe = analyze_recipe(raw)
    except AnalyzeError as exc:
        return render_template("error.html", message=str(exc)), 502

    return render_template("recipe.html", recipe=recipe)
