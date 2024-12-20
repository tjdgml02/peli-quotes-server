from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
from urllib import parse
import asyncio
import aiohttp
from pykospacing import Spacing
app = FastAPI()
spacing = Spacing()

@app.get("/book")
async def get_books(book_name: str = "", n: int = 1):
    urls = search_book_url(book_name, n)
    results = await asyncio.gather(*(get_book_info_result(url) for url in urls))
    return results

def search_book_url(book_name, n):
    url = "http://www.yes24.com/Product/Search?domain=BOOk&query=" + parse.quote(book_name)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    selector = f"#yesSchList > li:nth-child(-n+{n}) > div > div.item_info > div.info_row.info_name > a.gd_name"
    urls = ["http://www.yes24.com/" + a.attrs['href'] for a in soup.select(selector)]
    return urls

@app.get("/check")
async def get_check(text: str = ""):
    # text = spacing(text)
    return {"text": text}

async def get_book_info_result(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                html_content = await response.text()

        soup = BeautifulSoup(html_content, "html.parser")

        tags = []
        for tag in soup.select(
                "#infoset_goodsCate > div.infoSetCont_wrap > dl:nth-child(-n+1) > dd > ul > li > a"
        ):
            tags.append(tag.get_text(strip=True).replace(" ", ""))

        # tags = list(set(tags))

        main_title = soup.select_one(
            "#yDetailTopWrap > div.topColRgt > div.gd_infoTop > div > h2"
        ).get_text(strip=True)

        sub_title_element = soup.select_one(
            "#yDetailTopWrap > div.topColRgt > div.gd_infoTop > div > h3"
        )
        sub_title = sub_title_element.get_text(strip=True) if sub_title_element else None

        title = (
            f"{main_title}：{sub_title}" if sub_title else main_title
        )

        author = soup.select_one("#contents_author_grp1 > div.authorTit > div.author_name > a").get_text(strip=True)

        translator = []
        for a in soup.select("#divAuthorList > div.authorInfoGrp > div.authorTit > div"):
            a = a.get_text(strip=True)
            if ":" not in a: continue
            if "저" in a: continue
            i = a.find(":")
            translator.append(a[i+1:].strip())

        publisher = soup.select_one("#yDetailTopWrap > div.topColRgt > div.gd_infoTop > span.gd_pubArea > span.gd_pub > a").get_text(strip=True)

        publish_date = "-".join(
            [
                part[:-1]
                for part in soup.select_one(
                "#yDetailTopWrap > div.topColRgt > div.gd_infoTop > span.gd_pubArea > span.gd_date"
            ).get_text(strip=True).split(" ")
            ]
        )

        cover_url = (
                soup.select_one(
                    "#yDetailTopWrap > div.topColLft > div > div.gd_3dGrp > div > span.gd_img > em > img"
                )
                or soup.select_one(
            "#yDetailTopWrap > div.topColLft > div > span > em > img"
        )
        )
        cover_url = cover_url["src"] if cover_url else ""

        data = {
            "imageURI": cover_url,
            "title": title.replace("：", " ").replace("？", "").replace("/", "／").replace("\s{2,}", " "),
            "author": author,
            "translator": ", ".join(translator),
            "publisher": publisher,
            "category": tags[1] if len(tags) > 1 else "",
            "publishYear": publish_date,
            # "genre": " ".join(tags)
            "genre": tags[0]
        }



        return data

    except Exception as e:
        print(e)
        return {"error": str(e)}
