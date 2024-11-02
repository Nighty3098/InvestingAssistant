import asyncio
import re
import time
from datetime import datetime, timedelta

import bs4
import requests
from user_agent import generate_user_agent

from config import app, logger
from db import get_city_from_db
from func import (convert_to_utc, is_within_period, notify_user,
                  parse_time_period, to_local)

links = [
    "https://ru.investing.com/news/",
    "https://ru.investing.com/news/forex-news/",
    "https://ru.investing.com/news/commodities-news/",
    "https://ru.investing.com/news/stock-market-news/",
    "https://ru.investing.com/news/economic-indicators/",
    "https://ru.investing.com/news/economy/",
    "https://ru.investing.com/news/cryptocurrency-news/",
    "https://ru.investing.com/news/economic-indicators/",
    "https://www.investing.com/news/",
    "https://www.investing.com/news/forex-news/",
    "https://www.investing.com/news/commodities-news/",
    "https://www.investing.com/news/stock-market-news/",
    "https://www.investing.com/news/economic-indicators/",
    "https://www.investing.com/news/economy/",
    "https://www.investing.com/news/cryptocurrency-news/",
    "https://www.investing.com/news/economic-indicators/",
]


def parse_investing_news(url, period, user_id):
    """Investing.com parser."""

    headers = {"User-Agent": generate_user_agent()}
    logger.debug(f"Generate user agent: {headers}")

    try:
        timezone_info = get_city_from_db(user_id)

        if isinstance(timezone_info, tuple):
            timezone = timezone_info[0]
        else:
            timezone = timezone_info

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        html = response.text
        soup = bs4.BeautifulSoup(html, "html.parser")

        articles = soup.findAll("article", {"data-test": "article-item"})
        results = []
        seen_articles = set()

        for article in articles:
            try:
                title_tag = article.find("a", {"data-test": "article-title-link"})
                title = title_tag.text.strip() if title_tag else "title not found"

                date_tag = article.find("time", {"data-test": "article-publish-date"})
                date = date_tag["datetime"].strip() if date_tag else "date not found"

                article_url = (
                    title_tag["href"].strip() if title_tag else "link not found"
                )

                author_tag = article.find("span", {"data-test": "news-provider-name"})
                author = author_tag.text.strip() if author_tag else "author not found"

                about_tag = article.find("p", {"data-test": "article-description"})
                about = about_tag.text.strip() if about_tag else "about not found"

                logger.debug(f"Parsing {article_url} - {title}")

                unique_identifier = (title, article_url)

                if unique_identifier not in seen_articles and is_within_period(
                    date, period, user_id
                ):
                    seen_articles.add(unique_identifier)
                    result_string = f"\n\n🔥 **{title}**\n\n🌊 **{about}**\n\n✨ __{article_url}__\n\n📆 __{to_local(timezone, date)}__\n\n😁 __{author}__"
                    logger.debug(f"Adding {article_url} - {title} to results")
                    results.append(result_string)

            except Exception as e:
                logger.error(f"Error processing article: {e}")

        return results

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching news: {e}")
        return []


def start_parsing(period, user_id):
    results = []

    for link in links:
        logger.info(f"Parsing: {link}")
        logger.debug(period)
        results += parse_investing_news(link, period, user_id)

    return results


async def check_new_articles(user_id):
    seen_articles = set()

    while True:
        for link in links:
            logger.info("Parsing: " + link)
            articles = parse_investing_news(link, "10 minutes", user_id)
            for article in articles:
                if article not in seen_articles:
                    logger.debug(f"Added to seen articles: {article}")
                    seen_articles.add(article)
                    await notify_user(user_id, article)

        logger.info("Sleeping...")
        await asyncio.sleep(3600 / 6)


def run_check_new_articles(user_id):
    asyncio.run(check_new_articles(user_id))
