from flask import Flask, render_template, request
from scrapper import fetch_apt_trade

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.route('/')
def index():
    return render_template("index.html")

@app.route("/search")
def search():
    DEAL_YMD = request.args.get("DEAL_YMD")
    LAWD_CD = request.args.get("LAWD_CD")
    results = fetch_apt_trade(LAWD_CD, DEAL_YMD)
    return render_template("search.html", results=results)

if __name__ == '__main__':
    app.run(debug=True)