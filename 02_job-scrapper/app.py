from flask import Flask, render_template, request, send_file, redirect
from scrapper import search_incruit, search_saramin
from file import save_to_csv

app = Flask(__name__)

db = {}
page = 5

@app.route('/')
def hello_world():
    return render_template("index.html")

@app.route("/search")
def search():
    keyword = request.args.get("keyword")

    if keyword == "":
        return redirect("/")
    
    if keyword in db:
        jobs = db[keyword]
    else:
        incruit_jobs = search_incruit(keyword, page)
        saramin_jobs = search_saramin(keyword, page)

        jobs = incruit_jobs + saramin_jobs
        db[keyword] = jobs

    return render_template("search.html", jobs=enumerate(jobs), keyword=keyword, count=len(jobs))

@app.route("/file")
def file():
    keyword = request.args.get("keyword")

    if keyword == "":
        return redirect("/")
    
    if keyword in db:
        jobs = db[keyword]
    else:
        incruit_jobs =  search_incruit(keyword, page)
        saramin_jobs =  search_saramin(keyword, page)

        jobs = incruit_jobs + saramin_jobs
        
    save_to_csv(jobs)
    return send_file("./downloads.csv", as_attachment=True)


if __name__ == '__main__':
    app.run()