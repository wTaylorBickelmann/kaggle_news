import requests
from bs4 import BeautifulSoup
from newspaper import Article as NewsArticle
from database import save_article

class NewsScraper:
    def __init__(self, sources):
        self.sources = sources

    def scrape_source(self, url):
        try:
            article = NewsArticle(url)
            article.download()
            article.parse()
            
            article_data = {
                'title': article.title,
                'content': article.text,
                'source': url,
                'url': url
            }
            save_article(article_data)
            return True
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return False

    def scrape_all(self):
        for source in self.sources:
            self.scrape_source(source)

# Example news sources
NEWS_SOURCES = [
    'https://www.reuters.com/world/',
    'https://www.apnews.com/',
    'https://www.bbc.com/news'
]
