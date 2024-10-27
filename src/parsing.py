import requests
import bs4
import re
from config import logger
from user_agent import generate_user_agent
from datetime import datetime, timedelta

def is_date_within_hour(date_string):
    try:
        date_object = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")

        current_time = datetime.now()

        return (current_time - date_object) <= timedelta(hours=3)
    except ValueError as e:
        logger.error(f"Error: {e}")
        return False

def parse_investing_news(url):
    """Investing.com parser."""
    
    headers = {
        "User -Agent": generate_user_agent()
    }

    logger.debug(f"Generate user agent: {headers}")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        html = response.text
        soup = bs4.BeautifulSoup(html, 'html.parser')

        articles = soup.findAll("article", {"data-test": "article-item"})
        
        results = []

        for article in articles:
            try:
                title_tag = article.find("a", {"data-test": "article-title-link"})
                title = title_tag.text if title_tag else "title not found"
                
                date_tag = article.find("time", {"data-test": "article-publish-date"})
                date = date_tag['datetime'] if date_tag else "date not found"
                
                url = title_tag['href'] if title_tag else "link not found"
                
                author_tag = article.find("span", {"data-test": "news-provider-name"})
                author = author_tag.text if author_tag else "author not found"
                
                about_tag = article.find("p", {"data-test": "article-description"})
                about = about_tag.text if about_tag else "about not found"

                if is_date_within_hour(date):
                    result_string = f"\n\n__{date}__\n\n__{author}__\n\n**{title}**\n\n**{about}**\n\n__{url}__"
                    results.append(result_string)
                else:
                    pass

            except Exception as e:
                logger.error(f"Error: {e}")

        return results

    except requests.exceptions.RequestException as e:
        logger.error(f"Error: {e}")
        return []

def start_parsing():
    results = []
    links = [
        "https://www.investing.com/news/forex-news/",
        "https://www.investing.com/news/commodities-news/",
        "https://www.investing.com/news/stock-market-news/",
        "https://www.investing.com/news/economic-indicators/",
        "https://www.investing.com/news/economy/",
        "https://www.investing.com/news/cryptocurrency-news/"
    ]

    for link in links:
        logger.info(f"Parsing: {link}")
        results += parse_investing_news(link)

    return results