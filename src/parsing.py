import asyncio
import re
import time
from datetime import datetime, timedelta

import bs4
import requests
from user_agent import generate_user_agent

from config import app, logger
from db import (create_connection, get_city_from_db, get_stocks_list,
                process_stocks)
from func import (convert_to_utc, get_time_difference, is_within_period,
                  notify_user, parse_time_period, to_local)

links = [
    "https://ru.investing.com/news/",
    "https://ru.investing.com/news/forex-news/",
    "https://ru.investing.com/news/commodities-news/",
    "https://ru.investing.com/news/stock-market-news/",
    "https://ru.investing.com/news/economic-indicators/",
    "https://ru.investing.com/news/economy/",
    "https://ru.investing.com/news/cryptocurrency-news/",
    "https://ru.investing.com/news/economic-indicators/",
    # "https://www.investing.com/news/",
    # "https://www.investing.com/news/forex-news/",
    # "https://www.investing.com/news/commodities-news/",
    # "https://www.investing.com/news/stock-market-news/",
    # "https://www.investing.com/news/economic-indicators/",
    # "https://www.investing.com/news/economy/",
    # "https://www.investing.com/news/cryptocurrency-news/",
    # "https://www.investing.com/news/economic-indicators/",
]


def is_stocks_in_news(url, user_id, document_title, document_pre_text):
    headers = {"User-Agent": generate_user_agent()}
    logger.debug(f"Generate user agent: {headers}")

    try:
        stocks_info = process_stocks(create_connection(), user_id)
        tickets_with_company = [
            (stock["ticker"], stock["name"]) for stock in stocks_info
        ]

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        html = response.text
        soup = bs4.BeautifulSoup(html, "html.parser")

        title_element = soup.find("h1")
        if title_element:
            title = title_element.text.strip()
            logger.info(f"Title: {title}")
        else:
            logger.warning("Title element not found.")
            title = ""

        date_element = soup.find("time")
        if date_element:
            date = date_element.text.strip()
            logger.info(f"Date: {date}")
        else:
            logger.warning("Date element not found.")
            date = ""

        paragraphs = soup.find_all("p")
        article_text = "\n".join([para.text for para in paragraphs if para.text])

        tickers = [company[0] for company in tickets_with_company]
        company_names = [company[1] for company in tickets_with_company]

        mentions = {ticker: False for ticker in tickers}
        mentions.update({name: False for name in company_names})

        for data in tickets_with_company:
            logger.info(f"Checking stock: {data[0]}, Company: {data[1]}")

        for ticker in tickers:
            if ticker in article_text:
                mentions[ticker] = True

        for name in company_names:
            if name in article_text:
                mentions[name] = True

        for entity, is_mentioned in mentions.items():
            if is_mentioned:
                logger.info(f"Mention found: {entity}")
                return True
            else:
                logger.info(f"Not found: {entity}")

    except Exception as e:
        logger.error(e)
        return False

    return False


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
                    time_difference = get_time_difference(date, timezone)

                    result_string = f"\n\n🔥 **{title}**\n\n🌊 **{about}**\n\n✨ __{article_url}__\n\n📆 __{to_local(timezone, date)}__\n\n**{time_difference}**"
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
            articles = parse_investing_news(link, "1 minutes", user_id)
            for article in articles:
                if article not in seen_articles:
                    logger.debug(f"Added to seen articles: {article}")
                    seen_articles.add(article)
                    await notify_user(user_id, article)

        logger.info("Sleeping...")
        await asyncio.sleep(3600 / 60)


def run_check_new_articles(user_id):
    asyncio.run(check_new_articles(user_id))
