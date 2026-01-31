from flask import Flask, render_template
import json

app = Flask(__name__)

def wczytaj():
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

@app.route("/")
def index():
    dane = wczytaj()
    return render_template(
        "index.html",
        zawodnicy=dane["zawodnicy"],
        wyniki=dane["wyniki"],
        dyscypliny=dane["dyscypliny"]
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
