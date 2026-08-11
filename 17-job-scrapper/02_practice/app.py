from flask import Flask, render_template, request, send_file, redirect #flask라는 패키지에서, Flask, render_template, request, send_file, redirect를 가져온다
from scrapper import search_incruit     #scrapper.py에서 search.incruit를 가져온다.
from file import save_to_csv        #file.py에서 save_to_csv 라는 함수를 가져온다.

# Flask : 웹앱을 만들때 사용
# render_template : HTML 파일을 화면에 보여줄때 사용
# request : 사용자가 보낸 요청 정보를 가져올 때 사용
# send_file : 파일을 사용자에게 다운로드 시킬 때 사용
# redirect : 다른 주소로 이동시킬 때 사용

app = Flask(__name__) # 이제부터 이 파일(app.py)(더 정확히 말하면 app)을 웹사이트 서버로 사용하겠다

db = {} #검색결과를 잠깐 저장하는 딕셔너리(즉, 임시저장소) 이걸하는 이유는? 사용자가 "간호사"를 검색하면, db["간호사"]=jobs 이런식으로 저장되는데, 같은 검색어를 다시 검색했을 때, 해당 사이트에 다시 접속하지 않고 저장된 결과를 보여주기 위함.
page = 5 #검사할 페이지 수 

@app.route('/') #사용자가 웹 사이트 첫 화면에 접속했을 때 실행되는 부분. 이 주소로 접속하면 아래 함수가 실행됨
def hello_world():
    return render_template("index.html") #templates 안의 index.html을 보여준다

@app.route("/search") #(기본주소)/search로 들어가면, 아래의 함수를 실행함
def search():
    keyword = request.args.get("keyword") # 주소에서 검색어를 가져오는 코드.

    if keyword == "":       #검색어가 비어있다면?
        return redirect("/")        #메인으로 이동
    
    if keyword in db:       #이미 이전에 검색한 적이 있는 keyword라면?
        jobs = db[keyword]      #db안에 저장된 결과를 불러와라(처음 검색했을때보다 더 빨리 나옴)
    else:       #처음 검색한 keyword라면?
        jobs = search_incruit(keyword, page) #search_incruit라는 함수를 실행해서 jobs에 저장을 하고
        db[keyword] = jobs # 그 결과를 db에 저장

    return render_template("search.html", jobs=enumerate(jobs), keyword=keyword, count=len(jobs))       # 검색결과를 search.html에 보내서 화면에 보여줌
                                        #검색결과목록에 번호를 붙여서 보냄, 검색어를 HTML에 보냄, 검색 결과 개수를 HTML에 보냄

#csv 다운로드를 담당하는 부분
@app.route("/file")     #사용자가 '데이터다운로드' 라는 버튼을 누르면 이 주소로 이동함
def file():
    keyword = request.args.get("keyword") #주소에서 keyword를 가져온다

    if keyword == "": # 검색어가 없으면 메인으로 이동하고
        return redirect("/")
    
    if keyword in db: # 이미 검색한 결과가 있으면 그걸 사용한다
        jobs = db[keyword]
    else:
        jobs =  search_incruit(keyword, page) #처음하는거면 새로 검색한다

    save_to_csv(jobs)       #검색결과 jobs를 csv파일로 저장한다
    return send_file("./downloads.csv", as_attachment=True) #downloads.csv파일을 만들어서 저장한다.
                                        #브라우저에서 열지 말고 파일로 다운로드하게 하라는 뜻


if __name__ == '__main__': #app.py를 '직접' 실행할때만 
    app.run()       # app를 실행해라