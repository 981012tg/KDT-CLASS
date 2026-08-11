import requests     #웹페이지에 요청을 보내고 응답을 받는다
from bs4 import BeautifulSoup       #받아온 HTML에서 원하는 태그를 찾는다


def search_incruit(keyword, page=1): #검색어와 페이지 수를 받아서 공고 목록을 리스트로 반환, page 값을 따로 안넣으면 자동으로 1을 사용하겠다는 뜻
    # 1 -> 0
    # 2 -> 30
    # 3 -> 60

    jobs = []

    for i in range(page):       #page 수만큼 반복 
        page = 30 * i           #인크루트 url에 startbo=0 이런 부분이 있음. 즉, 페이지를 요청하기 위한 부분
        url = f"https://search.incruit.com/list/search.asp?col=job&kw={keyword}&startno={page}"
        r = requests.get(url)       #url로 실제 요청을 보내고, 그 결과를 r에 저장
        soup = BeautifulSoup(r.text, "html.parser") #r.text를 하면 HTML문자열로 저장하는데, 이는 태그 찾기가 불편해서, beautifulsoup을 써서 태그단위로 찾게함. 그 결과를 soup에 저장
        lis = soup.find_all("li", class_="c_col") #HTML 안에서 <li class="c_col"> 이런 태그를 전부 찾아서 리스트로 저장


        for li in lis: 
            company = li.find("a", class_="cpname").text   
            title = li.find("div", class_="cell_mid").find("div", class_="cl_top").find("a").text
            location = li.find("div", class_="cl_md").find_all("span")[0].text
            link = li.find("div", class_="cell_mid").find("div", class_="cl_top").find("a").get("href")
            
            job_data = {
                "company": company, 
                "title" : title, 
                "location": location, 
                "link" : link
            }

            jobs.append(job_data)

    return jobs

# from scrapper import search_incruit --> 이런식으로 가져다 쓰면 직접 실행한게 아니라 불러온것
# 이러면, __name__값이 "__main__"이 아니라 "scrapper가 됨"
# 파이썬 파일에는 자동으로 __name__이란 변수가 생김

# 밑의 부분은, 이 함수가 제대로 작동하는지 테스트를 하는것

if __name__ == "__main__": # 이 파일을 '직접' 실행할 때만 아래 코드를 실행하라
    result = search_incruit("간호사", 2) #2로 하면, 2페이지 까지 검색하겠다는 뜻
    print(result)
    print(len(result))
