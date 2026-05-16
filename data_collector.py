# data_collector.py
import requests
from bs4 import BeautifulSoup
import time


class URLGenerator:
    """Class to generate article URLs based on the base URL and article ID."""
    def __init__(self, base_url):
        self.base_url = base_url

    def generate(self, article_id):
        return f"{self.base_url}{article_id}/berita/sukan/{article_id}-some-article-title"


class DataCollector:
    """Class to handle web scraping and data extraction."""
    def __init__(self, retries=3, backoff=2):
        self.retries = retries
        self.backoff = backoff

    def scrape(self, url):
        """Scrape title and content from the article page."""
        for attempt in range(self.retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return self.parse_content(response.text, url)
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1}: Failed to fetch {url} - {e}")
                time.sleep(self.backoff)
        return None

    def parse_content(self, html, url):
        """Parse the HTML content and extract title and article."""
        soup = BeautifulSoup(html, "html.parser")

        # Validate if the section is related to "Sukan"
        sukan_section = soup.find('div', class_='section')
        if sukan_section:
            sukan_links = sukan_section.find_all('a', href=True)
            if not any('sukan' in link['href'].lower() for link in sukan_links):
                return None

        # Extract title
        title = soup.find('h1', class_='title').text.strip() if soup.find('h1', class_='title') else "No title found"

        # Remove unwanted sections
        for unwanted_section in soup.find_all('div', class_=['text-promo', 'related-article-inside-body']):
            unwanted_section.decompose()

        # Extract content
        article = soup.find('article')
        content = "\n".join(p.text.strip() for p in article.find_all('p')) if article else "No content found"

        return {"url": url, "title": title, "content": content} if content != "No content found" else None


def process_article(article_id, url_generator, collector):
    """Generate a URL and scrape its content."""
    url = url_generator.generate(article_id)
    return collector.scrape(url)