import asyncio
import re
import time
from datetime import datetime, timedelta

import bs4
import requests
from user_agent import generate_user_agent

from config import app, logger
from db import db
from func import (
    convert_to_utc,
    get_time_difference,
    is_within_period,
    notify_user,
    parse_time_period,
    to_local,
)
from model.influence_core import predict_price_influence

HTML_PARSER = "html.parser"

class NewsParser:
    def __init__(self) -> None:
        self.links = [
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

    def _parse_title_and_date(self, soup):
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
        return title, date

    def _get_tickers_and_names(self, stocks_info):
        tickers = [stock["ticker"] for stock in stocks_info]
        company_names = [stock["name"] for stock in stocks_info]
        return tickers, company_names

    def _check_mentions(self, article_text, tickers, company_names):
        mentions = {ticker: False for ticker in tickers}
        mentions.update({name: False for name in company_names})
        for ticker in tickers:
            if ticker in article_text:
                mentions[ticker] = True
        for name in company_names:
            if name in article_text:
                mentions[name] = True
        return mentions

    def is_stocks_in_news(self, url, user_id):
        headers = {"User-Agent": generate_user_agent()}
        logger.debug(f"Generate user agent: {headers}")
        try:
            stocks_info = db.process_stocks(user_id)
            tickers, company_names = self._get_tickers_and_names(stocks_info)
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            html = response.text
            soup = bs4.BeautifulSoup(html, HTML_PARSER)
            title, date = self._parse_title_and_date(soup)
            paragraphs = soup.find_all("p")
            article_text = "\n".join([para.text for para in paragraphs if para.text])
            mentions = self._check_mentions(article_text, tickers, company_names)
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

    def get_news_text(self, url):
        headers = {"User-Agent": generate_user_agent()}
        logger.debug(f"Generate user agent: {headers}")

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            html = response.text
            soup = bs4.BeautifulSoup(html, HTML_PARSER)

            paragraphs = soup.find_all("p")
            article_text = "\n".join([para.text for para in paragraphs if para.text])

            logger.debug(article_text)
            return article_text

        except Exception as e:
            logger.error(e)
            return ""

    def _get_timezone(self, user_id):
        timezone_info = db.get_city_from_db(user_id)
        if isinstance(timezone_info, tuple):
            return timezone_info[0]
        return timezone_info

    def _parse_article(self, article, seen_articles, period, user_id, timezone):
        try:
            title_tag = article.find("a", {"data-test": "article-title-link"})
            title = title_tag.text.strip() if title_tag else "title not found"
            date_tag = article.find("time", {"data-test": "article-publish-date"})
            date = date_tag["datetime"].strip() if date_tag else "date not found"
            article_url = title_tag["href"].strip() if title_tag else "link not found"
            about_tag = article.find("p", {"data-test": "article-description"})
            about = about_tag.text.strip() if about_tag else "about not found"
            logger.debug(f"Parsing {article_url} - {title}")
            unique_identifier = (title, article_url)
            if unique_identifier in seen_articles:
                return None
            if not is_within_period(date, period, user_id):
                return None
            seen_articles.add(unique_identifier)
            text = self.get_news_text(article_url)
            influence = predict_price_influence(text)
            result_string = f"\n\n🔥 **{title}**\n────────────────────────────\n✨ {influence}\n\n🌊 **{about}**\n────────────────────────────\n__{article_url}__\n\n📆 __{to_local(timezone, date)}__"
            logger.debug(f"Adding {article_url} - {title} to results")
            return result_string
        except Exception as e:
            logger.error(f"Error processing article: {e}")
            return None

    def parse_investing_news(self, url, period, user_id):
        """Investing.com parser."""
        headers = {"User-Agent": generate_user_agent()}
        logger.debug(f"Generate user agent: {headers}")
        try:
            timezone = self._get_timezone(user_id)
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            html = response.text
            soup = bs4.BeautifulSoup(html, HTML_PARSER)
            articles = soup.findAll("article", {"data-test": "article-item"})
            results = []
            seen_articles = set()
            for article in articles:
                result = self._parse_article(article, seen_articles, period, user_id, timezone)
                if result:
                    results.append(result)
            return results
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching news: {e}")
            return []

    def start_parsing(self, period, user_id):
        results = []

        for link in self.links:
            logger.info(f"Parsing: {link}")
            logger.debug(period)
            results += self.parse_investing_news(link, period, user_id)

        return results

    async def check_new_articles(self, user_id):
        seen_articles = set()

        while True:
            for link in self.links:
                logger.info("Parsing: " + link)
                articles = self.parse_investing_news(link, "2 minutes", user_id)
                for article in articles:
                    if article not in seen_articles:
                        await notify_user(user_id, article)

                        logger.debug(f"Added to seen articles: {article}")
                        seen_articles.add(article)

            logger.info("Sleeping...")
            await asyncio.sleep(120)


def run_check_new_articles(user_id):
    parser = NewsParser()
    asyncio.run(parser.check_new_articles(user_id))
