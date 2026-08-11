import requests
from bs4 import BeautifulSoup


def search_aladin(keyword, page=1):

    books = []

    for i in range(page):

        page_num = i + 1

        url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=All&KeyWord={keyword}&ViewType=Detail&ViewRowCount=25&page={page_num}"

        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        book_boxes = soup.find_all("div", class_="ss_book_box")

        for book_box in book_boxes:

            book_list = book_box.find("div", class_="ss_book_list")

            title_tag = book_list.find("a", class_="bo3")
            
            title = title_tag.text
            link = title_tag.get("href")

            info_list = book_list.find_all("li")[2]
            infos = info_list.find_all("a")

            authors = []
            illustrators = []
            translators = []

            publisher = ""
            published_date = ""

            info_text = info_list.text
            clean_text = info_text.replace(" ","").replace("\n", "")

            for info in infos:
                name = info.text

                if f"{name}(지은이)" in clean_text:
                    authors.append(name)
                elif f"{name}(그림)" in clean_text:
                    illustrators.append(name)
                elif f"{name}(옮긴이)" in clean_text:
                    translators.append(name)
                elif f"{name}|" in clean_text:
                    publisher = name
            
            if "|" in info_text:
                published_date = info_text.split("|")[1]
            
            author = ", ".join(authors)
            illustrator = ", ".join(illustrators)
            translator = ", ".join(translators)

            price_tags = book_box.find_all("a", class_="bo_used")
#############################################################################이까진 됐음






if __name__ == "__main__":

    keyword = input("검색할 책을 입력하세요: ")

    aladin_result = search_aladin(keyword, 2)

    print(aladin_result)
    print(len(aladin_result))