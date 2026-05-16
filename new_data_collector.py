import requests
from bs4 import BeautifulSoup
import time
import os


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
        # Validate section
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


def process_article(article_id, url_generator, collector, crawled_urls):
    """Generate a URL and scrape its content if not already crawled."""
    url = url_generator.generate(article_id)
    if url in crawled_urls:
        return None  # Skip if the article has already been crawled
    return collector.scrape(url)


def load_crawled_urls(file_path):
    """Load previously crawled URLs from a file."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return set(line.strip().split("URL: ")[1] for line in file if line.startswith("URL:"))
    return set()


def save_articles_to_file(articles, file_path, append=False):
    """Save articles to a file."""
    mode = "a" if append else "w"
    with open(file_path, mode, encoding="utf-8") as file:
        for article in articles:
            file.write(f"URL: {article['url']}\nTitle: {article['title']}\n\nContent:\n{article['content']}\n{'-'*80}\n")


