from flask import Flask, render_template, request
import requests

app = Flask(__name__)

BASE_URL = "https://api.jikan.moe/v4"


@app.route("/")
def home():
    try:
        response = requests.get(f"{BASE_URL}/top/anime", timeout=10)
        data = response.json()
        top_anime = data.get("data", [])[:12]
    except Exception:
        top_anime = []

    return render_template("index.html", top_anime=top_anime)


@app.route("/search")
def search():
    query = request.args.get("q", "")

    if not query:
        return render_template("search.html", anime_list=[], query=query)

    try:
        response = requests.get(
            f"{BASE_URL}/anime",
            params={"q": query, "limit": 16},
            timeout=10
        )
        data = response.json()
        anime_list = data.get("data", [])
    except Exception:
        anime_list = []

    return render_template("search.html", anime_list=anime_list, query=query)


@app.route("/anime/<int:anime_id>")
def anime_details(anime_id):
    try:
        response = requests.get(f"{BASE_URL}/anime/{anime_id}/full", timeout=10)
        data = response.json()
        anime = data.get("data", {})
    except Exception:
        anime = {}

    return render_template("details.html", anime=anime)


if __name__ == "__main__":
    app.run(debug=True)