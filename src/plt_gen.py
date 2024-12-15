import matplotlib.pyplot as plt
import numpy as np
import yfinance as yf
from keras.models import load_model

from config import logger


def create_plt_price(ticker, user_id):
    try:
        period = "5d"
        interval = "1h"

        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            threads=True,
            prepost=True,
        )

        plt.figure(figsize=(20, 15))
        plt.plot(
            data["Adj Close"],
            label="Adjusted Close Price",
            marker="o",
            color="blue",
            linestyle="-",
            linewidth=2,
            markersize=5,
        )

        max_price = data["Adj Close"].max()
        min_price = data["Adj Close"].min()
        max_date = data["Adj Close"].idxmax()
        min_date = data["Adj Close"].idxmin()

        for i, price in enumerate(data["Adj Close"]):
            if i % 2 == 0:
                plt.text(
                    data.index[i],
                    price + 1,
                    f"{price:.1f}",
                    fontsize=8,
                    ha="center",
                    va="top",
                )
                plt.plot(
                    [data.index[i], data.index[i]],
                    [price, price + 1],
                    color="black",
                    linestyle="--",
                    linewidth=0.5,
                )

        plt.annotate(
            f"Max: {max_price:.2f}",
            xy=(max_date, max_price),
            xytext=(max_date, max_price + 5),
            arrowprops=dict(
                facecolor="black",
            ),
            fontsize=10,
        )
        plt.annotate(
            f"Min: {min_price:.2f}",
            xy=(min_date, min_price),
            xytext=(min_date, min_price - 5),
            arrowprops=dict(
                facecolor="black",
            ),
            fontsize=10,
        )

        plt.title(
            f"{ticker} Price Over the {period} with interval {interval}", fontsize=16
        )
        plt.xlabel("Date", fontsize=14)
        plt.ylabel("Price (USD)", fontsize=14)
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(
            visible=True,
            linestyle="--",
        )

        plt.axhline(y=max_price, color="red", linestyle="--", label="Resistance")
        plt.axhline(y=min_price, color="green", linestyle="--", label="Support")

        plt.legend()
        plt.tight_layout()
        plt.savefig("stock_price_chart.png")
        plt.close()

        image_path = "stock_price_chart.png"

        return image_path
    except Exception as e:
        logger.error(f"Error in create_plt_price: {e}")
        return None

