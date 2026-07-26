import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime

def fetch_article_text(url, timeout=8):
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs)
        return text[:3000]
    except Exception:
        return ""

def fetch_news(query="India exam paper leak", max_results=10):
    url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:max_results]:
        published_date = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published_date = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")

        articles.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.get("published", ""),
            "published_date": published_date,
            "summary": entry.get("summary", "")
        })
    return articles

if __name__ == "__main__":
    results = fetch_news()
    for r in results:
        print(r["title"], "-", r["published_date"], "-", r["link"])