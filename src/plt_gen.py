import os

import matplotlib.pyplot as plt
import mplfinance as mpf
import yfinance as yf


def create_candle_price(stock_index, user_id):
    data = yf.download(stock_index, period="5d", interval="1h")

    if data.empty:
        print("Нет данных для указанного индекса.")
        return

    mpf.plot(
        data,
        type="candle",
        style="charles",
        title=f"{stock_index} - Price Chart",
        ylabel="Price (USD)",
        volume=False,
        savefig=os.path.join(os.getcwd(), "stock_candlestick.png"),
        figsize=(14, 7),
    )

    return os.path.join(os.getcwd(), "stock_candlestick.png")


def create_plt_price(stock_index, user_id):
    data = yf.download(stock_index, period="5d", interval="1h")

    if data.empty:
        print("Нет данных для указанного индекса.")
        return

    plt.figure(figsize=(14, 7))
    plt.plot(data.index, data["Open"], label="Open Price", color="red")

    for i in range(len(data)):
        plt.text(
            data.index[i],
            data["Open"][i] + 1,
            f"{data['Open'][i]:.2f}",
            fontsize=8,
            ha="center",
            va="bottom",
            color="black",
        )
        plt.plot(
            [
                data.index[i],
                data.index[i],
            ],
            [
                data["Open"][i],
                data["Open"][i] + 0.6,
            ],
            color="black",
            linestyle="--",
            linewidth=0.5,
        )

    plt.title(f"{stock_index} - Open Price")
    plt.xlabel("Date")
    plt.ylabel("Price")

    plt.grid()
    plt.legend()

    plt.plot(data.index, data["Close"], label="Close Price", color="orange")

    plt.title(f"{stock_index} - Close Price")
    plt.xlabel("Date")
    plt.ylabel("Price")

    plt.grid("on")
    plt.legend()

    path = os.path.join(os.getcwd(), "stock.png")

    plt.tight_layout()
    plt.savefig(path)

    return path


if __name__ == "__main__":
    create_plt_price("AAPL", "0")
    create_candle_price("AAPL", "0")
