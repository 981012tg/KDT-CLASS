import csv      #파이썬에서 csv파일을 만들기 위한 기본 모듈을 가져와라
from scrapper import search_incruit     #scrapper.py에 있는 search_incruit 함수를 가져와라

def save_to_csv(jobs):
    with open("./downloads.csv", "w", encoding="cp949") as file:        #현재 폴더에 downloads.csv라는 파일을 만들고,  쓰기모드로 연다. encoding은 한글이 깨지지 않게 저장하려고 넣은 인코딩
        csv_writer = csv.writer(file)       #csv파일에 데이터를 쓰기 위한 도구를 만든다.
        csv_writer.writerow(["No", "회사", "제목", "지역", "상세보기"]) #csv 파일의 첫번째 줄을 이렇게 할거다
        for i, job in enumerate(jobs):      # jobs 안에 있는 채용공고를 하나씩 꺼내서 index도 같이 쓴다
            csv_writer.writerow([i+1,  job["company"], job["title"], job['location'], job['link']])     # 공고 하나를 csv 파일 한줄로 이렇게 저장할거다. 이때 index는 0부터 시작하므로 +1을 해서 저장한다
        