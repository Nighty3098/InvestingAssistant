import os
from datetime import datetime, timedelta

import joblib
import matplotlib.pyplot as plt
import numpy as np
import yfinance as yf
from keras.models import load_model


class StockPredictor:
    def __init__(self):
        self.model_path = os.path.join(
            os.getcwd(), "IPSA_MODEL", "src", "stock_model.keras"
        )
        self.scaler_path = os.path.join(os.getcwd(), "IPSA_MODEL", "src", "scaler.save")

        self.model = load_model(self.model_path)
        self.scaler = joblib.load(self.scaler_path)

    def predict_price(self, ticker):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        # Загружаем данные с Yahoo Finance
        data = yf.download(
            ticker,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
        )

        # Проверяем наличие достаточного количества данных
        if len(data) < 60:
            raise ValueError("Not enough data to make a prediction.")

        # Используем последние 60 дней всех признаков
        last_60_days = data[
            ["Open", "Close", "High", "Low", "Adj Close", "Volume"]
        ].values[-60:]

        # Масштабируем данные
        last_60_days_scaled = self.scaler.transform(last_60_days)

        # Подготовка данных для модели
        X_test = []
        X_test.append(last_60_days_scaled)
        X_test = np.array(X_test)
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], X_test.shape[2]))

        # Предсказание цены
        predicted_price = self.model.predict(X_test)

        # Создаем массив для обратного преобразования с правильной формой
        last_day_features = last_60_days_scaled[-1].copy()  # Копируем последний день
        last_day_features[1] = predicted_price[0][
            0
        ]  # Заменяем цену закрытия на предсказанную

        # Выполняем обратное преобразование
        predicted_price_unscaled = self.scaler.inverse_transform(
            np.array([last_day_features])
        )

        return predicted_price_unscaled[0][1]  # Вернем предсказанную цену закрытия

    def analyze(self, ticker):
        predicted_price = self.predict_price(ticker)

        current_price = yf.download(ticker, period="1d")["Close"][-1]

        message = f"Predicted price for {ticker} next month: {predicted_price:.2f}$\nCurrent price: {current_price:.2f}$\n"

        if predicted_price > current_price:
            message += "Advice: Buy"
        elif predicted_price < current_price:
            message += "Advice: Sell"
        else:
            message += "Advice: Hold"

        return message

    def predict_plt(self, ticker):
        # Получаем предсказанную цену на следующий месяц
        predicted_price = self.predict_price(
            ticker
        )  # Это одно значение, предполагаем, что это цена через месяц
        historical_data = yf.download(ticker, period="6mo")

        # Определяем границы прогноза (например, ±5% от предсказанной цены)
        min_forecast = predicted_price * 0.95  # Минимум на 5% ниже
        max_forecast = predicted_price * 1.05  # Максимум на 5% выше

        # Создаем график
        plt.figure(figsize=(14, 7))

        # Исторические цены
        plt.plot(
            historical_data.index,
            historical_data["Open"],
            label="Historical Open Price",
            color="blue",
        )

        plt.plot(
            historical_data.index,
            historical_data["Close"],
            label="Historical Close Price",
            color="red",
        )

        # Предсказанная цена (на следующий месяц)
        future_dates = [
            historical_data.index[-1] + timedelta(days=i) for i in range(1, 31)
        ]
        predicted_prices = [predicted_price] * len(
            future_dates
        )  # Предполагаем, что цена остается постоянной на весь месяц

        plt.plot(
            future_dates,
            predicted_prices,
            color="orange",
            label="Predicted Price",
            linestyle="--",
        )

        # Отмечаем минимумы и максимумы
        plt.scatter(
            future_dates[0],
            min_forecast,
            color="purple",
            label="Min Forecast",
            zorder=5,
        )
        plt.scatter(
            future_dates[0], max_forecast, color="gold", label="Max Forecast", zorder=5
        )

        # Границы прогноза
        plt.axhline(
            y=min_forecast,
            color="purple",
            linestyle="--",
            label="Min Forecast Boundary",
        )
        plt.axhline(
            y=max_forecast, color="gold", linestyle="--", label="Max Forecast Boundary"
        )

        # Подписываем цены на соответствующих точках
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

        # Подписываем прогнозируемую цену
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

        plt.axhline(
            y=historical_data["Close"][-1],
            color="green",
            linestyle="--",
            label="Current Price",
        )

        plt.legend()

        # Сохранение графика
        plt.savefig(f"{ticker}_price_prediction.png", dpi=1000)

        # Показать график
        plt.show()

        plt.close()

        return f"{ticker}_price_prediction.png"


if __name__ == "__main__":
    stock_predictor = StockPredictor()
    print(stock_predictor.analyze("TSLA"))
    stock_predictor.predict_plt("TSLA")
