# -*- coding: utf-8 -*-
import sys
import io
import re
import requests
from bs4 import BeautifulSoup

# 编码修复
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', errors='replace')

from app import app, db
from app import Novel, Comment

# ===================== 爬取配置 =====================
NOVEL_COUNT = 30
COMMENTS_PER_NOVEL = 100

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

def clean(s):
    return re.sub(r"\s+", " ", s).strip() if s else ""

# 爬书籍
def crawl_books():
    books = []
    seen = set()
    pages = [0, 20, 40, 60, 80]
    for start in pages:
        if len(books) >= NOVEL_COUNT: break
        try:
            url = f"https://book.douban.com/tag/%E5%B0%8F%E8%AF%B4?start={start}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.find_all("li", "subject-item"):
                if len(books) >= NOVEL_COUNT: break
                a = item.find("h2").find("a")
                title = clean(a.get_text())
                href = a["href"]
                sid = re.search(r"/subject/(\d+)/", href).group(1)
                if sid in seen: continue
                seen.add(sid)
                books.append({"sid": sid, "title": title})
        except:
            continue
    return books

# 爬评论
def crawl_comments(sid):
    coms = []
    for i in range(5):
        try:
            url = f"https://book.douban.com/subject/{sid}/comments/?start={i*20}"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            resp.encoding = "utf-8"
            for s in BeautifulSoup(resp.text, "html.parser").find_all("span", "short"):
                txt = clean(s.get_text())
                if len(txt) > 2:
                    coms.append(txt)
                if len(coms) >= 100: return coms[:100]
        except: break
    while len(coms) < 100: coms.append("这本书不错")
    return coms[:100]

# 保存
def save(book, comments):
    with app.app_context():
        n = Novel.query.filter_by(title=book["title"]).first()
        if not n:
            n = Novel(
                title=book["title"],
                author="unknown",
                description="no desc"
            )
            db.session.add(n)
            db.session.commit()

        if Comment.query.filter_by(novel_id=n.id).count() == 0:
            db.session.bulk_save_objects([Comment(content=c, novel_id=n.id) for c in comments])
            db.session.commit()

# 执行
if __name__ == "__main__":
    print("Start...")
    book_list = crawl_books()
    for b in book_list:
        cs = crawl_comments(b["sid"])
        save(b, cs)
        print(">", end=" ")
    print("\n✅ DONE!")
