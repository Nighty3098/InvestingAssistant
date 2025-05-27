import datetime
import matplotlib.pyplot as plt
import yfinance as yf
import os

def create_plt_price(stock_index, user_id):
    data = yf.download(stock_index, period="5d", interval="1h")

    if data.empty:
        return

    current_price = float(data["Close"].iloc[-1])

    min_forecast = current_price * 0.95
    max_forecast = current_price * 1.05

    plt.figure(figsize=(10, 6))

    plt.plot(data.index, data["Open"], label="Open Price", color="blue")
    plt.plot(data.index, data["Close"], label="Close Price", color="red")

    plt.axhline(y=min_forecast, color="purple", linestyle="--", label="Min Forecast")
    plt.axhline(y=max_forecast, color="gold", linestyle="--", label="Max Forecast")

    plt.axhline(y=current_price, color="green", linestyle="--", label="Current Price")

    plt.text(data.index[-1], min_forecast + 2, f"{min_forecast:.2f}", fontsize=10, color="purple")
    plt.text(data.index[-1], max_forecast + 2, f"{max_forecast:.2f}", fontsize=10, color="gold")
    
    plt.text(data.index[-1], current_price + 2, f"{current_price:.2f}", fontsize=10, color="green")

    plt.title(f"Stock Prices for {stock_index} Over Last 5 Days")
    plt.xlabel("Date")
    plt.ylabel("Price")
    
    plt.xticks(rotation=45)
    
    plt.legend()
    
    filename = os.path.join(os.getcwd(), "client_data", f"stock_plot_{user_id}_{stock_index}.png")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

    return filename

if __name__ == "__main__":
    create_plt_price("NVDA", 1)
