import os
from datetime import datetime, timedelta

import joblib
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf  # Импортируем TensorFlow для управления сессиями
import yfinance as yf
from keras.models import load_model


class StockPredictor:
    def __init__(self):
        self.model_path = os.path.join(
            os.getcwd(), "IPSA_MODEL", "price", "stock_model.keras"
        )
        self.scaler_path = os.path.join(
            os.getcwd(), "IPSA_MODEL", "price", "scaler.save"
        )

        self.model = load_model(self.model_path)
        self.scaler = joblib.load(self.scaler_path)

    def predict_price(self, ticker):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        data = yf.download(
            ticker,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
        )

        last_365_days = data[
            ["Open", "Close", "High", "Low", "Adj Close", "Volume"]
        ].values[-365:]

        # Масштабируем данные
        last_365_days_scaled = self.scaler.transform(last_365_days)

        # Подготовка данных для модели
        X_test = []
        X_test.append(last_365_days_scaled)
        X_test = np.array(X_test)
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], X_test.shape[2]))

        # Предсказание вероятности
        predicted_probabilities = self.model.predict(X_test)

        # Освобождаем память после предсказания
        tf.keras.backend.clear_session()

        # Определяем предсказанную цену на основе вероятности
        predicted_price = last_365_days[-1, 1] * (1 + (predicted_probabilities[0][0] - 0.5) * 0.1)  # Примерный расчет

        return predicted_price, predicted_probabilities[0][0]  # Вернем предсказанную цену и вероятность

    def analyze(self, ticker, threshold=0.05):
        predicted_price, predicted_probability = self.predict_price(ticker)

        current_price_data = yf.download(ticker, period="1d")["Close"]

        if current_price_data.empty:
            print(f"No current price data found for ticker: {ticker}")
            return None

        current_price = current_price_data.iloc[-1]

        if isinstance(current_price, pd.Series):
            current_price = current_price.iloc[0]

        # Ensure both prices are floats
        current_price = float(current_price)
        predicted_price = float(predicted_price)

        # Form the message
        message = f"Predicted price for {ticker} next month: {predicted_price:.2f}$\nCurrent price: {current_price:.2f}$\n"

        print(f"Probability of price increase: {predicted_probability:.2f}")

        price_change_percentage = (predicted_price - current_price) / current_price

        message += f"────────────────────────────\nExpected price change: {price_change_percentage * 100:.2f}%\n"

        if price_change_percentage > threshold:
            message += "Advice: Buy"
        elif price_change_percentage < -threshold:
            message += "Advice: Sell"
        else:
            message += "Advice: Wait"
        return message

    def predict_plt(self, ticker, user_id):
        predicted_price, predicted_probability = self.predict_price(ticker)

        historical_data = yf.download(ticker, period="6mo")

        if historical_data.empty:
            print(f"No historical data found for ticker: {ticker}")
            return None

        # Определяем границы прогноза (например, ±5% от предсказанной цены)
        min_forecast = predicted_price * 0.95  # Минимум на 5% ниже
        max_forecast = predicted_price * 1.05  # Максимум на 5% выше

        plt.figure(figsize=(14, 7))

        plt.plot(
            historical_data.index,
            historical_data["Open"],
            label="Historical Open Price",
            color="blue",
            alpha=0.6,  # Уменьшаем непрозрачность для экономии памяти
        )

        plt.plot(
            historical_data.index,
            historical_data["Close"],
            label="Historical Close Price",
            color="red",
            alpha=0.6,  # Уменьшаем непрозрачность для экономии памяти
        )

        future_dates = [
            historical_data.index[-1] + timedelta(days=i + 30) for i in range(1, 31)
        ]

        predicted_prices = [predicted_price] * len(future_dates)

        plt.plot(
            future_dates,
            predicted_prices,
            color="orange",
            label="Predicted Price",
            linestyle="--",
            alpha=0.8,  # Уменьшаем непрозрачность для экономии памяти
        )

        plt.scatter(
            future_dates[0],
            min_forecast,
            color="purple",
            label="Min Forecast",
            zorder=5,
            s=50,  # Увеличиваем размер точки для лучшей видимости
        )

        plt.scatter(
            future_dates[0],
            max_forecast,
            color="gold",
            label="Max Forecast",
            zorder=5,
            s=50,  # Увеличиваем размер точки для лучшей видимости
        )

        plt.axhline(
            y=min_forecast,
            color="purple",
            linestyle="--",
            label="Min Forecast Boundary",
        )
        plt.axhline(
            y=max_forecast, color="gold", linestyle="--", label="Max Forecast Boundary"
        )

        plt.text(
            future_dates[0],
            min_forecast + 2,
            f"{min_forecast:.2f}",
            fontsize=10,
            color="purple",
        )
        plt.text(
            future_dates[0],
            max_forecast + 2,
            f"{max_forecast:.2f}",
            fontsize=10,
            color="gold",
        )

        plt.scatter(
            future_dates[0],
            predicted_price,
            color="red",
            label="Predicted Price Point",
            zorder=5,
        )
        plt.text(
            future_dates[0],
            predicted_price + 2,
            f"{predicted_price:.2f}",
            fontsize=10,
            color="red",
        )

        plt.title(f"Price Prediction for {ticker}")
        plt.xlabel("Date")
        plt.ylabel("Price")

        # Ensure single value
        current_price = float(historical_data["Close"].iloc[-1])

        plt.axhline(
            y=current_price,
            color="green",
            linestyle="--",
            label="Current Price",
        )

        filename = os.path.join(
            os.getcwd(), "client_data", f"stock_plot_predict_{user_id}_{ticker}.png"
        )

        plt.axis("on")
        plt.legend()
        plt.savefig(filename)

        plt.close()

        return filename


if __name__ == "__main__":
    stock_predictor = StockPredictor()
    print(stock_predictor.analyze("SBUX", 1))
    stock_predictor.predict_plt("SBUX", 1)
